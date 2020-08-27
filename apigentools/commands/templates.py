# Unless explicitly stated otherwise all files in this repository are licensed
# under the 3-clause BSD style license (see LICENSE).
# This product includes software developed at Datadog (https://www.datadoghq.com/).
# Copyright 2019-Present Datadog, Inc.
import contextlib
import glob
import logging
import os
import shutil
import subprocess
import tempfile
import time

import click

from apigentools.commands.command import Command, run_command_with_config
from apigentools.config import (
    OpenapiGitTemplatesConfig,
    OpenapiJarTemplatesConfig,
    DirectoryTemplatesConfig,
)
from apigentools.constants import (
    COMMAND_SYSTEM_KEY,
    OPENAPI_GENERATOR_GIT,
    SPEC_REPO_TEMPLATES_DIR,
)
from apigentools.utils import run_command

log = logging.getLogger(__name__)


@click.command()
@click.pass_context
def templates(ctx, **kwargs):
    """Get upstream templates and apply downstream patches"""
    run_command_with_config(TemplatesCommand, ctx, **kwargs)


class TemplatesCommand(Command):
    @contextlib.contextmanager
    def create_container(self, lc, spec_version):
        image = lc.container_opts_for(spec_version).image
        cn = "apigentools-created-container-{}".format(time.time())
        run_command(["docker", "create", "--name", cn, image])
        yield cn
        run_command(["docker", "rm", cn])

    def templates_for_language_spec_version(self, lc, spec_version):
        # TODO: select directory specified by "templates_dir" in "templates.source"
        # *before* applying patches
        templates_cfg = lc.templates_config_for(spec_version)
        if templates_cfg:
            log.info(
                "Obtaining upstream templates for %s/%s ...", lc.language, spec_version
            )
        else:
            log.info(
                "No templates configured for %s/%s, skipping", lc.language, spec_version
            )
            return 0

        from_container = not templates_cfg.source.system
        source_type = templates_cfg.source.type
        with tempfile.TemporaryDirectory() as td:
            patch_in = copy_from = td
            image = lc.container_opts_for(spec_version).image
            if isinstance(templates_cfg.source, OpenapiJarTemplatesConfig):
                jar_path = templates_cfg.source.jar_path
                if from_container:
                    log.info("Extracting openapi-generator jar from image %s", image)
                    new_jar_path = os.path.join(td, "openapi-generator.jar")
                    with self.create_container(lc, spec_version) as container:
                        run_command(
                            [
                                "docker",
                                "cp",
                                "{}:{}".format(container, jar_path),
                                new_jar_path,
                            ]
                        )
                    jar_path = new_jar_path
                run_command(["unzip", "-q", jar_path, "-d", td])
            elif isinstance(templates_cfg.source, DirectoryTemplatesConfig):
                lang_dir = os.path.join(
                    templates_cfg.source.directory_path,
                    templates_cfg.source.templates_dir,
                )
                output_dir = os.path.join(
                    td,
                    templates_cfg.source.templates_dir,
                )
                if from_container:
                    log.info("Extracting templates directory from image %s", image)
                    with self.create_container(lc, spec_version) as container:
                        run_command(
                            [
                                "docker",
                                "cp",
                                "{}:{}".format(container, lang_dir),
                                output_dir,
                            ]
                        )
                else:
                    if not os.path.exists(lang_dir):
                        log.error(
                            "Directory %s doesn't contain '%s' subdirectory with templates",
                            templates_cfg.source.directory_path,
                            templates_cfg.source.templates_dir,
                        )
                        return 1
                    shutil.copytree(
                        lang_dir,
                        os.path.join(td, templates_cfg.source.templates_dir),
                    )
            elif isinstance(templates_cfg.source, OpenapiGitTemplatesConfig):
                if from_container:
                    log.error(
                        "Templates with source 'openapi-git' must be used with '%s: true'",
                        COMMAND_SYSTEM_KEY,
                    )
                patch_in = copy_from = os.path.join(
                    td, "modules", "openapi-generator", "src", "main", "resources"
                )
                run_command(["git", "clone", OPENAPI_GENERATOR_GIT, td])
                run_command(
                    [
                        "git",
                        "-C",
                        td,
                        "checkout",
                        templates_cfg.source.git_committish,
                    ]
                )
            else:
                log.error("Unknown templates source type {}".format(source_type))
                return 1

            patches = templates_cfg.patches
            if patches:
                log.info("Applying patches to upstream templates ...")
                for p in patches:
                    try:
                        run_command(
                            [
                                "patch",
                                "--fuzz",
                                "0",
                                "--no-backup-if-mismatch",
                                "-p1",
                                "-i",
                                os.path.abspath(p),
                                "-d",
                                patch_in,
                            ]
                        )
                    except subprocess.CalledProcessError:
                        # at this point, the stdout/stderr of the process have been printed by
                        # `run_command`, so the user should have sufficient info to about what went wrong
                        log.error(
                            "Failed to apply patch %s, exiting as templates can't be processed",
                            p,
                        )
                        return 1

            # copy the processed templates from the temporary dir to templates dir
            outdir = os.path.join(SPEC_REPO_TEMPLATES_DIR, lc.language, spec_version)
            if os.path.exists(outdir):
                shutil.rmtree(outdir)
            shutil.copytree(
                os.path.join(copy_from, templates_cfg.source.templates_dir),
                outdir,
            )
        return 0

    def run(self):
        result = 0
        for language, version in self.yield_lang_version():
            lc = self.config.get_language_config(language)
            result += self.templates_for_language_spec_version(lc, version)
        return result

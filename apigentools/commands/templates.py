# Unless explicitly stated otherwise all files in this repository are licensed
# under the 3-clause BSD style license (see LICENSE).
# This product includes software developed at Datadog (https://www.datadoghq.com/).
# Copyright 2019-Present Datadog, Inc.
import glob
import logging
import os
import shutil
import subprocess
import tempfile
import time

import click

from apigentools import constants
from apigentools.commands.command import Command
from apigentools.config import Config
from apigentools.constants import OPENAPI_GENERATOR_GIT
from apigentools.utils import run_command, change_cwd, env_or_val

log = logging.getLogger(__name__)


@click.command()
@click.option(
    "-T",
    "--templates-output-dir",
    default=env_or_val("APIGENTOOLS_TEMPLATES_DIR", constants.DEFAULT_TEMPLATES_DIR),
    help="Path to directory where to put processed upstream templates (default: {})".format(
        constants.DEFAULT_TEMPLATES_DIR
    ),
)
@click.pass_context
def templates(ctx, **kwargs):
    """Get upstream templates and apply downstream patches"""
    ctx.obj.update(kwargs)
    cmd = TemplatesCommand({}, ctx.obj)
    with change_cwd(ctx.obj.get("spec_repo_dir")):
        cmd.config = Config.from_file(
            os.path.join(ctx.obj.get("config_dir"), constants.DEFAULT_CONFIG_FILE)
        )
        ctx.exit(cmd.run())


class TemplatesCommand(Command):
    def templates_for_language_spec_version(self, lc, spec_version):
        templates_cfg = lc.templates_config_for(spec_version)
        if not templates_cfg:
            log.info(
                "No templates configured for {}/{}, skipping", lc.language, spec_version
            )
            return 0
        with tempfile.TemporaryDirectory() as td:
            log.info("Obtaining upstream templates ...")
            patch_in = copy_from = td
            if templates_cfg["source"]["type"] == "openapi-jar":
                image = lc.container_opts_for(spec_version)["image"]
                log.info("Extracting openapi-generator jar from image {}".format(image))
                jar_path = templates_cfg["source"]["jar_path"]
                # TODO: properly create temp directory
                # TODO: properly remove created container
                cn = "very-unique-container-name-{}".format(time.time())
                run_command(["docker", "create", "--name", cn, image])
                run_command(
                    [
                        "docker",
                        "cp",
                        "{}:{}".format(cn, jar_path),
                        "/tmp/openapi-generator.jar",
                    ]
                )
                jar_path = "/tmp/openapi-generator.jar"
                run_command(["unzip", "-q", jar_path, "-d", td])
            elif templates_cfg["source"]["type"] == "local-dir":
                # TODO
                """
                for lang in self.config.languages:
                    lang_upstream_templates_dir = self.config.get_language_config(
                        lang
                    ).upstream_templates_dir
                    local_lang_dir = os.path.join(
                        self.args.get("local_path"), lang_upstream_templates_dir
                    )
                    if not os.path.exists(local_lang_dir):
                        log.error(
                            "Directory %s doesn't contain '%s' directory with templates. "
                            + "Make sure %s contains directories with templates for all languages",
                            self.args.get("templates_source"),
                            lang_upstream_templates_dir,
                            self.args.get("local_path"),
                            )
                        return 1
                    shutil.copytree(
                        local_lang_dir, os.path.join(td, lang_upstream_templates_dir)
                    )
                """
            else:
                # TODO
                """
                patch_in = copy_from = os.path.join(
                    td, "modules", "openapi-generator", "src", "main", "resources"
                )
                run_command(["git", "clone", OPENAPI_GENERATOR_GIT, td])
                run_command(
                    ["git", "-C", td, "checkout", self.args.get("git_committish")]
                )
                """

            patches = templates_cfg.get("patches")
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
            outdir = os.path.join(
                self.args.get("templates_output_dir"), lc.language, spec_version
            )
            if os.path.exists(outdir):
                shutil.rmtree(outdir)
            shutil.copytree(
                os.path.join(
                    copy_from, templates_cfg["source"].get("templates_dir", "")
                ),
                outdir,
            )
        return 0

    def run(self):
        result = 0
        for language, version in self.yield_lang_version():
            lc = self.config.get_language_config(language)
            result += self.templates_for_language_spec_version(lc, version)
        return result

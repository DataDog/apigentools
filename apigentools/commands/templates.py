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

import click

from apigentools import constants
from apigentools.commands.command import Command
from apigentools.config import Config
from apigentools.constants import OPENAPI_GENERATOR_GIT
from apigentools.utils import run_command, change_cwd, env_or_val

log = logging.getLogger(__name__)


@click.group()
@click.option(
    "-o",
    "--output-dir",
    default=env_or_val("APIGENTOOLS_TEMPLATES_DIR", constants.DEFAULT_TEMPLATES_DIR),
    help="Path to directory where to put processed upstream templates (default: {})".format(
        constants.DEFAULT_TEMPLATES_DIR
    ),
)
@click.option(
    "-p",
    "--template-patches-dir",
    default=env_or_val(
        "APIGENTOOLS_TEMPLATE_PATCHES_DIR", constants.DEFAULT_TEMPLATE_PATCHES_DIR
    ),
    help="Directory with patches for upstream templates (default: '{}')".format(
        constants.DEFAULT_TEMPLATE_PATCHES_DIR
    ),
)
@click.pass_obj
def templates(ctx_obj, **kwargs):
    """Get upstream templates and apply downstream patches"""
    ctx_obj.update(kwargs)


@templates.command()
@click.option("-u", "--repo-url", default=constants.OPENAPI_GENERATOR_GIT)
@click.option("--git-committish", default="master", nargs=1)
@click.pass_obj
def openapi_git(ctx_obj, **kwargs):
    """Pull templates from the git reposotiry specified by --repo-url and --git-committish"""
    ctx_obj.update(kwargs)
    ctx_obj["templates_source"] = "openapi-git"
    cmd = TemplatesCommand({}, ctx_obj)
    with change_cwd(ctx_obj.get("spec_repo_dir")):
        cmd.config = Config.from_file(
            os.path.join(ctx_obj.get("config_dir"), constants.DEFAULT_CONFIG_FILE)
        )
        cmd.run()



@templates.command()
@click.argument("local-path")
@click.pass_obj
def local_dir(ctx_obj, **kwargs):
    """Pull templates from the specified local-path"""
    ctx_obj.update(kwargs)
    ctx_obj["templates_source"] = "local-dir"
    cmd = TemplatesCommand({}, ctx_obj)

    with change_cwd(ctx_obj.get("spec_repo_dir")):
        cmd.config = Config.from_file(
            os.path.join(ctx_obj.get("config_dir"), constants.DEFAULT_CONFIG_FILE)
        )
        cmd.run()


@templates.command()
@click.argument(
    "jar-path", default=env_or_val("APIGENTOOLS_OPENAPI_JAR", constants.OPENAPI_JAR)
)
@click.pass_obj
def openapi_jar(ctx_obj, **kwargs):
    """Pull templates from the openapi-jar specified by jar-path"""
    ctx_obj.update(kwargs)
    ctx_obj["templates_source"] = "openapi-jar"
    cmd = TemplatesCommand({}, ctx_obj)
    with change_cwd(ctx_obj.get("spec_repo_dir")):
        cmd.config = Config.from_file(
            os.path.join(ctx_obj.get("config_dir"), constants.DEFAULT_CONFIG_FILE)
        )
        cmd.run()


class TemplatesCommand(Command):
    def run(self):
        with tempfile.TemporaryDirectory() as td:
            log.info("Obtaining upstream templates ...")
            patch_in = copy_from = td
            if self.args.get("templates_source") == "openapi-jar":
                run_command(["unzip", "-q", self.args.get("repo_url"), "-d", td])
            elif self.args.get("templates_source") == "local-dir":
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
            else:
                patch_in = copy_from = os.path.join(
                    td, "modules", "openapi-generator", "src", "main", "resources"
                )
                run_command(["git", "clone", OPENAPI_GENERATOR_GIT, td])
                run_command(
                    ["git", "-C", td, "checkout", self.args.get("git_committish")]
                )

            if os.path.exists(self.args.get("template_patches_dir")):
                log.info("Applying patches to upstream templates ...")
                patches = glob.glob(
                    os.path.join(self.args.get("template_patches_dir"), "*.patch")
                )
                for p in sorted(patches):
                    try:
                        run_command(
                            [
                                "patch",
                                "--fuzz",
                                "0",
                                "--no-backup-if-mismatch",
                                "-p1",
                                "-i",
                                os.path.abspath(
                                    os.path.join(
                                        self.args.get("template_patches_dir"),
                                        os.path.basename(p),
                                    )
                                ),
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
            languages = self.args.get("languages") or self.config.languages
            for lang in languages:
                upstream_templatedir = self.config.get_language_config(
                    lang
                ).upstream_templates_dir
                outlang_dir = os.path.join(self.args.get("output_dir"), lang)
                if os.path.exists(outlang_dir):
                    shutil.rmtree(outlang_dir)
                shutil.copytree(
                    os.path.join(copy_from, upstream_templatedir), outlang_dir
                )
        return 0

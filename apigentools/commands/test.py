# Unless explicitly stated otherwise all files in this repository are licensed
# under the 3-clause BSD style license (see LICENSE).
# This product includes software developed at Datadog (https://www.datadoghq.com/).
# Copyright 2019-Present Datadog, Inc.
import logging
import os
import subprocess

import click

from apigentools import constants
from apigentools.commands.command import Command
from apigentools.config import Config
from apigentools.constants import REDACTED_OUT_SECRET
from apigentools.utils import run_command, change_cwd, env_or_val

log = logging.getLogger(__name__)


@click.command()
@click.option("--no-cache", is_flag=True,
              default=env_or_val("APIGENTOOLS_TEST_BUILD_NO_CACHE", False, __type=bool),
              help="Build test image with --no-cache option",
              )
@click.option("--container-env", nargs=1,
              default=env_or_val("APIGENTOOLS_CONTAINER_ENV", [], __type=list),
              help="Additional environment variables to pass to containers running the tests, "
                   + "for example `--container-env API_KEY=123 OTHER_KEY=234`. Note that apigentools "
                   + "contains additional logic to treat these values as sensitive and avoid logging "
                   + "them during runtime. (NOTE: if the testing container itself prints this value, "
                   + "it *will* be logged as part of the test output by apigentools).")
@click.option("-g", "--generated-code-dir",
              default=env_or_val("APIGENTOOLS_GENERATED_CODE_DIR", constants.DEFAULT_GENERATED_CODE_DIR),
              help="Path to directory where to save the generated source code (default: '{}')".format(
                   constants.DEFAULT_GENERATED_CODE_DIR
              ))
@click.pass_obj
def test(ctx_obj, **kwargs):
    """Run tests for generated source code"""
    ctx_obj.update(kwargs)
    cmd = TestCommand({}, ctx_obj)

    with change_cwd(ctx_obj.get('spec_repo_dir')):
        cmd.config = Config.from_file(
            os.path.join(ctx_obj.get('config_dir'), constants.DEFAULT_CONFIG_FILE)
        )
        cmd.run()


class TestCommand(Command):
    def get_test_df_name(self, lang, version):
        fname = "Dockerfile.test"
        if version is not None:
            fname += ".{}".format(version)
        return os.path.join(self.get_generated_lang_dir(lang), fname)

    def get_test_image_name(self, lang, version):
        if version is None:
            return f"apigentools-test-{lang}"
        return f"apigentools-test-{lang}-{version}"

    def build_test_image(self, df_path, img_name):
        if os.path.exists(df_path):
            build = [
                "docker",
                "build",
                os.path.dirname(df_path),
                "-f",
                df_path,
                "-t",
                img_name,
            ]
            if self.args.get('no_cache'):
                build.append("--no-cache")
            run_command(build, combine_out_err=True)
            return img_name
        return None

    def run_test_image(self, img_name):
        log.info("Running tests: %s", img_name)
        cmd = ["docker", "run"]
        for i, ce in enumerate(self.args.get('container_env')):
            split = ce.split("=", 1)
            if len(split) != 2:
                raise ValueError(
                    "{} (passed in on position {})".format(REDACTED_OUT_SECRET, i)
                )
            cmd.append("-e")
            cmd.append({"item": "{}={}".format(split[0], split[1]), "secret": True})
        cmd.append(img_name)
        run_command(cmd, combine_out_err=True)

    def run(self):
        cmd_result = 0

        versions = self.args.get('api_versions') or self.config.spec_versions
        languages = self.args.get('languages') or self.config.languages

        for lang_name, lang_config in self.config.language_configs.items():
            # Skip any non user provided languages
            if lang_name not in languages:
                continue
            # we consider `None` version to represent the `Dockerfile.test` file (without prefix)
            for version in [None] + lang_config.spec_versions:
                spec_version_loggable = (
                    "non-version tests"
                    if version is None
                    else "spec version {}".format(version)
                )
                # Skip any non user provided versions
                if version is not None and version not in versions:
                    continue
                df_path = self.get_test_df_name(lang_name, version)
                img_name = self.get_test_image_name(lang_name, version)
                log.info(
                    "Looking up %s to test language %s, %s",
                    df_path,
                    lang_name,
                    spec_version_loggable,
                )

                # first, try building the image
                if not os.path.exists(df_path):
                    log.info("PASS: Could not find %s, skipping", df_path)
                    continue
                try:
                    img_name = self.build_test_image(df_path, img_name)
                    log.info("SUCCESS: built %s", img_name)
                except subprocess.CalledProcessError:
                    log.error(
                        "FAIL: Failed to build testing image for language %s, %s",
                        lang_name,
                        spec_version_loggable,
                    )
                    cmd_result = 1
                    continue

                # if building was successful, run the image
                try:
                    self.run_test_image(img_name)
                    log.info("SUCCESS: ran %s", img_name)
                except subprocess.CalledProcessError:
                    log.error(
                        "ERROR: Testing failed for language %s, %s",
                        lang_name,
                        spec_version_loggable,
                    )
                    cmd_result = 1
                except ValueError as e:
                    log.error(
                        "Bad container env '%s', must be in form KEY=VALUE", str(e)
                    )

        return cmd_result

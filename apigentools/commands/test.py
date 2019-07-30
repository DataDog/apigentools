# Unless explicitly stated otherwise all files in this repository are licensed
# under the 3-clause BSD style license (see LICENSE).
# This product includes software developed at Datadog (https://www.datadoghq.com/).
# Copyright 2019 Datadog, Inc.
import logging
import os
import subprocess

from apigentools.commands.command import Command
from apigentools.constants import REDACTED_OUT_SECRET
from apigentools.utils import run_command

log = logging.getLogger(__name__)


class TestCommand(Command):
    def get_test_df_name(self, lang, version):
        return os.path.join(
            self.get_generated_lang_dir(lang),
            "Dockerfile.test.{}".format(version)
        )

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
            if self.args.no_cache:
                build.append("--no-cache")
            run_command(build, combine_out_err=True)
            return img_name
        return None

    def run_test_image(self, img_name):
        log.info("Running tests: %s", img_name)
        cmd = ["docker", "run"]
        for i, ce in enumerate(self.args.container_env):
            split = ce.split("=", 1)
            if len(split) != 2:
                raise ValueError("{} (passed in on position {})".format(REDACTED_OUT_SECRET, i))
            cmd.append("-e")
            cmd.append({"item": "{}={}".format(split[0], split[1]), "secret": True})
        cmd.append(img_name)
        run_command(cmd, combine_out_err=True)

    def run(self):
        cmd_result = 0

        versions = self.args.api_versions or self.config.spec_versions
        languages = self.args.languages or self.config.languages

        for lang_name, lang_config in self.config.language_configs.items():
            # Skip any non user provided languages
            if lang_name not in languages:
                continue
            for version in lang_config.spec_versions:
                # Skip any non user provided versions
                if version not in versions:
                    continue
                df_path = self.get_test_df_name(lang_name, version)
                img_name = "apigentools-test-{lang}-{version}".format(
                    lang=lang_name, version=version
                )
                log.info(
                    "Looking up %s to test language %s, version %s",
                    df_path, lang_name, version
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
                        "FAIL: Failed to build testing image for language %s, spec version %s",
                        lang_name, version
                    )
                    cmd_result = 1
                    continue

                # if building was successful, run the image
                try:
                    self.run_test_image(img_name)
                    log.info("SUCCESS: ran %s", img_name)
                except subprocess.CalledProcessError:
                    log.error(
                        "ERROR: Testing failed for language %s, spec version %s",
                        lang_name, version
                    )
                    cmd_result =  1
                except ValueError as e:
                    log.error("Bad container env '%s', must be in form KEY=VALUE", str(e))

        return cmd_result

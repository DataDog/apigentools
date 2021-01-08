# Unless explicitly stated otherwise all files in this repository are licensed
# under the 3-clause BSD style license (see LICENSE).
# This product includes software developed at Datadog (https://www.datadoghq.com/).
# Copyright 2019-Present Datadog, Inc.
import logging
import os
import shlex
import subprocess

import click

from apigentools.commands.command import Command, run_command_with_config
from apigentools.constants import REDACTED_OUT_SECRET
from apigentools.utils import run_command, env_or_val

log = logging.getLogger(__name__)


@click.command()
@click.option(
    "--no-cache",
    is_flag=True,
    default=env_or_val("APIGENTOOLS_TEST_BUILD_NO_CACHE", False, __type=bool),
    help="Build test image with --no-cache option",
)
@click.option(
    "--container-env",
    multiple=True,
    default=env_or_val("APIGENTOOLS_CONTAINER_ENV", [], __type=list),
    help="Additional environment variables to pass to containers running the tests, "
    + "for example `--container-env API_KEY=123 --container-env OTHER_KEY=234`. Note that apigentools "
    + "contains additional logic to treat these values as sensitive and avoid logging "
    + "them during runtime. (NOTE: if the testing container itself prints this value, "
    + "it *will* be logged as part of the test output by apigentools).",
)
@click.option(
    "--docker-run-options",
    default=env_or_val("APIGENTOOLS_DOCKER_RUN_OPTIONS", None),
    help="Additional options passed to `docker run` command.",
)
@click.option(
    "--no-sensitive-output",
    is_flag=True,
    default=env_or_val("APIGENTOOLS_NO_SENSITIVE_OUTPUT", False),
    help="By default, it is considered that the environment values provided through --container-env "
    + "may contain sensitive values and the whole command and its output is therefore hidden. You "
    + "can override this behaviour by using this flag.",
)
@click.pass_context
def test(ctx, **kwargs):
    """Run tests for generated source code"""
    run_command_with_config(TestCommand, ctx, **kwargs)


class TestCommand(Command):
    def run(self):
        cmd_result = 0
        docker_run_options = shlex.split(self.args.get("docker_run_options") or "")

        for lang_name, version in self.yield_lang_version():
            language_config = self.config.get_language_config(lang_name)
            commands = language_config.test_commands_for(version)

            if not commands:
                log.info("No test commands found for %s/%s", lang_name, version)
                continue
            else:
                log.info("Running test commands for %s/%s", lang_name, version)

            env_override = {}
            for i, ce in enumerate(self.args.get("container_env")):
                split = ce.split("=", 1)
                if len(split) != 2:
                    print(self.args.get("container_env"))
                    raise ValueError(
                        "{} (passed in on position {})".format(REDACTED_OUT_SECRET, i)
                    )
                env_override[split[0]] = split[1]
            for command in commands:
                self.run_config_command(
                    command,
                    "{l}/{v}".format(l=lang_name, v=version),
                    language_config.generated_lang_version_dir_for(version),
                    language_config.chevron_vars_for(version),
                    env_override=env_override,
                    docker_run_options=docker_run_options,
                )

        return cmd_result

# Unless explicitly stated otherwise all files in this repository are licensed
# under the 3-clause BSD style license (see LICENSE).
# This product includes software developed at Datadog (https://www.datadoghq.com/).
# Copyright 2019 Datadog, Inc.
"""Manipulate OpenAPI specs and generate code using openapi-generator."""

import logging
import os

import click

from apigentools import constants

# from apigentools.commands import all_commands
from apigentools.commands.init import init
from apigentools.config import Config
from apigentools.utils import change_cwd, _set_log_level

log = logging.getLogger(__name__)


class ColonParamType(click.ParamType):
    name = "list"

    def convert(self, value, param, ctx):
        try:
            return value.split(":")
        except ValueError:
            self.fail("%s is not a valid list" % value, param, ctx)


@click.group(
    context_settings={
        "auto_envvar_prefix": "APIGENTOOLS",
        "help_option_names": ["-h", "--help"],
    },
    invoke_without_command=True,
)
@click.option(
    "--git-via-https",
    is_flag=True,
    envvar="APIGENTOOLS_GIT_VIA_HTTPS",
    help="Use HTTPS for interacting with the git repositories. " "Otherwise use SSH.",
)
@click.option(
    "--git-via-https-oauth-token",
    envvar="APIGENTOOLS_GIT_VIA_HTTPS_OAUTH_TOKEN",
    help="Insert OAuth token in the repo URL when using "
    "HTTPS for interacting with the git repositories.",
)
@click.option(
    "--git-via-https-installation-access-token",
    envvar="APIGENTOOLS_GIT_VIA_HTTPS_INSTALLATION_ACCESS_TOKEN",
    help="Insert installation access token (authenticate as Github app) "
    "in the repo URL when using HTTPS for interacting with "
    "the git repositories.",
)
@click.option(
    "-r",
    "--spec-repo-dir",
    envvar="APIGENTOOLS_SPEC_REPO_DIR",
    default=".",
    type=click.Path(file_okay=False, dir_okay=True, readable=True),
    help="Switch to this directory before doing anything else",
)
@click.option(
    "-c",
    "--config-dir",
    envvar="APIGENTOOLS_CONFIG_DIR",
    default=constants.DEFAULT_CONFIG_DIR,
    type=click.Path(file_okay=False, dir_okay=True, readable=True),
    help="Path to config directory",
)
@click.option(
    "-g",
    "--generated-code-dir",
    envvar="APIGENTOOLS_GENERATED_CODE_DIR",
    type=click.Path(file_okay=False, dir_okay=True, writable=True),
    default=constants.DEFAULT_GENERATED_CODE_DIR,
    help="Path to directory where to save the generated source code",
)
@click.option(
    "-l",
    "--languages",
    multiple=True,
    type=ColonParamType(),
    envvar="APIGENTOOLS_LANG",
    help="The language to run the specified action against. "
    "These must match what the config in the spec repo contains. "
    "Example: 'apigentools -l go -l java test' (Default: None to run all)",
)
@click.option(
    "-av",
    "--api-versions",
    multiple=True,
    envvar="APIGENTOOLS_API_VERSION",
    default=None,
    help="The API version to run the specified action against. "
    "These must match what the config in the spec repo contains. "
    "Example: 'apigentools -av v1 -av v2 test' (Default: None to run all)",
)
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    help="Whether or not to log the generation in verbose mode",
    callback=_set_log_level,
    expose_value=False,
)
@click.pass_context
def cli(ctx, **kwargs):
    """Manipulate OpenAPI specs and generate code using openapi-generator."""
    ctx.obj = kwargs
    ctx.obj["languages"] = tuple(l for ll in ctx.obj["languages"] for l in ll)
    if ctx.invoked_subcommand != "init":
        # command_class = all_commands[args.action]
        # command = command_class({}, args)
        # if args.action == "init":
        #     sys.exit(command.run())

        with change_cwd(kwargs["spec_repo_dir"]):
            ctx.obj["config"] = Config.from_file(
                os.path.join(kwargs["config_dir"], constants.DEFAULT_CONFIG_FILE)
            )
        # sys.exit(command.run())


cli.add_command(init)

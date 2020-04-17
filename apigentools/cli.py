# Unless explicitly stated otherwise all files in this repository are licensed
# under the 3-clause BSD style license (see LICENSE).
# This product includes software developed at Datadog (https://www.datadoghq.com/).
# Copyright 2019-Present Datadog, Inc.
import logging
import os

import click
from packaging import version

import apigentools
from apigentools import constants
from apigentools.commands import ALL_COMMANDS
from apigentools.config import Config
from apigentools.utils import (
    env_or_val,
    set_log,
    set_log_level,
    change_cwd,
    check_for_legacy_config,
)

log = logging.getLogger(__name__)


@click.group()
@click.option(
    "--verbose",
    default=env_or_val("APIGENTOOLS_VERBOSE", False, __type=bool),
    is_flag=True,
    help="Whether or not to log the generation in verbose mode",
)
@click.option(
    "--git-via-https",
    is_flag=True,
    default=env_or_val("APIGENTOOLS_GIT_VIA_HTTPS", False, __type=bool),
    help="Use HTTPS for interacting with the git repositories. Otherwise use SSH.",
)
@click.option(
    "--git-via-https-oauth-token",
    default=env_or_val("APIGENTOOLS_GIT_VIA_HTTPS_OAUTH_TOKEN", ""),
    help="Insert OAuth token in the repo URL when using HTTPS for interacting with the git repositories.",
)
@click.option(
    "--git-via-https-installation-access-token",
    default=env_or_val("APIGENTOOLS_GIT_VIA_HTTPS_INSTALLATION_ACCESS_TOKEN", ""),
    help="Insert installation access token (authenticate as Github app) in the repo URL when using"
    "HTTPS for interacting with the git repositories.",
)
@click.option(
    "-r",
    "--spec-repo-dir",
    default=env_or_val("APIGENTOOLS_SPEC_REPO_DIR", "."),
    help="Switch to this directory before doing anything else",
)
@click.option(
    "-l",
    "--languages",
    multiple=True,
    default=env_or_val("APIGENTOOLS_LANG", None, __type=list),
    help="The language to run the specified action against."
    "These must match what the config in the spec repo contains."
    "Ex: 'apigentools -l go -l java test' (Default: None to run all)",
)
@click.option(
    "-av",
    "--api-versions",
    multiple=True,
    default=env_or_val("APIGENTOOLS_API_VERSION", None),
    help="The API version to run the specified action against."
    "These must match what the config in the spec repo contains."
    "Ex: 'apigentools -av v1 -av v2 test' (Default: None to run all)",
)
@click.pass_context
@click.version_option()
def cli(ctx, **kwargs):
    """
    Manipulate OpenAPI specs and generate code using openapi-generator
    """
    # These global options get passed to the subcommands through the ctx object
    # since we're using click.pass_context and click.pass_obj
    ctx.obj = dict(kwargs)
    toplog = logging.getLogger(__name__.split(".")[0])
    set_log(toplog)
    check_min_version(ctx)
    if ctx.obj.get("verbose"):
        set_log_level(toplog, logging.DEBUG)


def check_min_version(click_ctx):
    with change_cwd(click_ctx.obj.get("spec_repo_dir")):
        configfile = os.path.join(
            os.path.join(constants.SPEC_REPO_CONFIG_DIR, constants.DEFAULT_CONFIG_FILE)
        )
        try:
            config = Config.from_file(configfile)
        except OSError:
            check_for_legacy_config(click_ctx, configfile)

        # Version like - "apigentools, version 0.10.1.dev27+dirty"
        min_version = config.raw_dict.get("apigentools_min_version", "0.0.0")
        actual_version = apigentools.__version__

        if version.parse(actual_version) < version.parse(min_version):
            click.echo(f"Apigentools is below {min_version}. Please upgrade to run generation and tests against latest code.", err=True)
            click_ctx.exit(1)


# Register all click sub-commands
for command in ALL_COMMANDS:
    cli.add_command(command)

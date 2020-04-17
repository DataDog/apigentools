# Unless explicitly stated otherwise all files in this repository are licensed
# under the 3-clause BSD style license (see LICENSE).
# This product includes software developed at Datadog (https://www.datadoghq.com/).
# Copyright 2020-Present Datadog, Inc.
import logging
import os

import click

from apigentools import constants
from apigentools.commands.command import Command, run_command_with_config
from apigentools.config import Config
from apigentools.utils import change_cwd, env_or_val

log = logging.getLogger(__name__)


@click.command()
@click.option(
    "-f",
    "--full-spec-file",
    default=env_or_val("APIGENTOOLS_FULL_SPEC_FILE", "full_spec.yaml"),
    help="Name of the OpenAPI full spec file to write (default: 'full_spec.yaml'). "
    + "Note that if some languages override config's spec_sections, additional "
    + "files will be generated with name pattern 'full_spec.<lang>.yaml'",
)
@click.option(
    "-L",
    "--list-languages",
    is_flag=True,
    help="List only what languages are supported",
)
@click.option(
    "-V", "--list-versions", is_flag=True, help="List only what versions are supported"
)
@click.pass_context
def config(ctx, **kwargs):
    """Displays information about the configuration for the spec being worked on, including supported languages,
    api versions, and the paths to the generated api yaml. These languages and api versions can be directly
    passed to the `--languages` and `--api-versions` flags of the supported commands."""
    run_command_with_config(ConfigCommand, ctx, **kwargs)


class ConfigCommand(Command):
    def run(self):
        # Yields tuples (language, version, spec_path)
        language_info = self.yield_lang_version_specfile()

        # Modify the returned data based on user flags
        if self.args.get("list_languages"):
            out = {lang_info[0] for lang_info in language_info}
        elif self.args.get("list_versions"):
            out = {lang_info[1] for lang_info in language_info}
        else:
            out = [lang_info for lang_info in language_info]

        click.echo(out)
        return 0

# Unless explicitly stated otherwise all files in this repository are licensed
# under the 3-clause BSD style license (see LICENSE).
# This product includes software developed at Datadog (https://www.datadoghq.com/).
# Copyright 2020-Present Datadog, Inc.
import logging
import os

import click

from apigentools import constants
from apigentools.commands.command import Command
from apigentools.config import Config
from apigentools.utils import change_cwd, env_or_val

log = logging.getLogger(__name__)


@click.command()
@click.option(
    "-s",
    "--spec-dir",
    default=env_or_val("APIGENTOOLS_SPEC_DIR", constants.DEFAULT_SPEC_DIR),
    help="Path to directory with OpenAPI specs (default: '{}')".format(
        constants.DEFAULT_SPEC_DIR
    ),
)
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
@click.pass_obj
def list_languages(ctx, **kwargs):
    """Initialize a new spec repo in the provided projectdir (will be created if it doesn't exist)"""
    ctx.update(kwargs)
    cmd = ListLanguagesCommand({}, ctx)
    with change_cwd(ctx.get("spec_repo_dir")):
        cmd.config = Config.from_file(
            os.path.join(ctx.get("config_dir"), constants.DEFAULT_CONFIG_FILE)
        )
        cmd.run()


class ListLanguagesCommand(Command):
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
        return out

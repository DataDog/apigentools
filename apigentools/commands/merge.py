# Unless explicitly stated otherwise all files in this repository are licensed
# under the 3-clause BSD style license (see LICENSE).
# This product includes software developed at Datadog (https://www.datadoghq.com/).
# Copyright 2019-Present Datadog, Inc.
import os
import logging

import click

from apigentools import config
from apigentools import constants
from apigentools.commands.command import Command, run_command_with_config
from apigentools.utils import write_full_spec, env_or_val

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
    "--filter-sections",
    help="Specify spec sections to filter out from the output",
    multiple=True,
)
@click.pass_context
def merge(ctx, **kwargs):
    """Merge OpenAPI spec"""
    run_command_with_config(MergeCommand, ctx, **kwargs)


class MergeCommand(Command):
    def _split_spec_file(self, spec_file):
        return spec_file.rsplit(constants.SPEC_REPO_SPEC_DIR, 1)[1].split(os.sep, 2)[1:]

    def run(self):
        cmd_result = 0
        fs_files = set()
        filter_sections = frozenset(self.args.get("filter_sections", ()))
        for language, version, fs_file in self.yield_lang_version_specfile():
            if fs_file in fs_files:
                continue
            fs_files.add(fs_file)

            write_full_spec(
                constants.SPEC_REPO_SPEC_DIR,
                version,
                self.config.get_language_config(language).spec_sections_for(version),
                fs_file,
                filter_sections,
            )

        return cmd_result

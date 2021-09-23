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
@click.argument("files", nargs=-1)
@click.pass_context
def validate(ctx, **kwargs):
    """Validate OpenAPI spec"""
    run_command_with_config(ValidateCommand, ctx, **kwargs)


class ValidateCommand(Command):
    def validate_spec(self, fs_path, language, version):
        log_string = (
            "of general spec"
            if language is None
            else "of spec for {}/{}".format(language, version)
        )
        log_string += " ({})".format(fs_path)
        lc = self.config.get_language_config(language)
        vcs = lc.validation_commands_for(version)
        if vcs:
            log.info("Running validation commands for %s/%s", language, version)
        else:
            log.info("No validation commands specified for %s/%s", language, version)

        for cmd in vcs:
            self.run_config_command(
                cmd,
                "validation",
                chevron_vars=lc.chevron_vars_for(
                    version, fs_path, config.PathRelativeTo.SPEC_REPO_DIR
                ),
            )
        log.info("Validation %s for API version %s successful", log_string, version)

    def _split_spec_file(self, spec_file):
        if not spec_file.startswith(constants.SPEC_REPO_SPEC_DIR):
            raise ValueError(spec_file)

        result = spec_file.rsplit(constants.SPEC_REPO_SPEC_DIR, 1)[1].split(os.sep, 2)[
            1:
        ]
        if len(result) != 2:
            raise IndexError(result)
        return result

    def run(self):
        files = self.args.get("files", [])
        try:
            files = [self._split_spec_file(spec_file) for spec_file in files]
        except (ValueError, IndexError):
            # If we can't parse the files as spec, it's probably that the
            # config changed, so let's do a complete validation
            files = []
        # Keep track of the spec files validated
        validated_files = set()
        cmd_result = 0
        fs_files = set()
        for language, version, fs_file in self.yield_lang_version_specfile():
            if fs_file in fs_files:
                continue
            fs_files.add(fs_file)

            if files:
                spec_sections = self.config.get_language_config(
                    language
                ).spec_sections_for(version)
                matching_files = {
                    (file_version, spec)
                    for file_version, spec in files
                    if (file_version, spec) not in validated_files
                    and version == file_version
                    and spec in spec_sections
                }
                validated_files.update(matching_files)

            # Generate full spec file is needed
            fs_path = write_full_spec(
                constants.SPEC_REPO_SPEC_DIR,
                version,
                self.config.get_language_config(language).spec_sections_for(version),
                fs_file,
            )

            if files and not matching_files:
                # Skip late so that the full spec is still written
                continue

            # Validate a spec file only once
            self.validate_spec(fs_path, language, version)

        return cmd_result

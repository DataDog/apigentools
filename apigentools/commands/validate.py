# Unless explicitly stated otherwise all files in this repository are licensed
# under the 3-clause BSD style license (see LICENSE).
# This product includes software developed at Datadog (https://www.datadoghq.com/).
# Copyright 2019-Present Datadog, Inc.
import logging
import os

import click

from apigentools import constants
from apigentools.commands.command import Command
from apigentools.config import Config
from apigentools.utils import run_command, write_full_spec, change_cwd, env_or_val

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
@click.pass_obj
def validate(ctx_obj, **kwargs):
    """Validate OpenAPI spec"""
    ctx_obj.update(kwargs)
    cmd = ValidateCommand({}, ctx_obj)

    with change_cwd(ctx_obj.get("spec_repo_dir")):
        cmd.config = Config.from_file(
            os.path.join(ctx_obj.get("config_dir"), constants.DEFAULT_CONFIG_FILE)
        )
        cmd.run()


class ValidateCommand(Command):
    def validate_spec(self, fs_path, language, version):
        log_string = (
            "of general spec"
            if language is None
            else "of spec for language {}".format(language)
        )
        log_string += " ({})".format(fs_path)
        try:
            run_command([self.config.codegen_exec, "validate", "-i", fs_path])
            self.run_validation_commands(fs_path)
            log.info("Validation %s for API version %s successful", log_string, version)
            return True
        except Exception as e:
            log_method = log.error
            if self.args.get("verbose"):
                log_method = log.exception
            log_method(
                "Validation %s for API version %s failed, see the output above for errors",
                log_string,
                version,
            )
            return False

    def run_validation_commands(self, spec_path):
        vcs = self.config.get_validation_commands()
        if vcs:
            log.info("Running custom validation commands")

        for cmd in vcs:
            self.run_config_command(cmd, "validation", chevron_vars={"spec": spec_path})

    def run(self):
        cmd_result = 0
        fs_files = set()
        for language, version, fs_file in self.yield_lang_version_specfile():
            if fs_file in fs_files:
                continue
            fs_files.add(fs_file)

            # Generate full spec file is needed
            fs_path = write_full_spec(
                self.config,
                self.args.get("spec_dir"),
                version,
                self.config.get_language_config(language).spec_sections,
                fs_file,
            )

            # Validate a spec file only once
            if not self.validate_spec(fs_path, language, version):
                cmd_result = 1

        return cmd_result

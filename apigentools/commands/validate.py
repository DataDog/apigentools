# Unless explicitly stated otherwise all files in this repository are licensed
# under the 3-clause BSD style license (see LICENSE).
# This product includes software developed at Datadog (https://www.datadoghq.com/).
# Copyright 2019-Present Datadog, Inc.
import logging

from apigentools.commands.command import Command
from apigentools.utils import run_command, write_full_specs

log = logging.getLogger(__name__)


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
            if self.args.verbose:
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
        languages = self.args.languages or self.config.languages
        versions = self.args.api_versions or self.config.spec_versions
        for version in versions:
            language_specs = write_full_specs(
                self.config,
                languages,
                self.args.spec_dir,
                version,
                self.args.full_spec_file,
            )
            for language, fs_path in language_specs.items():
                if not self.validate_spec(fs_path, language, version):
                    cmd_result = 1

        return cmd_result

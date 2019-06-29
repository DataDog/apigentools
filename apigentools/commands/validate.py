import logging

from apigentools.commands.command import Command
from apigentools.utils import run_command, write_full_spec

log = logging.getLogger(__name__)


class ValidateCommand(Command):
    def validate_spec(self, fs_path):
        try:
            run_command([self.config.codegen_exec, "validate", "-i", fs_path])
            log.info("Validation successful")
            return True
        except:
            log.error("Validation failed, see the output above for errors")
            return False

    def run(self):
        cmd_result = 0
        for version in self.config.spec_versions:
            fs_path = write_full_spec(self.config, self.args.spec_dir, version, self.args.full_spec_file)
            if not self.validate_spec(fs_path):
                cmd_result = 1

        return cmd_result
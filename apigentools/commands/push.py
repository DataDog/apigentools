# Unless explicitly stated otherwise all files in this repository are licensed
# under the 3-clause BSD style license (see LICENSE).
# This product includes software developed at Datadog (https://www.datadoghq.com/).
# Copyright 2019 Datadog, Inc.
import logging
import tempfile
import time
import subprocess

from apigentools.commands.command import Command
from apigentools.utils import change_cwd, run_command, get_current_commit

log = logging.getLogger(__name__)


class PushCommand(Command):

    def run(self):
        created_branches = {}
        cmd_result = 0

        languages = self.args.languages or self.config.languages
        commit_msg = "Regenerate client from commit {} of spec repo".format(get_current_commit(self.args.spec_repo_dir))
        commit_msg = self.args.push_commit_msg or commit_msg

        for lang_name, lang_config in self.config.language_configs.items():
            # Skip any languages not specified by the user
            if lang_name not in languages:
                continue

            gen_dir = self.get_generated_lang_dir(lang_name)
            # Assumes all generated changes are in the gen_dir directory
            # This is done by default in the `generate` command.
            with change_cwd(gen_dir):
                repo = "{}/{}".format(lang_config.github_org, lang_config.github_repo)
                branch_name = '{}/{}'.format(lang_name, time.time())
                try:
                    run_command(['git', 'checkout', '-b', branch_name])
                    run_command(['git', 'add', '-A'])
                    run_command(['git', 'commit', '-a', '-m', commit_msg])
                    run_command(['git', 'push', 'origin', 'HEAD'])
                    created_branches[repo] = branch_name
                except subprocess.CalledProcessError as e:
                    log.error("Error running git commands: {}".format(e))
                    cmd_result+=1
                    continue
        log.info('Apigentools created the following branches:')
        log.info('\n'.join('{} : {}'.format(key, value) for key, value in created_branches.items()))
        return cmd_result

import logging
import os
from pprint import pformat
import tempfile
import time

from apigentools.commands.command import Command
from apigentools.utils import change_cwd, run_command

log = logging.getLogger(__name__)

REPO_URL = 'git@github.com:{}/{}.git'

# [TODO] setup an argument for this to be used
# By default git uses whatever SSH keys are setup locally
GIT_SSH = "GIT_SSH_COMMAND='ssh -i {}' "

class PushCommand(Command):

    def run(self):
        created_branches = {}
        cmd_result = 0

        for lang_name, lang_config in self.config.language_configs.items():
            # Note: We assume that its one repo for all versions.
            # Git shallow clone the repository into a temp dir
            with tempfile.TemporaryDirectory() as temp_repo_dir:
                repo = REPO_URL.format(lang_config.github_org, lang_config.github_repo)
                run_command(['git', 'clone', '--depth=2', repo, temp_repo_dir])
                for version in lang_config.spec_versions:
                    # Copy the contents of the generated dir into the git clone
                    # Make a branch and push all changes up to that branch
                    # Print branch name for each repo
                    gen_dir = self.get_generated_lang_version_dir(lang_name, version)
                    run_command(['cp', '-R', gen_dir, temp_repo_dir])

                # Now that we have the major versions copied into the cloned repo, lets make a branch and push
                with change_cwd(temp_repo_dir):
                    branch_name = '{}/{}'.format(lang_name, time.time())
                    run_command(['git', 'checkout', '-b', branch_name])
                    run_command(['git', 'push', 'origin', 'HEAD'])
                    created_branches[repo] = branch_name
            log.info('Apigentools created the following branches:')
            log.info('\n'.join('{} : {}'.format(key, value) for key, value in created_branches.items()))
        return cmd_result

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
    def get_push_branch(self, lang_name):
        """ Get name of branch to create and push. If the default branch doesn't exist,
        it will be returned, otherwise a new feature branch name will be returned.

        :param lang_name: Name of language to include in a new feature branch
        :type language: ``str``
        :return: Name of the branch to create and push
        :rtype: ``str``
        """
        push_branch = self.args.default_branch
        try:
            run_command(["git", "rev-parse", "--verify", push_branch])
            # if the default branch exists, we'll create and push a new feature branch
            push_branch = "{}/{}".format(lang_name, time.time())
        except subprocess.CalledProcessError:
            # if the default branch doesn't exist, we'll create and push it
            pass
        return push_branch

    def git_status_empty(self):
        # I hope that `--porcelain` doesn't mean this is fragile ¯\_(ツ)_/¯
        status = run_command(["git", "status", "--porcelain"])
        result = {}
        for line in status.stdout.splitlines():
            line = line.strip()
            if line:
                k, v = line.split(maxsplit=1)
                result.setdefault(k, [])
                result[k].append(v)

        if result == {} or result == {"M": [".apigentools-info"]}:
            return True
        return False

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
            log.info("Running push for language {}".format(lang_name))

            gen_dir = self.get_generated_lang_dir(lang_name)
            # Assumes all generated changes are in the gen_dir directory
            # This is done by default in the `generate` command.
            with change_cwd(gen_dir):
                repo = "{}/{}".format(lang_config.github_org, lang_config.github_repo)
                branch_name = self.get_push_branch(lang_name)
                try:
                    if self.args.skip_if_no_changes and self.git_status_empty():
                        log.info("Only .apigentools file changed for language {}, skipping".format(lang_name))
                        continue
                    run_command(['git', 'checkout', '-b', branch_name], dry_run=self.args.dry_run)
                    run_command(['git', 'add', '-A'], dry_run=self.args.dry_run)
                    run_command(['git', 'commit', '-a', '-m', commit_msg], dry_run=self.args.dry_run)
                    run_command(['git', 'push', 'origin', 'HEAD'], dry_run=self.args.dry_run)
                    created_branches[repo] = branch_name
                except subprocess.CalledProcessError as e:
                    log.error("Error running git commands: {}".format(e))
                    cmd_result+=1
                    continue
        log.info('Apigentools created the following branches:')
        log.info('\n'.join('{} : {}'.format(key, value) for key, value in created_branches.items()))
        return cmd_result

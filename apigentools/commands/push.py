# Unless explicitly stated otherwise all files in this repository are licensed
# under the 3-clause BSD style license (see LICENSE).
# This product includes software developed at Datadog (https://www.datadoghq.com/).
# Copyright 2019-Present Datadog, Inc.
import logging
import subprocess
import time

import click

from apigentools.commands.command import Command, run_command_with_config
from apigentools.utils import change_cwd, get_current_commit, run_command, env_or_val

log = logging.getLogger(__name__)


@click.command()
@click.option(
    "--default-branch",
    help="Default branch of client repo - if it doesn't exist, it will be created and pushed to instead of a new feature branch",
    default=env_or_val("APIGENTOOLS_DEFAULT_PUSH_BRANCH", "master"),
)
@click.option(
    "--dry-run",
    help="Do a dry run of push (don't actually create and push new branches)",
    is_flag=True,
    default=False,
)
@click.option(
    "--push-commit-msg",
    help="Message to use for the commit when pushing the auto generated clients",
    default=env_or_val("APIGENTOOLS_COMMIT_MSG", ""),
)
@click.option(
    "--skip-if-no-changes",
    help="Skip committing/pushing for all repositories where only .apigentools-info has changed",
    is_flag=True,
    default=env_or_val("APIGENTOOLS_SKIP_IF_NO_CHANGES", False, __type=bool),
)
@click.option(
    "--git-email",
    help="Email of the user to author git commits as. Note this will permanently"
    "modify the local repos git config to use this author",
    default=env_or_val("APIGENTOOLS_GIT_AUTHOR_EMAIL", None),
)
@click.option(
    "--git-name",
    help="Name of the user to author git commits as. Note this will permanently"
    " modify the local repos git config to use this author",
    default=env_or_val("APIGENTOOLS_GIT_AUTHOR_NAME", None),
)
@click.option(
    "--force",
    "-f",
    help="Force push the branch",
    is_flag=True,
    default=env_or_val("APIGENTOOLS_FORCE_PUSH", False, __type=bool),
)
@click.option(
    "--exit-code",
    help="Return exit code 100 if no branch was pushed when using --skip-if-no-changes, 0 if successfully pushed",
    is_flag=True,
    default=env_or_val("APIGENTOOLS_PUSH_EXIT_CODE", False, __type=bool),
)
@click.pass_context
def push(ctx, **kwargs):
    """Push the generated source code into each git repository specified in the config"""
    run_command_with_config(PushCommand, ctx, **kwargs)


class PushCommand(Command):
    def get_push_branch(self, lang_name):
        """Get name of branch to create and push. If the default branch doesn't exist,
        it will be returned, otherwise a new feature branch name will be returned.

        :param lang_name: Name of language to include in a new feature branch
        :type language: ``str``
        :return: Name of the branch to create and push
        :rtype: ``str``
        """
        push_branch = self.args.get("default_branch")
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

        languages = self.args.get("languages") or self.config.languages
        commit_msg = "Regenerate client from commit {} of spec repo".format(
            get_current_commit()
        )
        commit_msg = self.args.get("push_commit_msg") or commit_msg

        for lang_name, lang_config in self.config.languages.items():
            # Skip any languages not specified by the user
            if lang_name not in languages:
                continue

            if not lang_config.github_repo:
                log.warning(
                    "Skipping repository push for {} because github_repo is empty".format(
                        lang_name
                    )
                )
                continue

            log.info("Running push for language {}".format(lang_name))

            gen_dir = lang_config.generated_lang_dir
            # Assumes all generated changes are in the gen_dir directory
            # This is done by default in the `generate` command.
            with change_cwd(gen_dir):
                repo = "{}/{}".format(lang_config.github_org, lang_config.github_repo)
                branch_name = self.get_push_branch(lang_name)
                try:
                    if self.args.get("skip_if_no_changes") and self.git_status_empty():
                        log.info(
                            "Only .apigentools file changed for language {}, skipping".format(
                                lang_name
                            )
                        )
                        if self.args.get("exit_code"):
                            cmd_result = 100
                        continue

                    self.setup_git_config()

                    run_command(
                        ["git", "checkout", "-b", branch_name],
                        dry_run=self.args.get("dry_run"),
                    )
                    run_command(["git", "add", "-A"], dry_run=self.args.get("dry_run"))
                    run_command(
                        ["git", "commit", "-a", "-m", commit_msg],
                        dry_run=self.args.get("dry_run"),
                    )
                    push_commandline = ["git", "push", "origin", "HEAD"]
                    if self.args.get("force", False):
                        push_commandline.append("-f")
                    run_command(
                        push_commandline,
                        dry_run=self.args.get("dry_run"),
                    )
                    created_branches[repo] = branch_name
                except subprocess.CalledProcessError as e:
                    log.error("Error running git commands: {}".format(e))
                    cmd_result += 1
                    continue
        log.info("Apigentools created the following branches:")
        log.info(
            "\n".join(
                "{} : {}".format(key, value) for key, value in created_branches.items()
            )
        )
        return cmd_result

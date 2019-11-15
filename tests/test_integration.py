import os

import flexmock
import pytest

from apigentools.commands.init import InitCommand

def test_init(tmpdir):
    original_dir = os.getcwd()
    try:
        temp_dir = tmpdir.mkdir("test_init_git_dir")
        os.chdir(temp_dir)
        args = flexmock.flexmock(no_git_repo=False, projectdir=temp_dir)
        cmd_instance = InitCommand({}, args)
        cmd_instance.run()
        #sets do not presume the output of os.walk() will be ordered
        dir_entries = set(dir_entry[0] for dir_entry in os.walk("."))
        # the layout of git repos has changed over time, this dir may or may not be present
        if "./.git/branches" in dir_entries:
            dir_entries.remove("./.git/branches")
        assert dir_entries == {
            '.', './generated', './template-patches',
            './config', './config/languages', './downstream-templates',
            './spec', './spec/v1', './templates', './.git',
            './.git/objects', './.git/objects/pack',
            './.git/objects/info', './.git/info', './.git/hooks',
            './.git/refs', './.git/refs/heads', './.git/refs/tags'
                }

    # move back to original dir since temp_dir is deleted on exiting with block
    finally:
        os.chdir(original_dir)

    #test --no-git-repo
    try:
        temp_dir = tmpdir.mkdir("test_init_no_git_dir")
        os.chdir(temp_dir)
        args = flexmock.flexmock(no_git_repo=True, projectdir=temp_dir)
        cmd_instance = InitCommand({}, args)
        cmd_instance.run()
        dir_entries = set(dir_entry[0] for dir_entry in os.walk("."))
        assert dir_entries == {
            '.', './generated', './template-patches', './config',
            './config/languages', './downstream-templates', './spec',
            './spec/v1', './templates'
            }

    finally:
        os.chdir(original_dir)

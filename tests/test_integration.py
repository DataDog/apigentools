import os

import flexmock
import pytest

from apigentools.commands.init import InitCommand


def test_init(tmpdir):
    # directories created by init command
    directory_names = {
        'generated',
        'template-patches',
        'config',
        os.path.join('config', 'languages'),
        'downstream-templates',
        'spec',
        os.path.join('spec', 'v1'),
        'templates',
    }
    temp_dir = tmpdir.mkdir("test_init_git_dir")
    args = flexmock.flexmock(no_git_repo=False, projectdir=temp_dir)
    cmd_instance = InitCommand({}, args)
    cmd_instance.run()
    # sets do not presume the output of os.walk() will be ordered
    dir_entries = set(dir_entry[0] for dir_entry in os.walk(temp_dir))
    # create a set of expected directory names to test against
    test_dirs = set(os.path.join(temp_dir, name) for name in directory_names)
    # the contents of git repos may change again
    test_dirs.add(os.path.join(temp_dir, '.git'))
    assert test_dirs.issubset(dir_entries)

    # test --no-git-repo
    temp_dir = tmpdir.mkdir("test_init_no_git_dir")
    args = flexmock.flexmock(no_git_repo=True, projectdir=temp_dir)
    cmd_instance = InitCommand({}, args)
    cmd_instance.run()
    dir_entries = set(dir_entry[0] for dir_entry in os.walk(temp_dir))
    # create a set of expected directory names to test against, and add the
    # root temp_dir since it's in the output of `os.walk()`
    test_dirs = set(os.path.join(temp_dir, name) for name in directory_names)
    test_dirs.add(temp_dir)
    assert dir_entries == test_dirs

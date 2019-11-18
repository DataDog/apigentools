import os

import flexmock
import pytest

from apigentools.commands.init import InitCommand

temp_dir = "/temp_dir"
TEST_DIRS = {
    temp_dir,
    os.path.join(temp_dir, 'generated'),
    os.path.join(temp_dir, 'template-patches'),
    os.path.join(temp_dir, 'config'),
    os.path.join(temp_dir, 'config/languages'),
    os.path.join(temp_dir, 'downstream-templates'),
    os.path.join(temp_dir, 'spec'),
    os.path.join(temp_dir, 'spec/v1'),
    os.path.join(temp_dir, 'templates'),
}

def test_init(tmpdir):
    temp_dir = tmpdir.mkdir("test_init_git_dir")
    args = flexmock.flexmock(no_git_repo=False, projectdir=temp_dir)
    cmd_instance = InitCommand({}, args)
    cmd_instance.run()
    # sets do not presume the output of os.walk() will be ordered
    dir_entries = set(dir_entry[0] for dir_entry in os.walk(temp_dir))
    # the layout of git repos has changed over time, so only look for the top
    # .git directory
    # test_dirs = {
    # temp_dir,
    # os.path.join(temp_dir, 'generated'),
    # os.path.join(temp_dir, 'template-patches'),
    # os.path.join(temp_dir, 'config'),
    # os.path.join(temp_dir, 'config/languages'),
    # os.path.join(temp_dir, 'downstream-templates'),
    # os.path.join(temp_dir, 'spec'),
    # os.path.join(temp_dir, 'spec/v1'),
    # os.path.join(temp_dir, 'templates'),
    # os.path.join(temp_dir, '.git'),
    # }
    TEST_DIRS = TEST_DIRS.add(os.path.join(temp_dir, '.git'))
    assert TEST_DIRS.issubset(dir_entries)

    # assert test_dirs.issubset(dir_entries)

    # test --no-git-repo
    temp_dir = tmpdir.mkdir("test_init_no_git_dir")
    args = flexmock.flexmock(no_git_repo=True, projectdir=temp_dir)
    cmd_instance = InitCommand({}, args)
    cmd_instance.run()
    dir_entries = set(dir_entry[0] for dir_entry in os.walk(temp_dir))
    test_dirs = {
    temp_dir,
    os.path.join(temp_dir, 'generated'),
    os.path.join(temp_dir, 'template-patches'),
    os.path.join(temp_dir, 'config'),
    os.path.join(temp_dir, 'config/languages'),
    os.path.join(temp_dir, 'downstream-templates'),
    os.path.join(temp_dir, 'spec'),
    os.path.join(temp_dir, 'spec/v1'),
    os.path.join(temp_dir, 'templates')
        }
    assert dir_entries == test_dirs

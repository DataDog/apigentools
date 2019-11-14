import os
import tempfile

import flexmock
import pytest

from apigentools.commands.init import InitCommand
# in case I need this later
FIXTURE_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)),
    'fixtures',)

def test_init():
    original_dir = os.getcwd()
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            args = flexmock.flexmock(no_git_repo=False, projectdir=temp_dir)
            cmd_instance = InitCommand({}, args)
            cmd_instance.run()
            #TODO - check that subdirectories and yaml are also correct
            dir_entries = set(dir_entry[0] for dir_entry in os.walk("."))
            #sets do not presume the output of os.walk() will be ordered
            assert dir_entries == {'.', './generated', './template-patches', './config', './config/languages', './downstream-templates', './spec', './spec/v1', './templates', './.git', './.git/objects', './.git/objects/pack', './.git/objects/info', './.git/info', './.git/hooks', './.git/refs', './.git/refs/heads', './.git/refs/tags'}
    # move back to original dir since tempdir is deleted on exiting with block
    except Exception as e:
        raise e
    finally:
        os.chdir(original_dir)

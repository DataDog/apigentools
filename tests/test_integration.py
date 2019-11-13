import os
import subprocess
import tempfile

import pytest


# in case I need this later
FIXTURE_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)),
    'fixtures',)

def test_setup():
    #pip install apigentools locally
    # os.chdir("../apigentools") # dir is root of repo? - re
    result = subprocess.run(["pip", "install", "-e", os.curdir], check=True)
    assert result.returncode == 0


def test_init():
    dir_names = ["config", "generated", "template-patches", "downstream-templates", "spec", "templates", ".git"]
    with tempfile.TemporaryDirectory() as temp_dir:
        result = subprocess.run(["apigentools", "init", temp_dir], check=True)
        assert result.returncode == 0
        #check that all the directories are present and correct
        with os.scandir(temp_dir) as scan_results:
            dir_entry_list = [dir_entry.name for dir_entry in scan_results if dir_entry.is_dir() is True]
        assert sorted(dir_names) == sorted(dir_entry_list)


def test_generate():
    #testing that generate command throws an error if init is not run first
    with pytest.raises(subprocess.CalledProcessError):
        result = subprocess.run(["apigentools", "generate"], check=True)

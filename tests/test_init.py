import json
import os
import yaml

import flexmock

from apigentools import constants
from apigentools.commands import init as cmd_instance

EXPECTED_DIRECTORY_NAMES = {
    constants.DEFAULT_GENERATED_CODE_DIR,
    constants.DEFAULT_TEMPLATE_PATCHES_DIR,
    constants.DEFAULT_CONFIG_DIR,
    os.path.join(constants.DEFAULT_CONFIG_DIR, constants.LANGUAGE_OAPI_CONFIGS),
    constants.DEFAULT_DOWNSTREAM_TEMPLATES_DIR,
    constants.DEFAULT_SPEC_DIR,
    os.path.join(constants.DEFAULT_SPEC_DIR, "v1"),
    constants.DEFAULT_TEMPLATES_DIR,
}


def test_init(invoke):
    """Verify directories created by init command."""
    projectdir = "test_init_git_dir"
    result = invoke(["init", projectdir])
    assert 0 == result.exit_code

    # sets do not presume the output of os.walk() will be ordered
    dir_entries = set(dir_entry[0] for dir_entry in os.walk(projectdir))
    # create a set of expected directory names to test against
    test_dirs = set(os.path.join(projectdir, name) for name in EXPECTED_DIRECTORY_NAMES)
    # the directories created in git repos have changed in the past, so only
    # checking for the root .git directory
    test_dirs.add(os.path.join(projectdir, ".git"))

    assert test_dirs.issubset(dir_entries)

    # test that file contents are what they are supposed to be
    with open(
        os.path.join(
            projectdir, constants.DEFAULT_CONFIG_DIR, constants.DEFAULT_CONFIG_FILE,
        )
    ) as f:
        assert cmd_instance.CONFIG_FILE_JSON == json.loads(f.read())

    with open(
        os.path.join(
            projectdir, constants.DEFAULT_SPEC_DIR, "v1", constants.HEADER_FILE_NAME,
        )
    ) as f:
        assert yaml.dump(cmd_instance.V1_HEADER_JSON) == f.read()

    with open(
        os.path.join(
            projectdir,
            constants.DEFAULT_SPEC_DIR,
            "v1",
            constants.SHARED_SECTION_NAME + ".yaml",
        )
    ) as f:
        assert yaml.dump(cmd_instance.V1_SHARED_JSON) == f.read()

    with open(os.path.join(projectdir, ".gitignore")) as f:
        assert cmd_instance.GITIGNORE == f.readlines()


def test_init_no_git(invoke):
    """Verify directories created by init command without git."""
    # test --no-git-repo
    projectdir = "test_init_no_git_dir"
    result = invoke(["init", "-g", projectdir])
    assert 0 == result.exit_code

    dir_entries = set(dir_entry[0] for dir_entry in os.walk(projectdir))
    # create a set of expected directory names to test against, and add the
    # root projectdir since it's in the output of `os.walk()`
    test_dirs = set(os.path.join(projectdir, name) for name in EXPECTED_DIRECTORY_NAMES)
    test_dirs.add(projectdir)

    assert dir_entries == test_dirs

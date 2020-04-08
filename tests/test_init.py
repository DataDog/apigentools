# Unless explicitly stated otherwise all files in this repository are licensed
# under the 3-clause BSD style license (see LICENSE).
# This product includes software developed at Datadog (https://www.datadoghq.com/).
# Copyright 2019-Present Datadog, Inc.
import os

import yaml

from apigentools import constants
from apigentools.commands.init import InitCommand


def test_init(tmpdir):
    # directories created by init command
    EXPECTED_DIRECTORY_NAMES = {
        constants.SPEC_REPO_GENERATED_DIR,
        constants.SPEC_REPO_CONFIG_DIR,
        os.path.join(
            constants.SPEC_REPO_CONFIG_DIR, constants.SPEC_REPO_LANGUAGES_CONFIG_DIR
        ),
        constants.SPEC_REPO_SPEC_DIR,
        os.path.join(constants.SPEC_REPO_SPEC_DIR, "v1"),
        constants.SPEC_REPO_TEMPLATES_DIR,
    }

    temp_dir = tmpdir.mkdir("test_init_git_dir")
    args = {"no_git_repo": False, "projectdir": temp_dir}
    cmd_instance = InitCommand({}, args)
    cmd_instance.run()

    # sets do not presume the output of os.walk() will be ordered
    dir_entries = set(dir_entry[0] for dir_entry in os.walk(temp_dir))
    # create a set of expected directory names to test against
    test_dirs = set(os.path.join(temp_dir, name) for name in EXPECTED_DIRECTORY_NAMES)
    # the directories created in git repos have changed in the past, so only
    # checking for the root .git directory
    test_dirs.add(os.path.join(temp_dir, ".git"))

    assert test_dirs.issubset(dir_entries)

    # test that file contents are what they are supposed to be
    with open(
        os.path.join(
            temp_dir, constants.SPEC_REPO_CONFIG_DIR, constants.DEFAULT_CONFIG_FILE
        )
    ) as f:
        assert cmd_instance.CONFIG_FILE_JSON == yaml.safe_load(f.read())

    with open(
        os.path.join(
            temp_dir, constants.SPEC_REPO_SPEC_DIR, "v1", constants.HEADER_FILE_NAME
        )
    ) as f:
        assert yaml.dump(cmd_instance.V1_HEADER_JSON) == f.read()

    with open(
        os.path.join(
            temp_dir, constants.SPEC_REPO_SPEC_DIR, "v1", constants.SHARED_FILE_NAME,
        )
    ) as f:
        assert yaml.dump(cmd_instance.V1_SHARED_JSON) == f.read()

    with open(os.path.join(temp_dir, ".gitignore")) as f:
        assert cmd_instance.GITIGNORE == f.readlines()

    # test --no-git-repo
    temp_dir = tmpdir.mkdir("test_init_no_git_dir")
    args = {"no_git_repo": True, "projectdir": temp_dir}

    cmd_instance = InitCommand({}, args)
    cmd_instance.run()

    dir_entries = set(dir_entry[0] for dir_entry in os.walk(temp_dir))
    # create a set of expected directory names to test against, and add the
    # root temp_dir since it's in the output of `os.walk()`
    test_dirs = set(os.path.join(temp_dir, name) for name in EXPECTED_DIRECTORY_NAMES)
    test_dirs.add(temp_dir)

    assert dir_entries == test_dirs

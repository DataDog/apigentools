# Unless explicitly stated otherwise all files in this repository are licensed
# under the 3-clause BSD style license (see LICENSE).
# This product includes software developed at Datadog (https://www.datadoghq.com/).
# Copyright 2019-Present Datadog, Inc.
import json
import os

import flexmock
import pytest
import yaml

from apigentools import constants
from apigentools.commands.init import InitCommand


def test_init(tmpdir):
    # directories created by init command
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

    temp_dir = tmpdir.mkdir("test_init_git_dir")
    args = flexmock.flexmock(no_git_repo=False, projectdir=temp_dir)
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
            temp_dir, constants.DEFAULT_CONFIG_DIR, constants.DEFAULT_CONFIG_FILE
        )
    ) as f:
        assert cmd_instance.CONFIG_FILE_JSON == json.loads(f.read())

    with open(
        os.path.join(
            temp_dir, constants.DEFAULT_SPEC_DIR, "v1", constants.HEADER_FILE_NAME
        )
    ) as f:
        assert yaml.dump(cmd_instance.V1_HEADER_JSON) == f.read()

    with open(
        os.path.join(
            temp_dir,
            constants.DEFAULT_SPEC_DIR,
            "v1",
            constants.SHARED_SECTION_NAME + ".yaml",
        )
    ) as f:
        assert yaml.dump(cmd_instance.V1_SHARED_JSON) == f.read()

    with open(os.path.join(temp_dir, ".gitignore")) as f:
        assert cmd_instance.GITIGNORE == f.readlines()

    # test --no-git-repo
    temp_dir = tmpdir.mkdir("test_init_no_git_dir")
    args = flexmock.flexmock(no_git_repo=True, projectdir=temp_dir)
    cmd_instance = InitCommand({}, args)
    cmd_instance.run()

    dir_entries = set(dir_entry[0] for dir_entry in os.walk(temp_dir))
    # create a set of expected directory names to test against, and add the
    # root temp_dir since it's in the output of `os.walk()`
    test_dirs = set(os.path.join(temp_dir, name) for name in EXPECTED_DIRECTORY_NAMES)
    test_dirs.add(temp_dir)

    assert dir_entries == test_dirs

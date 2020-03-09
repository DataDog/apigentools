# Unless explicitly stated otherwise all files in this repository are licensed
# under the 3-clause BSD style license (see LICENSE).
# This product includes software developed at Datadog (https://www.datadoghq.com/).
# Copyright 2019-Present Datadog, Inc.
import json
import os

import flexmock

from apigentools.commands.list_languages import ListLanguagesCommand
from apigentools.config import Config


SPEC_CONFIG = {
    "spec_versions": ["v1"],
    "languages": {"test-lang1": {"spec_versions": ["v1", "v2"]}, "test-lang2": {}},
}
SPEC_CONFIG_OBJ = Config.from_dict(SPEC_CONFIG)


def test_list_languages():
    # Setup the arguments (The CLI tooling would do this, but we're testing the command
    # after that gets setup
    args = flexmock.flexmock()
    args.list_languages = None
    args.list_versions = None

    cmd = ListLanguagesCommand(SPEC_CONFIG_OBJ, args)
    actual_languages = cmd.run()
    assert actual_languages == [
        {"test-lang1": "v1"},
        {"test-lang1": "v2"},
        {"test-lang2": "v1"},
    ]


def test_list_only_languages():
    # Setup the arguments (The CLI tooling would do this, but we're testing the command
    # after that gets setup
    args = flexmock.flexmock()
    args.list_languages = True
    args.list_versions = None

    cmd = ListLanguagesCommand(SPEC_CONFIG_OBJ, args)
    actual_languages = cmd.run()
    assert actual_languages == ["test-lang1", "test-lang2"]


def test_list_only_versions():
    # Setup the arguments (The CLI tooling would do this, but we're testing the command
    # after that gets setup
    args = flexmock.flexmock()
    args.list_languages = None
    args.list_versions = True

    cmd = ListLanguagesCommand(SPEC_CONFIG_OBJ, args)
    actual_languages = cmd.run()
    assert actual_languages == ["v1", "v2"]

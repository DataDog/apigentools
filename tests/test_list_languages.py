# Unless explicitly stated otherwise all files in this repository are licensed
# under the 3-clause BSD style license (see LICENSE).
# This product includes software developed at Datadog (https://www.datadoghq.com/).
# Copyright 2019-Present Datadog, Inc.
import json

import pytest
import tempfile

from apigentools.commands.list_languages import ListLanguagesCommand, list_languages
from apigentools.config import Config


SPEC_CONFIG = {
    "spec_versions": ["v1", "v2"],
    "languages": {
        "test-lang1": {"spec_versions": []},
        "test-lang2": {"spec_versions": ["v1"]},
    },
    "spec_sections": {"v1": [], "v2": []},
}
SPEC_CONFIG_OBJ = Config.from_dict(SPEC_CONFIG)


@pytest.fixture
def setup_spec():
    with tempfile.NamedTemporaryFile("w+") as fp:
        fp.write(json.dumps(SPEC_CONFIG))
        fp.flush()
        yield fp.name


def test_list_languages(setup_spec):
    # Setup the arguments (The CLI tooling would do this, but we're testing the command
    # after that gets setup
    args = {"spec_dir": setup_spec, "full_spec_file": "full_spec.yaml"}

    cmd = ListLanguagesCommand(SPEC_CONFIG_OBJ, args)
    actual_languages = cmd.run()
    assert sorted(actual_languages) == sorted(
        [
            ("test-lang1", "v1", f"{setup_spec}/v1/full_spec.test-lang1.yaml"),
            ("test-lang1", "v2", f"{setup_spec}/v2/full_spec.test-lang1.yaml"),
            ("test-lang2", "v1", f"{setup_spec}/v1/full_spec.test-lang2.yaml"),
        ]
    )


def test_list_only_languages(setup_spec):
    # Setup the arguments (The CLI tooling would do this, but we're testing the command
    # after that gets setup
    args = {
        "list_languages": True,
        "spec_dir": setup_spec,
        "full_spec_file": "full_spec.yaml",
    }

    cmd = ListLanguagesCommand(SPEC_CONFIG_OBJ, args)
    actual_languages = cmd.run()
    assert set(actual_languages) == set(["test-lang1", "test-lang2"])


def test_list_only_versions(setup_spec):
    # Setup the arguments (The CLI tooling would do this, but we're testing the command
    # after that gets setup
    args = {
        "list_versions": True,
        "spec_dir": setup_spec,
        "full_spec_file": "full_spec.yaml",
    }

    cmd = ListLanguagesCommand(SPEC_CONFIG_OBJ, args)
    actual_languages = cmd.run()
    assert set(actual_languages) == set(["v1", "v2"])

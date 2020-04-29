# Unless explicitly stated otherwise all files in this repository are licensed
# under the 3-clause BSD style license (see LICENSE).
# This product includes software developed at Datadog (https://www.datadoghq.com/).
# Copyright 2019-Present Datadog, Inc.
import json

import pytest
import tempfile

from apigentools.commands.list_config import ConfigCommand
from apigentools.config import Config


SPEC_CONFIG = {
    "spec_versions": ["v1", "v2"],
    "languages": {
        "test-lang1": {
            "spec_versions": [],
            "spec_sections": {"v1": [], "v2": []},
            "library_version": "1.0.0",
        },
        "test-lang2": {"spec_versions": ["v1"], "library_version": "1.0.0"},
    },
    "spec_sections": {"v1": ["x.yaml"], "v2": ["y.yaml"]},
}
SPEC_CONFIG_OBJ = Config.from_dict(SPEC_CONFIG)


@pytest.fixture
def setup_spec():
    with tempfile.NamedTemporaryFile("w+") as fp:
        fp.write(json.dumps(SPEC_CONFIG))
        fp.flush()
        yield fp.name


def test_config(setup_spec, capsys):
    # Setup the arguments (The CLI tooling would do this, but we're testing the command
    # after that gets setup
    args = {"spec_dir": setup_spec, "full_spec_file": "full_spec.yaml"}

    ConfigCommand(SPEC_CONFIG_OBJ, args).run()
    captured = capsys.readouterr()
    out = captured.out
    assert f"'test-lang1', 'v1', 'spec/v1/full_spec.test-lang1.yaml'" in out
    assert f"'test-lang1', 'v2', 'spec/v2/full_spec.test-lang1.yaml'" in out
    assert f"'test-lang2', 'v1', 'spec/v1/full_spec.yaml'" in out


def test_config_only_languages(setup_spec, capsys):
    # Setup the arguments (The CLI tooling would do this, but we're testing the command
    # after that gets setup
    args = {
        "list_languages": True,
        "spec_dir": setup_spec,
        "full_spec_file": "full_spec.yaml",
    }

    ConfigCommand(SPEC_CONFIG_OBJ, args).run()
    captured = capsys.readouterr()
    assert captured.out.strip() in [
        "{'test-lang1', 'test-lang2'}",
        "{'test-lang2', 'test-lang1'}",
    ]


def test_config_only_versions(setup_spec, capsys):
    # Setup the arguments (The CLI tooling would do this, but we're testing the command
    # after that gets setup
    args = {
        "list_versions": True,
        "spec_dir": setup_spec,
        "full_spec_file": "full_spec.yaml",
    }

    ConfigCommand(SPEC_CONFIG_OBJ, args).run()
    captured = capsys.readouterr()
    assert captured.out.strip() in ["{'v1', 'v2'}", "{'v2', 'v1'}"]


def test_config_jsonpath_list(setup_spec, capsys):
    args = {
        "full_spec_file": "full_spec.yaml",
        "jsonpath": "$.spec_versions",
    }

    ConfigCommand(SPEC_CONFIG_OBJ, args).run()
    captured = capsys.readouterr()
    assert captured.out.strip() == '[["v1", "v2"]]'


def test_config_jsonpath_get(setup_spec, capsys):
    args = {
        "full_spec_file": "full_spec.yaml",
        "jsonpath": "$.languages.test-lang1.library_version",
        "_get_value": True,
    }

    ConfigCommand(SPEC_CONFIG_OBJ, args).run()
    captured = capsys.readouterr()
    assert captured.out.strip() == '"1.0.0"'

    args = {
        "full_spec_file": "full_spec.yaml",
        "jsonpath": "$.spec_versions",
        "_get_value": True,
    }

    ConfigCommand(SPEC_CONFIG_OBJ, args).run()
    captured = capsys.readouterr()
    assert captured.out.strip() == '["v1", "v2"]'

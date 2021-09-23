# Unless explicitly stated otherwise all files in this repository are licensed
# under the 3-clause BSD style license (see LICENSE).
# This product includes software developed at Datadog (https://www.datadoghq.com/).
# Copyright 2019-Present Datadog, Inc.

import sys

import pytest

from flexmock import flexmock

from apigentools.commands.validate import ValidateCommand
from apigentools.config import Config


SPEC_CONFIG = {
    "spec_versions": ["v1", "v2"],
    "languages": {
        "test-lang1": {"library_version": "1.0.0"},
        "test-lang2": {
            "spec_versions": ["v1"],
            "spec_sections": {"v1": ["x.yaml", "x2.yaml"]},
            "library_version": "1.0.0",
        },
        "test-lang3": {
            "spec_versions": ["v1"],
            "spec_sections": {"v1": ["z.yaml"]},
            "library_version": "1.0.0",
        },
    },
    "spec_sections": {"v1": ["x.yaml"], "v2": ["y.yaml"]},
}
SPEC_CONFIG_OBJ = Config.from_dict(SPEC_CONFIG)


def test_spec_filtering():
    calls = []

    def validate_spec(fs_path, language, version):
        calls.append((fs_path, language, version))

    val_command = ValidateCommand(
        SPEC_CONFIG_OBJ,
        {"files": ["spec/v1/x.yaml"], "full_spec_file": "full_spec.yaml"},
    )
    val_command.validate_spec = validate_spec

    flexmock(sys.modules["apigentools.commands.validate"]).should_receive(
        "write_full_spec"
    )

    val_command.run()

    assert calls == [(None, "test-lang1", "v1")]


def test_validate_with_config():
    calls = []

    def validate_spec(fs_path, language, version):
        calls.append((fs_path, language, version))

    val_command = ValidateCommand(
        SPEC_CONFIG_OBJ,
        {"files": ["config/config.yaml"], "full_spec_file": "full_spec.yaml"},
    )
    val_command.validate_spec = validate_spec

    flexmock(sys.modules["apigentools.commands.validate"]).should_receive(
        "write_full_spec"
    )

    val_command.run()

    assert calls == [
        (None, "test-lang1", "v1"),
        (None, "test-lang1", "v2"),
        (None, "test-lang2", "v1"),
        (None, "test-lang3", "v1"),
    ]


@pytest.mark.parametrize("file", ["config/functions/validate.js", "spec/root.yaml"])
def test_spec_filtering_regression(file):
    calls = []

    def validate_spec(fs_path, language, version):
        calls.append((fs_path, language, version))

    val_command = ValidateCommand(
        SPEC_CONFIG_OBJ,
        {"files": [file], "full_spec_file": "full_spec.yaml"},
    )
    val_command.validate_spec = validate_spec

    flexmock(sys.modules["apigentools.commands.validate"]).should_receive(
        "write_full_spec"
    )

    val_command.run()

    assert calls == [
        (None, "test-lang1", "v1"),
        (None, "test-lang1", "v2"),
        (None, "test-lang2", "v1"),
        (None, "test-lang3", "v1"),
    ]

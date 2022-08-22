# Unless explicitly stated otherwise all files in this repository are licensed
# under the 3-clause BSD style license (see LICENSE).
# This product includes software developed at Datadog (https://www.datadoghq.com/).
# Copyright 2019-Present Datadog, Inc.

import sys

from flexmock import flexmock

from apigentools.commands.merge import MergeCommand
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


SIMPLE_SPEC_CONFIG = {
    "spec_versions": ["v1"],
    "languages": {
        "test-lang1": {"library_version": "1.0.0"},
    },
    "spec_sections": {"v1": ["x.yaml"]},
}
SIMPLE_SPEC_CONFIG_OBJ = Config.from_dict(SIMPLE_SPEC_CONFIG)


def test_merge():
    merge_command = MergeCommand(
        SPEC_CONFIG_OBJ,
        {"full_spec_file": "full_spec.yaml"},
    )
    flexmock(sys.modules["apigentools.commands.merge"]).should_receive(
        "write_full_spec"
    )

    assert merge_command.run() == 0


def test_filter_merge():
    merge_command = MergeCommand(
        SPEC_CONFIG_OBJ,
        {"full_spec_file": "full_spec.yaml", "filter_sections": ["x-bar"]},
    )

    flexmock(sys.modules["apigentools.commands.merge"]).should_receive(
        "write_full_spec"
        ).with_args(str, str, list, str, frozenset(["x-bar"]))

    assert merge_command.run() == 0

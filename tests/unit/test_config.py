# Unless explicitly stated otherwise all files in this repository are licensed
# under the 3-clause BSD style license (see LICENSE).
# This product includes software developed at Datadog (https://www.datadoghq.com/).
# Copyright 2019-Present Datadog, Inc.
import os

import pytest

from apigentools.config import Config, ConfigCommand, LanguageConfig

FIXTURE_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "fixtures")


def test_config():
    config = {
        "languages": {
            "java": {
                "upstream_templates_dir": "Java",
                "commands": {
                    "pre": [
                        {"commandline": ["some", "cmd"], "description": "Some command"}
                    ]
                },
            }
        },
        "user_agent_client_name": "MyClient",
    }

    c = Config.from_dict(config)
    # check a value that was explicitly given
    assert c.user_agent_client_name == "MyClient"
    # check a value that should have a default
    assert c.codegen_exec == "openapi-generator"

    with pytest.raises(KeyError):
        c.unknown

    java = c.get_language_config("java")
    assert type(java) == LanguageConfig
    assert java.upstream_templates_dir == "Java"

    pre = java.get_stage_commands("pre")[0]
    assert type(pre) == ConfigCommand
    assert pre.description == "Some command"
    assert pre.commandline == ["some", "cmd"]


def test_config_from_file():
    c = Config.from_file(os.path.join(FIXTURE_DIR, "good_config_json.json"))
    assert c.user_agent_client_name == "MyClient"
    assert c.codegen_exec == "openapi-generator"

    # check the "inheritance" of "spec_versions" and "spec_sections"
    assert c.get_language_config("java").spec_versions == ["v1", "v2"]
    assert c.get_language_config("java").spec_sections["v1"] == ["user.yaml"]
    assert c.get_language_config("java").spec_sections["v2"] == [
        "user.yaml",
        "permission.yaml",
    ]
    assert c.get_language_config("java").generate_extra_args == [
        "--skip-overwrite",
        "--generate-alias-as-model",
    ]
    assert c.get_language_config("go").generate_extra_args == [
        "--generate-alias-as-model"
    ]

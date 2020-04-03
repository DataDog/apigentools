# Unless explicitly stated otherwise all files in this repository are licensed
# under the 3-clause BSD style license (see LICENSE).
# This product includes software developed at Datadog (https://www.datadoghq.com/).
# Copyright 2019-Present Datadog, Inc.
import os

import pytest

from apigentools.config import Config, ConfigCommand, LanguageConfig
from apigentools import constants

FIXTURE_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "fixtures")


config_sample = {
    "languages": {
        "java": {
            "default": {
                "templates": {
                    "patches": ["patch1", "patch2"],
                    "source": {
                        "type": "openapi-jar",
                        "jar_path": "/some/path.jar",
                        "templates_dir": "Java",
                    },
                },
                "commands": {
                    "pre": [
                        {
                            "commandline": ["some", "pre", "cmd"],
                            "description": "Some pre command",
                        }
                    ],
                    "post": [
                        {
                            "commandline": ["some", "post", "cmd"],
                            "description": "Some post command",
                        }
                    ],
                },
            },
            "v1": {
                "container_image": "other:image",
                "commands": {
                    "pre": [
                        {
                            "commandline": ["v1", "pre", "cmd"],
                            "description": "Some pre command",
                        }
                    ]
                },
            },
            "spec_sections": ["v1", "v2"],
        }
    },
    "user_agent_client_name": "MyClient",
}


def check_config(c):
    # check a value that was explicitly given
    assert c.user_agent_client_name == "MyClient"
    # check a value that should have a default
    assert c.container_image == constants.DEFAULT_CONTAINER_IMAGE

    with pytest.raises(KeyError):
        c.unknown

    java = c.get_language_config("java")
    assert type(java) == LanguageConfig
    cmd = java.pre_commands_for("v1")[0]
    assert type(cmd) == ConfigCommand
    assert cmd.commandline == ["v1", "pre", "cmd"]
    assert java.post_commands_for("v2")[0].commandline == ["some", "post", "cmd"]
    assert java.container_image_for("v1") == "other:image"
    assert java.container_image_for("v2") == constants.DEFAULT_CONTAINER_IMAGE
    assert java.templates_config_for("v1") == {
        "patches": ["patch1", "patch2"],
        "source": {
            "type": "openapi-jar",
            "jar_path": "/some/path.jar",
            "templates_dir": "Java",
        },
    }
    assert java.templates_config_for("v1") == java.templates_config_for("v2")


def test_config():
    c = Config.from_dict(config_sample)
    check_config(c)


def test_config_from_file():
    c = Config.from_file(os.path.join(FIXTURE_DIR, "good_config_yaml.yaml"))
    check_config(c)

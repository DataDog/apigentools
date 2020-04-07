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
            "container_opts": {
                "image": "java:image",
                "environment": {"LEVEL": "1", "JAVA": "y",},
            },
            "generation": {
                "default": {
                    "container_opts": {"environment": {"LEVEL": "2", "DEFAULT": "y",},},
                    "templates": {
                        "patches": ["patch1", "patch2"],
                        "source": {
                            "type": "openapi-jar",
                            "jar_path": "/some/path.jar",
                            "templates_dir": "Java",
                        },
                    },
                    "commands": [
                        {
                            "container_opts": {
                                "environment": {"LEVEL": "3", "CMD": "y",},
                            },
                            "commandline": ["some", "pre", "cmd"],
                            "description": "Some pre command",
                        },
                        {
                            "commandline": ["some", "post", "cmd"],
                            "description": "Some post command",
                        },
                    ],
                },
                "v1": {
                    "container_opts": {
                        "image": "other:image",
                        "inherit": False,
                        "environment": {"LEVEL": "2", "V1": "y",},
                    },
                    "commands": [
                        {
                            "commandline": ["v1", "pre", "cmd"],
                            "description": "Some pre command",
                        }
                    ],
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

    with pytest.raises(KeyError):
        c.unknown

    java = c.get_language_config("java")
    assert type(java) == LanguageConfig
    assert java.language_container_opts == {
        "environment": {"LEVEL": "1", "JAVA": "y",},
        "image": "java:image",
        "inherit": True,
        "system": False,
    }

    cmd = java.commands_for("v1")[0]
    assert type(cmd) == ConfigCommand
    assert cmd.commandline == ["v1", "pre", "cmd"]

    assert java.commands_for("v2")[1].commandline == ["some", "post", "cmd"]

    # make sure that nothing was inherited for v1
    assert java.container_opts_for("v1") == {
        "environment": {"LEVEL": "2", "V1": "y"},
        "image": "other:image",
        "inherit": False,
        "system": False,
    }
    # make sure that environment was inherited properly for V2
    assert java.container_opts_for("v2") == {
        "environment": {"JAVA": "y", "DEFAULT": "y", "LEVEL": "2"},
        "image": "java:image",
        "inherit": True,
        "system": False,
    }

    # when we have one command taken from "default" for V1 vs V2, it should inherit proper container_opts
    assert java.commands_for("v1")[0].container_opts == {
        "environment": {"LEVEL": "2", "V1": "y"},
        "image": "other:image",
        "inherit": False,
        "system": False,
    }
    assert java.commands_for("v2")[1].container_opts == {
        "environment": {"LEVEL": "2", "JAVA": "y", "DEFAULT": "y"},
        "image": "java:image",
        "inherit": True,
        "system": False,
    }

    # test inherited values on cmd itself
    assert java.commands_for("v2")[0].container_opts == {
        "environment": {"JAVA": "y", "DEFAULT": "y", "CMD": "y", "LEVEL": "3"},
        "image": "java:image",
        "inherit": True,
        "system": False,
    }

    # test templates config
    assert java.templates_config_for("v1") == {
        "patches": ["patch1", "patch2"],
        "source": {
            "type": "openapi-jar",
            "jar_path": "/some/path.jar",
            "templates_dir": "Java",
        },
    }
    assert java.templates_config_for("v1") == java.templates_config_for("v2")


def test_config_from_dict():
    c = Config.from_dict(config_sample)
    check_config(c)


def test_config_from_file():
    c = Config.from_file(os.path.join(FIXTURE_DIR, "good_config_yaml.yaml"))
    check_config(c)

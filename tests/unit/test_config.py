# Unless explicitly stated otherwise all files in this repository are licensed
# under the 3-clause BSD style license (see LICENSE).
# This product includes software developed at Datadog (https://www.datadoghq.com/).
# Copyright 2019-Present Datadog, Inc.
import os

import pytest

from apigentools.config import (
    Config,
    ConfigCommand,
    LanguageConfig,
    OpenapiJarTemplatesConfig,
)

FIXTURE_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "fixtures")


config_sample = {
    "languages": {
        "java": {
            "container_opts": {
                "image": "java:image",
                "environment": {
                    "LEVEL": "1",
                    "JAVA": "y",
                },
            },
            "generation": {
                "default": {
                    "container_opts": {
                        "environment": {
                            "LEVEL": "2",
                            "DEFAULT": "y",
                        },
                    },
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
                                "environment": {
                                    "LEVEL": "3",
                                    "CMD": "y",
                                },
                            },
                            "commandline": ["some", "pre", "cmd"],
                            "description": "Some pre command",
                        },
                        {
                            "commandline": ["some", "post", "cmd"],
                            "description": "Some post command",
                        },
                    ],
                    # NOTE: the scenario here is that the tests must not be defined in v1,
                    # but must be defined in default; then we check that container_opts
                    # were properly inherited from v1 and not from default
                    "tests": [
                        {"commandline": ["echo", "1"]},
                        {
                            "container_opts": {"environment": {"LEVEL": "3"}},
                            "commandline": ["echo", "1"],
                        },
                    ],
                },
                "v1": {
                    "container_opts": {
                        "image": "other:image",
                        "inherit": False,
                        "environment": {
                            "LEVEL": "2",
                            "V1": "y",
                        },
                    },
                    "commands": [
                        {
                            "commandline": ["v1", "pre", "cmd"],
                            "description": "Some pre command",
                        }
                    ],
                    "validation_commands": [],  # no validation for v1
                },
            },
            "github_repo_name": "my-gh-repo",
            "library_version": "1.0.0",
            "spec_versions": ["v1", "v2"],
            "version_path_template": "{{spec_version}}/",
        }
    },
    "spec_versions": ["v1", "v2"],
    "spec_sections": {},
    "user_agent_client_name": "MyClient",
    "validation_commands": [{"commandline": ["echo", "1"]}],
}


def check_config(c):
    # check a value that was explicitly given
    assert c.user_agent_client_name == "MyClient"
    # check a value that should have a default

    with pytest.raises(AttributeError):
        c.unknown

    java = c.get_language_config("java")
    assert type(java) == LanguageConfig
    assert java.container_opts == {
        "environment": {
            "LEVEL": "1",
            "JAVA": "y",
        },
        "image": "java:image",
        "inherit": True,
        "system": False,
        "workdir": ".",
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
        "workdir": ".",
    }
    # make sure that environment was inherited properly for V2
    assert java.container_opts_for("v2") == {
        "environment": {"JAVA": "y", "DEFAULT": "y", "LEVEL": "2"},
        "image": "java:image",
        "inherit": True,
        "system": False,
        "workdir": ".",
    }

    # when we have one command taken from "default" for V1 vs V2, it should inherit proper container_opts
    assert java.commands_for("v1")[0].container_opts == {
        "environment": {"LEVEL": "2", "V1": "y"},
        "image": "other:image",
        "inherit": False,
        "system": False,
        "workdir": ".",
    }
    assert java.commands_for("v2")[1].container_opts == {
        "environment": {"LEVEL": "2", "JAVA": "y", "DEFAULT": "y"},
        "image": "java:image",
        "inherit": True,
        "system": False,
        "workdir": ".",
    }

    # test inherited values on cmd itself
    assert java.commands_for("v2")[0].container_opts == {
        "environment": {"JAVA": "y", "DEFAULT": "y", "CMD": "y", "LEVEL": "3"},
        "image": "java:image",
        "inherit": True,
        "system": False,
        "workdir": ".",
    }

    # make sure that container_opts are inherited properly when commands are defined
    # on "default" generation, but container_opts are overriden on a specific version
    assert java.test_commands_for("v1")[0].container_opts == {
        "environment": {"LEVEL": "2", "V1": "y"},
        "image": "other:image",
        "inherit": False,
        "system": False,
        "workdir": ".",
    }
    assert java.test_commands_for("v1")[1].container_opts == {
        "environment": {"LEVEL": "3", "V1": "y"},
        "image": "other:image",
        "inherit": True,
        "system": False,
        "workdir": ".",
    }

    # test templates config
    tplcfg = java.templates_config_for("v1")
    assert tplcfg.patches == ["patch1", "patch2"]
    assert tplcfg.source.type == "openapi-jar"
    assert isinstance(tplcfg.source, OpenapiJarTemplatesConfig)
    assert tplcfg.source.jar_path == "/some/path.jar"
    assert tplcfg.source.templates_dir == "Java"
    assert java.templates_config_for("v1") == java.templates_config_for("v2")

    assert java.generated_lang_dir.strip("/") == "generated/my-gh-repo"
    assert (
        java.generated_lang_version_dir_for("v1").strip("/")
        == "generated/my-gh-repo/v1"
    )

    expected_chevron_vars = {
        "github_repo_name": "my-gh-repo",
        "github_repo_org": None,
        "github_repo_url": "github.com//my-gh-repo",
        "language_name": "java",
        "library_version": "1.0.0",
        "user_agent_client_name": "MyClient",
    }

    assert java.chevron_vars_for() == expected_chevron_vars
    expected_chevron_vars.update(
        {
            "config_dir": "../../../config",
            "full_spec_path": "../../../spec/v1/full_spec.yaml",
            "language_config": "../../../config/languages/java_v1.json",
            "spec_version": "v1",
            "templates_dir": "../../../templates/java/v1",
            "version_output_dir": ".",
            "top_level_dir": "../",
        }
    )
    assert (
        java.chevron_vars_for("v1", "spec/v1/full_spec.yaml") == expected_chevron_vars
    )

    assert java.validation_commands_for("v1") == []
    v2vcs = java.validation_commands_for("v2")
    assert len(v2vcs) == 1
    assert v2vcs[0].container_opts == {
        "environment": {"JAVA": "y", "DEFAULT": "y", "LEVEL": "2"},
        "image": "java:image",
        "inherit": True,
        "system": False,
        "workdir": ".",
    }
    assert v2vcs[0].commandline == ["echo", "1"]


def test_config_from_dict():
    c = Config.from_dict(config_sample)
    check_config(c)


def test_config_from_file():
    c = Config.from_file(os.path.join(FIXTURE_DIR, "good_config_yaml.yaml"))
    check_config(c)

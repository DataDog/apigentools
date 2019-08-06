import pytest

from apigentools.config import Config, LanguageConfig, LanguageCommand


def test_config():
    config = {
        "languages": {
            "java": {
                "upstream_templates_dir": "Java",
                "commands": {
                    "pre": [
                        {"commandline": ["some", "cmd"], "description": "Some command"}
                    ]
                }
            }
        },
        "user_agent_client_name": "MyClient"
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
    assert type(pre) == LanguageCommand
    assert pre.description == "Some command"
    assert pre.commandline == ["some", "cmd"]
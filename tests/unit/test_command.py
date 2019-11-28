import flexmock

from apigentools.commands.command import Command
from apigentools.config import Config


class MyCommand(Command):
    def run(self):
        return 0


def test_command_get_generated_lang_dir():
    args = flexmock(generated_code_dir="/some/path")
    config = Config.from_dict(
        {"languages": {"java": {"github_repo_name": "repo-name"}}}
    )
    mc = MyCommand(config=config, args=args)
    assert mc.get_generated_lang_dir("java") == "/some/path/repo-name"


def test_command_get_generated_lang_version_dir():
    args = flexmock(generated_code_dir="/some/path")
    config = Config.from_dict(
        {
            "languages": {
                "java": {
                    "github_repo_name": "repo-name",
                    "version_path_template": "{{spec_version}}",
                }
            }
        }
    )
    mc = MyCommand(config=config, args=args)
    assert mc.get_generated_lang_version_dir("java", "v1") == "/some/path/repo-name/v1"

import json
import os

import flexmock
import pytest


from apigentools.commands.generate import GenerateCommand
from apigentools.config import Config, LanguageConfig
from apigentools.utils import run_command

FIXTURE_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "fixtures",)


# pull_repository
# write dot apitgentools info
# render_downstream_templates
# run_language_commands


def test_get_missing_templates(tmpdir):
    temp_dir = tmpdir.mkdir("missing_templates")
    languages = ["python", "go", "ruby"]
    args = flexmock(template_dir=temp_dir)
    cmd = GenerateCommand({}, args)
    missing = cmd.get_missing_templates(languages)
    assert missing == languages


def test_get_version_from_lang_oapi_config():
    args = flexmock()
    cmd = GenerateCommand({}, args)
    with open(os.path.join(FIXTURE_DIR, "go_oapi_config.json")) as f:
        oapi_config = json.loads(f.read())
    result = cmd.get_version_from_lang_oapi_config(oapi_config)
    assert result == "0.0.1"


def test_get_image_name():
    args = flexmock(generated_with_image="apigentools:latest")
    cmd = GenerateCommand({}, args)
    result = cmd.get_image_name()
    assert result == "apigentools:latest"


def test_get_codegen_version():
    args = flexmock()
    cfg = Config(
        {
            "codegen_exec": "openapi-generator",
            "languages": {},
            "server_base_urls": {},
            "spec_sections": {},
            "spec_versions": [],
            "generate_extra_args": [],
            "user_agent_client_name": "OpenAPI",
        }
    )
    cmd = GenerateCommand(cfg, args)
    expected_result = run_command([cmd.config.codegen_exec, "version"])
    expected_result = expected_result.stdout.strip()
    # this is the version of openapi-generator we are using
    assert cmd.get_codegen_version() == expected_result


def test_get_stamp():
    args = flexmock(generated_with_image=None, spec_repo_dir=".", additional_stamp=[])
    cfg = Config(
        {
            "codegen_exec": "openapi-generator",
            "languages": {},
            "server_base_urls": {},
            "spec_sections": {},
            "spec_versions": [],
            "generate_extra_args": [],
            "user_agent_client_name": "OpenAPI",
        }
    )
    cmd = GenerateCommand(cfg, args)
    stamp = cmd.get_stamp()
    # import pdb; pdb.set_trace()
    assert "Generated with" in stamp
    assert "codegen version" in stamp


# def test_pull_repository(tmpdir):
#     #how/where are config languages set?
#     temp_dir = tmpdir.mkdir("generated_lang_dir")
#     cfg = Config({
#         "codegen_exec": "openapi-generator",
#         "languages": {},
#         "server_base_urls": {},
#         "spec_sections": {},
#         "spec_versions": [],
#         "generate_extra_args": [],
#         "user_agent_client_name": "OpenAPI"
#     })
#     args = flexmock(git_via_https=True, generated_code_dir=temp_dir)
#     cmd = GenerateCommand(cfg, args) # config dir needs get_language_config?
#     language = flexmock(language="python")
#     dir_contents = cmd.pull_repository(language)
#     dir_contents = [el for el in dir_contents]
#     import pdb; pdb.set_trace()


# def test_render_downstream_templates(tmpdir):
#     temp_dir = tmpdir.mkdir("downstream-templates")
#     args = flexmock()
#     cmd = GenerateCommand({}, args)
#     language = "python"
#     cmd.render_downstream_templates(language, temp_dir)
#     dir_walk = os.walk(temp_dir)
#     dir_walk = [dir for dir in dir_walk]

#     import pdb; pdb.set_trace()


# not working?
def test_write_dot_apigentools_info(tmpdir):
    temp_dir = tmpdir.mkdir("generated")
    repo_dir = tmpdir.mkdir("generated/repo_name")

    args = flexmock(action='generate', additional_stamp=[], api_versions=None, builtin_templates=False, clone_repo=False, config_dir='config', downstream_templates_dir='downstream-templates', full_spec_file='full_spec.yaml', generated_code_dir=temp_dir, generated_with_image=None, git_via_https=False, git_via_https_installation_access_token='', git_via_https_oauth_token='', languages=None, spec_dir='spec', spec_repo_dir='.', template_dir='templates', verbose=False, github_repo_name="repo_name")
    raw_dict = {
        "codegen_exec": "openapi-generator",
        "languages": {"java":{"github_repo_name": "repo_name"}},
        "server_base_urls": {},
        "spec_sections": {},
        "spec_versions": [],
        "generate_extra_args": [],
        "user_agent_client_name": "OpenAPI",
    }
    cfg = Config(raw_dict)
    cmd = GenerateCommand(cfg, args)
    language = "java"
    language_cfg = LanguageConfig(language=language, raw_dict=raw_dict, top_level_config=cfg)
    cmd.write_dot_apigentools_info(language)

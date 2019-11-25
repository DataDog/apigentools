import json
import os

import flexmock
import pytest


from apigentools.commands.generate import GenerateCommand
from apigentools.config import Config, LanguageConfig
from apigentools.utils import run_command

FIXTURE_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)),
    'fixtures',)


# pull_repository
# write dot apitgentools info
# get stamp
# render_downstream_templates
# run_language_commands


def test_get_missing_templates(tmpdir):
    temp_dir = tmpdir.mkdir("missing_templates")
    languages = ["python", "go", "ruby"]
    args = flexmock(template_dir=temp_dir)
    cmd = GenerateCommand({}, args)
    missing = cmd.get_missing_templates(languages)
    #what if order is different?
    assert missing == languages

def test_get_version_from_lang_oapi_config():
    args = flexmock()
    cmd = GenerateCommand({}, args)
    with open(os.path.join(FIXTURE_DIR, "go_oapi_config.json")) as f:
        oapi_config = json.loads(f.read())
    result = cmd.get_version_from_lang_oapi_config(oapi_config)
    assert result == '0.0.1'

def test_get_image_name():
    args = flexmock(generated_with_image='apigentools:latest')
    cmd = GenerateCommand({}, args)
    result = cmd.get_image_name()
    assert result == 'apigentools:latest'


def test_get_codegen_version():
    args = flexmock()
    cfg = Config({
            "codegen_exec": "openapi-generator",
            "languages": {},
            "server_base_urls": {},
            "spec_sections": {},
            "spec_versions": [],
            "generate_extra_args": [],
            "user_agent_client_name": "OpenAPI"
        })
    cmd = GenerateCommand(cfg, args)
    expected_result = run_command([cmd.config.codegen_exec, "version"])
    expected_result = expected_result.stdout.strip()
     # this is the version of openapi-generator we are using
    assert cmd.get_codegen_version() == expected_result

# def test_pull_repository(tmpdir):
#     temp_dir = tmpdir.mkdir("generated_lang_dir")
#     args = flexmock(git_via_https=True, generated_code_dir=temp_dir)
#     cmd = GenerateCommand({}, args) # config dir needs get_language_config?
#     language = flexmock(language="python")
#     dir_contents = cmd.pull_repository(language)
#     dir_contents = [el for el in dir_contents]
#     import pdb; pdb.set_trace()



# def test_render_downstream_templates(tmpdir):
#     temp_dir = tmpdir.mkdir("downstream-templates")
#     args = flexmock()
#     cmd = GenerateCommand({}, args)
#     langage = "python"
#     cmd.render_downstream_templates(langage, temp_dir)
#     dir_walk = os.walk(temp_dir)
#     dir_walk = [dir for dir in dir_walk]

#     import pdb; pdb.set_trace()

# def test_write_dot_apigentools_info(tmpdir):
#     temp_dir = tmpdir.mkdir("dot_apigentools")
#     args = flexmock(generated_code_dir=temp_dir)
#     cmd = GenerateCommand({}, args)
#     raw_dict = {
#     "codegen_exec": "openapi-generator",
#     "languages": {
#         "go": {
#             "github_repo_name": "my-api-client-go",
#             "github_org_name": "myorg",
#             "spec_versions": ["v1"],
#             "version_path_template": "myapi_{{spec_version}}"
#         }
#     },
#     "server_base_urls": {
#         "v1": "https://api.myserver.com/v1"
#     },
#     "spec_sections": {
#         "v1": ["users.yaml"]
#     },
#     "spec_versions": [
#         "v1"
#     ]
# }
#     language = "python"
#     top_level_config = flexmock()
#     cfg = LanguageConfig(language=language, raw_dict=raw_dict, top_level_config=top_level_config)
#     cmd.write_dot_apigentools_info(language)






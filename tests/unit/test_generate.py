import json
import os
import subprocess

import flexmock
import pytest


from apigentools.commands.generate import GenerateCommand
from apigentools.config import Config, LanguageConfig
from apigentools.utils import run_command

FIXTURE_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "fixtures",)


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
    with open(os.path.join(FIXTURE_DIR, "raw_dict.json"), "r") as f:
        raw_dict = json.loads(f.read())
    cfg = Config(raw_dict)
    cmd = GenerateCommand(cfg, args)
    expected_result = run_command([cmd.config.codegen_exec, "version"])
    expected_result = expected_result.stdout.strip()
    # this is the version of openapi-generator we are using
    assert cmd.get_codegen_version() == expected_result


def test_get_stamp():
    args = flexmock(generated_with_image=None, spec_repo_dir=".", additional_stamp=[])
    with open(os.path.join(FIXTURE_DIR, "raw_dict.json"), "r") as f:
        raw_dict = json.loads(f.read())
    cfg = Config(raw_dict)
    cmd = GenerateCommand(cfg, args)
    stamp = cmd.get_stamp()
    assert "Generated with" in stamp
    assert "codegen version" in stamp


def test_pull_repository(tmpdir):
    temp_dir = tmpdir.mkdir("generated_lang_dir")
    args = flexmock(
        action="generate",
        additional_stamp=[],
        api_versions=None,
        builtin_templates=False,
        clone_repo=False,
        config_dir="config",
        downstream_templates_dir=temp_dir,
        full_spec_file="full_spec.yaml",
        generated_code_dir=temp_dir,
        generated_with_image=None,
        git_via_https=True,
        git_via_https_installation_access_token="",
        git_via_https_oauth_token="",
        languages=None,
        spec_dir="spec",
        spec_repo_dir=".",
        template_dir="templates",
        verbose=False,
        github_repo_name="apigentools",
    )
    with open(os.path.join(FIXTURE_DIR, "raw_dict.json"), "r") as f:
        raw_dict = json.loads(f.read())
    cfg = Config(raw_dict)
    language = LanguageConfig(language="java", raw_dict=raw_dict, top_level_config=cfg)
    cmd = GenerateCommand(cfg, args)
    # git pull of https://github.com/DataDog/apigentools.git
    cmd.pull_repository(language)
    # make a list of the names of the directories from the repo
    dir_contents = [el[1] for el in os.walk(temp_dir)]
    assert [
        ".azure-pipelines",
        "apigentools",
        "tests",
        "docs",
        "hooks",
        ".github",
        ".git",
    ] in dir_contents


def test_write_dot_apigentools_info(tmpdir):
    temp_dir = tmpdir.mkdir("generated")
    repo_dir = tmpdir.mkdir("generated/DataDog")

    args = flexmock(
        action="generate",
        additional_stamp=[],
        api_versions=None,
        builtin_templates=False,
        clone_repo=False,
        config_dir="config",
        downstream_templates_dir="downstream-templates",
        full_spec_file="full_spec.yaml",
        generated_code_dir=temp_dir,
        generated_with_image=None,
        git_via_https=False,
        git_via_https_installation_access_token="",
        git_via_https_oauth_token="",
        languages=None,
        spec_dir="spec",
        spec_repo_dir=".",
        template_dir="templates",
        verbose=False,
        github_repo_name="repo_name",
    )
    with open(os.path.join(FIXTURE_DIR, "raw_dict.json"), "r") as f:
        raw_dict = json.loads(f.read())
    cfg = Config(raw_dict)
    cmd = GenerateCommand(cfg, args)
    language_cfg = LanguageConfig(
        language="java", raw_dict=raw_dict, top_level_config=cfg
    )
    cmd.write_dot_apigentools_info("java")
    with open(os.path.join(repo_dir, ".apigentools-info"), "r") as f:
        info = f.read()
    # testing that some of the keys are present in the .apigentools-info file
    assert "additional_stamps" in info
    assert "apigentools_version" in info
    assert "codegen_version" in info


def test_run_language_commands(tmpdir):
    temp_dir = tmpdir.mkdir("temp_dir")
    phase = "pre"
    language = "java"
    args = flexmock(
        action="generate",
        additional_stamp=[],
        api_versions=None,
        builtin_templates=False,
        clone_repo=False,
        config_dir="config",
        downstream_templates_dir="downstream-templates",
        full_spec_file="full_spec.yaml",
        generated_code_dir=temp_dir,
        generated_with_image=None,
        git_via_https=False,
        git_via_https_installation_access_token="",
        git_via_https_oauth_token="",
        languages=None,
        spec_dir="spec",
        spec_repo_dir=".",
        template_dir="templates",
        verbose=False,
        github_repo_name="repo_name",
    )
    with open(os.path.join(FIXTURE_DIR, "raw_dict.json"), "r") as f:
        raw_dict = json.loads(f.read())
    cfg = Config(raw_dict)
    cmd = GenerateCommand(cfg, args)
    cmd.run_language_commands(language, phase, temp_dir)
    # this runs, but I'm not sure what the commands are?


def test_render_downstream_templates(tmpdir):
    temp_dir = tmpdir.mkdir("generated")
    with open(os.path.join(FIXTURE_DIR, "raw_dict.json"), "r") as f:
        raw_dict = json.loads(f.read())
    language = "java"
    args = flexmock(
        action="generate",
        additional_stamp=[],
        api_versions=None,
        builtin_templates=False,
        clone_repo=False,
        config_dir="config",
        downstream_templates_dir="downstream-templates",
        full_spec_file="full_spec.yaml",
        generated_code_dir=temp_dir,
        generated_with_image=None,
        git_via_https=False,
        git_via_https_installation_access_token="",
        git_via_https_oauth_token="",
        languages=None,
        spec_dir="spec",
        spec_repo_dir=".",
        template_dir="templates",
        verbose=False,
        github_repo_name="repo_name",
    )
    cfg = Config(raw_dict)
    cmd = GenerateCommand(cfg, args)
    cmd.render_downstream_templates(language, temp_dir)
    walk = os.walk(os.path.join("downstream-templates", language))

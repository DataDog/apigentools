# Unless explicitly stated otherwise all files in this repository are licensed
# under the 3-clause BSD style license (see LICENSE).
# This product includes software developed at Datadog (https://www.datadoghq.com/).
# Copyright 2019-Present Datadog, Inc.
import json
import logging
import os

import click
import yaml

from apigentools import constants
from apigentools.commands.command import Command
from apigentools.utils import change_cwd, run_command, maximum_supported_config_version

log = logging.getLogger(__name__)


@click.command()
@click.argument("projectdir")
@click.option(
    "-g",
    "--no-git-repo",
    help="Don't initialize a git repository in the project directory",
    default=False,
    is_flag=True,
)
@click.pass_context
def init(ctx, **kwargs):
    """Initialize a new spec repo in the provided projectdir (will be created if it doesn't exist)"""
    ctx.obj.update(kwargs)
    cmd = InitCommand({}, ctx.obj)
    ctx.exit(cmd.run())


class InitCommand(Command):
    CONFIG_FILE_JSON = {
        "config_version": str(maximum_supported_config_version()),
        "container_opts": {
            constants.COMMAND_IMAGE_KEY: constants.DEFAULT_CONTAINER_IMAGE,
        },
        "languages": {},
        "spec_sections": {
            "v1": [constants.HEADER_FILE_NAME, constants.SHARED_FILE_NAME]
        },
        "spec_versions": ["v1"],
    }
    V1_HEADER_JSON = {
        "info": {
            "contact": {},
            "description": "Collection of all public API endpoints.",
            "title": "My API endpoints",
            "version": "1.0",
        },
        "openapi": "3.0.0",
        "servers": [{"url": "https://api.example.com/v1"}],
    }
    V1_SHARED_JSON = {
        "components": {
            "schemas": {},
            "parameters": {},
            "securitySchemes": {},
            "requestBodies": {},
            "responses": {},
            "headers": {},
            "examples": {},
            "links": {},
            "callbacks": {},
        },
        "security": [],
        "tags": [],
    }
    GITIGNORE = [
        "!generated\n",
        "generated/*\n",
        "!generated/.gitkeep\n",
        "spec/*/full_spec.yaml\n",
        "!templates\n",
        "templates/*\n",
        "templates/\n",
        ".gitkeep/n",
    ]

    def run(self):
        cmd_result = 0
        log.info("Initializing a new project directory")
        is_repo = not self.args.get("no_git_repo")

        os.makedirs(self.args.get("projectdir"), exist_ok=True)
        with change_cwd(self.args.get("projectdir")):
            dirs = {
                "config_dir": constants.SPEC_REPO_CONFIG_DIR,
                "languages_config_dir": os.path.join(
                    constants.SPEC_REPO_CONFIG_DIR,
                    constants.SPEC_REPO_LANGUAGES_CONFIG_DIR,
                ),
                "generated_dir": constants.SPEC_REPO_GENERATED_DIR,
                "spec_dir": constants.SPEC_REPO_SPEC_DIR,
                "spec_v1_dir": os.path.join(constants.SPEC_REPO_SPEC_DIR, "v1"),
                "templates_dir": constants.SPEC_REPO_TEMPLATES_DIR,
            }
            for _, v in dirs.items():
                os.makedirs(v, exist_ok=True)
            config_file = os.path.join(
                dirs["config_dir"], constants.DEFAULT_CONFIG_FILE
            )
            if not os.path.exists(config_file):
                with open(config_file, "w") as f:
                    yaml.dump(self.CONFIG_FILE_JSON, f, indent=2)
            v1_header = os.path.join(dirs["spec_v1_dir"], constants.HEADER_FILE_NAME)
            v1_shared = os.path.join(dirs["spec_v1_dir"], constants.SHARED_FILE_NAME)
            if not os.path.exists(v1_header):
                with open(v1_header, "w") as f:
                    yaml.dump(self.V1_HEADER_JSON, f)
            if not os.path.exists(v1_shared):
                with open(v1_shared, "w") as f:
                    yaml.dump(self.V1_SHARED_JSON, f)
            if is_repo:
                log.info("Creating a git repo in the new spec project directory")
                run_command(["git", "init"], log_level=logging.DEBUG)
                for d in [dirs["generated_dir"], dirs["templates_dir"]]:
                    with open(os.path.join(d, ".gitkeep"), "w"):
                        pass
                if not os.path.exists(".gitignore"):
                    with open(".gitignore", "w") as f:
                        f.writelines(self.GITIGNORE)
        return cmd_result

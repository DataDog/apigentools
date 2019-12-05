# Unless explicitly stated otherwise all files in this repository are licensed
# under the 3-clause BSD style license (see LICENSE).
# This product includes software developed at Datadog (https://www.datadoghq.com/).
# Copyright 2019 Datadog, Inc.
import json
import logging
import os

import yaml

from apigentools import constants
from apigentools.commands.command import Command
from apigentools.utils import change_cwd, run_command

log = logging.getLogger(__name__)


class InitCommand(Command):
    CONFIG_FILE_JSON = {
        "codegen_exec": "openapi-generator",
        "languages": {},
        "spec_sections": {"v1": []},
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
        is_repo = not self.args.no_git_repo

        os.makedirs(self.args.projectdir, exist_ok=True)
        with change_cwd(self.args.projectdir):
            dirs = {
                "config_dir": constants.DEFAULT_CONFIG_DIR,
                "downstream_templates_dir": constants.DEFAULT_DOWNSTREAM_TEMPLATES_DIR,
                "languages_config_dir": os.path.join(
                    constants.DEFAULT_CONFIG_DIR, constants.DEFAULT_LANGUAGES_CONFIG_DIR
                ),
                "generated_dir": constants.DEFAULT_GENERATED_CODE_DIR,
                "spec_dir": constants.DEFAULT_SPEC_DIR,
                "spec_v1_dir": os.path.join(constants.DEFAULT_SPEC_DIR, "v1"),
                "template_patches_dir": constants.DEFAULT_TEMPLATE_PATCHES_DIR,
                "templates_dir": constants.DEFAULT_TEMPLATES_DIR,
            }
            for _, v in dirs.items():
                os.makedirs(v, exist_ok=True)
            config_file = os.path.join(
                dirs["config_dir"], constants.DEFAULT_CONFIG_FILE
            )
            if not os.path.exists(config_file):
                with open(config_file, "w") as f:
                    json.dump(self.CONFIG_FILE_JSON, f, indent=4)
            v1_header = os.path.join(dirs["spec_v1_dir"], constants.HEADER_FILE_NAME)
            v1_shared = os.path.join(
                dirs["spec_v1_dir"], constants.SHARED_SECTION_NAME + ".yaml"
            )
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

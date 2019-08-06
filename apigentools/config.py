# Unless explicitly stated otherwise all files in this repository are licensed
# under the 3-clause BSD style license (see LICENSE).
# This product includes software developed at Datadog (https://www.datadoghq.com/).
# Copyright 2019 Datadog, Inc.
import json

class Config:
    def __init__(self, raw_dict):
        # TODO: verify the schema of the raw config dict, possibly use jsonschema for that
        self.raw_dict = raw_dict
        self.defaults = {
            "codegen_exec": "openapi-generator",
            "languages": {},
            "server_base_urls": {},
            "spec_sections": {},
            "spec_versions": [],
            "user_agent_client_name": "OpenAPI"
        }
        self.language_configs = {}
        for lang, conf in raw_dict.get("languages", {}).items():
            self.language_configs[lang] = LanguageConfig(lang, conf)

    def __getattr__(self, attr):
        if attr not in self.raw_dict:
            if attr not in self.defaults:
                raise KeyError("{} is not a recognized configuration key".format(attr))
            else:
                return self.defaults[attr]
        return self.raw_dict[attr]

    def get_language_config(self, lang):
        return self.language_configs[lang]

    @classmethod
    def from_file(cls, fpath):
        with open(fpath) as f:
            config = json.load(f)

        return cls(config)

    @classmethod
    def from_dict(cls, d):
        return cls(d)


class LanguageConfig:
    def __init__(self, language, raw_dict):
        self.language = language
        self.raw_dict = raw_dict

    @property
    def post_commands(self):
        return self.get_stage_commands("post")

    @property
    def pre_commands(self):
        return self.get_stage_commands("pre")

    @property
    def upstream_templates_dir(self):
        return self.raw_dict.get("upstream_templates_dir", self.language)

    def __getattr__(self, attr):
        return self.raw_dict[attr]

    def get_stage_commands(self, stage):
        cmds = self.raw_dict.get("commands", {}).get(stage, [])
        cmd_objects = []
        for cmd in cmds:
            cmd_objects.append(LanguageCommand(stage, cmd))
        return cmd_objects

    @property
    def github_repo(self):
        return self.raw_dict.get('github_repo_name')

    @property
    def github_org(self):
        return self.raw_dict.get('github_org_name')

    @property
    def command_env(self):
        return self.raw_dict.get("command_env", {})


class LanguageCommand:
    def __init__(self, stage, config):
        self.stage = stage
        self.config = config

    @property
    def description(self):
        return self.config.get("description", "Generic command")

    @property
    def commandline(self):
        return self.config["commandline"]

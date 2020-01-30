# Unless explicitly stated otherwise all files in this repository are licensed
# under the 3-clause BSD style license (see LICENSE).
# This product includes software developed at Datadog (https://www.datadoghq.com/).
# Copyright 2019-Present Datadog, Inc.
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
            "generate_extra_args": [],
            "user_agent_client_name": "OpenAPI",
            "validation_commands": [],
        }
        self.language_configs = {}
        for lang, conf in raw_dict.get("languages", {}).items():
            self.language_configs[lang] = LanguageConfig(lang, conf, self)

    def __getattr__(self, attr):
        if attr not in self.raw_dict:
            if attr not in self.defaults:
                raise KeyError("{} is not a recognized configuration key".format(attr))
            else:
                return self.defaults[attr]
        return self.raw_dict[attr]

    def get_language_config(self, lang):
        return self.language_configs[lang]

    def get_validation_commands(self):
        cmd_objects = []
        for cmd in self.validation_commands:
            cmd_objects.append(ConfigCommand("validation", cmd))
        return cmd_objects

    @classmethod
    def from_file(cls, fpath):
        with open(fpath) as f:
            config = json.load(f)

        return cls(config)

    @classmethod
    def from_dict(cls, d):
        return cls(d)


class LanguageConfig:
    def __init__(self, language, raw_dict, top_level_config):
        self.language = language
        self.raw_dict = raw_dict
        self.top_level_config = top_level_config

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
            cmd_objects.append(ConfigCommand(stage, cmd))
        return cmd_objects

    @property
    def github_repo(self):
        return self.raw_dict.get("github_repo_name")

    @property
    def github_org(self):
        return self.raw_dict.get("github_org_name")

    @property
    def command_env(self):
        return self.raw_dict.get("command_env", {})

    @property
    def generate_extra_args(self):
        return self.raw_dict.get(
            "generate_extra_args", self.top_level_config.generate_extra_args
        )

    @property
    def spec_versions(self):
        return self.raw_dict.get("spec_versions", self.top_level_config.spec_versions)

    @property
    def spec_sections(self):
        # This goes through all spec versions defined for the language; if spec sections
        # for a spec version aren't defined in language's spec_sections, they're taken
        # from the top-level spec_sections
        res = {}
        lang_sections = self.raw_dict.get("spec_sections", {})
        top_sections = self.top_level_config.spec_sections
        for sv in self.spec_versions:
            if sv in lang_sections:
                res[sv] = lang_sections[sv]
            else:
                res[sv] = top_sections[sv]
        return res


class ConfigCommand:
    def __init__(self, stage, config):
        self.stage = stage
        self.config = config

    @property
    def description(self):
        return self.config.get("description", "Generic command")

    @property
    def commandline(self):
        return self.config["commandline"]

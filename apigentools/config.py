# Unless explicitly stated otherwise all files in this repository are licensed
# under the 3-clause BSD style license (see LICENSE).
# This product includes software developed at Datadog (https://www.datadoghq.com/).
# Copyright 2019-Present Datadog, Inc.
import yaml

from apigentools import constants


class Config:
    def __init__(self, raw_dict):
        # TODO: verify the schema of the raw config dict, possibly use jsonschema for that
        self.raw_dict = raw_dict
        self.defaults = {
            "container_image": constants.DEFAULT_CONTAINER_IMAGE,
            "languages": {},
            "spec_sections": {},
            "spec_versions": [],
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
        fake_language = LanguageConfig(None, {}, self)
        for cmd in self.validation_commands:
            cmd_objects.append(ConfigCommand(None, "validation", cmd, fake_language))
        return cmd_objects

    @classmethod
    def from_file(cls, fpath):
        with open(fpath) as f:
            config = yaml.safe_load(f)

        return cls(config)

    @classmethod
    def from_dict(cls, d):
        return cls(d)

    def spec_sections_for(self, version):
        return self.raw_dict.get("spec_sections", {}).get(version, [])


class LanguageConfig:
    def __init__(self, language, raw_dict, top_level_config):
        self.language = language
        self.raw_dict = raw_dict
        self.top_level_config = top_level_config

    def get_commands(self, version, stage):
        raw = self.raw_dict.get("default", {}).get("commands", {}).get(stage, [])
        if version in self.raw_dict:
            version_cmds = self.raw_dict[version].get("commands", {})
            if stage in version_cmds:
                raw = version_cmds[stage]
        ret = []
        for r in raw:
            ret.append(ConfigCommand(version, stage, r, self))
        return ret

    def post_commands_for(self, version):
        return self.get_commands(version, "post")

    def pre_commands_for(self, version):
        return self.get_commands(version, "pre")

    def generate_commands_for(self, version):
        return self.get_commands(version, "generate")

    @property
    def github_repo(self):
        return self.raw_dict.get("github_repo_name")

    @property
    def github_org(self):
        return self.raw_dict.get("github_org_name")

    @property
    def version_path_template(self):
        return self.raw_dict.get("version_path_template", "")

    @property
    def library_version(self):
        return self.raw_dict["library_version"]

    @property
    def spec_versions(self):
        return self.raw_dict.get("spec_versions", self.top_level_config.spec_versions)

    def spec_sections_for(self, version):
        spec_sections = self.raw_dict.get("spec_sections", {})
        if version in spec_sections:
            return spec_sections[version]
        return self.top_level_config.spec_sections_for(version)

    def templates_config_for(self, version):
        tpl_cfg = self.raw_dict.get("default", {}).get("templates", {})
        if version in self.raw_dict and "templates" in self.raw_dict[version]:
            tpl_cfg = self.raw_dict[version]["templates"]
        return tpl_cfg

    def container_image_for(self, version):
        return (
            self.raw_dict.get(version, {}).get("container_image", None)
            or self.raw_dict.get("default", {}).get("container_image")
            or self.top_level_config.container_image
        )

    @property
    def downstream_templates(self):
        return self.raw_dict.get("downstream_templates", {})


class ConfigCommand:
    def __init__(self, version, stage, config, language_config):
        self.version = version
        self.stage = stage
        self.config = config
        self.language_config = language_config

    @property
    def description(self):
        return self.config.get("description", "Generic command")

    @property
    def commandline(self):
        return self.config["commandline"]

    @property
    def container_opts(self):
        copts = {
            "image": self.language_config.container_image_for(self.version),
        }
        if "container_opts" in self.config:
            copts.update(self.config["container_opts"])
        return copts

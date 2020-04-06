# Unless explicitly stated otherwise all files in this repository are licensed
# under the 3-clause BSD style license (see LICENSE).
# This product includes software developed at Datadog (https://www.datadoghq.com/).
# Copyright 2019-Present Datadog, Inc.
import yaml

from apigentools import constants
from apigentools.utils import inherit_container_opts


class Config:
    def __init__(self, raw_dict):
        # TODO: verify the schema of the raw config dict, possibly use jsonschema for that
        self.raw_dict = raw_dict
        self.defaults = {
            "container_opts": {"image": constants.DEFAULT_CONTAINER_IMAGE,},
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
        self.generation = raw_dict.get("generation", {})
        self.top_level_config = top_level_config

    def get_commands(self, version):
        raw = self.generation.get(version, {}).get("commands", [])
        if not raw:
            raw = self.generation.get("default", {}).get("commands", [])
        ret = []
        for r in raw:
            ret.append(ConfigCommand(version, r, self))
        return ret

    def commands_for(self, version):
        return self.get_commands(version)

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
        tpl_cfg = self.generation.get("default", {}).get("templates", {})
        if version in self.generation and "templates" in self.generation[version]:
            tpl_cfg = self.generation[version]["templates"]
        return tpl_cfg

    @property
    def language_container_opts(self):
        lco = self.raw_dict.get("container_opts", {})
        return inherit_container_opts(lco, self.top_level_config.container_opts)

    def container_opts_for(self, version):
        version_co = self.generation.get(version, {}).get("container_opts", {})
        if not version_co:
            version_co = self.generation.get("default", {}).get("container_opts", {})
        return inherit_container_opts(version_co, self.language_container_opts)

    @property
    def downstream_templates(self):
        return self.raw_dict.get("downstream_templates", {})


class ConfigCommand:
    def __init__(self, version, config, language_config):
        self.version = version
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
        return inherit_container_opts(
            self.config.get("container_opts", {}),
            self.language_config.container_opts_for(self.version),
        )

# Unless explicitly stated otherwise all files in this repository are licensed
# under the 3-clause BSD style license (see LICENSE).
# This product includes software developed at Datadog (https://www.datadoghq.com/).
# Copyright 2019-Present Datadog, Inc.
import json
import pathlib

from typing import Dict, List, Optional

from pydantic import BaseModel, BaseSettings, Field, validator


class ConfigCommand(BaseModel):
    """Command line configuration."""

    commandline: List[str]
    description: str = "Generic command"


class LanguageConfig(BaseModel):
    """Language configuration."""

    language: str
    github_repo: Optional[str]
    github_org: Optional[str]
    commands: Optional[Dict[str, List[ConfigCommand]]]
    command_env: Optional[Dict]
    version_path_template: Optional[str]
    upstream_templates_dir: Optional[str]
    spec_sections: Optional[Dict]
    spec_versions: Optional[List]
    generate_extra_args: Optional[List]

    class Config:
        fields = {
            "github_repo": "github_repo_name",
            "github_org": "github_org_name",
        }


class Config(BaseSettings):
    """Define configuration schema."""

    codegen_exec = "openapi-generator"
    server_base_urls: Optional[Dict] = {}
    spec_sections: Optional[Dict] = {}
    spec_versions: Optional[List] = []
    generate_extra_args: Optional[List] = []
    user_agent_client_name = "OpenAPI"
    validation_commands: Optional[List[ConfigCommand]] = []
    languages: Optional[Dict[str, LanguageConfig]] = {}

    @validator("languages", pre=True)
    def validate_languages(cls, v, field, **kwargs):
        top_level_config = kwargs["values"]
        spec_versions = top_level_config["spec_versions"]

        for lang, config in v.items():
            config.setdefault("language", lang)
            config.setdefault("upstream_templates_dir", config["language"])

            # This goes through all spec versions defined for the language; if spec sections
            # for a spec version aren't defined in language's spec_sections, they're taken
            # from the top-level spec_sections
            config.setdefault("spec_sections", {})
            spec_sections = config["spec_sections"]

            config.setdefault("spec_versions", spec_versions)

            for sv in config["spec_versions"]:
                if sv not in spec_sections:
                    spec_sections[sv] = top_level_config["spec_sections"][sv]

            # Pass defaults for everything else
            for attr in field.type_.__fields__:
                if attr in top_level_config:
                    config.setdefault(attr, top_level_config[attr])

        return v

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @classmethod
    def from_file(cls, fpath):
        with open(fpath) as f:
            config = json.load(f)

        return cls(**config)

    @classmethod
    def from_dict(cls, d):
        return cls(**d)

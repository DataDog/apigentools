# Unless explicitly stated otherwise all files in this repository are licensed
# under the 3-clause BSD style license (see LICENSE).
# This product includes software developed at Datadog (https://www.datadoghq.com/).
# Copyright 2019-Present Datadog, Inc.
import chevron
import glob as glob_
import functools
import json
import pathlib

from enum import Enum
from typing import Dict, List, Optional, Union, MutableSequence

from pydantic import BaseModel, BaseSettings, Field, validator

from .utils import glob_re, volumes_from


class CommandArgumentFunctions(str, Enum):
    """Argument functions."""

    def __new__(cls, func):
        obj = str.__new__(cls, func.func.__name__)
        obj._value_ = func.func.__name__
        obj.function = func.func
        return obj

    def __call__(self, *args, **kwargs):
        return self.function(*args, **kwargs)

    glob = functools.partial(glob_.glob)
    glob_re = functools.partial(glob_re)
    volumes_from = functools.partial(volumes_from)


class StringArgument(str):
    def __call__(self, chevron_vars: Optional[Dict] = None):
        yield chevron.render(self, chevron_vars)


class ListArgument(list, MutableSequence[StringArgument]):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for index, arg in enumerate(self):
            self[index] = StringArgument(arg)

    def __call__(self, chevron_vars: Optional[Dict] = None):
        yield [value for arg in self for value in arg(chevron_vars)]


class FunctionArgument(BaseModel):
    """Expand command argument using build-in functions."""

    function: CommandArgumentFunctions
    args: List[StringArgument] = []
    kwargs: Dict[str, Union[StringArgument, ListArgument]] = {}

    @validator("args")
    def validate_args(cls, v):
        return [StringArgument(arg) for arg in v]

    @validator("kwargs")
    def validate_kwargs(cls, v):
        return {
            key: StringArgument(arg) if isinstance(arg, str) else ListArgument(arg)
            for key, arg in v.items()
        }

    def __call__(self, chevron_vars: Optional[Dict] = None):
        kwargs = {}
        for key, arg in self.kwargs.items():
            for value in arg(chevron_vars):
                kwargs[key] = value

        result = self.function(
            *(res for arg in self.args for res in arg(chevron_vars)), **kwargs
        )
        if isinstance(result, list):
            yield from result
        else:
            yield result


class ConfigCommand(BaseModel):
    """Command line configuration."""

    commandline: List[Union[StringArgument, FunctionArgument]]
    description: str = "Generic command"

    @validator("commandline")
    def validate_commandline(cls, v, field):
        return [StringArgument(arg) if isinstance(arg, str) else arg for arg in v]

    def __call__(self, chevron_vars: Optional[Dict] = None):
        for arg in self.commandline:
            yield from arg(chevron_vars)


class LanguageConfig(BaseModel):
    """Language configuration."""

    language: str
    github_repo: Optional[str]
    github_org: Optional[str]
    commands: Optional[Dict[str, List[ConfigCommand]]] = {}
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
    container_apigentools_image: Optional[str]
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

    @classmethod
    def from_file(cls, fpath):
        with open(fpath) as f:
            config = json.load(f)

        return cls(**config)

    @classmethod
    def from_dict(cls, d):
        return cls(**d)

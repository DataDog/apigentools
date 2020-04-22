# Unless explicitly stated otherwise all files in this repository are licensed
# under the 3-clause BSD style license (see LICENSE).
# This product includes software developed at Datadog (https://www.datadoghq.com/).
# Copyright 2019-Present Datadog, Inc.
import copy
import os
from typing import Dict, List, MutableSequence, Optional, Union

import chevron
from pydantic import BaseModel, BaseSettings, validator
import yaml

from apigentools import constants
from apigentools.utils import inherit_container_opts


class ContainerImageBuild(BaseModel):
    dockerfile: str
    context: str = "."


class ContainerOpts(BaseModel):
    environment: Optional[Dict[str, str]] = {}
    image: Union[Optional[str], ContainerImageBuild]
    inherit: Optional[bool] = True
    # we don't set a default for these values, because we want to know whether we should inherit their value from parent
    # (if value is not set) or not (if value is set)
    system: Optional[bool]
    workdir: Optional[str]


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

    function: str
    args: List[StringArgument] = []
    kwargs: Dict[str, Union[StringArgument, ListArgument]] = {}

    @validator("args")
    def validate_args(cls, v):
        return [StringArgument(arg) for arg in v]


class ConfigCommand(BaseModel):
    """Command line configuration."""

    commandline: List[Union[StringArgument, FunctionArgument]]
    container_opts: Optional[ContainerOpts]
    description: str = "Generic command"

    @validator("commandline")
    def validate_commandline(cls, v, field):
        return [StringArgument(arg) if isinstance(arg, str) else arg for arg in v]

    def __call__(self, chevron_vars: Optional[Dict] = None):
        for arg in self.commandline:
            yield from arg(chevron_vars)

    def postprocess(self, parent):
        self.container_opts = inherit_container_opts(
            self.container_opts, parent.container_opts
        )


class TemplatesSourceConfig(BaseModel):
    type: str
    system: Optional[bool] = False
    templates_dir: str


class OpenapiJarTemplatesConfig(TemplatesSourceConfig):
    jar_path: str


class OpenapiGitTemplatesConfig(TemplatesSourceConfig):
    git_committish: str


class DirectoryTemplatesConfig(TemplatesSourceConfig):
    directory_path: str


class TemplatesConfig(BaseModel):
    patches: Optional[List] = []
    source: Union[
        OpenapiJarTemplatesConfig, OpenapiGitTemplatesConfig, DirectoryTemplatesConfig
    ]

    @validator("source", pre=True)
    def source_validator(cls, v):
        # NOTE: in Python 3.8, we can just do `type: Literal["openapi-jar"]` and similar on the
        # individual classes and omit this function
        tp = v.get("type")
        if tp == "openapi-jar":
            return OpenapiJarTemplatesConfig(**v)
        elif tp == "openapi-git":
            return OpenapiGitTemplatesConfig(**v)
        elif tp == "directory":
            return DirectoryTemplatesConfig(**v)
        else:
            raise ValueError("{} is not a recognized template source type".format(tp))


class VersionGeneration(BaseModel):
    container_opts: Optional[ContainerOpts]
    commands: Optional[List[ConfigCommand]]
    templates: Optional[TemplatesConfig]
    tests: Optional[List[ConfigCommand]]

    def postprocess(self, parent, vname, default_generation=None):
        if self.commands is None:
            self.commands = (
                copy.deepcopy(default_generation.commands) if default_generation else []
            )
        if self.tests is None:
            self.tests = (
                copy.deepcopy(default_generation.tests) if default_generation else []
            )
        if self.templates is None:
            self.templates = (
                copy.deepcopy(default_generation.templates)
                if default_generation
                else []
            )

        if default_generation is not None:
            if self.container_opts is None:
                self.container_opts = copy.deepcopy(default_generation.container_opts)
        self.container_opts = inherit_container_opts(
            self.container_opts, parent.container_opts
        )

        for c in self.commands:
            c.postprocess(self)
        for t in self.tests:
            t.postprocess(self)


class LanguageConfig(BaseModel):
    __slots__ = ("language", "user_agent_client_name")

    class Config:
        fields = {
            "github_repo": "github_repo_name",
            "github_org": "github_org_name",
        }

    container_opts: Optional[ContainerOpts]
    downstream_templates: Dict[str, str] = {}
    generation: Dict[str, VersionGeneration] = {}
    github_repo: Optional[str] = None
    github_org: Optional[str] = None
    library_version: str
    spec_sections: Optional[Dict]
    spec_versions: Optional[List]
    version_path_template: Optional[str] = ""

    def postprocess(self, parent, lname):
        # https://github.com/samuelcolvin/pydantic/issues/655#issuecomment-570312649
        object.__setattr__(self, "language", lname)
        object.__setattr__(
            self, "user_agent_client_name", parent.user_agent_client_name
        )

        # This goes through all spec versions defined for the language; if spec sections
        # for a spec version aren't defined in language's spec_sections, they're taken
        # from the top-level spec_sections
        if self.spec_versions is None:
            self.spec_versions = copy.deepcopy(parent.spec_versions)
        if self.spec_sections is None:
            self.spec_sections = copy.deepcopy(parent.spec_sections)

        for sv in self.spec_versions:
            if sv not in parent.spec_versions:
                raise AttributeError(
                    "{} version not found in top-level versions".format(sv)
                )
            if sv not in self.spec_sections:
                self.spec_sections[sv] = copy.deepcopy(parent.spec_sections.get(sv, []))

        self.container_opts = inherit_container_opts(
            self.container_opts, parent.container_opts
        )

        # postprocess default section first, because the other sections use it
        if "default" in self.generation:
            self.generation["default"].postprocess(self, "default", None)

        for version in self.spec_versions:
            version_generation = self.generation.get(version)
            if version_generation is None:
                version_generation = copy.deepcopy(self.generation.get("default"))
                self.generation[version] = version_generation
            if version_generation:
                version_generation.postprocess(
                    self, version, self.generation.get("default")
                )

    def commands_for(self, version):
        return self.generation[version].commands

    def test_commands_for(self, version):
        return self.generation[version].tests

    def spec_sections_for(self, version):
        return self.spec_sections[version]

    def templates_config_for(self, version):
        return self.generation[version].templates

    def container_opts_for(self, version):
        return self.generation[version].container_opts

    def chevron_vars_for(self, version=None, spec_path=None):
        chevron_vars = {
            "github_repo_name": self.github_repo,
            "github_repo_org": self.github_org,
            "language_name": self.language,
            "library_version": self.library_version,
            "user_agent_client_name": self.user_agent_client_name,
        }
        chevron_vars["github_repo_url"] = chevron.render(
            constants.GITHUB_REPO_URL_TEMPLATE, chevron_vars
        )
        if version:
            version_output_dir = self.generated_lang_version_dir_for(version)
            # where is the spec repo relative to version_output_dir
            version_output_dir_nesting_level = len(
                version_output_dir.strip("/").split("/")
            )
            spec_repo_from_version_output_dir = "../" * version_output_dir_nesting_level
            top_level_from_version_output_dir = (
                "../" * (version_output_dir_nesting_level - 2) or "."
            )
            templates_dir = os.path.join(
                spec_repo_from_version_output_dir,
                constants.SPEC_REPO_TEMPLATES_DIR,
                self.language,
                version,
            )
            language_oapi_config_path = os.path.join(
                constants.SPEC_REPO_CONFIG_DIR,
                constants.SPEC_REPO_LANGUAGES_CONFIG_DIR,
                "{lang}_{v}.json".format(lang=self.language, v=version),
            )
            language_config_path = os.path.join(
                spec_repo_from_version_output_dir, language_oapi_config_path
            )

            chevron_vars.update(
                {
                    "language_config": language_config_path,
                    "spec_version": version,
                    "templates_dir": templates_dir,
                    "top_level_dir": top_level_from_version_output_dir,
                    "version_output_dir": ".",
                }
            )
            if spec_path:
                full_spec_path = os.path.join(
                    spec_repo_from_version_output_dir, spec_path
                )
                chevron_vars["full_spec_path"] = full_spec_path

        return chevron_vars

    @property
    def generated_lang_dir(self):
        """ Returns path to the directory with generated code for this language

        :return: path to directory with generated language code
        :rtype: ``str``
        """
        return os.path.join(constants.SPEC_REPO_GENERATED_DIR, self.github_repo,)

    def generated_lang_version_dir_for(self, version):
        """ Returns path to the directory with generated code for given spec version.

        :param version: spec version to get path for
        :type version: ``str``
        :return: path to directory with generated language code
        :rtype: ``str``
        """
        return os.path.join(
            self.generated_lang_dir,
            chevron.render(self.version_path_template, {"spec_version": version}),
        )


class Config(BaseSettings):
    container_opts: Optional[ContainerOpts]
    minimum_apigentools_version: Optional[str] = "0.0.0"
    spec_sections: Optional[Dict] = {}
    spec_versions: Optional[List] = []
    user_agent_client_name: str = "OpenAPI"
    # because we access a lot of the other attributes in the custom validator for languages,
    # we define it as the last attribute, so that we make sure that all the other attributes
    # are already validated (pydantic validates args in order they're defined)
    languages: Optional[Dict[str, LanguageConfig]] = {}
    validation_commands: Optional[List[ConfigCommand]] = []

    def get_language_config(self, lang):
        return self.languages[lang]

    def spec_sections_for(self, version):
        return self.spec_sections.get(version, [])

    @classmethod
    def from_file(cls, fpath):
        with open(fpath) as f:
            config = yaml.safe_load(f)
        return cls(**config).postprocess()

    @classmethod
    def from_dict(cls, d):
        return cls(**copy.deepcopy(d)).postprocess()

    def postprocess(self):
        self.container_opts = inherit_container_opts(
            self.container_opts, ContainerOpts(image=constants.DEFAULT_CONTAINER_IMAGE)
        )
        for lname, lconfig in self.languages.items():
            lconfig.postprocess(self, lname)
        for vc in self.validation_commands:
            vc.postprocess(self)
        return self

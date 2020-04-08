# Unless explicitly stated otherwise all files in this repository are licensed
# under the 3-clause BSD style license (see LICENSE).
# This product includes software developed at Datadog (https://www.datadoghq.com/).
# Copyright 2019-Present Datadog, Inc.
import abc
import glob
import logging
import os

import chevron

from apigentools.config import Config
from apigentools import constants
from apigentools.utils import (
    change_cwd,
    get_full_spec_file_name,
    glob_re,
    run_command,
)

log = logging.getLogger(__name__)


def run_command_with_config(command_class, click_ctx, **kwargs):
    click_ctx.obj.update(kwargs)
    cmd = command_class({}, click_ctx.obj)

    with change_cwd(click_ctx.obj.get("spec_repo_dir")):
        configfile = os.path.join(
            os.path.join(constants.SPEC_REPO_CONFIG_DIR, constants.DEFAULT_CONFIG_FILE)
        )
        try:
            cmd.config = Config.from_file(configfile)
        except OSError:
            if os.path.exists(os.path.join(constants.SPEC_REPO_CONFIG_DIR, "config.json")):
                log.error("It looks like your spec repo is using old configuration format no longer supported by this apigentools version")
                log.error("Please upgrade your configuration: https://apigentools.readthedocs.io/en/latest/upgrading#from-0x-series-to-1x-series")
            else:
                log.error(
                    "Couldn't find {}. Are you running in spec repo?".format(configfile)
                )
            click_ctx.exit(1)
        click_ctx.exit(cmd.run())


class Command(abc.ABC):
    def __init__(self, config, args):
        self.config = config
        self.args = args

    def yield_lang_version(self, languages=None, versions=None):
        languages = set(
            languages or self.args.get("languages", []) or self.config.languages
        )
        allowed_versions = set(
            versions or self.args.get("api_versions", []) or self.config.spec_versions
        )
        for language in sorted(languages):
            language_config = self.config.get_language_config(language)
            versions = set(language_config.spec_versions or self.config.spec_versions)
            for version in sorted(versions & allowed_versions):
                yield language, version

    def yield_lang_version_specfile(self, languages=None, versions=None):
        """Yield valid combinations of (language, version, specfile)."""
        for language, version in self.yield_lang_version():
            language_config = self.config.get_language_config(language)
            language_config = self.config.get_language_config(language)
            spec_version_dir = os.path.join(constants.SPEC_REPO_SPEC_DIR, version)
            suffix = (
                language
                if language_config.spec_sections_for(version)
                != self.config.spec_sections_for(version)
                else None
            )
            yield language, version, os.path.join(
                spec_version_dir,
                get_full_spec_file_name(self.args.get("full_spec_file"), suffix),
            )

    def get_generated_lang_dir(self, lang):
        """ Returns path to the directory with generated code for given language.

        :param lang: language to get path for
        :type lang: ``str``
        :return: path to directory with generated language code
        :rtype: ``str``
        """
        return os.path.join(
            constants.SPEC_REPO_GENERATED_DIR,
            self.config.get_language_config(lang).github_repo,
        )

    def get_generated_lang_version_dir(self, lang, version):
        """ Returns path to the directory with generated code for given combination of language
        and spec version.

        :param lang: language to get path for
        :type lang: ``str``
        :param version: spec version to get path for
        :type version: ``str``
        :return: path to directory with generated language code
        :rtype: ``str``
        """
        lc = self.config.get_language_config(lang)
        return os.path.join(
            self.get_generated_lang_dir(lang),
            chevron.render(lc.version_path_template, {"spec_version": version}),
        )

    def setup_git_config(self, cwd=None):
        """Update git config for this repository to use the provided author's email/name.

        If not specified, use the setup from the system/global
        """
        if self.args.get("git_email"):
            run_command(
                ["git", "config", "user.email", self.args.get("git_email")],
                dry_run=self.args.get("dry_run", False),
                cwd=cwd,
            )
        if self.args.get("git_name"):
            run_command(
                ["git", "config", "user.name", self.args.get("git_name")],
                dry_run=self.args.get("dry_run", False),
                cwd=cwd,
            )

    def _render_command_args(self, args, chevron_vars):
        """ Recursively renders all args, including list items and dict values """
        retval = args

        if isinstance(args, str):
            retval = chevron.render(args, chevron_vars)
        elif isinstance(args, list):
            retval = []
            for i in args:
                retval.append(self._render_command_args(i, chevron_vars))
        elif isinstance(args, dict):
            retval = {}
            for k, v in args.items():
                retval[k] = self._render_command_args(v, chevron_vars)

        return retval

    def run_config_command(
        self,
        command,
        what_command,
        cwd=".",
        chevron_vars=None,
        additional_functions=None,
    ):
        log.info("Running command '%s'", command.description)

        if chevron_vars is None:
            chevron_vars = {}
        chevron_vars["cwd"] = cwd

        to_run = []
        for part in self._render_command_args(command.commandline, chevron_vars):
            if isinstance(part, dict):
                allowed_functions = {
                    "glob": glob.glob,
                    "glob_re": glob_re,
                }
                allowed_functions.update(additional_functions or {})
                function_name = part.get("function")
                function = allowed_functions.get(function_name)
                if function:
                    with change_cwd(cwd):
                        result = function(
                            *part.get("args", []), **part.get("kwargs", {})
                        )
                    # NOTE: we may need to improve this logic if/when we add more functions
                    result = self._render_command_args(result, chevron_vars)
                    if isinstance(result, list):
                        to_run.extend(result)
                    else:
                        to_run.append(result)
                else:
                    raise ValueError(
                        "Unknow function '{f}' in command '{d}' for '{l}'".format(
                            f=function_name, d=command.description, l=what_command
                        )
                    )
            else:
                to_run.append(str(part))

        additional_env = {}
        if command.container_opts.get(constants.COMMAND_SYSTEM_KEY):
            additional_env = command.container_opts.get(
                constants.COMMAND_ENVIRONMENT_KEY, {}
            )
        else:
            # dockerize
            to_run = [
                "docker",
                "run",
                "--rm",
                "-v",
                "{}:{}".format(os.getcwd(), "/tmp/spec-repo"),
                "--entrypoint",
                to_run[0],
                "--workdir",
                os.path.join("/tmp/spec-repo", cwd),
                command.container_opts[constants.COMMAND_IMAGE_KEY],
            ] + to_run[1:]
        run_command(to_run, additional_env=additional_env)

    @abc.abstractmethod
    def run(self):
        pass

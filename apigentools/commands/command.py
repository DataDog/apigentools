# Unless explicitly stated otherwise all files in this repository are licensed
# under the 3-clause BSD style license (see LICENSE).
# This product includes software developed at Datadog (https://www.datadoghq.com/).
# Copyright 2019-Present Datadog, Inc.
import abc
import glob
import logging
import os

import chevron

from apigentools.utils import (
    get_full_spec_file_name,
    glob_re,
    run_command,
    volumes_from,
)

log = logging.getLogger(__name__)


class Command(abc.ABC):
    def __init__(self, config, args):
        self.config = config
        self.args = args

    def yield_lang_version_specfile(self, languages=None, versions=None):
        """Yield valid combinations of (language, version, specfile)."""
        languages = set(
            languages or self.args.get("languages", []) or self.config.languages
        )
        allowed_versions = set(
            versions or self.args.get("api_versions", []) or self.config.spec_versions
        )
        for language in languages:
            language_config = self.config.languages[language]
            versions = set(language_config.spec_versions or self.config.spec_versions)
            for version in versions & allowed_versions:
                spec_version_dir = os.path.join(self.args.get("spec_dir"), version)
                suffix = (
                    language
                    if language_config.spec_sections != self.config.spec_sections
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
            self.args.get("generated_code_dir"),
            self.config.languages[lang].github_repo,
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
        lc = self.config.languages[lang]
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
        self, command, what_command, additional_env=None, chevron_vars=None
    ):
        log.info("Running command '%s'", command.description)

        if chevron_vars is None:
            chevron_vars = {}
        chevron_vars["cwd"] = os.getcwd()

        to_run = list(command(chevron_vars=chevron_vars))
        run_command(to_run, additional_env=additional_env)

    @abc.abstractmethod
    def run(self):
        pass

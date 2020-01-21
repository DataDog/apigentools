# Unless explicitly stated otherwise all files in this repository are licensed
# under the 3-clause BSD style license (see LICENSE).
# This product includes software developed at Datadog (https://www.datadoghq.com/).
# Copyright 2019-Present Datadog, Inc.
import abc
import os

import chevron

from apigentools.utils import run_command


class Command(abc.ABC):
    def __init__(self, config, args):
        self.config = config
        self.args = args

    def get_generated_lang_dir(self, lang):
        """ Returns path to the directory with generated code for given language.

        :param lang: language to get path for
        :type lang: ``str``
        :return: path to directory with generated language code
        :rtype: ``str``
        """
        return os.path.join(self.args.generated_code_dir, self.config.get_language_config(lang).github_repo_name,)

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
            self.get_generated_lang_dir(lang), chevron.render(lc.version_path_template, {"spec_version": version}),
        )

    def setup_git_config(self, cwd=None):
        """Update git config for this repository to use the provided author's email/name.

        If not specified, use the setup from the system/global
        """
        if self.args.git_email:
            run_command(
                ["git", "config", "user.email", self.args.git_email],
                dry_run=getattr(self.args, "dry_run", False),
                cwd=cwd,
            )
        if self.args.git_name:
            run_command(
                ["git", "config", "user.name", self.args.git_name],
                dry_run=getattr(self.args, "dry_run", False),
                cwd=cwd,
            )

    @abc.abstractmethod
    def run(self):
        pass

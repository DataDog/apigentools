# Unless explicitly stated otherwise all files in this repository are licensed
# under the 3-clause BSD style license (see LICENSE).
# This product includes software developed at Datadog (https://www.datadoghq.com/).
# Copyright 2019 Datadog, Inc.
import abc
import os

import chevron

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
        return os.path.join(
            self.args.generated_code_dir,
            self.config.get_language_config(lang).github_repo_name
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
            chevron.render(lc.version_path_template, {'spec_version': version}),
        )

    @abc.abstractmethod
    def run(self):
        pass
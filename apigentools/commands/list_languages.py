# Unless explicitly stated otherwise all files in this repository are licensed
# under the 3-clause BSD style license (see LICENSE).
# This product includes software developed at Datadog (https://www.datadoghq.com/).
# Copyright 2020-Present Datadog, Inc.
import logging

from apigentools.commands.command import Command

log = logging.getLogger(__name__)


class ListLanguagesCommand(Command):
    def run(self):
        language_versions_pairs = []
        global_spec_versions = self.config.spec_versions
        complete_spec_versions = set()

        # Construct an object containing the languages and which API versions those languages support
        languages = self.config.language_configs.keys()
        for language in languages:
            language_versions = (
                self.config.language_configs.get(language).spec_versions
                or global_spec_versions
            )
            for version in language_versions:
                language_versions_pairs.append({language: version})
                complete_spec_versions.add(version)

        # Modify the returned data based on user flags
        if self.args.list_languages:
            return [language for language in languages]
        elif self.args.list_versions:
            return [version for version in complete_spec_versions]
        else:
            return language_versions_pairs

# Unless explicitly stated otherwise all files in this repository are licensed
# under the 3-clause BSD style license (see LICENSE).
# This product includes software developed at Datadog (https://www.datadoghq.com/).
# Copyright 2020-Present Datadog, Inc.
import logging

from apigentools.commands.command import Command

log = logging.getLogger(__name__)


class ListLanguagesCommand(Command):
    def run(self):
        languages = self.config.language_configs.keys()
        for language in languages:
            log.info(language)
        return languages

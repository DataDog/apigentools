# Unless explicitly stated otherwise all files in this repository are licensed
# under the 3-clause BSD style license (see LICENSE).
# This product includes software developed at Datadog (https://www.datadoghq.com/).
# Copyright 2019-Present Datadog, Inc.
from apigentools.commands.generate import GenerateCommand
from apigentools.commands.init import InitCommand
from apigentools.commands.list_languages import ListLanguagesCommand
from apigentools.commands.push import PushCommand
from apigentools.commands.split import SplitCommand
from apigentools.commands.templates import TemplatesCommand
from apigentools.commands.test import TestCommand
from apigentools.commands.validate import ValidateCommand

all_commands = {
    "generate": GenerateCommand,
    "init": InitCommand,
    "list-languages": ListLanguagesCommand,
    "push": PushCommand,
    "split": SplitCommand,
    "templates": TemplatesCommand,
    "test": TestCommand,
    "validate": ValidateCommand,
}

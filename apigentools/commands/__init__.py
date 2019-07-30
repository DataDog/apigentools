from apigentools.commands.init import InitCommand
from apigentools.commands.generate import GenerateCommand
from apigentools.commands.push import PushCommand
from apigentools.commands.split import SplitCommand
from apigentools.commands.templates import TemplatesCommand
from apigentools.commands.test import TestCommand
from apigentools.commands.validate import ValidateCommand

all_commands = {
    "init": InitCommand,
    "generate": GenerateCommand,
    "split": SplitCommand,
    "templates": TemplatesCommand,
    "test": TestCommand,
    "validate": ValidateCommand,
    "push": PushCommand,
}

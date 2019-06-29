from apigentools.commands.generate import GenerateCommand
from apigentools.commands.split import SplitCommand
from apigentools.commands.templates import TemplatesCommand
from apigentools.commands.validate import ValidateCommand

all_commands = {
    "generate": GenerateCommand,
    "split": SplitCommand,
    "templates": TemplatesCommand,
    "validate": ValidateCommand,
}
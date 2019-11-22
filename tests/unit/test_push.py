

import flexmock
import pytest


from apigentools.commands.push import PushCommand

args = flexmock.flexmock(default_branch="a_branch")

cmd = PushCommand({}, args)
cmd.get

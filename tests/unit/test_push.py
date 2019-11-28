import subprocess

import flexmock
import pytest

from apigentools import utils
from apigentools.commands.push import PushCommand
from apigentools.utils import run_command


def test_get_push_branch():
    # test with branch in args
    default_branch = "default_branch"
    args = flexmock.flexmock(default_branch=default_branch)
    a_hash = "a_hash"
    push_branch = "push_branch"

    mock_utils = flexmock(utils)
    mock_utils.should_call("run_command")
    mock_utils.should_receive("run_command").with_args(
        "git", "rev-parse", "--verify", push_branch
    ).and_return(a_hash)

    lang_name = "lang_name"
    cmd = PushCommand({}, args)

    branch = cmd.get_push_branch(lang_name)

    assert branch == default_branch


def test_get_push_branch_subprocess_error():
    default_branch = "default_branch"
    args = flexmock.flexmock(default_branch=default_branch)

    flexmock(subprocess).should_receive("run").and_return(
        subprocess.CalledProcessError(1, 1)
    )

    lang_name = "lang_name"
    cmd = PushCommand({}, args)

    branch = cmd.get_push_branch(lang_name)

    assert lang_name in branch


def test_git_status_empty_false():
    # test when git status returns something
    args = flexmock.flexmock()
    flexmock(subprocess).should_receive("run").and_return(
        subprocess.CompletedProcess(
            1,
            0,
            """"M tests/unit/test_push.py
    ?? .coverage
    ?? .eggs/
    ?? apigentools/.coverage
    ?? tests/.coverage""",
        )
    )
    cmd = PushCommand({}, args)
    result = cmd.git_status_empty()
    assert result == False


def test_git_status_empty_true():
    args = flexmock.flexmock()
    flexmock(subprocess).should_receive("run").and_return(
        subprocess.CompletedProcess(1, 0, "M .apigentools-info")
    )
    cmd = PushCommand({}, args)
    result = cmd.git_status_empty()
    assert result == True

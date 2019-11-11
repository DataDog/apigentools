import copy
import logging
import os
import subprocess
import tempfile

import flexmock
import pytest

from apigentools.constants import REDACTED_OUT_SECRET
from apigentools.utils import change_cwd, env_or_val, fmt_cmd_out_for_log, get_current_commit, log, run_command, set_log, validate_duplicates


@pytest.mark.parametrize("env_var, default, args, typ, kwargs, set_env_to, expected", [
    ("APIGENTOOLS_TEST", "default", [], str, {}, None, "default"),
    ("APIGENTOOLS_TEST", "default", [], str, {}, "nondefault", "nondefault"),
    ("APIGENTOOLS_TEST", lambda x: x, ["spam"], str, {}, None, "spam"),
    ("APIGENTOOLS_TEST", lambda x: x, ["spam"], str, {}, "nondefault", "nondefault"),
    ("APIGENTOOLS_TEST", False, [], bool, {}, "TrUe", True),
    ("APIGENTOOLS_TEST", True, [], bool, {}, "FaLsE", False),
    ("APIGENTOOLS_TEST", [], [], list, {}, "foo:bar:baz", ["foo", "bar", "baz"]),
    ("APIGENTOOLS_TEST", 0, [], int, {}, "123", 123),
    ("APIGENTOOLS_TEST", 0.0, [], float, {}, "123.123", 123.123),
])
def test_env_or_val(env_var, default, args, typ, kwargs, set_env_to, expected):
    if set_env_to is None:
        if env_var in os.environ:
            del os.environ[env_var]
    else:
        os.environ[env_var] = set_env_to

    assert env_or_val(env_var, default, *args, __type=typ, **kwargs) == expected


def test_run_command(caplog):
    cmd = ["run", "this"]
    log_level = logging.INFO
    additional_env = {"SOME_ADDITIONAL_ENV": "value"}
    env = copy.deepcopy(os.environ)
    env.update(additional_env)
    combine_out_err = False

    flexmock(subprocess).should_receive("run").\
        with_args(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, text=True, env=env).\
        and_return(subprocess.CompletedProcess(cmd, 0, "stdout", "stderr"))
    res = run_command(cmd, log_level=log_level, additional_env=additional_env, combine_out_err=combine_out_err)
    assert res.returncode == 0
    assert res.stdout == "stdout"
    assert res.stderr == "stderr"

    flexmock(subprocess).should_receive("run").\
        with_args(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, text=True, env=env).\
        and_raise(subprocess.CalledProcessError(1, cmd, "stdout", "stderr"))
    with pytest.raises(subprocess.CalledProcessError):
        run_command(cmd, log_level=log_level, additional_env=additional_env, combine_out_err=combine_out_err)

    # test that secrets are not logged
    set_log(log)
    caplog.clear()
    caplog.set_level(logging.DEBUG, logger=log.name)
    secret = "abcdefg"
    cmd = ["run", {"secret": True, "item": secret}]
    flexmock(subprocess).should_receive("run").\
        with_args(["run", "abcdefg"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, text=True, env=env).\
        and_return(subprocess.CompletedProcess(cmd, 0, "stdout", "stderr"))
    res = run_command(cmd, log_level=log_level, additional_env=additional_env, combine_out_err=combine_out_err)
    assert secret not in caplog.text
    assert REDACTED_OUT_SECRET in caplog.text


def test_change_cwd():
    present_dir = os.getcwd()
    with tempfile.TemporaryDirectory() as target_dir:
        with change_cwd(target_dir):
            assert os.getcwd() == os.path.realpath(target_dir)
        assert os.getcwd() == present_dir

def test_get_current_commit(caplog):
    current_commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"],text=True, capture_output=True)
    assert current_commit.stdout.strip() == get_current_commit(".")
    with caplog.at_level(logging.WARNING):
        with tempfile.TemporaryDirectory() as target_dir:
            get_current_commit(target_dir)
            for record in caplog.records:
                assert "Failed getting current git commit" in record


def test_validate_duplicates():
    with pytest.raises(ValueError):
        validate_duplicates(["a", "b"], ["b", "c"])



def test_fmt_cmd_out_for_log():
    fake_CalledProcessError = flexmock.flexmock(returncode=1, stdout="stdout", stderr="stderr")
    result = fmt_cmd_out_for_log(fake_CalledProcessError, combine_out_err=True)
    assert result == 'RETCODE: 1\nOUTPUT:\nstdout'
    result = fmt_cmd_out_for_log(fake_CalledProcessError, combine_out_err=False)
    assert result == 'RETCODE: 1\nSTDOUT:\nstdoutSTDERR:\nstderr'
    fake_CompletedProcessError = flexmock.flexmock(returncode=1, stdout="stdout", stderr="stderr")
    result = fmt_cmd_out_for_log(fake_CompletedProcessError, combine_out_err=True)
    assert result == 'RETCODE: 1\nOUTPUT:\nstdout'
















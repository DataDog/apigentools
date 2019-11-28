import copy
import logging
import os
import subprocess

import flexmock
import pytest

from apigentools.constants import REDACTED_OUT_SECRET
from apigentools.utils import (
    change_cwd,
    env_or_val,
    fmt_cmd_out_for_log,
    get_current_commit,
    log,
    logging_enabled,
    run_command,
    set_log,
    set_log_level,
    validate_duplicates,
)


@pytest.mark.parametrize(
    "env_var, default, args, typ, kwargs, set_env_to, expected",
    [
        ("APIGENTOOLS_TEST", "default", [], str, {}, None, "default"),
        ("APIGENTOOLS_TEST", "default", [], str, {}, "nondefault", "nondefault"),
        ("APIGENTOOLS_TEST", lambda x: x, ["spam"], str, {}, None, "spam"),
        (
            "APIGENTOOLS_TEST",
            lambda x: x,
            ["spam"],
            str,
            {},
            "nondefault",
            "nondefault",
        ),
        ("APIGENTOOLS_TEST", False, [], bool, {}, "TrUe", True),
        ("APIGENTOOLS_TEST", True, [], bool, {}, "FaLsE", False),
        ("APIGENTOOLS_TEST", [], [], list, {}, "foo:bar:baz", ["foo", "bar", "baz"]),
        ("APIGENTOOLS_TEST", 0, [], int, {}, "123", 123),
        ("APIGENTOOLS_TEST", 0.0, [], float, {}, "123.123", 123.123),
    ],
)
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

    flexmock(subprocess).should_receive("run").with_args(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
        text=True,
        env=env,
    ).and_return(subprocess.CompletedProcess(cmd, 0, "stdout", "stderr"))
    res = run_command(
        cmd,
        log_level=log_level,
        additional_env=additional_env,
        combine_out_err=combine_out_err,
    )
    assert res.returncode == 0
    assert res.stdout == "stdout"
    assert res.stderr == "stderr"

    flexmock(subprocess).should_receive("run").with_args(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
        text=True,
        env=env,
    ).and_raise(subprocess.CalledProcessError(1, cmd, "stdout", "stderr"))
    with pytest.raises(subprocess.CalledProcessError):
        run_command(
            cmd,
            log_level=log_level,
            additional_env=additional_env,
            combine_out_err=combine_out_err,
        )

    # test that secrets are not logged
    set_log(log)
    caplog.clear()
    caplog.set_level(logging.DEBUG, logger=log.name)
    secret = "abcdefg"
    cmd = ["run", {"secret": True, "item": secret}]
    flexmock(subprocess).should_receive("run").with_args(
        ["run", "abcdefg"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
        text=True,
        env=env,
    ).and_return(subprocess.CompletedProcess(cmd, 0, "stdout", "stderr"))
    res = run_command(
        cmd,
        log_level=log_level,
        additional_env=additional_env,
        combine_out_err=combine_out_err,
    )
    assert secret not in caplog.text
    assert REDACTED_OUT_SECRET in caplog.text


def test_change_cwd(tmpdir):
    present_dir = os.getcwd()
    target_dir = tmpdir.mkdir("target_dir")
    with change_cwd(target_dir):
        assert os.getcwd() == os.path.realpath(target_dir)
    assert os.getcwd() == present_dir


def test_get_current_commit(caplog, tmpdir):
    with caplog.at_level(logging.WARNING):
        target_dir = tmpdir.mkdir("target_dir")
        get_current_commit(target_dir)
        for record in caplog.records:
            assert "Failed getting current git commit" in record
    flexmock(subprocess).should_receive("run").and_return(
        subprocess.CompletedProcess(1, 0, "some_hash")
    )
    assert get_current_commit(".") == "some_hash"


def test_validate_duplicates():
    with pytest.raises(ValueError) as err:
        validate_duplicates(["a", "b"], ["b", "c"])
        assert "Duplicate field" in str(err.value)


def test_fmt_cmd_out_for_log():
    fake_CalledProcessError = flexmock.flexmock(
        returncode=1, stdout="stdout", stderr="stderr"
    )
    result = fmt_cmd_out_for_log(fake_CalledProcessError, combine_out_err=True)
    assert result == "RETCODE: 1\nOUTPUT:\nstdout"

    result = fmt_cmd_out_for_log(fake_CalledProcessError, combine_out_err=False)
    assert result == "RETCODE: 1\nSTDOUT:\nstdoutSTDERR:\nstderr"

    result = fmt_cmd_out_for_log(fake_CalledProcessError, combine_out_err=True)
    assert result == "RETCODE: 1\nOUTPUT:\nstdout"


def test_logging_enabled(caplog):
    with logging_enabled(enabled=False):
        for record in caplog.records:
            assert "NOTSET" in record

    with logging_enabled(enabled=True):
        for record in caplog.records:
            assert "CRITICAL" in record


def test_set_log_level(caplog):
    set_log_level(log, "INFO")
    for record in caplog.records:
        assert "INFO" in record
        assert "DEBUG" not in record


def test_set_log_level_critical(caplog):
    set_log_level(log, "CRITICAL")
    for record in caplog.records:
        assert "CRITICAL" in record
        assert "INFO" not in record


def test_set_log_default(caplog):
    set_log(log)
    for record in caplog.records:
        assert "INFO" in record

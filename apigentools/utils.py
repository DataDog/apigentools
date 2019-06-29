import contextlib
import copy
import logging
import os
import subprocess
import sys

import yaml

from apigentools.constants import HEADER_FILE_NAME, SHARED_SECTION_NAME

log = logging.getLogger(__name__)


def set_log(log):
    fmt = logging.Formatter("%(levelname)s: %(message)s")
    sh = logging.StreamHandler(sys.stderr)
    sh.setLevel(logging.DEBUG)
    sh.setFormatter(fmt)
    log.addHandler(sh)
    log.setLevel(logging.INFO)


def set_log_level(log, level):
    log.setLevel(level)


@contextlib.contextmanager
def change_cwd(change_to):
    """ A context manager to temporarily change current working directory

    :param change_to: Path to change current working directory to
    :type change_to: ``str``
    """
    curdir = os.getcwd()
    os.chdir(change_to)
    try:
        yield
    finally:
        os.chdir(curdir)


def env_or_val(env, val, *args, **kwargs):
    """ Return value of environment variable (if it's defined) or a given fallback value

    :param env: Environment variable to look for
    :type env: ``str``
    :param val: Either the fallback value or function to call to compute it
    :type val: ``str`` or a function
    :param args: If ``val`` is a function, these are the ``*args`` to pass to that function
    :type args: ``list``
    :param kwargs: If ``val`` is a function, these are the ``**kwargs`` to pass to that function
    :type kwargs: ``dict``
    :return: Either the env value (if defined) or the fallback value
    :rtype: ``str``
    """
    if env not in os.environ:
        if isinstance(val, type(env_or_val)):
            val = val(*args, **kwargs)
        return val
    return os.environ.get(env)


def get_current_commit():
    """ Get short name of the current commit

    :return: The commit short name (e.g. ``abcd123``)
    :rtype: ``str``
    """
    log.debug("Getting current commit for stamping ...")
    res = run_command(["git", "rev-parse", "--short", "HEAD"], log_level=logging.DEBUG)
    return res.stdout.strip()


def run_command(cmd, log_level=logging.INFO, additional_env=None):
    """ Wrapper for running subprocesses with reasonable logging.

    :param cmd: Command to run as subprocess
    :type cmd: ``list`` of ``str``
    :param log_level: Level to log messages at (defaults to ``logging.INFO``)
    :type log_level: ``int``
    :param additional_env: Additional environment values to add to current environment
        while executing the command (``None`` or empty dict for no additional values)
    :type additional_env: ``dict`` or ``NoneType``
    :raise: ``subprocess.CalledProcessError`` if subprocess fails
    :return: Result of the called subprocess
    :rtype: ``subprocess.CompletedProcess``
    """
    try:
        env = copy.deepcopy(os.environ)
        if additional_env:
            env.update(additional_env)
        log.log(log_level, "Running command '{}'".format(" ".join(cmd)))
        result = subprocess.run(cmd, capture_output=True, check=True, text=True, env=env)
        log.log(log_level, "Command result:\n{}".format(fmt_cmd_out_for_log(result)))
    except subprocess.CalledProcessError as e:
        log.log(
            log_level,
            "Error in called process:\n{}".format(fmt_cmd_out_for_log(e))
        )
        raise

    return result


def fmt_cmd_out_for_log(result_or_error):
    """ Formats result of (or error raised from) subprocess.run for logging.

    :param result_or_error: Result/error to format
    :type result_or_error: ``subprocess.CalledProcessError`` or ``subprocess.CompletedProcess``
    :return: Formatted result/error
    :rtype: ``str``
    """
    return "RETCODE: {rc}\nSTDOUT:\n{o}STDERR:\n{e}".format(
        rc=result_or_error.returncode,
        o=result_or_error.stdout,
        e=result_or_error.stderr,
    )


def write_full_spec(config, spec_dir, version, full_spec_file):
    """ Write a full OpenAPI spec file

    :param config: apigentools config
    :type config: ``apigentools.config.Config``
    :param spec_dir: Directory containing per-major-version subdirectories
        with parts of OpenAPI spec to combine
    :type spec_dir: ``str``
    :param full_spec_file: Name of the output file for the combined OpenAPI spec
    :type full_spec_file: ``str``
    :return: Path to the written combined OpenAPI spec file
    :rtype: ``str``
    """
    spec_version_dir = os.path.join(spec_dir, version)
    fs_path = os.path.join(spec_version_dir, full_spec_file)
    log.info("Writing OpenAPI spec to %s", fs_path)

    filenames = config.spec_sections[version] + [SHARED_SECTION_NAME + ".yaml", HEADER_FILE_NAME]
    full_spec = {
        "paths": {},
        "tags": [],
         "components": {
             "schemas": {},
             "securitySchemes": {},
         },
         "servers": [{"url": config.server_base_urls[version]}],
         "security": []
     }

    for filename in filenames:
        fpath = os.path.join(spec_version_dir, filename)
        if not os.path.exists(fpath):
            continue
        with open(fpath) as infile:
            loaded = yaml.safe_load(infile.read())
            if filename == HEADER_FILE_NAME:
                full_spec.update(loaded)
            else:
                full_spec["paths"].update(loaded.get("paths", {}))
                full_spec["tags"].extend(loaded.get("tags", []))
                full_spec["components"]["schemas"].update(loaded.get("components", {}).get("schemas", {}))
                full_spec["components"]["securitySchemes"].update(loaded.get("components", {}).get("securitySchemes", {})),
                full_spec["security"].extend(loaded.get("security", {}))

    with open(fs_path, "w", encoding="utf-8") as f:
        f.write(yaml.dump(full_spec))
        log.debug("Writing the full spec: {}".format(yaml.dump(full_spec)))
    return fs_path
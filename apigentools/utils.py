# Unless explicitly stated otherwise all files in this repository are licensed
# under the 3-clause BSD style license (see LICENSE).
# This product includes software developed at Datadog (https://www.datadoghq.com/).
# Copyright 2019-Present Datadog, Inc.
import contextlib
import copy
import glob
import logging
import os
import re
import subprocess
import sys

from packaging import version
import yaml
from yaml import CSafeDumper
from yaml import CSafeLoader

from apigentools import constants, __version__
from apigentools import errors

log = logging.getLogger(__name__)

COMPONENT_FIELDS = [
    "schemas",
    "parameters",
    "securitySchemes",
    "requestBodies",
    "responses",
    "headers",
    "examples",
    "links",
    "callbacks",
]


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
    """A context manager to temporarily change current working directory

    :param change_to: Path to change current working directory to
    :type change_to: ``str``
    """
    curdir = os.getcwd()
    os.chdir(change_to)
    try:
        yield
    finally:
        os.chdir(curdir)


def env_or_val(env, val, *args, __type=str, **kwargs):
    """Return value of environment variable (if it's defined) or a given fallback value

    :param env: Environment variable to look for
    :type env: ``str``
    :param val: Either the fallback value or function to call to compute it
    :type val: ``str`` or a function
    :param args: If ``val`` is a function, these are the ``*args`` to pass to that function
    :type args: ``list``
    :param __type: type of value to return when extracting from env variable, can be one of
        ``str``, ``int``, ``float``, ``bool``, ``list``
    :type __type: ``type``
    :param kwargs: If ``val`` is a function, these are the ``**kwargs`` to pass to that function
    :type kwargs: ``dict``
    :return: Either the env value (if defined) or the fallback value
    :rtype: ``str``
    """
    if env not in os.environ:
        if isinstance(val, type(env_or_val)):
            val = val(*args, **kwargs)
        return val
    retval = os.environ.get(env)
    if __type in [str, int, float]:
        return __type(retval)
    elif __type is bool:
        if retval.lower() in ["true", "1", "yes"]:
            return True
        else:
            return False
    elif __type is list:
        return retval.split(":")
    else:
        raise ValueError("__type must be one of: str, int, float, bool, list")


def get_current_commit(repo_path="."):
    """Get short name of the current commit

    :param repo_path: Path of the repository to get current commit for
    :type repo_path: ``str``
    :return: The commit short name (e.g. ``abcd123``)
    :rtype: ``str``
    """
    log.debug("Getting current commit for stamping ...")
    with change_cwd(repo_path):
        try:
            res = run_command(
                ["git", "rev-parse", "--short", "HEAD"], log_level=logging.DEBUG
            )
        except subprocess.CalledProcessError:
            # not a git repository
            log.debug(
                "Failed getting current git commit for %s, not a git repository",
                repo_path,
            )
            return None
        return res.stdout.strip()


@contextlib.contextmanager
def logging_enabled(enabled):
    """A context manager to turn of logging temporarily

    :param enabled: If ``True``, logging will be on, if ``False``, logging will be off
    :type enabled: ``bool``
    """
    if not enabled:
        logging.disable(logging.CRITICAL)
    try:
        yield
    finally:
        logging.disable(logging.NOTSET)


def run_command(
    cmd,
    log_level=logging.DEBUG,
    additional_env=None,
    combine_out_err=False,
    dry_run=False,
    sensitive_output=False,
    **kwargs
):
    """Wrapper for running subprocesses with reasonable logging.

    :param cmd: Command to run as subprocess. Members are either strings (directly used
        to construct the command) or dicts. Dicts must have the form of
        ``{"item": "someitem", "secret": <bool value>}``. In this case, the ``item`` is used to
        construct the command and won't be logged if ``secret`` is set to ``True``.
    :type cmd: ``list`` of ``str`` or ``dict`` items
    :param log_level: Level to log messages at (defaults to ``logging.INFO``)
    :type log_level: ``int``
    :param additional_env: Additional environment values to add to current environment
        while executing the command (``None`` or empty dict for no additional values)
    :type additional_env: ``dict`` or ``NoneType``
    :raise: ``subprocess.CalledProcessError`` if subprocess fails
    :param combine_out_err: Whether or not to combine stdout and stderr of the subprocess
        into a single stream (more human readable when they're interleaved),
        defaults to `False`
    :type combine_out_err: ``bool``
    :param dry_run: Whether or not this is a dry run (``True``, commands are not executed, just logged)
        or real run (``False``)
    :type dry_run: ``bool``
    :param sensitive_output: Whether or not the output of the called subprocess is sensitive or not.
        If true, all logging will be suppressed and if a subprocess.CalledProcessError is raised,
        its attributes will be empty (note that this has no effect when ``dry_run=True``)
    :type sensitive_output: ``bool``
    :return: Result of the called subprocess
    :rtype: ``subprocess.CompletedProcess``
    """
    cmd_strlist = []
    cmd_logstr = []
    for member in cmd:
        if isinstance(member, dict):
            cmd_strlist.append(member["item"])
            if member.get("secret", False):
                cmd_logstr.append(constants.REDACTED_OUT_SECRET)
            else:
                cmd_logstr.append(member["item"])
        else:
            cmd_strlist.append(member)
            cmd_logstr.append(member)
    do_log = dry_run or not sensitive_output
    with logging_enabled(do_log):
        try:
            env = copy.deepcopy(os.environ)
            if additional_env:
                env.update(additional_env)
            log.log(
                log_level,
                "%sRunning command '%s'",
                "(DRYRUN) " if dry_run else "",
                " ".join(cmd_logstr),
            )
            if dry_run:
                result = subprocess.CompletedProcess(cmd_strlist, 0)
            else:
                stdout = subprocess.PIPE
                stderr = subprocess.STDOUT if combine_out_err else subprocess.PIPE
                result = subprocess.run(
                    cmd_strlist,
                    stdout=stdout,
                    stderr=stderr,
                    check=True,
                    text=True,
                    env=env,
                    **kwargs
                )
                log.log(
                    log_level,
                    "Command result:\n{}".format(
                        fmt_cmd_out_for_log(result, combine_out_err)
                    ),
                )
        except subprocess.CalledProcessError as e:
            if sensitive_output:
                raise subprocess.CalledProcessError(
                    e.returncode,
                    ["command with sensitive output"],
                    output=None,
                    stderr=None,
                ) from None  # use `from None to prevent exception chaining if there is sensitive output`
            log.log(
                log_level,
                "Error in called process:\n{}".format(
                    fmt_cmd_out_for_log(e, combine_out_err)
                ),
            )
            raise

        return result


def fmt_cmd_out_for_log(result_or_error, combine_out_err):
    """Formats result of (or error raised from) subprocess.run for logging.

    :param result_or_error: Result/error to format
    :type result_or_error: ``subprocess.CalledProcessError`` or ``subprocess.CompletedProcess``
    :param combine_out_err: Whether or not stdout and stderr of the subprocess are combined
        into a single stream (more human readable when they're interleaved),
        defaults to `False`
    :type combine_out_err: ``bool``
    :return: Formatted result/error
    :rtype: ``str``
    """
    if combine_out_err:
        return "\nRETCODE: {rc}\nOUTPUT:\n{o}".format(
            rc=result_or_error.returncode, o=result_or_error.stdout
        )
    else:
        return "\nRETCODE: {rc}\nSTDOUT:\n{o}STDERR:\n{e}".format(
            rc=result_or_error.returncode,
            o=result_or_error.stdout,
            e=result_or_error.stderr,
        )


def get_full_spec_file_name(default_fsf, l):
    """Get full-spec filename for given language

    * General spec is always named exactly as ``default_fsf``
    * If there's at least one ``.`` in ``default_fsf``, then the right-most one
      is replaced by ``.{language}.``, e.g. ``full_spec.yaml`` becomes
      ``full_spec.java.yaml``
    * If there's no dot in ``default_fsf``, then ``.{language}`` is appended,
      e.g. ``full_spec`` becomes ``full_spec.java``

    :param default_fsf: a filename for the general spec
    :type default_fsf: ``str``
    :param l: language to construct the spec name for
    :type l: ``str`` or ``NoneType``
    """
    if l is None:
        return default_fsf

    if "." in default_fsf:
        # since there's no "replace one occurence from right" in Python, we
        # 1) reverse the original string, 2) replace the first dot with `.{language}.`
        # 3) reverse the result
        return default_fsf[::-1].replace(".", ".{}.".format(l[::-1]), 1)[::-1]

    return "{}.{}".format(default_fsf, l)


def write_full_spec(
    spec_dir, spec_version, spec_sections, fs_path, filter_sections=None
):
    """Write a full OpenAPI spec file

    :param spec_dir: Directory containing per-major-version subdirectories
        with parts of OpenAPI spec to combine
    :type spec_dir: ``str``
    :param spec_version: Version of spec to construct full spec file for
    :type spec_version: ``str``
    :param spec_sections: List of spec sections to combine
    :type spec_sections: ``list`` of ``str``
    :param fs_path: Full path of the output file for the combined OpenAPI spec
    :type fs_path: ``str``
    :param filter_sections: If specified. list of spec keys to remove.
    :return: Path to the written combined OpenAPI spec file
    :rtype: ``str``
    """
    spec_version_dir = os.path.join(spec_dir, spec_version)
    full_spec = {
        "paths": {},
        "tags": [],
        "components": {
            "schemas": {},
            "parameters": {},
            "securitySchemes": {},
            "requestBodies": {},
            "responses": {},
            "headers": {},
            "examples": {},
            "links": {},
            "callbacks": {},
        },
        "security": [],
    }
    for filename in spec_sections:
        fpath = os.path.join(spec_version_dir, filename)
        if not os.path.exists(fpath):
            raise errors.SpecSectionNotFoundError(spec_version, filename, fpath)
        with open(fpath) as infile:
            loaded = yaml.load(infile, Loader=CSafeLoader)
            if filter_sections:
                loaded = filter_keys(loaded, filter_sections)
            for k, v in loaded.get("paths", {}).items():
                full_spec["paths"].setdefault(k, {})
                validate_duplicates(v, full_spec["paths"][k])
                full_spec["paths"][k].update(v)

            validate_duplicates(loaded.get("tags", []), full_spec.get("tags", []))
            full_spec["tags"].extend(loaded.get("tags", []))

            validate_duplicates(
                loaded.get("security", []), full_spec.get("security", [])
            )
            full_spec["security"].extend(loaded.get("security", []))

            for field in COMPONENT_FIELDS:
                # Validate there aren't duplicate fields across files
                # Note: This won't raise an error if there is a duplicate component in a single file
                # That would alredy be deduped by the safe_load above.
                validate_duplicates(
                    loaded.get("components", {}).get(field, {}).keys(),
                    full_spec.get("components", {}).get(field).keys(),
                )
                full_spec["components"][field].update(
                    loaded.get("components", {}).get(field, {})
                )

            # https://speccy.io/rules/1-rulesets#openapi-tags-alphabetical
            full_spec["tags"].sort(key=lambda x: x["name"])

            # handle the rest of top level attributes
            loaded_keys = set(loaded.keys()) - set(
                ["components", "paths", "security", "tags"]
            )
            validate_duplicates(loaded_keys, full_spec.keys())
            for k in loaded_keys:
                full_spec[k] = loaded[k]

    with open(fs_path, "w", encoding="utf-8") as f:
        yaml.dump(full_spec, f, Dumper=CSafeDumper)
    return fs_path


def validate_duplicates(loaded_keys, full_spec_keys):
    for key in loaded_keys:
        if key in full_spec_keys:
            raise ValueError("Duplicate field {} found in spec. Exiting".format(key))


def filter_keys(spec, sections):
    result = {}
    for key, value in spec.items():
        if key in sections:
            continue
        if isinstance(value, dict):
            value = filter_keys(value, sections)
        result[key] = value
    return result


def glob_re(glob_pattern, re_filter):
    glob_result = glob.glob(glob_pattern)
    re_compiled = re.compile(re_filter)

    result = [r for r in glob_result if re_compiled.match(r)]
    log.debug('"glob_re" result: %s', result)
    return result


def inherit_container_opts(local, parent):
    """Implements handling of inheritance of container_opts

    :param local: Container opts that are inheriting
    :type local: ``ContainerOpts``
    :param parent: Container opts that need to be inherited from
    :type parent: ``ContainerOpts``
    """
    if local is None:
        local = copy.deepcopy(parent)
    else:
        local = copy.deepcopy(local)
        if local.inherit:
            # each attribute we add in future might need special handling
            # to properly implement its inheritance

            # get copy of parent environment and update it with local environment
            updated_env = copy.deepcopy(parent.environment)
            updated_env.update(local.environment)
            local.environment = updated_env
            if local.system is None:
                local.system = parent.system
            if local.workdir is None:
                local.workdir = parent.workdir

    # we always inherit parent image if not set locally
    if not local.image:
        local.image = parent.image or constants.DEFAULT_CONTAINER_IMAGE
    if local.system is None:
        local.system = False
    if local.workdir is None:
        local.workdir = "."

    return local


def check_for_legacy_config(click_ctx, configfile):
    if os.path.exists(os.path.join(constants.SPEC_REPO_CONFIG_DIR, "config.json")):
        log.error(
            "It looks like your spec repo is using old configuration format no longer supported by this apigentools version"
        )
        log.error(
            "Please upgrade your configuration: https://apigentools.readthedocs.io/en/latest/upgrading#from-0x-series-to-1x-series"
        )
    else:
        log.error("Couldn't find {}. Are you running in spec repo?".format(configfile))
    click_ctx.exit(1)


def maximum_supported_config_version():
    v = version.parse(__version__)
    maxv = "{}.{}".format(*v.release[:2])
    return version.parse(maxv)

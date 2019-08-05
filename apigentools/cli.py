# Unless explicitly stated otherwise all files in this repository are licensed
# under the 3-clause BSD style license (see LICENSE).
# This product includes software developed at Datadog (https://www.datadoghq.com/).
# Copyright 2019 Datadog, Inc.
import argparse
import logging
import os
import sys

from apigentools.config import Config
from apigentools.commands import all_commands
from apigentools.utils import change_cwd, env_or_val, set_log, set_log_level

from apigentools import constants

log = logging.getLogger(__name__)


def get_cli_parser():
    p = argparse.ArgumentParser(
        description="Manipulate OpenAPI specs and generate code using openapi-generator",
    )
    p.add_argument(
        "-r", "--spec-repo-dir",
        default=env_or_val("APIGENTOOLS_SPEC_REPO_DIR", "."),
        help="Switch to this directory before doing anything else",
    )
    p.add_argument(
        "-c", "--config-dir",
        default=env_or_val("APIGENTOOLS_CONFIG_DIR", constants.DEFAULT_CONFIG_DIR),
        help="Path to config directory (default: '{}')".format(constants.DEFAULT_CONFIG_DIR),
    )
    p.add_argument(
        "-v", "--verbose",
        default=env_or_val("APIGENTOOLS_VERBOSE", False, __type=bool),
        action='store_true',
        help="Whether or not to log the generation in verbose mode",
    )
    p.add_argument(
        "-g", "--generated-code-dir",
        default=env_or_val("APIGENTOOLS_GENERATED_CODE_DIR", constants.DEFAULT_GENERATED_CODE_DIR),
        help="Path to directory where to save the generated source code (default: '{}')".format(constants.DEFAULT_GENERATED_CODE_DIR),
    )
    p.add_argument(
        "-l", "--languages",
        action="append",
        default=env_or_val("APIGENTOOLS_LANG", None),
        help="The language to run the specified action against. These must match what the config in the spec repo contains. Ex: 'apigentools -l go -l java test' (Default: None to run all)",
    )
    p.add_argument(
        "-av", "--api-versions",
        action="append",
        default=env_or_val("APIGENTOOLS_API_VERSION", None),
        help="The API version to run the specified action against. These must match what the config in the spec repo contains. Ex: 'apigentools -av v1 -av v2 test' (Default: None to run all)",
    )
    sp = p.add_subparsers(dest="action", required=True)

    generate_parser = sp.add_parser(
        "generate",
        help="Generate client code"
    )
    generate_parser.add_argument(
        "-s", "--spec-dir",
        default=env_or_val("APIGENTOOLS_SPEC_DIR", constants.DEFAULT_SPEC_DIR),
        help="Path to directory with OpenAPI specs (default: '{}')".format(constants.DEFAULT_SPEC_DIR),
    )
    generate_parser.add_argument(
        "-f", "--full-spec-file",
        default=env_or_val("APIGENTOOLS_FULL_SPEC_FILE", "full_spec.yaml"),
        help="Name of the OpenAPI full spec file to write (default: 'full_spec.yaml')",
    )
    generate_parser.add_argument(
        "--additional-stamp",
        nargs="*",
        help="Additional components to add to the 'apigentoolsStamp' variable passed to templates",
        default=env_or_val("APIGENTOOLS_ADDITIONAL_STAMP", [], __type=list),
        type=list,
    )
    generate_parser.add_argument(
        "-i", "--generated-with-image",
        default=env_or_val("APIGENTOOLS_IMAGE", None),
        help="Override the tag of the image with which the client code was generated",
    )
    generate_parser.add_argument(
        "-d", "--downstream-templates-dir",
        default=env_or_val("APIGENTOOLS_DOWNSTREAM_TEMPLATES_DIR", constants.DEFAULT_DOWNSTREAM_TEMPLATES_DIR),
        help="Path to directory with downstream templates (default: '{}')".format(constants.DEFAULT_DOWNSTREAM_TEMPLATES_DIR),
    )

    template_group = generate_parser.add_mutually_exclusive_group()
    template_group.add_argument(
        "-t", "--template-dir",
        default=env_or_val("APIGENTOOLS_TEMPLATES_DIR", constants.DEFAULT_TEMPLATES_DIR),
        help="Path to directory with processed upstream templates (default: '{}')".format(constants.DEFAULT_TEMPLATES_DIR),
    )
    template_group.add_argument(
        "--builtin-templates",
        action="store_true",
        default=False,
        help="Use unpatched upstream templates",
    )

    templates_parser = sp.add_parser(
        "templates",
        help="Get upstream templates and apply downstream patches",
    )
    templates_parser.add_argument(
        "-o", "--output-dir",
        default=env_or_val("APIGENTOOLS_TEMPLATES_DIR", constants.DEFAULT_TEMPLATES_DIR),
        help="Path to directory where to put processed upstream templates (default: {})".format(constants.DEFAULT_TEMPLATES_DIR),
    )
    templates_parser.add_argument(
        "-p", "--template-patches-dir",
        default=env_or_val("APIGENTOOLS_TEMPLATE_PATCHES_DIR", constants.DEFAULT_TEMPLATE_PATCHES_DIR),
        help="Directory with patches for upstream templates (default: '{}')".format(constants.DEFAULT_TEMPLATE_PATCHES_DIR),
    )
    templates_source = templates_parser.add_subparsers(
        dest="templates_source",
        required=True,
        help="Source of upstream templates"
    )
    jar_parser = templates_source.add_parser(
        "openapi-jar",
        help="Obtain upstream templates from openapi-generator jar",
    )
    jar_parser.add_argument(
        "jar_path",
        help="Path to openapi-generator jar file",
    )
    local_parser = templates_source.add_parser(
        "local-dir",
        help="Obtain upstream templates from a local directory (e.g. an openapi-generator git checkout)",
    )
    local_parser.add_argument(
        "local_path",
        help="Path to directory with openapi-generator upstream templates",
    )
    git_parser = templates_source.add_parser(
        "openapi-git",
        help="Obtain upstream templates from openapi-generator git repository",
    )
    git_parser.add_argument(
        "-u", "--repo_url",
        default=constants.OPENAPI_GENERATOR_GIT,
        help="URL of the openapi-generator repo (default: '{}')".format(constants.OPENAPI_GENERATOR_GIT),
    )
    git_parser.add_argument(
        "git_committish",
        default="master",
        nargs="?",
        help="Git 'committish' to check out before obtaining templates (default: 'master')"
    )

    validate_parser = sp.add_parser(
        "validate",
        help="Validate OpenAPI spec",
    )
    # these are duplicated with generate_parser, we should deduplicate
    validate_parser.add_argument(
        "-s", "--spec-dir",
        default=env_or_val("APIGENTOOLS_SPEC_DIR", constants.DEFAULT_SPEC_DIR),
        help="Path to directory with OpenAPI specs (default: '{}')".format(constants.DEFAULT_SPEC_DIR),
    )
    validate_parser.add_argument(
        "-f", "--full-spec-file",
        default=env_or_val("APIGENTOOLS_FULL_SPEC_FILE", "full_spec.yaml"),
        help="Name of the OpenAPI full spec file to write (default: 'full_spec.yaml')",
    )

    test_parser = sp.add_parser(
        "test",
        help="Run tests for generated source code"
    )
    test_parser.add_argument(
        "--no-cache",
        action="store_true",
        default=env_or_val("APIGENTOOLS_TEST_BUILD_NO_CACHE", False, __type=bool),
        help="Build test image with --no-cache option",
    )
    test_parser.add_argument(
        "-g", "--generated-code-dir",
        default=env_or_val("APIGENTOOLS_GENERATED_CODE_DIR", constants.DEFAULT_GENERATED_CODE_DIR),
        help="Path to directory where to save the generated source code (default: '{}')".format(constants.DEFAULT_GENERATED_CODE_DIR),
    )
    test_parser.add_argument(
        "--container-env",
        nargs="*",
        default=env_or_val("APIGENTOOLS_CONTAINER_ENV", [], __type=list),
        help="Additional environment variables to pass to containers running the tests, " +
             "for example `--container-env API_KEY=123 OTHER_KEY=234`. Note that apigentools " +
             "contains additional logic to treat these values as sensitive and avoid logging " +
             "them during runtime. (NOTE: if the testing container itself prints this value, " +
             "it *will* be logged as part of the test output by apigentools)."
    )

    split_parser = sp.add_parser(
        "split",
        help="Split single OpenAPI spec file into multiple files"
    )
    split_parser.add_argument(
        "-i", "--input-file",
        required=True,
        help="Path to the OpenAPI full spec file to split",
    )
    split_parser.add_argument(
        "-s", "--spec-dir",
        default=env_or_val("APIGENTOOLS_SPEC_DIR", constants.DEFAULT_SPEC_DIR),
        help="Path to directory with OpenAPI specs (default: '{}')".format(constants.DEFAULT_SPEC_DIR),
    )
    split_parser.add_argument(
        "-v", "--api-version",
        default=env_or_val("APIGENTOOLS_SPLIT_SPEC_VERSION", "v1"),
        help="Version of API that the input spec describes (default: 'v1')",
    )

    push_parser = sp.add_parser(
        "push",
        help="[WIP Not Yet Available] Push the generated source code into each git repository specified in the config",
    )
    push_parser.add_argument(
        "--use_https",
        action="store_true",
        help="Use HTTPS to interact with the github repositories (default: False and uses SSH)",
        default=False
    )

    init_parser = sp.add_parser(
        "init",
        help="Initialize a new spec repo",
    )
    init_parser.add_argument(
        "projectdir",
        help="Directory to create the new project in (will be created if it doesn't exist)",
    )
    init_parser.add_argument(
        "-g", "--no-git-repo",
        help="Don't initialize a git repository in the project directory",
        default=False,
        action="store_true",
    )

    return p


def cli():
    toplog = logging.getLogger(__name__.split(".")[0])
    set_log(toplog)
    args = get_cli_parser().parse_args()
    if args.verbose:
        set_log_level(toplog, logging.DEBUG)

    command_class = all_commands[args.action]
    command = command_class({}, args)
    if args.action == "init":
        sys.exit(command.run())

    with change_cwd(args.spec_repo_dir):
        command.config = Config.from_file(os.path.join(args.config_dir, constants.DEFAULT_CONFIG_FILE))
        sys.exit(command.run())

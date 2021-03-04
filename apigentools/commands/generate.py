# Unless explicitly stated otherwise all files in this repository are licensed
# under the 3-clause BSD style license (see LICENSE).
# This product includes software developed at Datadog (https://www.datadoghq.com/).
# Copyright 2019-Present Datadog, Inc.
import collections
import copy
import datetime
import json
import logging
import os
import re
import subprocess

import chevron
import click

from apigentools import __version__, constants
from apigentools.commands.command import Command, run_command_with_config
from apigentools.commands.templates import TemplatesCommand
from apigentools.constants import GENERATION_BLACKLIST_FILENAME
from apigentools.utils import (
    get_current_commit,
    run_command,
    write_full_spec,
    env_or_val,
    change_cwd,
)

log = logging.getLogger(__name__)

REPO_SSH_URL = "git@github.com:{}/{}.git"
REPO_HTTPS_URL = "https://{}github.com/{}/{}.git"


@click.command()
@click.option(
    "--clone-repo",
    is_flag=True,
    default=env_or_val("APIGENTOOLS_PULL_REPO", False, __type=bool),
    help="When specified, clones the client repository before running code generation",
)
@click.option(
    "--branch",
    default=env_or_val("APIGENTOOLS_PULL_REPO_BRANCH", None),
    help="When specified, changes the client repository branch before running code generation",
)
@click.option(
    "--is-ancestor",
    default=env_or_val("APIGENTOOLS_IS_ANCESTOR", None),
    help="Checks that the --branch is ancestor of specified base branch (default: None). "
    "Useful to enforce in CI that the feature branch is on top of master branch: "
    "--branch feature --is-ancestor master.",
)
@click.option(
    "-f",
    "--full-spec-file",
    default=env_or_val("APIGENTOOLS_FULL_SPEC_FILE", "full_spec.yaml"),
    help="Name of the OpenAPI full spec file to write (default: 'full_spec.yaml'). "
    + "Note that if some languages override config's spec_sections, additional "
    + "files will be generated with name pattern 'full_spec.<lang>.yaml'",
)
@click.option(
    "--additional-stamp",
    multiple=True,
    nargs=10,
    help="Additional components to add to the 'apigentoolsStamp' variable passed to templates",
    default=env_or_val("APIGENTOOLS_ADDITIONAL_STAMP", (), __type=list),
)
@click.option(
    "--git-email",
    help="Email of the user to author git commits as. Note this will permanently"
    " modify the local repos git config to use this author",
    default=env_or_val("APIGENTOOLS_GIT_AUTHOR_EMAIL", None),
)
@click.option(
    "--git-name",
    help="Name of the user to author git commits as. Note this will permanently"
    " modify the local repos git config to use this author",
    default=env_or_val("APIGENTOOLS_GIT_AUTHOR_NAME", None),
)
@click.option(
    "--skip-templates",
    is_flag=True,
    default=env_or_val("APIGENTOOLS_SKIP_TEMPLATES", False, __type=bool),
    help="When specified, skips the templates generation step",
)
@click.option(
    "--delete-generated-files",
    is_flag=True,
    default=False,
    help="Delete generated files in output_dir before generation",
)
@click.pass_context
def generate(ctx, **kwargs):
    """Generate client code"""
    run_command_with_config(GenerateCommand, ctx, **kwargs)


class GenerateCommand(Command):
    __cached_codegen_version = None
    # NOTE: update docs/spec_repo.md when changing this
    __default_generate_command = [
        "openapi-generator",
        "generate",
        "--http-user-agent",
        "{{user_agent_client_name}}/{{library_version}}/{{language_name}}",
        "-g",
        "{{language_name}}",
        "-c",
        "{{language_config}}",
        "-i",
        "{{full_spec_path}}",
        "-o",
        "{{version_output_dir}}",
        "--additional-properties",
        "apigentoolsStamp='{{stamp}}'",
    ]

    def get_default_generate_function(self, builtin_templates):
        """Returns a function that can be used in commands to expand to the default generate command.

        :param builtin_templates: Whether or not openapi-generator builtin templates should be used
        :type builtin_templates: ``bool``
        :return: Function that expands to the default generate command
        :rtype: ``function``
        """
        ret = copy.deepcopy(self.__default_generate_command)
        if not builtin_templates:
            ret.extend(["-t", "{{templates_dir}}"])

        def inner():
            return ret

        return inner

    def run_language_commands(self, language, version, cwd, chevron_vars=None):
        """Runs commands specified in language settings for given language and phase

        :param language: Language to run commands for
        :type language: ``str``
        :param version: Version to run commands for
        :type version: ``str``
        :param cwd: Directory to change to while executing all commands
        :type cwd: ``str``
        :param chevron_vars: Placeholders to replace in command
        :type chevron_vars: ``dict``
        """
        lc = self.config.get_language_config(language)
        commands = lc.commands_for(version)
        log.info("Running commands for %s/%s", language, version)

        use_builtin_templates = not bool(lc.templates_config_for(version))
        default_generate_func = self.get_default_generate_function(
            use_builtin_templates
        )

        for command in commands:
            self.run_config_command(
                command,
                "{l}/{v}".format(l=language, v=version),
                cwd,
                chevron_vars,
                additional_functions={
                    "openapi_generator_generate": default_generate_func
                },
            )

    def render_downstream_templates(self, language_config, chevron_vars):
        """Render the templates included in this repository under `downstream-templates/`

        :param language_config: Config of language to render templates for
        :type language_config: ``LanguageConfig``
        :param chevron_vars: Rendering context for chevron to provide to templates
        :type chevron_vars: ``dict``
        """
        tpls = language_config.downstream_templates
        if not tpls:
            log.info("No downstream templates for %s", language_config.language)
            return

        log.info("Rendering downstream templates ...")

        for source, destination in tpls.items():
            target_path = os.path.join(language_config.generated_lang_dir, destination)
            # build the full path to the target if it doesn't exist
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            log.info("Writing {target}".format(target=target_path))
            with open(source) as temp, open(target_path, "w") as target:
                target.write(chevron.render(temp, chevron_vars))

    def get_stamp(self):
        """Get string for "stamping" files for trackability

        :return: Stamp, for example:
            "Generated with: apigentools version X.Y.Z (image: apigentools:X.Y.Z); spec repo commit abcd123"
        :rtype: ``str``
        """
        stamp = "Generated with: apigentools version {version}".format(
            version=__version__
        )
        spec_repo_commit = get_current_commit(".")
        stamp = (stamp,)
        if spec_repo_commit:
            stamp + ("spec repo commit {commit}".format(commit=spec_repo_commit),)
        return "; ".join(stamp + (self.args.get("additional_stamp", ())))

    def write_dot_apigentools_info(self, language_config, version):
        """Write a record for language/version in .apigentools-info file in the top-level directory of the language

        :param language_config: Config of language to write .apigentools-info for
        :type language: ``LanguageConfig``
        :param version: Version to write .apigentools-info record for
        :type version: ``str``
        """
        outfile = os.path.join(language_config.generated_lang_dir, ".apigentools-info")
        loaded = {}
        if os.path.exists(outfile):
            with open(outfile) as f:
                try:
                    loaded = json.load(f)
                except json.JSONDecodeError:
                    log.debug("Couldn't read .apigentools-info, will overwrite")
                if str(loaded.get("info_version")) == "1":
                    log.info("Detected .apigentools-info version 1, will rewrite")
                    loaded = {}

        info = {
            "additional_stamps": self.args.get("additional_stamp"),
            "info_version": "2",
        }
        loaded.update(info)
        loaded.setdefault("spec_versions", {})
        loaded["spec_versions"][version] = {
            "apigentools_version": __version__,
            "regenerated": str(datetime.datetime.utcnow()),
            "spec_repo_commit": get_current_commit("."),
        }
        with open(outfile, "w") as f:
            json.dump(loaded, f, indent=4)

    def run(self):
        info = collections.defaultdict(dict)
        fs_files = set()

        # first, generate full spec for all major versions of the API
        for language, version, fs_file in self.yield_lang_version_specfile():
            info[language][version] = fs_file

            if fs_file in fs_files:
                log.info(f"Reuse {fs_file} for {language} and {version}")
                continue
            fs_files.add(fs_file)

            # Generate full spec file is needed
            write_full_spec(
                constants.SPEC_REPO_SPEC_DIR,
                version,
                self.config.get_language_config(language).spec_sections_for(version),
                fs_file,
            )
            log.info(f"Generated {fs_file} for {language}/{version}")

        pull_repo = self.args.get("clone_repo")

        # now, for each language generate a client library for every major version that is explicitly
        # listed in its settings (meaning that we can have languages that don't support all major
        # API versions)
        for language, versions in info.items():
            language_config = self.config.get_language_config(language)
            general_chevron_vars = language_config.chevron_vars_for()
            general_chevron_vars["stamp"] = self.get_stamp()

            # Clone the language target repo into the output directory
            if pull_repo:
                self.pull_repository(language_config, branch=self.args.get("branch"))

            if self.args.get("delete_generated_files"):
                self.remove_generated_files(language_config)

            for version, input_spec in versions.items():
                if self.args.get("skip_templates"):
                    log.info(
                        "Skipping templates processing for {}/{}".format(
                            language, version
                        )
                    )
                else:
                    tpl_cmd_args = copy.deepcopy(self.args)
                    tpl_cmd_args["languages"] = [language]
                    tpl_cmd_args["api_versions"] = [version]
                    template_cmd = TemplatesCommand(self.config, tpl_cmd_args)
                    retval = template_cmd.run()
                    if retval != 0:
                        return retval
                log.info("Generation in %s/%s", language, version)
                version_output_dir = language_config.generated_lang_version_dir_for(
                    version
                )
                os.makedirs(version_output_dir, exist_ok=True)
                self.run_language_commands(
                    language,
                    version,
                    version_output_dir,
                    language_config.chevron_vars_for(version, input_spec),
                )
                self.write_dot_apigentools_info(language_config, version)

            self.render_downstream_templates(
                language_config, language_config.chevron_vars_for()
            )

        return 0

    def pull_repository(self, language, branch=None):
        if not language.github_repo:
            log.warning("Skipping repository clone because github_repo is empty")
            return
        output_dir = language.generated_lang_dir
        secret_repo_url = False
        if self.args.get("git_via_https"):
            checkout_url = ""
            if self.args.get("git_via_https_oauth_token"):
                checkout_url = "{}:x-oauth-basic@".format(
                    self.args.get("git_via_https_oauth_token")
                )
            elif self.args.get("git_via_https_installation_access_token"):
                checkout_url = "x-access-token:{}@".format(
                    self.args.get("git_via_https_installation_access_token")
                )
            if checkout_url:
                secret_repo_url = True
            repo = REPO_HTTPS_URL.format(
                checkout_url, language.github_org, language.github_repo
            )
        else:
            repo = REPO_SSH_URL.format(language.github_org, language.github_repo)

        try:
            log_repo = (
                "{}/{}".format(language.github_org, language.github_repo)
                if secret_repo_url
                else repo
            )
            log.info("Pulling repository %s", log_repo)
            run_command(
                [
                    "git",
                    "clone",
                    "--depth=2",
                    {"item": repo, "secret": secret_repo_url},
                    output_dir,
                ],
                sensitive_output=secret_repo_url,
            )
        except subprocess.CalledProcessError as e:
            log.error(
                "Error cloning repo {0} into {1}. Make sure {1} is empty first".format(
                    log_repo, output_dir
                )
            )
            raise e

        if branch is not None:
            try:
                run_command(["git", "fetch", "origin", branch], cwd=output_dir)
                run_command(["git", "branch", branch, "FETCH_HEAD"], cwd=output_dir)
                run_command(["git", "checkout", branch], cwd=output_dir)
            except subprocess.CalledProcessError:
                # if the branch doesn't exist, we stay in the default one
                branch = None

        if branch is not None and self.args.get("is_ancestor"):
            try:
                run_command(
                    [
                        "git",
                        "merge-base",
                        "--is-ancestor",
                        self.args.get("is_ancestor"),
                        branch,
                    ],
                    cwd=output_dir,
                )
            except subprocess.CalledProcessError:
                log.warning(
                    f"{self.args.get('is_ancestor')} is not ancestor of branch {branch}, attempting to update branch"
                )
                try:
                    self.setup_git_config(cwd=output_dir)
                    run_command(
                        [
                            "git",
                            "merge",
                            "--no-ff",
                            "--allow-unrelated-histories",
                            self.args.get("is_ancestor"),
                        ],
                        cwd=output_dir,
                    )
                except subprocess.CalledProcessError:
                    log.error(
                        f"Could not merge {self.args.get('is_ancestor')} to {branch} to keep it up-to-date"
                    )
                    raise

    def remove_generated_files(self, language_config):
        """
        Remove all generated files from the generate output directory
        Files are deemed as "generated" if they match any regex in the .generated_files file
        at the root of the output repository.
        """
        blacklist_regexes = set()
        output_dir = os.path.abspath(language_config.generated_lang_dir)
        blacklist_file = os.path.join(output_dir, GENERATION_BLACKLIST_FILENAME)

        log.info(f"Removing generated files from the output directory: {output_dir}")

        if not os.path.exists(blacklist_file):
            log.warning(
                f"File: {blacklist_file} doesn't exist, skipping removal of generated files"
            )
            return

        # We should already be in this directory, but its explicit and safer since we're deleting
        with change_cwd(output_dir):
            # Read in and compile the regexes of files we want to delete
            with open(blacklist_file, "r") as blacklist_file:
                for line in blacklist_file.readlines():
                    blacklist_regexes.add(re.compile(line.strip()))

            # Get all files from current directory recursively
            all_files = [
                os.path.relpath(os.path.join(root, filename), start=output_dir)
                for root, _, files in os.walk(output_dir)
                for filename in files
            ]
            # Match the regex against the list of all files and delete
            for file in all_files:
                if any(
                    blacklist_regex.match(file) for blacklist_regex in blacklist_regexes
                ):
                    log.debug(f"Removing generated file: {file}")
                    os.remove(file)

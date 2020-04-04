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
import subprocess

import chevron
import click

from apigentools import __version__, constants
from apigentools.commands.command import Command
from apigentools.commands.templates import TemplatesCommand
from apigentools.config import Config, ConfigCommand
from apigentools.constants import GITHUB_REPO_URL_TEMPLATE
from apigentools.utils import (
    change_cwd,
    get_current_commit,
    run_command,
    write_full_spec,
    env_or_val,
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
@click.pass_context
def generate(ctx, **kwargs):
    """Generate client code"""
    ctx.obj.update(kwargs)
    cmd = GenerateCommand({}, ctx.obj)
    with change_cwd(ctx.obj.get("spec_repo_dir")):
        cmd.config = Config.from_file(
            os.path.join(constants.SPEC_REPO_CONFIG_DIR, constants.DEFAULT_CONFIG_FILE)
        )
        ctx.exit(cmd.run())


class GenerateCommand(Command):
    __cached_codegen_version = None
    __default_generate_command = ConfigCommand(
        "default",
        "generate",
        {
            "description": "Generate code using openapi-generator",
            "use_container": True,
            "commandline": [
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
                "-t",
                "templates/{{language_name}}/{{spec_version}}",
            ],
        },
        None,
    )

    def run_language_commands(
        self, language, version, phase, cwd, chevron_vars=None, default_commands=None
    ):
        """ Runs commands specified in language settings for given language and phase

        :param language: Language to run commands for
        :type language: ``str``
        :param version: Version to run commands for
        :type version: ``str``
        :param phase: Phase to run commands for (either ``pre``, ``generate`` or ``post``)
        :type phase: ``str``
        :param cwd: Directory to change to while executing all commands
        :type cwd: ``str``
        :param chevron_vars: Placeholders to replace in command
        :type chevron_vars: ``dict``
        """
        lc = self.config.get_language_config(language)
        commands = lc.get_commands(version, phase) or default_commands or []
        if commands:
            log.info("Running '%s' commands for %s/%s", phase, language, version)
        else:
            log.info("No '%s' commands found for %s/%s", phase, language, version)

        for command in commands:
            self.run_config_command(
                command,
                "language '{l}'".format(l=language),
                cwd,
                chevron_vars=chevron_vars,
            )

    def render_downstream_templates(self, language_config, chevron_vars):
        """ Render the templates included in this repository under `downstream-templates/`

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
            target_path = os.path.join(
                self.get_generated_lang_dir(language_config.language), destination
            )
            # build the full path to the target if it doesn't exist
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            log.info("Writing {target}".format(target=target_path))
            with open(source) as temp, open(target_path, "w") as target:
                target.write(chevron.render(temp, chevron_vars))

    def get_stamp(self):
        """ Get string for "stamping" files for trackability

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
        return "; ".join(stamp + (self.args.get("additional_stamp")))

    def write_dot_apigentools_info(self, language, version):
        """ Write a record for language/version in .apigentools-info file in the top-level directory of the language

        :param language: Language to write .apigentools-info for
        :type language: ``str``
        :param version: Version to write .apigentools-info record for
        :type version: ``str``
        """
        outfile = os.path.join(
            self.get_generated_lang_dir(language), ".apigentools-info"
        )
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
            "apigentools_version": __version__,
            "info_version": "2",
            "spec_repo_commit": get_current_commit("."),
        }
        loaded.update(info)
        loaded.setdefault("spec_versions", {})
        loaded["spec_versions"][version] = {
            "regenerated": str(datetime.datetime.utcnow())
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
            log.info(f"Generated {fs_file} for {language} and {version}")

        pull_repo = self.args.get("clone_repo")

        # now, for each language generate a client library for every major version that is explicitly
        # listed in its settings (meaning that we can have languages that don't support all major
        # API versions)
        for language, versions in info.items():
            language_config = self.config.get_language_config(language)
            general_chevron_vars = {
                "github_repo_name": language_config.github_repo,
                "github_repo_org": language_config.github_org,
                "github_repo_url": chevron.render(
                    GITHUB_REPO_URL_TEMPLATE, language_config.raw_dict
                ),
                "language_name": language,
                "library_version": language_config.library_version,
                "stamp": self.get_stamp(),
                "user_agent_client_name": self.config.user_agent_client_name,
            }

            # Clone the language target repo into the output directory
            if pull_repo:
                self.pull_repository(language_config, branch=self.args.get("branch"))

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
                log.info("Generation in %s, spec version %s", language, version)
                language_oapi_config_path = os.path.join(
                    constants.SPEC_REPO_CONFIG_DIR,
                    constants.SPEC_REPO_LANGUAGES_CONFIG_DIR,
                    "{lang}_{v}.json".format(lang=language, v=version),
                )
                version_output_dir = self.get_generated_lang_version_dir(
                    language, version
                )

                chevron_vars = copy.deepcopy(general_chevron_vars)
                chevron_vars.update(
                    {
                        "full_spec_path": input_spec,
                        "language_config": language_oapi_config_path,
                        "spec_version": version,
                        "version_output_dir": version_output_dir,
                    }
                )
                default_generate_cmd = copy.deepcopy(self.__default_generate_command)
                default_generate_cmd.language_config = language_config

                os.makedirs(version_output_dir, exist_ok=True)
                self.run_language_commands(
                    language, version, "pre", version_output_dir, chevron_vars
                )

                self.run_language_commands(
                    language,
                    version,
                    "generate",
                    ".",
                    chevron_vars,
                    [default_generate_cmd],
                )

                self.run_language_commands(
                    language, version, "post", version_output_dir, chevron_vars
                )
                self.write_dot_apigentools_info(language, version)

            self.render_downstream_templates(language_config, general_chevron_vars)

        return 0

    def pull_repository(self, language, branch=None):
        output_dir = self.get_generated_lang_dir(language.language)
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

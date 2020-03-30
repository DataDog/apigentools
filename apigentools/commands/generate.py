# Unless explicitly stated otherwise all files in this repository are licensed
# under the 3-clause BSD style license (see LICENSE).
# This product includes software developed at Datadog (https://www.datadoghq.com/).
# Copyright 2019-Present Datadog, Inc.
import collections
import copy
import json
import logging
import os
import subprocess

import chevron
import click

from apigentools import __version__, constants
from apigentools.commands.command import Command
from apigentools.commands.templates import TemplatesCommand
from apigentools.config import Config
from apigentools.constants import GITHUB_REPO_URL_TEMPLATE, LANGUAGE_OAPI_CONFIGS
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
    "-s",
    "--spec-dir",
    default=env_or_val("APIGENTOOLS_SPEC_DIR", constants.DEFAULT_SPEC_DIR),
    help="Path to directory with OpenAPI specs (default: '{}')".format(
        constants.DEFAULT_SPEC_DIR
    ),
)
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
    "-i",
    "--generated-with-image",
    default=env_or_val("APIGENTOOLS_IMAGE", None),
    help="Override the tag of the image with which the client code was generated",
)
@click.option(
    "-d",
    "--downstream-templates-dir",
    default=env_or_val(
        "APIGENTOOLS_DOWNSTREAM_TEMPLATES_DIR",
        constants.DEFAULT_DOWNSTREAM_TEMPLATES_DIR,
    ),
    help="Path to directory with downstream templates (default: '{}')".format(
        constants.DEFAULT_DOWNSTREAM_TEMPLATES_DIR
    ),
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
    "-t",
    "--template-dir",
    default=env_or_val("APIGENTOOLS_TEMPLATES_DIR", constants.DEFAULT_TEMPLATES_DIR),
    help="Path to directory with processed upstream templates (default: '{}')".format(
        constants.DEFAULT_TEMPLATES_DIR
    ),
)
@click.option(
    "--builtin-templates",
    is_flag=True,
    default=False,
    help="Use unpatched upstream templates",
)
@click.option(
    "-T",
    "--templates-output-dir",
    default=env_or_val("APIGENTOOLS_TEMPLATES_DIR", constants.DEFAULT_TEMPLATES_DIR),
    help="Path to directory where to put processed upstream templates (default: {})".format(
        constants.DEFAULT_TEMPLATES_DIR
    ),
)
@click.option(
    "--templates-source",
    type=click.Choice(
        [
            constants.TEMPLATES_SOURCE_LOCAL_DIR,
            constants.TEMPLATES_SOURCE_OPENAPI_GIT,
            constants.TEMPLATES_SOURCE_OPENAPI_JAR,
            constants.TEMPLATES_SOURCE_SKIP,
        ],
        case_sensitive=False,
    ),
    default=env_or_val("APIGENTOOLS_TEMPLATES_SOURCE", constants.TEMPLATES_SOURCE_SKIP),
    help="Source to use for obtaining templates to be processed (default: 'skip')",
)
@click.option(
    "-p",
    "--template-patches-dir",
    default=env_or_val(
        "APIGENTOOLS_TEMPLATE_PATCHES_DIR", constants.DEFAULT_TEMPLATE_PATCHES_DIR
    ),
    help="Directory with patches for upstream templates (default: '{}')".format(
        constants.DEFAULT_TEMPLATE_PATCHES_DIR
    ),
)
@click.option(
    "--jar-path",
    nargs=1,
    default=env_or_val("APIGENTOOLS_OPENAPI_JAR", constants.OPENAPI_JAR),
    help="Path to openapi-generator jar file (use if --templates-source=openapi-jar)",
)
@click.option(
    "-u",
    "--repo_url",
    default=constants.OPENAPI_GENERATOR_GIT,
    help="URL of the openapi-generator repo (default: '{}'; use if --templates-source=openapi-git)".format(
        constants.OPENAPI_GENERATOR_GIT
    ),
)
@click.option(
    "--git-committish",
    default="master",
    nargs=1,
    help="Git 'committish' to check out before obtaining templates "
    "(default: 'master'; use if --templates-source=openapi-git)",
)
@click.pass_context
def generate(ctx, **kwargs):
    """Generate client code"""
    ctx.obj.update(kwargs)
    cmd = GenerateCommand({}, ctx.obj)
    with change_cwd(ctx.obj.get("spec_repo_dir")):
        cmd.config = Config.from_file(
            os.path.join(ctx.obj.get("config_dir"), constants.DEFAULT_CONFIG_FILE)
        )
        ctx.exit(cmd.run())


class GenerateCommand(Command):
    __cached_codegen_version = None

    def run_language_commands(self, language, phase, cwd, chevron_vars=None):
        """ Runs commands specified in language settings for given language and phase

        :param language: Language to run commands for
        :type language: ``str``
        :param phase: Phase to run commands for (either ``pre`` or ``post``)
        :type phase: ``str``
        :param cwd: Directory to change to while executing all commands
        :type cwd: ``str``
        :param chevron_vars: Placeholders to replace in command
        :type chevron_vars: ``dict``
        """
        with change_cwd(cwd):
            lc = self.config.languages[language]
            commands = lc.commands.get(phase, [])
            if commands:
                log.info("Running '%s' commands for language '%s'", phase, language)
            else:
                log.info("No '%s' commands found for language '%s'", phase, language)

            for command in commands:
                self.run_config_command(
                    command,
                    "language '{l}'".format(l=language),
                    lc.command_env,
                    chevron_vars=chevron_vars,
                )

    def render_downstream_templates(self, language, downstream_templates_dir):
        """ Render the templates included in this repository under `downstream-templates/`

        :param language: Language to render templates for (also has to be a subdirectory
            of the directory given by ``downstream_templates_dir``)
        :type language: ``str``
        :param downstream_templates_dir: Path to the directory with downstream templates
        :type downstream_templates_dir: ``str``
        """
        log.info("Rendering downstream templates ...")
        templates_dir = os.path.join(downstream_templates_dir, language)
        if not os.path.exists(templates_dir):
            return

        settings = dict(self.config.languages[language])
        settings["github_repo_url"] = chevron.render(GITHUB_REPO_URL_TEMPLATE, settings)
        settings["apigentoolStamp"] = self.get_stamp()

        for root, _, files in os.walk(templates_dir):
            for f in files:
                template_path = os.path.join(root, f)
                relative_path = template_path[len(templates_dir) :].strip("/")
                target_path = os.path.join(
                    self.get_generated_lang_dir(language), relative_path
                )
                # build the full path to the target if doesn't exist
                os.makedirs(os.path.dirname(target_path), exist_ok=True)
                log.info("Writing {target}".format(target=target_path))
                with open(template_path) as temp, open(target_path, "w") as target:
                    target.write(chevron.render(temp, settings))

    def get_version_from_lang_oapi_config(self, oapi_config):
        """ Gets the version of package from the given language config.

        :param oapi_config: the loaded language config
        :type oapi_config: ``dict`
        :return: package version
        :rtype: ``str``
        :raises: ``KeyError`` if no version is found
        """
        for kname in ["packageVersion", "artifactVersion"]:
            if kname in oapi_config:
                return oapi_config[kname]

        raise KeyError("no package version found in language config")

    def get_image_name(self):
        """ Assuming that this invocation of apigentools is running in an image and the specified
        image tag is `:latest`, this function will replace it with `:git-1234abc`. Otherwise it will
        return unmodified image name.
        """
        image = self.args.get("generated_with_image")

        if image is not None and image.endswith(":latest"):
            hash_file = os.environ.get(
                "_APIGENTOOLS_GIT_HASH_FILE", "/var/lib/apigentools/git-hash"
            )
            try:
                with open(hash_file, "r") as f:
                    git_hash = f.read().strip()
                    if git_hash:
                        tag = "git-{}".format(git_hash[:7])
                        image = image[: -len("latest")] + tag
            except Exception as e:
                log.debug(
                    "Failed reading git hash from {}: {}".format(hash_file, str(e))
                )

        return image

    def get_stamp(self):
        """ Get string for "stamping" files for trackability

        :return: Stamp, for example:
            "Generated with: apigentools version X.Y.Z (image: apigentools:X.Y.Z); spec repo commit abcd123"
        :rtype: ``str``
        """
        stamp = "Generated with: apigentools version {version}".format(
            version=__version__
        )
        if self.get_image_name() is None:
            stamp += " (non-container run)"
        else:
            stamp += " (image: '{image}')".format(image=self.get_image_name())
        spec_repo_commit = get_current_commit(self.args.get("spec_repo_dir"))
        stamp = (stamp,)
        if spec_repo_commit:
            stamp + ("spec repo commit {commit}".format(commit=spec_repo_commit),)
        stamp + ("codegen version {v}".format(v=self.get_codegen_version()),)
        return "; ".join(stamp + (self.args.get("additional_stamp")))

    def get_codegen_version(self):
        """ Gets and caches version of the configured codegen_exec. Returns the cached result on subsequent invocations.

        :return: Codegen version, for example ``4.1.0``; ``None`` if getting the version failed
        :rtype: ``str``
        """
        if self.__cached_codegen_version is None:
            try:
                res = run_command([self.config.codegen_exec, "version"])
                self.__cached_codegen_version = res.stdout.strip()
            except subprocess.CalledProcessError:
                pass

        return self.__cached_codegen_version

    def write_dot_apigentools_info(self, language):
        """ Write .apigentools-info file in the top-level directory of the given language

        :param language: Language to write .apigentools-info for
        :type language: ``str``
        """
        outfile = os.path.join(
            self.get_generated_lang_dir(language), ".apigentools-info"
        )
        info = {
            "additional_stamps": self.args.get("additional_stamp"),
            "apigentools_version": __version__,
            "codegen_version": self.get_codegen_version(),
            "info_version": "1",
            "image": self.get_image_name(),
            "spec_repo_commit": get_current_commit(self.args.get("spec_repo_dir")),
        }
        with open(outfile, "w") as f:
            json.dump(info, f, indent=4)

    def get_missing_templates(self, languages):
        missing = []
        for language in languages:
            if not os.path.exists(
                os.path.join(self.args.get("template_dir"), language)
            ):
                missing.append(language)
        return missing

    def run(self):
        if self.args.get("templates_source") == constants.TEMPLATES_SOURCE_SKIP:
            log.info("Skipping templates processing")
        else:
            log.info("Generating templates")
            template_cmd = TemplatesCommand({}, self.args)
            template_cmd.config = Config.from_file(
                os.path.join(self.args.get("config_dir"), constants.DEFAULT_CONFIG_FILE)
            )
            templates_result = template_cmd.run()
            if templates_result != 0:
                return templates_result
            log.info(
                "Templates processed successfully, proceeding with code generation"
            )

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
                self.config,
                self.args.get("spec_dir"),
                version,
                self.config.languages[language].spec_sections,
                fs_file,
            )
            log.info(f"Generated {fs_file} for {language} and {version}")

        pull_repo = self.args.get("clone_repo")

        missing_templates = self.get_missing_templates(info.keys())
        if missing_templates and not self.args.get("builtin_templates"):
            log.error(
                "Missing templates for %s; please run `apigentools templates` first",
                ", ".join(missing_templates),
            )
            return 1

        # cache codegen version
        if self.get_codegen_version() is None:
            log.error("Failed to get codegen version, exiting")
            return 1

        # now, for each language generate a client library for every major version that is explicitly
        # listed in its settings (meaning that we can have languages that don't support all major
        # API versions)
        for language, versions in info.items():
            language_config = self.config.languages[language]

            # Clone the language target repo into the output directory
            if pull_repo:
                self.pull_repository(language_config, branch=self.args.get("branch"))

            for version, input_spec in versions.items():
                chevron_vars = {"spec_version": version}  # used to modify commands

                log.info("Generation in %s, spec version %s", language, version)
                language_oapi_config_path = os.path.join(
                    self.args.get("config_dir"),
                    LANGUAGE_OAPI_CONFIGS,
                    "{lang}_{v}.json".format(lang=language, v=version),
                )
                with open(language_oapi_config_path) as lcp:
                    language_oapi_config = json.load(lcp)
                version_output_dir = self.get_generated_lang_version_dir(
                    language, version
                )

                # get the language-specific spec if it exists, fallback to the general one
                generate_cmd = [
                    self.config.codegen_exec,
                    "generate",
                    "--http-user-agent",
                    "{c}/{v}/{l}".format(
                        c=self.config.user_agent_client_name,
                        v=self.get_version_from_lang_oapi_config(language_oapi_config),
                        l=language,
                    ),
                    "-g",
                    language,
                    "-c",
                    language_oapi_config_path,
                    "-i",
                    input_spec,
                    "-o",
                    version_output_dir,
                    "--additional-properties",
                    "apigentoolsStamp='{stamp}'".format(stamp=self.get_stamp()),
                ]

                if not self.args.get("builtin_templates"):
                    generate_cmd.extend(
                        ["-t", os.path.join(self.args.get("template_dir"), language)]
                    )

                if language_config.generate_extra_args:
                    generate_cmd.extend(language_config.generate_extra_args)

                os.makedirs(version_output_dir, exist_ok=True)
                self.run_language_commands(
                    language, "pre", version_output_dir, chevron_vars
                )

                run_command(
                    self._render_command_args(generate_cmd, chevron_vars),
                    additional_env=language_config.command_env,
                )

                self.run_language_commands(
                    language, "post", version_output_dir, chevron_vars
                )

                self.render_downstream_templates(
                    language, self.args.get("downstream_templates_dir")
                )

            # Write the apigentools.info file once per language
            # after each nested folder has been created
            self.write_dot_apigentools_info(language)

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

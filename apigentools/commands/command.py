# Unless explicitly stated otherwise all files in this repository are licensed
# under the 3-clause BSD style license (see LICENSE).
# This product includes software developed at Datadog (https://www.datadoghq.com/).
# Copyright 2019-Present Datadog, Inc.
import abc
import glob
import logging
import os
import subprocess

import chevron

from apigentools.config import Config, ContainerImageBuild, FunctionArgument
from apigentools import constants
from apigentools import errors
from apigentools.utils import (
    change_cwd,
    fmt_cmd_out_for_log,
    get_full_spec_file_name,
    glob_re,
    run_command,
    check_for_legacy_config,
)

log = logging.getLogger(__name__)


def run_command_with_config(command_class, click_ctx, **kwargs):
    click_ctx.obj.update(kwargs)
    cmd = command_class({}, click_ctx.obj)

    with change_cwd(click_ctx.obj.get("spec_repo_dir")):
        configfile = os.path.join(
            os.path.join(constants.SPEC_REPO_CONFIG_DIR, constants.DEFAULT_CONFIG_FILE)
        )
        try:
            cmd.config = Config.from_file(configfile)
        except OSError:
            check_for_legacy_config(click_ctx, configfile)
        try:
            click_ctx.exit(cmd.run())
        except errors.ApigentoolsError as e:
            log.error("Apigentools error: %s", e)
        except subprocess.CalledProcessError as e:
            log.error("Failed running subprocess: %s", e.cmd)
            log.error(fmt_cmd_out_for_log(e, False))
            click_ctx.exit(1)


class Command(abc.ABC):
    def __init__(self, config, args):
        self.config = config
        self.args = args

    def yield_lang_version(self, languages=None, versions=None):
        languages = set(
            languages or self.args.get("languages", []) or self.config.languages
        )
        allowed_versions = set(
            versions or self.args.get("api_versions", []) or self.config.spec_versions
        )
        for language in sorted(languages):
            language_config = self.config.get_language_config(language)
            versions = set(language_config.spec_versions or self.config.spec_versions)
            for version in sorted(versions & allowed_versions):
                yield language, version

    def yield_lang_version_specfile(self, languages=None, versions=None):
        """Yield valid combinations of (language, version, specfile)."""
        for language, version in self.yield_lang_version(languages, versions):
            language_config = self.config.get_language_config(language)
            spec_version_dir = os.path.join(constants.SPEC_REPO_SPEC_DIR, version)
            suffix = (
                language
                if language_config.spec_sections_for(version)
                != self.config.spec_sections_for(version)
                else None
            )
            yield language, version, os.path.join(
                spec_version_dir,
                get_full_spec_file_name(self.args.get("full_spec_file"), suffix),
            )

    def setup_git_config(self, cwd=None):
        """Update git config for this repository to use the provided author's email/name.

        If not specified, use the setup from the system/global
        """
        if self.args.get("git_email"):
            run_command(
                ["git", "config", "user.email", self.args.get("git_email")],
                dry_run=self.args.get("dry_run", False),
                cwd=cwd,
            )
        if self.args.get("git_name"):
            run_command(
                ["git", "config", "user.name", self.args.get("git_name")],
                dry_run=self.args.get("dry_run", False),
                cwd=cwd,
            )

    def _render_command_args(self, args, chevron_vars):
        """Recursively renders all args, including list items and dict values"""
        retval = args

        if isinstance(args, str):
            retval = chevron.render(args, chevron_vars)
        elif isinstance(args, list):
            retval = []
            for i in args:
                retval.append(self._render_command_args(i, chevron_vars))
        elif isinstance(args, dict):
            retval = {}
            for k, v in args.items():
                retval[k] = self._render_command_args(v, chevron_vars)
        elif isinstance(args, FunctionArgument):
            args.args = self._render_command_args(args.args, chevron_vars)
            args.kwargs = self._render_command_args(args.kwargs, chevron_vars)

        return retval

    def run_config_command(
        self,
        command,
        what_command,
        cwd=".",
        chevron_vars=None,
        additional_functions=None,
        env_override=None,
        docker_run_options=None,
    ):
        log.info("Running command '%s'", command.description)

        env_override = env_override or {}
        if chevron_vars is None:
            chevron_vars = {}
        chevron_vars["cwd"] = cwd

        to_run = []
        for part in self._render_command_args(command.commandline, chevron_vars):
            if isinstance(part, FunctionArgument):
                allowed_functions = {"glob": glob.glob, "glob_re": glob_re}
                allowed_functions.update(additional_functions or {})
                function_name = part.function
                function = allowed_functions.get(function_name)
                if function:
                    with change_cwd(cwd):
                        result = function(*part.args, **part.kwargs)
                    # NOTE: we may need to improve this logic if/when we add more functions
                    result = self._render_command_args(result, chevron_vars)
                    if isinstance(result, list):
                        to_run.extend(result)
                    else:
                        to_run.append(result)
                else:
                    raise ValueError(
                        "Unknow function '{f}' in command '{d}' for '{l}'".format(
                            f=function_name, d=command.description, l=what_command
                        )
                    )
            else:
                to_run.append(str(part))

        additional_env = command.container_opts.environment
        additional_env.update(env_override)
        is_system = command.container_opts.system
        run_command_args = {}
        if is_system:
            run_command_args.update({"additional_env": additional_env, "cwd": cwd})
        else:
            image = command.container_opts.image
            if isinstance(image, ContainerImageBuild):
                image_name = "apigentools-test-{}".format(
                    what_command.replace("/", "-")
                )
                dockerfile = self._render_command_args(image.dockerfile, chevron_vars)
                context = self._render_command_args(image.context, chevron_vars)
                with change_cwd(cwd):
                    run_command(
                        ["docker", "build", context, "-t", image_name, "-f", dockerfile]
                    )
                image = image_name
            # dockerize
            workdir = os.path.join(
                "/tmp/spec-repo",
                cwd,
                self._render_command_args(
                    command.container_opts.workdir,
                    chevron_vars,
                ),
            )
            dockerized = [
                "docker",
                "run",
                "--rm",
                "-v",
                "{}:{}".format(os.getcwd(), "/tmp/spec-repo"),
                "--workdir",
                workdir,
            ]
            if to_run:
                dockerized.extend(["--entrypoint", to_run[0]])
            for k, v in additional_env.items():
                dockerized.extend(["-e", "{}={}".format(k, v)])
            if docker_run_options:
                dockerized.extend(docker_run_options)

            dockerized.extend([image] + to_run[1:])
            to_run = dockerized

        run_command(to_run, **run_command_args)

    @abc.abstractmethod
    def run(self):
        pass

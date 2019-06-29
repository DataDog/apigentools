import copy
import glob
import json
import logging
import os

import chevron

from apigentools import __version__
from apigentools.commands.command import Command
from apigentools.constants import GITHUB_REPO_URL_TEMPLATE, LANGUAGE_OAPI_CONFIGS
from apigentools.utils import change_cwd, run_command, write_full_spec

log = logging.getLogger(__name__)


class GenerateCommand(Command):
    def run_language_commands(self, language, phase, cwd):
        """ Runs commands specified in language settings for given language and phase

        :param language: Language to run commands for
        :type language: ``str``
        :param phase: Phase to run commands for (either ``pre`` or ``post``)
        :type phase: ``str``
        :param cwd: Directory to change to while executing all commands
        :type cwd: ``str``
        """
        with change_cwd(cwd):
            lc = self.config.get_language_config(language)
            commands = lc.get_stage_commands(phase)
            if commands:
                log.info("Running '%s' commands for language '%s'", phase, language)
            else:
                log.info("No '%s' commands found for language '%s'", phase, language)

            for command in commands:
                log.info("Running command '%s'", command.description)
                to_run = []
                for part in command.commandline:
                    if isinstance(part, dict):
                        allowed_functions = {"glob": glob.glob}
                        function_name = part.get("function")
                        function = allowed_functions.get(function_name)
                        if function:
                            result = function(*part.get("args", []), **part.get("kwargs", {}))
                            # NOTE: we may need to improve this logic if/when we add more functions
                            if isinstance(result, list):
                                to_run.extend(result)
                            else:
                                to_run.append(result)
                        else:
                            raise ValueError(
                                "Unknow function '{f}' in command '{d}' for language '{l}'".format(
                                f=function_name, d=command.description, l=language
                            ))
                    else:
                        to_run.append(str(part))

                run_command(to_run, additional_env=lc.command_env)

    def render_downstream_templates(self, language, downstream_templates_dir, generated_code_dir):
        """ Render the templates included in this repository under `downstream-templates/`

        :param language: Language to render templates for (also has to be a subdirectory
            of the directory given by ``downstream_templates_dir``)
        :type language: ``str``
        :param downstream_templates_dir: Path to the directory with downstream templates
        :type downstream_templates_dir: ``str``
        :param generated_code_dir: Path to the directory in which to put results
        :type generated_code_dir: ``str``
        """
        log.info("Rendering downstream templates ...")
        templates_dir = os.path.join(downstream_templates_dir, language)
        if not os.path.exists(templates_dir):
            return

        settings = copy.deepcopy(self.config.get_language_config(language).raw_dict)
        settings["github_repo_url"] = chevron.render(GITHUB_REPO_URL_TEMPLATE, settings)

        for root, _, files in os.walk(templates_dir):
            for f in files:
                template_path = os.path.join(root, f)
                relative_path = template_path[len(templates_dir):].strip("/")
                target_path = os.path.join(
                    generated_code_dir,
                    settings["github_repo_name"],
                    relative_path,
                )
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

    def run(self):
        fs_paths = {}

        # first, generate full spec for all major versions of the API
        for version in self.config.spec_versions:
            fs_paths[version] = write_full_spec(
                self.config, self.args.spec_dir, version, self.args.full_spec_file
            )

        # now, for each language generate a client library for every major version that is explicitly
        # listed in its settings (meaning that we can have languages that don't support all major
        # API versions)
        for language in self.config.languages:
            language_config = self.config.get_language_config(language)
            for version in language_config.spec_versions:
                log.info("Generation in %s, spec version %s", language, version)
                language_oapi_config_path = os.path.join(
                    self.args.config_dir,
                    LANGUAGE_OAPI_CONFIGS,
                    "{lang}_{v}.json".format(lang=language, v=version)
                )
                with open(language_oapi_config_path) as lcp:
                    language_oapi_config = json.load(lcp)
                version_output_dir = os.path.join(
                    self.args.generated_code_dir,
                    language_config.github_repo_name,
                    chevron.render(language_config.version_path_template, {'spec_version': version})
                )

                stamp = "Generated with: image {img}; apigentools version {version}".format(
                    img=self.args.generated_with_image,
                    version=__version__,
                )
                stamp = "; ".join([stamp] + self.args.additional_stamp)

                generate_cmd = [
                    self.config.codegen_exec,
                    "generate",
                    "--http-user-agent",
                    "DataDog/{v}/{l}".format(
                        v=self.get_version_from_lang_oapi_config(language_oapi_config),
                        l=language
                    ),
                    "-g", language,
                    "-c", language_oapi_config_path,
                    "-i", fs_paths[version],
                    "-o", version_output_dir,
                    "--additional-properties",
                    "apigentoolsStamp='{stamp}'".format(stamp=stamp),
                ]

                if not self.args.builtin_templates:
                    generate_cmd.extend(["-t", os.path.join(self.args.template_dir, language)])

                os.makedirs(version_output_dir, exist_ok=True)
                self.run_language_commands(language, "pre", version_output_dir)

                run_command(generate_cmd, additional_env=language_config.command_env)

                self.run_language_commands(language, "post", version_output_dir)

                self.render_downstream_templates(
                    language,
                    self.args.downstream_templates_dir,
                    self.args.generated_code_dir,
                )

        return 0
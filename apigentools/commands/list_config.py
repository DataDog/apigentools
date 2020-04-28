# Unless explicitly stated otherwise all files in this repository are licensed
# under the 3-clause BSD style license (see LICENSE).
# This product includes software developed at Datadog (https://www.datadoghq.com/).
# Copyright 2020-Present Datadog, Inc.
import json
import logging

import click
import jsonpath_ng

from apigentools.commands.command import Command, run_command_with_config
from apigentools.utils import env_or_val

log = logging.getLogger(__name__)


@click.group(invoke_without_command=True)
@click.option(
    "-f",
    "--full-spec-file",
    default=env_or_val("APIGENTOOLS_FULL_SPEC_FILE", "full_spec.yaml"),
    help="Name of the OpenAPI full spec file to write (default: 'full_spec.yaml'). "
    + "Note that if some languages override config's spec_sections, additional "
    + "files will be generated with name pattern 'full_spec.<lang>.yaml'",
)
@click.option(
    "-L",
    "--list-languages",
    is_flag=True,
    help="List only what languages are supported",
)
@click.option(
    "-V", "--list-versions", is_flag=True, help="List only what versions are supported"
)
@click.pass_context
def config(ctx, **kwargs):
    """Displays information about the configuration for the spec being worked on, including supported languages,
    api versions, and the paths to the generated api yaml. These languages and api versions can be directly
    passed to the `--languages` and `--api-versions` flags of the supported commands."""
    if ctx.invoked_subcommand is None:
        run_command_with_config(ConfigCommand, ctx, **kwargs)


@config.command()
@click.option(
    "--single-value",
    is_flag=True,
    default=False,
    help="Assuming the JSONPath result is a single value, print it without brackets/braces/parentheses.",
)
@click.argument("jsonpath",)
@click.pass_context
def jsonpath(ctx, **kwargs):
    """ Search expanded config for given JSONPATH. """
    run_command_with_config(ConfigCommand, ctx, **kwargs)


class ConfigCommand(Command):
    def run(self):
        if "jsonpath" in self.args is not None:
            try:
                jsonpath_expr = jsonpath_ng.parse(self.args["jsonpath"])
                result = jsonpath_expr.find(self.config.dict())
                if self.args["single_value"]:
                    if len(result) == 1 and isinstance(
                        result[0].value, (str, int, float, bool)
                    ):
                        print(result[0].value)
                    else:
                        log.error(
                            "--single-value provided, but result doesn't have 1 value: %s",
                            [
                                match.value
                                for match in jsonpath_expr.find(self.config.dict())
                            ],
                        )
                        return 1
                else:
                    print(
                        json.dumps(
                            [
                                match.value
                                for match in jsonpath_expr.find(self.config.dict())
                            ]
                        )
                    )
            except Exception as e:  # jsonpath_ng parser really does `raise Exception`, not a more specific exception class
                log.error("Failed parsing JSONPath expression: %s", e)
                return 1

        else:
            # Yields tuples (language, version, spec_path)
            language_info = self.yield_lang_version_specfile()

            # Modify the returned data based on user flags
            if self.args.get("list_languages"):
                out = {lang_info[0] for lang_info in language_info}
            elif self.args.get("list_versions"):
                out = {lang_info[1] for lang_info in language_info}
            else:
                out = [lang_info for lang_info in language_info]

            click.echo(out)
        return 0

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


@config.command("get")
@click.option(
    "-r",
    "--raw",
    is_flag=True,
    default=False,
    help="If the result is a simple value (string, number or boolean), it will be written directly without quotes",
)
@click.argument(
    "jsonpath",
)
@click.pass_context
def jsonpath(ctx, **kwargs):
    """Search expanded config for a single value by given JSONPATH."""
    kwargs["_get_value"] = True
    run_command_with_config(ConfigCommand, ctx, **kwargs)


@config.command("list")
@click.argument(
    "jsonpath",
)
@click.pass_context
def jsonpath(ctx, **kwargs):
    """Search expanded config for values by given JSONPATH."""
    run_command_with_config(ConfigCommand, ctx, **kwargs)


class ConfigCommand(Command):
    def run(self):
        if "jsonpath" in self.args is not None:
            try:
                jsonpath_expr = jsonpath_ng.parse(self.args["jsonpath"])
                result_values = [
                    match.value for match in jsonpath_expr.find(self.config.dict())
                ]
                if self.args.get("_get_value", False):
                    if len(result_values) == 1:
                        to_print = json.dumps(result_values[0])
                        if isinstance(to_print, str) and self.args.get("raw", False):
                            to_print = to_print.strip('"')
                        print(to_print)
                    else:
                        log.error(
                            "Result doesn't have exactly 1 value: %s", result_values
                        )
                        return 1
                else:
                    print(json.dumps(result_values))
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

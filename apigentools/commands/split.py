# Unless explicitly stated otherwise all files in this repository are licensed
# under the 3-clause BSD style license (see LICENSE).
# This product includes software developed at Datadog (https://www.datadoghq.com/).
# Copyright 2019-Present Datadog, Inc.
import copy
import logging
import os
import re
import sys

import click
import yaml

from apigentools import constants
from apigentools.commands.command import Command, run_command_with_config
from apigentools.commands.validate import ValidateCommand
from apigentools.constants import HEADER_FILE_NAME, SHARED_FILE_NAME
from apigentools.utils import env_or_val

log = logging.getLogger(__name__)


@click.command()
@click.argument("input-file")
@click.option(
    "-v",
    "--api-version",
    default=env_or_val("APIGENTOOLS_SPLIT_SPEC_VERSION", "v1"),
    help="Version of API that the input spec describes (default: 'v1')",
)
@click.pass_context
def split(ctx, **kwargs):
    """Split single specified input-file OpenAPI spec file into multiple files"""
    run_command_with_config(SplitCommand, ctx, **kwargs)


class SplitCommand(Command):
    def get_shared_section_name(self):
        return os.path.splitext(SHARED_FILE_NAME)[0]

    def deduplicate_tags(self, all_sections, all_tags):
        """Find all tags that appear in more than one section and move them
        to the ``shared`` section.

        :param all_sections: dict of all existing sections
        :type all_sections: ``dict``
        :param all_tags: list of all existing tags
        :type all_tags: ``list``
        """
        tag_sections = {}
        for section_name, section in all_sections.items():
            if section_name == self.get_shared_section_name():
                continue
            for tag in section["tags"]:
                tag_sections.setdefault(tag["name"], [])
                tag_sections[tag["name"]].append(section_name)
        for tag_name, section_names in tag_sections.items():
            if len(section_names) > 1:
                tag = self.get_tag_object(all_tags, tag_name)
                for section_name in section_names:
                    all_sections[section_name]["tags"].remove(tag)
                all_sections[self.get_shared_section_name()]["tags"].append(tag)

    def deduplicate_components(self, all_sections, all_components):
        """Find all component schemas that appear in more than one section and move them
        to the ``shared`` section.

        :param all_sections: dict of all existing sections
        :type all_sections: ``dict``
        :param all_tags: dict of all existing components
        :type all_tags: ``dict``
        """
        # NOTE: while this function is very similar to deduplicate_tags, it would actually
        # not be very easy (or readable) to unify them, so we keep them separate
        component_sections = {}
        for section_name, section in all_sections.items():
            if section_name == self.get_shared_section_name():
                continue
            for schema_name in section["components"]["schemas"]:
                component_sections.setdefault(schema_name, [])
                component_sections[schema_name].append(section_name)
        for schema_name, section_names in component_sections.items():
            if len(section_names) > 1:
                schema = all_components["schemas"][schema_name]
                for section_name in section_names:
                    all_sections[section_name]["components"]["schemas"].pop(schema_name)
                all_sections[self.get_shared_section_name()]["components"]["schemas"][
                    schema_name
                ] = schema

    def get_endpoints_for_sections(self, all_endpoints):
        """Get mapping of "top-level" endpoints to all endpoints under them.

        Example result:
        {"/api/v1/user": ["/api/v1/user", "/api/v1/user/{username}"],
        "/api/v1/org": ["/api/v1/org", "/api/v1/org/{id}", "/api/v1/org/id/idp_metadata"]}

        :param all_endpoints: list of all endpoints
        :type all_endpoints: ``list`` of ``str``
        :return: mapping of top-level endpoints to all endpoints under them
        :rtype: ``dict``
        """
        endpoints_sections = {}
        for endpoint in all_endpoints:
            add_endpoint = True
            for section in copy.deepcopy(list(endpoints_sections.keys())):
                if section.startswith(endpoint) and section != endpoint:
                    endpoints_sections[endpoint] = set([endpoint])
                    endpoints_sections[endpoint].update(endpoints_sections.pop(section))
                    add_endpoint = False
                elif endpoint.startswith(section):
                    endpoints_sections[section].add(endpoint)
                    add_endpoint = False
            if add_endpoint:
                endpoints_sections[endpoint] = set([endpoint])
        return endpoints_sections

    def get_section_output_path(self, outdir, section):
        """Get name of output file for given section of and OpenAPI spec.

        For example, for section name ``/api/v1/somepath``, the result would be
        ``{outdir}/somepath.yaml``.

        :param outdir: directory in which the output file should be put
        :type outdir: ``str``
        :param section: name of the section
        :type section: ``str``
        :return: full path of the output file for given section
        :rtype: ``str``
        """
        section = section.strip("/")
        if section.endswith(".yaml"):
            section = os.path.splitext(section)[0]
        if section.startswith("api/v"):
            section = section.split("/", 2)[2]
        section = re.sub(r"[^0-9a-zA-Z]+", "_", section)
        return os.path.join(outdir, section + ".yaml")

    def get_tag_object(self, all_tags, tag_name):
        """Return tag object (a dict with ``name`` and ``description`` keys) for given tag name.

        :param all_tags: list of tags to search
        :type all_tags: ``list``
        :param tag_name: tag to search for
        :type tag_name: ``str``
        :return: tag (if found) or ``None`` (if not found)
        :rtype: ``dict`` or ``NoneType``
        """
        for tag_object in all_tags:
            if tag_object["name"] == tag_name:
                return tag_object
        return None

    def update_section_components(self, section, components):
        """Searches for all referenced schemas throughout the whole section and adds
        them to ``section["components"]["schemas"]``.

        :param section: section to process
        :type section: ``dict``
        :param components: dict containing all existing components
        :type components: ``dict``
        """
        for endpoint, endpoint_methods in section["paths"].items():
            for method, method_attrs in endpoint_methods.items():
                self.update_components_recursive(
                    section, components, method_attrs, "{}.{}".format(endpoint, method)
                )

    def update_components_recursive(self, section, components, struct, struct_path):
        """A recursive function to traverse arbitrary data structure, search for all
        referenced schemas and add them to ``section["components"]["schemas"]``.

        :param section: section to process
        :type section: ``dict``
        :param components: dict containing all existing components
        :type components: ``dict``
        :param struct: structure to traverse
        :type struct: any
        :param struct_path: dotted path in parent structure of given structure to make debugging
            easier and print useful error messages
        :type struct_path: ``str``
        """
        if isinstance(struct, list):
            for i, item in enumerate(struct):
                self.update_components_recursive(
                    section, components, item, "{}.{}".format(struct_path, i)
                )
        elif isinstance(struct, dict):
            for k, v in struct.items():
                if k == "$ref":
                    schema_name = v.split("/")[-1]
                    schema = components["schemas"].get(schema_name, None)
                    if not schema:
                        log.warning(
                            "Schema %s referenced in %s doesn't have a definition in 'components'",
                            schema_name,
                            struct_path,
                        )
                    else:
                        section["components"]["schemas"][schema_name] = schema
                        # schemas can reference other schemas
                        self.update_components_recursive(
                            section,
                            components,
                            schema,
                            "{}.$ref({})".format(struct_path, v),
                        )
                else:
                    self.update_components_recursive(
                        section, components, v, "{}.{}".format(struct_path, k)
                    )
        else:
            pass  # primitive type that we can't traverse any more => just pass

    def update_section_tags(self, section, tags):
        """Search for all tags referenced in all endpoints in given section and add them
        to ``section["tags"]``.

        :param section: section to process
        :type section: ``dict``
        :param tags: list of all existing tags
        :type tags: ``list``
        """
        for endpoint, endpoint_methods in section["paths"].items():
            for method, method_attrs in endpoint_methods.items():
                for tag_name in method_attrs.get("tags", []):
                    tag_object = self.get_tag_object(tags, tag_name)
                    if not tag_object:
                        log.warning(
                            "Tag %s listed in %s.%s doesn't have a definition in 'tags' list",
                            tag_name,
                            endpoint,
                            method,
                        )
                    elif tag_object not in section["tags"]:
                        section["tags"].append(tag_object)

    def run(self):
        vc = ValidateCommand(self.config, self.args)
        if not vc.validate_spec(self.args.get("input_file"), None, None):
            log.error("Input OpenAPI spec is not valid, can't proceed with splitting.")
            sys.exit(1)
        log.info("Input OpenAPI spec is valid, proceeding with splitting.")
        outdir = os.path.join(
            constants.SPEC_REPO_SPEC_DIR, self.args.get("api_version")
        )
        with open(self.args.get("input_file")) as f:
            loaded_spec = yaml.safe_load(f)
        paths = loaded_spec.pop("paths")
        components = loaded_spec.pop("components")
        tags = loaded_spec.pop("tags")

        # first, write header
        with open(os.path.join(outdir, HEADER_FILE_NAME), "w") as f:
            f.write(yaml.dump(loaded_spec, default_flow_style=False))

        # now split the spec into multiple sections per top-level API endpoint
        all_sections = {
            self.get_shared_section_name(): {"components": {"schemas": {}}, "tags": []}
        }
        for section_name, endpoints in self.get_endpoints_for_sections(
            paths.keys()
        ).items():
            section = {"paths": {}, "components": {"schemas": {}}, "tags": []}
            for endpoint in endpoints:
                section["paths"][endpoint] = paths[endpoint]
            self.update_section_tags(section, tags)
            self.update_section_components(section, components)
            all_sections[section_name] = section

        # some schemas/tags may appear in multiple sections - move them to "shared" section
        self.deduplicate_tags(all_sections, tags)
        self.deduplicate_components(all_sections, components)

        # write out all the sections
        for section_name, section in all_sections.items():
            with open(self.get_section_output_path(outdir, section_name), "w") as f:
                f.write(yaml.dump(section, default_flow_style=False))
        return 0

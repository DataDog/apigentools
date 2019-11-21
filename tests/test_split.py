import os
import yaml

import flexmock
import pytest

from apigentools.commands.split import SplitCommand
from apigentools.constants import SHARED_SECTION_NAME

# in case I need this
FIXTURES_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "fixtures")


# deduplicate_components
# update_section_components
# update_components_recursive
# update_section_tags


def test_get_endpoints_for_sections():
    args = flexmock.flexmock()
    cmd = SplitCommand({}, args)
    all_endpoints = [
        "api/v1/sheep/",
        "api/v1/alpacas/",
        "api/v1/rabbits/",
        "api/v1/sheep/shetland",
        "api/v1/sheep/herdwick",
        "api/v1/sheep/blue_faced_leicester",
        "api/v1/sheep/merino",
        "api/v1/alpacas/suri",
        "api/v1/alpacas/huacaya",
        "api/v1/rabbits/angora",
    ]

    expected_endpoints = cmd.get_endpoints_for_sections(all_endpoints)

    assert expected_endpoints == {
        "api/v1/sheep/": {
            "api/v1/sheep/blue_faced_leicester",
            "api/v1/sheep/merino",
            "api/v1/sheep/",
            "api/v1/sheep/herdwick",
            "api/v1/sheep/shetland",
        },
        "api/v1/alpacas/": {
            "api/v1/alpacas/suri",
            "api/v1/alpacas/",
            "api/v1/alpacas/huacaya",
        },
        "api/v1/rabbits/": {"api/v1/rabbits/", "api/v1/rabbits/angora"},
    }


def test_get_section_output_path():
    args = flexmock.flexmock()
    cmd = SplitCommand({}, args)
    section = "api/v1/soups"
    outdir = "spec/v1"
    expected_path = cmd.get_section_output_path(outdir, section)
    assert expected_path == "spec/v1/soups.yaml"


def test_get_tag_object():
    args = flexmock.flexmock()
    cmd = SplitCommand({}, args)
    all_tags = [{'name': 'pet', 'description': 'Everything about your Pets'}, {'name': 'store', 'description': 'Access to Petstore orders'}, {'name': 'user', 'description': 'Operations about user'}, {'name': 'cute'}]
    tag_name = "pet"
    tag_object = cmd.get_tag_object(all_tags, tag_name)
    assert tag_object == {'name': 'pet', 'description': 'Everything about your Pets'}

def test_deduplicate_tags_and_components():
    # uses petstore.yaml; should probably change that
    args = flexmock.flexmock()
    cmd = SplitCommand({}, args)
    with open(os.path.join(FIXTURES_DIR, "petstore.yaml")) as f:
        loaded_spec = yaml.safe_load(f)
    paths = loaded_spec.pop("paths")
    components = loaded_spec.pop("components")
    tags = loaded_spec.pop("tags")

    all_sections = {SHARED_SECTION_NAME: {"components": {"schemas": {}}, "tags": []}}
    for section_name, endpoints in cmd.get_endpoints_for_sections(paths.keys()).items():
        section = {"paths": {}, "components": {"schemas": {}}, "tags": []}
        for endpoint in endpoints:
            section["paths"][endpoint] = paths[endpoint]
        cmd.update_section_tags(section, tags)
    expected_tags = [
        {"name": "pet", "description": "Everything about your Pets"},
        {"name": "store", "description": "Access to Petstore orders"},
        {"name": "user", "description": "Operations about user"},
    ]
    # assert tags == expected_tags # this doesn't remove tags? the validator yells about duplicates so how would they get here?












import os
import yaml

import flexmock
import pytest

from apigentools.commands.split import SplitCommand

# in case I need this
# FIXTURES_DIR = os.path.join(
#     os.path.dirname(os.path.realpath(__file__)), "fixtures", "split_fixtures"
# )

# deduplicate_tags
# deduplicate_components
# get_tag_object
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

    endpoints_sections = cmd.get_endpoints_for_sections(all_endpoints)

    assert endpoints_sections == {
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
    path = cmd.get_section_output_path(outdir, section)
    assert path == "spec/v1/soups.yaml"


def test_update_section_components():

    section = {
        "paths": {
            "/api/v1/users": {
                "get": {
                    "description": "Get all registered users",
                    "operationId": "GetAllUsers",
                    "responses": {
                        "200": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/Users"
                                    }
                                }
                            },
                            "description": "OK",
                        },
                        "400": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/Error400"
                                    }
                                }
                            },
                            "description": "Bad Request",
                        },
                    },
                    "summary": "Get all users",
                }
            }
        },
        "components": {"schemas": {}},
        "tags": [],
    }

    components = {
        "callbacks": {},
        "examples": {},
        "headers": {},
        "links": {},
        "parameters": {},
        "requestBodies": {},
        "responses": {},
        "schemas": {
            "Error400": {
                "properties": {
                    "errors": {"items": {"type": "string"}, "type": "array"}
                },
                "type": "object",
            },
            "User": {
                "properties": {
                    "email": {"format": "email", "type": "string"},
                    "name": {"type": "string"},
                },
                "type": "object",
            },
            "Users": {
                "properties": {
                    "users": {
                        "items": {"$ref": "#/components/schemas/User"},
                        "type": "array",
                    }
                },
                "type": "object",
            },
        },
        "securitySchemes": {},
    }

    args = flexmock.flexmock()
    cmd = SplitCommand({}, args)
    # import pdb; pdb.set_trace()

def test_get_tag_object():
    pass
    all_tags = ["a_duplicate", "some_more"]


# def test_split_deduplicate_tags():
#    # test split -i
#     args = flexmock(
#         input_file=os.path.join(FIXTURES_DIR, "full_spec.yaml"),action='split',
#         api_version='v1', api_versions=None, config_dir='config',
#         generated_code_dir='generated', git_via_https=False,
#         git_via_https_installation_access_token='',
#         git_via_https_oauth_token='', languages=None, spec_dir='spec',
#         spec_repo_dir='.', verbose=False
#         )

#     cmd = SplitCommand({}, args)
#     with open(os.path.join(FIXTURES_DIR,"spec", "v1","full_spec.yaml")) as f:
#         loaded_spec = yaml.safe_load(f)
#         paths = loaded_spec.pop("paths")
#         components = loaded_spec.pop("components")
#         tags = loaded_spec.pop("tags")
#     all_sections = {"shared": {"components": {"schemas": {}}, "tags": []}}
#     for section_name, endpoints in cmd.get_endpoints_for_sections(paths.keys()).items():
#         section = {"paths": {}, "components": {"schemas": {}}, "tags": []}
#         for endpoint in endpoints:
#             section["paths"][endpoint] = paths[endpoint]

#         # cmd.update_section_tags(section, tags)
#         # cmd.update_section_components(section, components)
#         all_sections[section_name] = section

#     all_sections = {'shared': {'components': {'schemas': {}}, 'tags': []}}

# cmd.deduplicate_tags(all_sections, tags)


# all_sections = {'shared': {'components': {'schemas': {}}, 'tags': []}, '/api/v1/users': {'paths': {'/api/v1/users': {'get': {'description': 'Get all registered users', 'operationId': 'GetAllUsers', 'responses': {'200': {'content': {'application/json': {'schema': {'$ref': '#/components/schemas/Users'}}}, 'description': 'OK'}, '400': {'content': {'application/json': {'schema': {'$ref': '#/components/schemas/Error400'}}}, 'description': 'Bad Request'}}, 'summary': 'Get all users'}}}, 'components': {'schemas': {'Users': {'properties': {'users': {'items': {'$ref': '#/components/schemas/User'}, 'type': 'array'}}, 'type': 'object'}, 'User': {'properties': {'email': {'format': 'email', 'type': 'string'}, 'name': {'type': 'string'}}, 'type': 'object'}, 'Error400': {'properties': {'errors': {'items': {'type': 'string'}, 'type': 'array'}}, 'type': 'object'}}}, 'tags': []}}

# tags = []

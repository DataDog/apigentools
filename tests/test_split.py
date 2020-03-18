# Unless explicitly stated otherwise all files in this repository are licensed
# under the 3-clause BSD style license (see LICENSE).
# This product includes software developed at Datadog (https://www.datadoghq.com/).
# Copyright 2019-Present Datadog, Inc.
import json
import os

import flexmock

from apigentools.commands.split import SplitCommand

FIXTURES_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "fixtures")


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
    all_tags = [
        {"name": "book", "description": "Book information"},
        {"name": "store", "description": "Access to bookstore orders"},
        {"name": "user", "description": "Operations about user"},
    ]
    tag_name = "book"
    tag_object = cmd.get_tag_object(all_tags, tag_name)
    assert tag_object == {"name": "book", "description": "Book information"}


def test_deduplicate_tags():
    with open(os.path.join(FIXTURES_DIR, "deduplicate_tags.json")) as f:
        all_sections = json.loads(f.read())

    tags = [{"name": "book", "description": "book information"}]

    args = flexmock.flexmock()
    cmd = SplitCommand({}, args)
    cmd.deduplicate_tags(all_sections, tags)
    assert (
        all_sections["shared"]["tags"] == []
    )  # the current sample yaml does not have shared tags


def test_update_section_tags():
    args = flexmock.flexmock()
    cmd = SplitCommand({}, args)
    update_section_tags_section = {
        "paths": {
            "/book": {
                "post": {
                    "tags": ["book"],
                    "summary": "Add a new book to the store",
                    "description": "",
                    "operationId": "addBook",
                    "responses": {"405": {"description": "Invalid input"}},
                    "security": [{"bookstore_auth": ["write:books", "read:books"]}],
                    "requestBody": {"$ref": "#/components/requestBodies/Book"},
                }
            }
        },
        "components": {"schemas": {}},
        "tags": [],
    }

    tags = [{"name": "book", "description": "book information"}]

    cmd.update_section_tags(update_section_tags_section, tags)
    assert update_section_tags_section["tags"] == [
        {"name": "book", "description": "book information"}
    ]


def test_update_section_components():
    section = {
        "paths": {
            "/book": {
                "post": {
                    "tags": ["book"],
                    "summary": "Add a new book to the store",
                    "description": "",
                    "operationId": "addBook",
                    "responses": {"405": {"description": "Invalid input"}},
                    "security": [{"bookstore_auth": ["write:books", "read:books"]}],
                    "requestBody": {"$ref": "#/components/requestBodies/Book"},
                }
            }
        },
        "components": {"schemas": {}},
        "tags": [{"name": "book", "description": "book information"}],
    }

    with open(
        os.path.join(FIXTURES_DIR, "update_section_components_components.json")
    ) as f:
        components = json.loads(f.read())

    # adds schemas to ``section["components"]["schemas"]`` -> starts as {}
    args = flexmock.flexmock()
    cmd = SplitCommand({}, args)
    cmd.update_section_components(section, components)

    assert section["components"]["schemas"] == {
        "Book": {
            "title": "a Book",
            "description": "A book for sale",
            "type": "object",
            "required": ["name", "photoUrls"],
            "properties": {
                "id": {"type": "integer", "format": "int64"},
                "photoUrls": {
                    "type": "array",
                    "xml": {"name": "photoUrl", "wrapped": True},
                    "items": {"type": "string"},
                },
                "status": {
                    "type": "string",
                    "description": "pet status in the store",
                    "enum": ["available", "pending", "sold"],
                },
            },
            "xml": {"name": "Book"},
        }
    }


def test_deduplicate_components():
    with open(
        os.path.join(FIXTURES_DIR, "deduplicate_components_all_sections.json")
    ) as f:
        all_sections = json.loads(f.read())

    with open(
        os.path.join(FIXTURES_DIR, "deduplicate_components_components.json")
    ) as f:
        components = json.loads(f.read())

    args = flexmock.flexmock()
    cmd = SplitCommand({}, args)
    components = cmd.deduplicate_components(all_sections, components)

    assert all_sections["shared"] == {
        "components": {"schemas": {}},
        "tags": [],
    }  # current sample yaml has no shared components

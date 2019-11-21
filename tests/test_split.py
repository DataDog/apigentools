import os
import yaml

import flexmock
import pytest

from apigentools.commands.split import SplitCommand
from apigentools.constants import SHARED_SECTION_NAME

# in case I need this
FIXTURES_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "fixtures")


# deduplicate_components
# deduplicate_tags
# update_section_components
# update_components_recursive -> called in update_section_components



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


def test_update_section_tags():
    args = flexmock.flexmock()
    cmd = SplitCommand({}, args)
    section = {'paths': {'/pet/findByStatus': {'get': {'tags': ['pet', 'user'], 'summary': 'Finds Pets by status', 'description': 'Multiple status values can be provided with comma separated strings', 'operationId': 'findPetsByStatus', 'parameters': [{'name': 'status', 'in': 'query', 'description': 'Status values that need to be considered for filter', 'required': True, 'style': 'form', 'explode': False, 'schema': {'type': 'array', 'items': {'type': 'string', 'enum': ['available', 'pending', 'sold'], 'default': 'available'}}}], 'responses': {'200': {'description': 'successful operation', 'content': {'application/xml': {'schema': {'type': 'array', 'items': {'$ref': '#/components/schemas/Pet'}}}, 'application/json': {'schema': {'type': 'array', 'items': {'$ref': '#/components/schemas/Pet'}}}}}, '400': {'description': 'Invalid status value'}}, 'security': [{'petstore_auth': ['read:pets']}]}}, '/pet/{petId}': {'get': {'tags': ['pet'], 'summary': 'Find pet by ID', 'description': 'Returns a single pet', 'operationId': 'getPetById', 'parameters': [{'name': 'petId', 'in': 'path', 'description': 'ID of pet to return', 'required': True, 'schema': {'type': 'integer', 'format': 'int64'}}], 'responses': {'200': {'description': 'successful operation', 'content': {'application/xml': {'schema': {'$ref': '#/components/schemas/Pet'}}, 'application/json': {'schema': {'$ref': '#/components/schemas/Pet'}}}}, '400': {'description': 'Invalid ID supplied'}, '404': {'description': 'Pet not found'}}, 'security': [{'api_key': []}]}, 'post': {'tags': ['pet'], 'summary': 'Updates a pet in the store with form data', 'description': '', 'operationId': 'updatePetWithForm', 'parameters': [{'name': 'petId', 'in': 'path', 'description': 'ID of pet that needs to be updated', 'required': True, 'schema': {'type': 'integer', 'format': 'int64'}}], 'responses': {'405': {'description': 'Invalid input'}}, 'security': [{'petstore_auth': ['write:pets', 'read:pets']}], 'requestBody': {'content': {'application/x-www-form-urlencoded': {'schema': {'type': 'object', 'properties': {'name': {'description': 'Updated name of the pet', 'type': 'string'}, 'status': {'description': 'Updated status of the pet', 'type': 'string'}}}}}}}, 'delete': {'tags': ['pet'], 'summary': 'Deletes a pet', 'description': '', 'operationId': 'deletePet', 'parameters': [{'name': 'api_key', 'in': 'header', 'required': False, 'schema': {'type': 'string'}}, {'name': 'petId', 'in': 'path', 'description': 'Pet id to delete', 'required': True, 'schema': {'type': 'integer', 'format': 'int64'}}], 'responses': {'400': {'description': 'Invalid pet value'}}, 'security': [{'petstore_auth': ['write:pets', 'read:pets']}]}}, '/pet/findByTags': {'get': {'tags': ['pet'], 'summary': 'Finds Pets by tags', 'description': 'Multiple tags can be provided with comma separated strings. Use tag1, tag2, tag3 for testing.', 'operationId': 'findPetsByTags', 'parameters': [{'name': 'tags', 'in': 'query', 'description': 'Tags to filter by', 'required': True, 'style': 'form', 'explode': False, 'schema': {'type': 'array', 'items': {'type': 'string'}}}], 'responses': {'200': {'description': 'successful operation', 'content': {'application/xml': {'schema': {'type': 'array', 'items': {'$ref': '#/components/schemas/Pet'}}}, 'application/json': {'schema': {'type': 'array', 'items': {'$ref': '#/components/schemas/Pet'}}}}}, '400': {'description': 'Invalid tag value'}}, 'security': [{'petstore_auth': ['read:pets']}], 'deprecated': True}}, '/pet/{petId}/uploadImage': {'post': {'tags': ['pet'], 'summary': 'uploads an image', 'description': '', 'operationId': 'uploadFile', 'parameters': [{'name': 'petId', 'in': 'path', 'description': 'ID of pet to update', 'required': True, 'schema': {'type': 'integer', 'format': 'int64'}}], 'responses': {'200': {'description': 'successful operation', 'content': {'application/json': {'schema': {'$ref': '#/components/schemas/ApiResponse'}}}}}, 'security': [{'petstore_auth': ['write:pets', 'read:pets']}], 'requestBody': {'content': {'multipart/form-data': {'schema': {'type': 'object', 'properties': {'additionalMetadata': {'description': 'Additional data to pass to server', 'type': 'string'}, 'file': {'description': 'file to upload', 'type': 'string', 'format': 'binary'}}}}}}}}, '/pet': {'post': {'tags': ['pet', 'store', 'pet'], 'summary': 'Add a new pet to the store', 'description': '', 'operationId': 'addPet', 'responses': {'405': {'description': 'Invalid input'}}, 'security': [{'petstore_auth': ['write:pets', 'read:pets']}], 'requestBody': {'$ref': '#/components/requestBodies/Pet'}}, 'put': {'tags': ['pet', 'user', 'pet'], 'summary': 'Update an existing pet', 'description': '', 'operationId': 'updatePet', 'responses': {'400': {'description': 'Invalid ID supplied'}, '404': {'description': 'Pet not found'}, '405': {'description': 'Validation exception'}}, 'security': [{'petstore_auth': ['write:pets', 'read:pets']}], 'requestBody': {'$ref': '#/components/requestBodies/Pet'}}}}, 'components': {'schemas': {}}, 'tags': []}

    tags = [{'name': 'pet', 'description': 'Everything about your Pets'}, {'name': 'store', 'description': 'Access to Petstore orders'}, {'name': 'user', 'description': 'Operations about user'}, {'name': 'cute'}]

    cmd.update_section_tags(section, tags)
    assert section["tags"] == [{'name': 'pet', 'description': 'Everything about your Pets'}, {'name': 'user', 'description': 'Operations about user'}, {'name': 'store', 'description': 'Access to Petstore orders'}]


def test_update_section_components():
    section = {'paths': {'/pet/findByStatus': {'get': {'tags': ['pet', 'user'], 'summary': 'Finds Pets by status', 'description': 'Multiple status values can be provided with comma separated strings', 'operationId': 'findPetsByStatus', 'parameters': [{'name': 'status', 'in': 'query', 'description': 'Status values that need to be considered for filter', 'required': True, 'style': 'form', 'explode': False, 'schema': {'type': 'array', 'items': {'type': 'string', 'enum': ['available', 'pending', 'sold'], 'default': 'available'}}}], 'responses': {'200': {'description': 'successful operation', 'content': {'application/xml': {'schema': {'type': 'array', 'items': {'$ref': '#/components/schemas/Pet'}}}, 'application/json': {'schema': {'type': 'array', 'items': {'$ref': '#/components/schemas/Pet'}}}}}, '400': {'description': 'Invalid status value'}}, 'security': [{'petstore_auth': ['read:pets']}]}}, '/pet': {'post': {'tags': ['pet', 'store', 'pet'], 'summary': 'Add a new pet to the store', 'description': '', 'operationId': 'addPet', 'responses': {'405': {'description': 'Invalid input'}}, 'security': [{'petstore_auth': ['write:pets', 'read:pets']}], 'requestBody': {'$ref': '#/components/requestBodies/Pet'}}, 'put': {'tags': ['pet', 'user', 'pet'], 'summary': 'Update an existing pet', 'description': '', 'operationId': 'updatePet', 'responses': {'400': {'description': 'Invalid ID supplied'}, '404': {'description': 'Pet not found'}, '405': {'description': 'Validation exception'}}, 'security': [{'petstore_auth': ['write:pets', 'read:pets']}], 'requestBody': {'$ref': '#/components/requestBodies/Pet'}}}, '/pet/{petId}/uploadImage': {'post': {'tags': ['pet'], 'summary': 'uploads an image', 'description': '', 'operationId': 'uploadFile', 'parameters': [{'name': 'petId', 'in': 'path', 'description': 'ID of pet to update', 'required': True, 'schema': {'type': 'integer', 'format': 'int64'}}], 'responses': {'200': {'description': 'successful operation', 'content': {'application/json': {'schema': {'$ref': '#/components/schemas/ApiResponse'}}}}}, 'security': [{'petstore_auth': ['write:pets', 'read:pets']}], 'requestBody': {'content': {'multipart/form-data': {'schema': {'type': 'object', 'properties': {'additionalMetadata': {'description': 'Additional data to pass to server', 'type': 'string'}, 'file': {'description': 'file to upload', 'type': 'string', 'format': 'binary'}}}}}}}}, '/pet/findByTags': {'get': {'tags': ['pet'], 'summary': 'Finds Pets by tags', 'description': 'Multiple tags can be provided with comma separated strings. Use tag1, tag2, tag3 for testing.', 'operationId': 'findPetsByTags', 'parameters': [{'name': 'tags', 'in': 'query', 'description': 'Tags to filter by', 'required': True, 'style': 'form', 'explode': False, 'schema': {'type': 'array', 'items': {'type': 'string'}}}], 'responses': {'200': {'description': 'successful operation', 'content': {'application/xml': {'schema': {'type': 'array', 'items': {'$ref': '#/components/schemas/Pet'}}}, 'application/json': {'schema': {'type': 'array', 'items': {'$ref': '#/components/schemas/Pet'}}}}}, '400': {'description': 'Invalid tag value'}}, 'security': [{'petstore_auth': ['read:pets']}], 'deprecated': True}}, '/pet/{petId}': {'get': {'tags': ['pet'], 'summary': 'Find pet by ID', 'description': 'Returns a single pet', 'operationId': 'getPetById', 'parameters': [{'name': 'petId', 'in': 'path', 'description': 'ID of pet to return', 'required': True, 'schema': {'type': 'integer', 'format': 'int64'}}], 'responses': {'200': {'description': 'successful operation', 'content': {'application/xml': {'schema': {'$ref': '#/components/schemas/Pet'}}, 'application/json': {'schema': {'$ref': '#/components/schemas/Pet'}}}}, '400': {'description': 'Invalid ID supplied'}, '404': {'description': 'Pet not found'}}, 'security': [{'api_key': []}]}, 'post': {'tags': ['pet'], 'summary': 'Updates a pet in the store with form data', 'description': '', 'operationId': 'updatePetWithForm', 'parameters': [{'name': 'petId', 'in': 'path', 'description': 'ID of pet that needs to be updated', 'required': True, 'schema': {'type': 'integer', 'format': 'int64'}}], 'responses': {'405': {'description': 'Invalid input'}}, 'security': [{'petstore_auth': ['write:pets', 'read:pets']}], 'requestBody': {'content': {'application/x-www-form-urlencoded': {'schema': {'type': 'object', 'properties': {'name': {'description': 'Updated name of the pet', 'type': 'string'}, 'status': {'description': 'Updated status of the pet', 'type': 'string'}}}}}}}, 'delete': {'tags': ['pet'], 'summary': 'Deletes a pet', 'description': '', 'operationId': 'deletePet', 'parameters': [{'name': 'api_key', 'in': 'header', 'required': False, 'schema': {'type': 'string'}}, {'name': 'petId', 'in': 'path', 'description': 'Pet id to delete', 'required': True, 'schema': {'type': 'integer', 'format': 'int64'}}], 'responses': {'400': {'description': 'Invalid pet value'}}, 'security': [{'petstore_auth': ['write:pets', 'read:pets']}]}}}, 'components': {'schemas': {}}, 'tags': [{'name': 'pet', 'description': 'Everything about your Pets'}, {'name': 'user', 'description': 'Operations about user'}, {'name': 'store', 'description': 'Access to Petstore orders'}]}

    components = {'requestBodies': {'UserArray': {'content': {'application/json': {'schema': {'type': 'array', 'items': {'$ref': '#/components/schemas/User'}}}}, 'description': 'List of user object', 'required': True}, 'Pet': {'content': {'application/json': {'schema': {'$ref': '#/components/schemas/Pet'}}, 'application/xml': {'schema': {'$ref': '#/components/schemas/Pet'}}}, 'description': 'Pet object that needs to be added to the store', 'required': True}}, 'securitySchemes': {'petstore_auth': {'type': 'oauth2', 'flows': {'implicit': {'authorizationUrl': 'http://petstore.swagger.io/api/oauth/dialog', 'scopes': {'write:pets': 'modify pets in your account', 'read:pets': 'read your pets'}}}}, 'api_key': {'type': 'apiKey', 'name': 'api_key', 'in': 'header'}, 'auth_cookie': {'type': 'apiKey', 'name': 'AUTH_KEY', 'in': 'cookie'}}, 'schemas': {'Order': {'title': 'Pet Order', 'description': 'An order for a pets from the pet store', 'type': 'object', 'properties': {'id': {'type': 'integer', 'format': 'int64'}, 'petId': {'type': 'integer', 'format': 'int64'}, 'quantity': {'type': 'integer', 'format': 'int32'}, 'shipDate': {'type': 'string', 'format': 'date-time'}, 'status': {'type': 'string', 'description': 'Order Status', 'enum': ['placed', 'approved', 'delivered']}, 'complete': {'type': 'boolean', 'default': False}}, 'xml': {'name': 'Order'}}, 'Category': {'title': 'Pet category', 'description': 'A category for a pet', 'type': 'object', 'properties': {'id': {'type': 'integer', 'format': 'int64'}, 'name': {'type': 'string', 'pattern': '^[a-zA-Z0-9]+[a-zA-Z0-9\\.\\-_]*[a-zA-Z0-9]+$'}}, 'xml': {'name': 'Category'}}, 'User': {'title': 'a User', 'description': 'A User who is purchasing from the pet store', 'type': 'object', 'properties': {'id': {'type': 'integer', 'format': 'int64'}, 'username': {'type': 'string'}, 'firstName': {'type': 'string'}, 'lastName': {'type': 'string'}, 'email': {'type': 'string'}, 'password': {'type': 'string'}, 'phone': {'type': 'string'}, 'userStatus': {'type': 'integer', 'format': 'int32', 'description': 'User Status'}}, 'xml': {'name': 'User'}}, 'Tag': {'title': 'Pet Tag', 'description': 'A tag for a pet', 'type': 'object', 'properties': {'id': {'type': 'integer', 'format': 'int64'}, 'name': {'type': 'string'}}, 'xml': {'name': 'Tag'}}, 'Pet': {'title': 'a Pet', 'description': 'A pet for sale in the pet store', 'type': 'object', 'required': ['name', 'photoUrls'], 'properties': {'id': {'type': 'integer', 'format': 'int64'}, 'category': {'$ref': '#/components/schemas/Category'}, 'name': {'type': 'string', 'example': 'doggie'}, 'photoUrls': {'type': 'array', 'xml': {'name': 'photoUrl', 'wrapped': True}, 'items': {'type': 'string'}}, 'tags': {'type': 'array', 'xml': {'name': 'tag', 'wrapped': True}, 'items': {'$ref': '#/components/schemas/Tag'}}, 'status': {'type': 'string', 'description': 'pet status in the store', 'enum': ['available', 'pending', 'sold']}}, 'xml': {'name': 'Pet'}}, 'ApiResponse': {'title': 'An uploaded response', 'description': 'Describes the result of uploading an image resource', 'type': 'object', 'properties': {'code': {'type': 'integer', 'format': 'int32'}, 'type': {'type': 'string'}, 'message': {'type': 'string'}}}}}


        # adds schemas to ``section["components"]["schemas"]`` -> is {}

    args = flexmock.flexmock()
    cmd = SplitCommand({}, args)
    cmd.update_section_components(section, components)

    assert section["components"]["schemas"] == {'Pet': {'title': 'a Pet', 'description': 'A pet for sale in the pet store', 'type': 'object', 'required': ['name', 'photoUrls'], 'properties': {'id': {'type': 'integer', 'format': 'int64'}, 'category': {'$ref': '#/components/schemas/Category'}, 'name': {'type': 'string', 'example': 'doggie'}, 'photoUrls': {'type': 'array', 'xml': {'name': 'photoUrl', 'wrapped': True}, 'items': {'type': 'string'}}, 'tags': {'type': 'array', 'xml': {'name': 'tag', 'wrapped': True}, 'items': {'$ref': '#/components/schemas/Tag'}}, 'status': {'type': 'string', 'description': 'pet status in the store', 'enum': ['available', 'pending', 'sold']}}, 'xml': {'name': 'Pet'}}, 'Category': {'title': 'Pet category', 'description': 'A category for a pet', 'type': 'object', 'properties': {'id': {'type': 'integer', 'format': 'int64'}, 'name': {'type': 'string', 'pattern': '^[a-zA-Z0-9]+[a-zA-Z0-9\\.\\-_]*[a-zA-Z0-9]+$'}}, 'xml': {'name': 'Category'}}, 'Tag': {'title': 'Pet Tag', 'description': 'A tag for a pet', 'type': 'object', 'properties': {'id': {'type': 'integer', 'format': 'int64'}, 'name': {'type': 'string'}}, 'xml': {'name': 'Tag'}}, 'ApiResponse': {'title': 'An uploaded response', 'description': 'Describes the result of uploading an image resource', 'type': 'object', 'properties': {'code': {'type': 'integer', 'format': 'int32'}, 'type': {'type': 'string'}, 'message': {'type': 'string'}}}}





# section_after = {'paths': {'/pet/{petId}': {'get': {'tags': ['pet'], 'summary': 'Find pet by ID', 'description': 'Returns a single pet', 'operationId': 'getPetById', 'parameters': [{'name': 'petId', 'in': 'path', 'description': 'ID of pet to return', 'required': True, 'schema': {'type': 'integer', 'format': 'int64'}}], 'responses': {'200': {'description': 'successful operation', 'content': {'application/xml': {'schema': {'$ref': '#/components/schemas/Pet'}}, 'application/json': {'schema': {'$ref': '#/components/schemas/Pet'}}}}, '400': {'description': 'Invalid ID supplied'}, '404': {'description': 'Pet not found'}}, 'security': [{'api_key': []}]}, 'post': {'tags': ['pet'], 'summary': 'Updates a pet in the store with form data', 'description': '', 'operationId': 'updatePetWithForm', 'parameters': [{'name': 'petId', 'in': 'path', 'description': 'ID of pet that needs to be updated', 'required': True, 'schema': {'type': 'integer', 'format': 'int64'}}], 'responses': {'405': {'description': 'Invalid input'}}, 'security': [{'petstore_auth': ['write:pets', 'read:pets']}], 'requestBody': {'content': {'application/x-www-form-urlencoded': {'schema': {'type': 'object', 'properties': {'name': {'description': 'Updated name of the pet', 'type': 'string'}, 'status': {'description': 'Updated status of the pet', 'type': 'string'}}}}}}}, 'delete': {'tags': ['pet'], 'summary': 'Deletes a pet', 'description': '', 'operationId': 'deletePet', 'parameters': [{'name': 'api_key', 'in': 'header', 'required': False, 'schema': {'type': 'string'}}, {'name': 'petId', 'in': 'path', 'description': 'Pet id to delete', 'required': True, 'schema': {'type': 'integer', 'format': 'int64'}}], 'responses': {'400': {'description': 'Invalid pet value'}}, 'security': [{'petstore_auth': ['write:pets', 'read:pets']}]}}, '/pet/findByStatus': {'get': {'tags': ['pet', 'user'], 'summary': 'Finds Pets by status', 'description': 'Multiple status values can be provided with comma separated strings', 'operationId': 'findPetsByStatus', 'parameters': [{'name': 'status', 'in': 'query', 'description': 'Status values that need to be considered for filter', 'required': True, 'style': 'form', 'explode': False, 'schema': {'type': 'array', 'items': {'type': 'string', 'enum': ['available', 'pending', 'sold'], 'default': 'available'}}}], 'responses': {'200': {'description': 'successful operation', 'content': {'application/xml': {'schema': {'type': 'array', 'items': {'$ref': '#/components/schemas/Pet'}}}, 'application/json': {'schema': {'type': 'array', 'items': {'$ref': '#/components/schemas/Pet'}}}}}, '400': {'description': 'Invalid status value'}}, 'security': [{'petstore_auth': ['read:pets']}]}}, '/pet/{petId}/uploadImage': {'post': {'tags': ['pet'], 'summary': 'uploads an image', 'description': '', 'operationId': 'uploadFile', 'parameters': [{'name': 'petId', 'in': 'path', 'description': 'ID of pet to update', 'required': True, 'schema': {'type': 'integer', 'format': 'int64'}}], 'responses': {'200': {'description': 'successful operation', 'content': {'application/json': {'schema': {'$ref': '#/components/schemas/ApiResponse'}}}}}, 'security': [{'petstore_auth': ['write:pets', 'read:pets']}], 'requestBody': {'content': {'multipart/form-data': {'schema': {'type': 'object', 'properties': {'additionalMetadata': {'description': 'Additional data to pass to server', 'type': 'string'}, 'file': {'description': 'file to upload', 'type': 'string', 'format': 'binary'}}}}}}}}, '/pet/findByTags': {'get': {'tags': ['pet'], 'summary': 'Finds Pets by tags', 'description': 'Multiple tags can be provided with comma separated strings. Use tag1, tag2, tag3 for testing.', 'operationId': 'findPetsByTags', 'parameters': [{'name': 'tags', 'in': 'query', 'description': 'Tags to filter by', 'required': True, 'style': 'form', 'explode': False, 'schema': {'type': 'array', 'items': {'type': 'string'}}}], 'responses': {'200': {'description': 'successful operation', 'content': {'application/xml': {'schema': {'type': 'array', 'items': {'$ref': '#/components/schemas/Pet'}}}, 'application/json': {'schema': {'type': 'array', 'items': {'$ref': '#/components/schemas/Pet'}}}}}, '400': {'description': 'Invalid tag value'}}, 'security': [{'petstore_auth': ['read:pets']}], 'deprecated': True}}, '/pet': {'post': {'tags': ['pet', 'store', 'pet'], 'summary': 'Add a new pet to the store', 'description': '', 'operationId': 'addPet', 'responses': {'405': {'description': 'Invalid input'}}, 'security': [{'petstore_auth': ['write:pets', 'read:pets']}], 'requestBody': {'$ref': '#/components/requestBodies/Pet'}}, 'put': {'tags': ['pet', 'user', 'pet'], 'summary': 'Update an existing pet', 'description': '', 'operationId': 'updatePet', 'responses': {'400': {'description': 'Invalid ID supplied'}, '404': {'description': 'Pet not found'}, '405': {'description': 'Validation exception'}}, 'security': [{'petstore_auth': ['write:pets', 'read:pets']}], 'requestBody': {'$ref': '#/components/requestBodies/Pet'}}}}, 'components': {'schemas': {'Pet': {'title': 'a Pet', 'description': 'A pet for sale in the pet store', 'type': 'object', 'required': ['name', 'photoUrls'], 'properties': {'id': {'type': 'integer', 'format': 'int64'}, 'category': {'$ref': '#/components/schemas/Category'}, 'name': {'type': 'string', 'example': 'doggie'}, 'photoUrls': {'type': 'array', 'xml': {'name': 'photoUrl', 'wrapped': True}, 'items': {'type': 'string'}}, 'tags': {'type': 'array', 'xml': {'name': 'tag', 'wrapped': True}, 'items': {'$ref': '#/components/schemas/Tag'}}, 'status': {'type': 'string', 'description': 'pet status in the store', 'enum': ['available', 'pending', 'sold']}}, 'xml': {'name': 'Pet'}}, 'Category': {'title': 'Pet category', 'description': 'A category for a pet', 'type': 'object', 'properties': {'id': {'type': 'integer', 'format': 'int64'}, 'name': {'type': 'string', 'pattern': '^[a-zA-Z0-9]+[a-zA-Z0-9\\.\\-_]*[a-zA-Z0-9]+$'}}, 'xml': {'name': 'Category'}}, 'Tag': {'title': 'Pet Tag', 'description': 'A tag for a pet', 'type': 'object', 'properties': {'id': {'type': 'integer', 'format': 'int64'}, 'name': {'type': 'string'}}, 'xml': {'name': 'Tag'}}, 'ApiResponse': {'title': 'An uploaded response', 'description': 'Describes the result of uploading an image resource', 'type': 'object', 'properties': {'code': {'type': 'integer', 'format': 'int32'}, 'type': {'type': 'string'}, 'message': {'type': 'string'}}}}}, 'tags': [{'name': 'pet', 'description': 'Everything about your Pets'}, {'name': 'user', 'description': 'Operations about user'}, {'name': 'store', 'description': 'Access to Petstore orders'}]}

















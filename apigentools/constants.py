# Unless explicitly stated otherwise all files in this repository are licensed
# under the 3-clause BSD style license (see LICENSE).
# This product includes software developed at Datadog (https://www.datadoghq.com/).
# Copyright 2019-Present Datadog, Inc.
COMMAND_ENVIRONMENT_KEY = "environment"
COMMAND_IMAGE_KEY = "image"
COMMAND_INHERIT_KEY = "inherit"
COMMAND_SYSTEM_KEY = "system"
CONFIG_CONTAINER_IMAGE_KEY = "container_apigentools_image"
DEFAULT_CONFIG_FILE = "config.yaml"
DEFAULT_CONTAINER_IMAGE = "datadog/apigentools:latest"
LANGUAGE_OAPI_CONFIGS = "languages"
OPENAPI_GENERATOR_GIT = "https://github.com/OpenAPITools/openapi-generator"
GITHUB_REPO_URL_TEMPLATE = "github.com/{{github_org_name}}/{{github_repo_name}}"
HEADER_FILE_NAME = "header.yaml"
SHARED_FILE_NAME = "shared.yaml"
REDACTED_OUT_SECRET = "<apigentools:secret-value-redacted-out>"
OPENAPI_JAR = "openapi-generator.jar"
OPENAPI_JAR_IN_CONTAINER = "/usr/bin/openapi-generator-cli.jar"
SPEC_REPO_CONFIG_DIR = "config"
SPEC_REPO_GENERATED_DIR = "generated"
SPEC_REPO_LANGUAGES_CONFIG_DIR = "languages"
SPEC_REPO_SPEC_DIR = "spec"
SPEC_REPO_TEMPLATES_DIR = "templates"
TEMPLATES_SOURCE_LOCAL_DIR = "local-dir"
TEMPLATES_SOURCE_OPENAPI_GIT = "openapi-git"
TEMPLATES_SOURCE_OPENAPI_JAR = "openapi-jar"
TEMPLATES_SOURCE_SKIP = "skip"

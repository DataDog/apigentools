#!/bin/bash -e
# (C) Datadog, Inc. 2019
# All rights reserved
# Licensed under a 3-clause BSD style license (see LICENSE)

if [[ "$#" -eq 0 ]]; then
    # run the full workflow - validate, process templates and generate client code
    /usr/bin/apigentools \
        --spec-repo-dir ${APIGENTOOLS_SPEC_REPO_DIR} \
        validate

    /usr/bin/apigentools \
        --spec-repo-dir ${APIGENTOOLS_SPEC_REPO_DIR} \
        templates \
        openapi-jar \
        `npm list --global --depth=0 --parseable @openapitools/openapi-generator-cli`/bin/openapi-generator.jar

    /usr/bin/apigentools \
        --spec-repo-dir ${APIGENTOOLS_SPEC_REPO_DIR} \
        generate

    /usr/bin/apigentools \
        --spec-repo-dir ${APIGENTOOLS_SPEC_REPO_DIR} \
        test
else
    # this will use the APIGENTOOLS_* env values as defaults, so users
    # can override them, but don't have to specify if they want to keep defaults
    /usr/bin/apigentools "$@"
fi

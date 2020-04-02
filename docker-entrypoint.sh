#!/bin/bash -e
# (C) Datadog, Inc. 2019
# All rights reserved
# Licensed under a 3-clause BSD style license (see LICENSE)

# NOTE: we only use this if the old "container-apigentools" executable is used
if [[ "$#" -eq 0 && "$APIGENTOOLS_WHOLE_WORKFLOW" == "true" ]]; then
    # run the full workflow - validate, process templates and generate client code
    python3 -m apigentools \
        --spec-repo-dir ${APIGENTOOLS_SPEC_REPO_DIR} \
        validate

    python3 -m apigentools \
        --spec-repo-dir ${APIGENTOOLS_SPEC_REPO_DIR} \
        generate

    python3 -m apigentools \
        --spec-repo-dir ${APIGENTOOLS_SPEC_REPO_DIR} \
        test
else
    # this will use the APIGENTOOLS_* env values as defaults, so users
    # can override them, but don't have to specify if they want to keep defaults
    python3 -m apigentools "$@"
fi

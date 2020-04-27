# Unless explicitly stated otherwise all files in this repository are licensed
# under the 3-clause BSD style license (see LICENSE).
# This product includes software developed at Datadog (https://www.datadoghq.com/).
# Copyright 2019-Present Datadog, Inc.


class ApigentoolsError(Exception):
    pass


class SpecSectionNotFoundError(ApigentoolsError):
    def __init__(self, spec_version, spec_section, path):
        self.spec_version = spec_version
        self.spec_section = spec_section
        self.path = path

    def __str__(self):
        return f"Spec section '{self.spec_section}' not found for api version '{self.spec_version}' ({self.path})"

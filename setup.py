# Unless explicitly stated otherwise all files in this repository are licensed
# under the 3-clause BSD style license (see LICENSE).
# This product includes software developed at Datadog (https://www.datadoghq.com/).
# Copyright 2019 Datadog, Inc.

import os

from setuptools import setup

version_template = """\
# Unless explicitly stated otherwise all files in this repository are licensed
# under the 3-clause BSD style license (see LICENSE).
# This product includes software developed at Datadog (https://www.datadoghq.com/).
# Copyright 2019 Datadog, Inc.

__version__ = "{version}"
"""

setup(
    use_scm_version={
        "local_scheme": "dirty-tag",
        "write_to": os.path.join("apigentools", "version.py"),
        "write_to_template": version_template,
    }
)

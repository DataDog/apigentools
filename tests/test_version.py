# Unless explicitly stated otherwise all files in this repository are licensed
# under the 3-clause BSD style license (see LICENSE).
# This product includes software developed at Datadog (https://www.datadoghq.com/).
# Copyright 2019-Present Datadog, Inc.


def test_version():
    """Check the version import works."""
    from apigentools import __version__
    from pkg_resources import get_distribution

    assert __version__ == get_distribution("apigentools").version

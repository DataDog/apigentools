# Unless explicitly stated otherwise all files in this repository are licensed
# under the 3-clause BSD style license (see LICENSE).
# This product includes software developed at Datadog (https://www.datadoghq.com/).
# Copyright 2019-Present Datadog, Inc.
import pytest
import yaml

from apigentools.constants import MIN_CONFIG_VERSION
from apigentools.utils import maximum_supported_config_version


@pytest.mark.parametrize(
    "config,success,stderr",
    [
        ({}, True, ""),
        ({"minimum_apigentools_version": "1.0"}, True, ""),
        ({"config_version": str(MIN_CONFIG_VERSION)}, True, ""),
        ({"config_version": str(maximum_supported_config_version())}, True, ""),
        (
            {"minimum_apigentools_version": "99999999"},
            False,
            "Apigentools is below the minimum version: 99999999 for this spec repo",
        ),
        (
            {"config_version": "0.0.0"},
            False,
            "This apigentools version supports config of version at least {}".format(
                MIN_CONFIG_VERSION
            ),
        ),
        (
            {"config_version": "99999999"},
            False,
            "This apigentools version supports config of version at most {}".format(
                maximum_supported_config_version()
            ),
        ),
    ],
)
def test_versions(tmpdir, script_runner, config, success, stderr):
    config_dir = tmpdir.mkdir("config")

    with tmpdir.as_cwd():
        with open(str(config_dir.join("config.yaml")), "w") as f:
            yaml.dump(config, f)
        ret = script_runner.run("apigentools", "--verbose", "config", "-L")
        assert ret.success is success
        assert stderr in ret.stderr

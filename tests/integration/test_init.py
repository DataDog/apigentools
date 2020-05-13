# Unless explicitly stated otherwise all files in this repository are licensed
# under the 3-clause BSD style license (see LICENSE).
# This product includes software developed at Datadog (https://www.datadoghq.com/).
# Copyright 2019-Present Datadog, Inc.
import os


def test_init(tmpdir, script_runner):
    with tmpdir.as_cwd():
        ret = script_runner.run("apigentools", "--verbose", "init", "myspecrepo")
        assert ret.success
        assert os.path.exists(os.path.join("myspecrepo", "config", "config.yaml"))

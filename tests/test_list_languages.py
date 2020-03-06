# Unless explicitly stated otherwise all files in this repository are licensed
# under the 3-clause BSD style license (see LICENSE).
# This product includes software developed at Datadog (https://www.datadoghq.com/).
# Copyright 2019-Present Datadog, Inc.
import json
import os

import flexmock

from apigentools.commands.list_languages import ListLanguagesCommand
from apigentools.config import Config


def test_list_languages():
    spec_config = {"languages": {"test-lang1": {}, "test-lang2": {}}}
    spec_config_obj = Config.from_dict(spec_config)
    args = flexmock.flexmock()
    cmd = ListLanguagesCommand(spec_config_obj, args)
    actual_languages = cmd.run()
    assert actual_languages == spec_config["languages"].keys()

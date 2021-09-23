# Unless explicitly stated otherwise all files in this repository are licensed
# under the 3-clause BSD style license (see LICENSE).
# This product includes software developed at Datadog (https://www.datadoghq.com/).
# Copyright 2019-Present Datadog, Inc.
from apigentools.commands.generate import generate
from apigentools.commands.init import init
from apigentools.commands.list_config import config
from apigentools.commands.merge import merge
from apigentools.commands.push import push
from apigentools.commands.split import split
from apigentools.commands.templates import templates
from apigentools.commands.test import test
from apigentools.commands.validate import validate

ALL_COMMANDS = [generate, init, config, merge, push, split, templates, test, validate]

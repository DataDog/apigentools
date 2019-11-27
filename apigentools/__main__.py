# Unless explicitly stated otherwise all files in this repository are licensed
# under the 3-clause BSD style license (see LICENSE).
# This product includes software developed at Datadog (https://www.datadoghq.com/).
# Copyright 2019 Datadog, Inc.
"""Allow CLI execution using 'python -m apigentools'."""

from apigentool.cli import cli

if __name__ == '__main__':  # pragma: no cover
    cli()

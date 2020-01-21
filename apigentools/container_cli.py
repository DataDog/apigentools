#!/usr/bin/env python3
# Unless explicitly stated otherwise all files in this repository are licensed
# under the 3-clause BSD style license (see LICENSE).
# This product includes software developed at Datadog (https://www.datadoghq.com/).
# Copyright 2019-Present Datadog, Inc.
import argparse
import copy
import json
import logging
import os
import subprocess
import sys

from apigentools import constants
from apigentools.utils import set_log

log = logging.getLogger(__name__)


def container_cli():
    toplog = logging.getLogger(__name__.split(".")[0])
    set_log(toplog)

    parser = argparse.ArgumentParser(description="Run apigentools in a container")
    parser.add_argument(
        "--spec-repo-volume",
        default=os.path.abspath(os.getcwd()),
        help="Full path to spec repo (defaults to current working directory)",
    )
    args, remainder = parser.parse_known_args()

    if len(remainder) > 0 and (":" in remainder[0] or "/" in remainder[0]):
        log.error(
            "Since apigentools 0.9.0, container-apigentools doesn't accept image as argument."
        )
        new_args = copy.deepcopy(sys.argv)
        new_args.remove(remainder[0])
        log.error("Rerun with: %s", " ".join(new_args))
        sys.exit(1)

    # get image to use - either it's specified as environment variable or we get
    # it from config or we use a default value
    image = os.environ.get("APIGENTOOLS_IMAGE")
    if image is None:
        config = os.path.join(
            args.spec_repo_volume,
            os.environ.get(
                constants.ENV_APIGENTOOLS_CONFIG_DIR, constants.DEFAULT_CONFIG_DIR
            ),
            constants.DEFAULT_CONFIG_FILE,
        )
        with open(config, "r") as f:
            try:
                loaded_config = json.load(f)
                image = loaded_config.get(constants.CONFIG_CONTAINER_IMAGE_KEY)
            except json.JSONDecodeError as e:
                log.error("Failed to parse {}: {}".format(config, str(e)))
                sys.exit(1)
    if image is None:
        image = constants.DEFAULT_CONTAINER_IMAGE
    log.info("Using apigentools image %s", image)

    mountpoints = {
        args.spec_repo_volume: ("/var/lib/apigentools/spec-repo", None),
        "/var/run/docker.sock": ("/var/run/docker.sock", None),
        os.path.expanduser("~/.ssh"): ("/root/.ssh/", "ro"),
    }

    command = ["docker", "run", "--rm"]
    # Some people on MacOS use `UseKeychain` option not recognized by linux ssh
    # so make sure we ignore it
    command.append("-e")
    command.append('GIT_SSH_COMMAND=ssh -o "IgnoreUnknown *"')
    for k, v in os.environ.items():
        if k.startswith("APIGENTOOLS_"):
            if k == "APIGENTOOLS_IMAGE":
                pass
            command.append("-e")
            command.append("{}={}".format(k, v))
    command.extend(["-e", "APIGENTOOLS_IMAGE={}".format(image)])

    for mountdir, mountopts in mountpoints.items():
        command.append("-v")
        command.append("{}:{}".format(mountdir, mountopts[0]))
        if mountopts[1] is not None:
            command[-1] = "{}:{}".format(command[-1], mountopts[1])
    command.append(image)
    command.extend(remainder)

    # if using latest, explictly pull to actually get latest image
    if ":" not in image or image.endswith(":latest"):
        log.info("Detected usage of ':latest' image, pulling it now ...")
        subprocess.call(["docker", "pull", image])
    log.debug("Executing %s", command)
    os.execlp("docker", *command)

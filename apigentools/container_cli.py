#!/usr/bin/env python3
# (C) Datadog, Inc. 2019
# All rights reserved
# Licensed under a 3-clause BSD style license (see LICENSE)
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
    parser.add_argument(
        "apigentools_args",
        nargs=argparse.REMAINDER,
        help="Arguments to pass to apigentools running inside the container",
    )
    args = parser.parse_args()

    if len(args.apigentools_args) > 0 and (
        ":" in args.apigentools_args[0] or "/" in args.apigentools_args[0]
    ):
        log.error(
            "Since apigentools 0.9.0, container-apigentools doesn't accept image as argument."
        )
        new_args = copy.deepcopy(sys.argv)
        new_args.remove(args.apigentools_args[0])
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
        args.spec_repo_volume: "/var/lib/apigentools/spec-repo",
        "/var/run/docker.sock": "/var/run/docker.sock",
    }

    command = ["docker", "run", "--rm"]
    for k, v in os.environ.items():
        if k.startswith("APIGENTOOLS_"):
            command.append("-e")
            command.append("{}={}".format(k, v))
    for mountdir, mountpoint in mountpoints.items():
        command.append("-v")
        command.append("{}:{}".format(mountdir, mountpoint))
    command.append(image)
    command.extend(args.apigentools_args)

    # if using latest, explictly pull to actually get latest image
    if ":" not in image or image.endswith(":latest"):
        log.info("Detected usage of ':latest' image, pulling it now ...")
        subprocess.call(["docker", "pull", image])
    log.debug("Executing %s", command)
    os.execlp("docker", *command)

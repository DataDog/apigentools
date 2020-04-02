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
import warnings

from apigentools.cli import cli
from apigentools import constants
from apigentools.utils import set_log

log = logging.getLogger(__name__)


def is_container_apigentools_entrypoint(parser):
    if parser.prog == "container-apigentools":
        return True
    return False


def container_cli():
    parser = argparse.ArgumentParser(
        description="Run apigentools in a container", add_help=False
    )
    parser.add_argument(
        "--spec-repo-volume",
        default=os.path.abspath(os.getcwd()),
        help="Full path to spec repo (defaults to current working directory)",
    )
    args, remainder = parser.parse_known_args()
    warnings.simplefilter("default")
    if is_container_apigentools_entrypoint(parser):
        warnings.warn(
            "container-apigentools has been deprecated, use apigentools instead",
            DeprecationWarning,
        )

    # init command is an exception that we don't want to run inside the container
    # as we wouldn't know what directory to mount inside it
    if len(remainder) > 0 and remainder[0] == "init":
        cli()

    if len(remainder) > 0 and remainder[0] in ["-h", "--help"]:
        # if `apigentools --help` is called, we want to display both help for the local argparse
        # and help for the apigentools running inside the container
        parser.print_help()

    toplog = logging.getLogger(__name__.split(".")[0])
    set_log(toplog)

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
        if os.path.exists(config):
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

    # we add "-ti" so that git cloning can stop and ask for passphrase for keys if necessary
    command = ["docker", "run", "-ti", "--rm"]
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
    if is_container_apigentools_entrypoint(parser):
        # invoke the whole validate/generate/test workflow when running via the old container-apigentools entrypoint
        command.extend(["-e", "APIGENTOOLS_WHOLE_WORKFLOW=true"])

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

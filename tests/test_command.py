import os

from flexmock import flexmock
import pytest

from apigentools.commands import command
from apigentools.constants import DEFAULT_CONTAINER_IMAGE
from apigentools.config import ConfigCommand, ContainerOpts
from apigentools import utils


class MyCommand(command.Command):
    def run(self):
        pass


class TestCommand:
    EXPECTED_DOCKER_INVOCATION = [
        "docker",
        "run",
        "--rm",
        "-v",
        os.getcwd() + ":/tmp/spec-repo",
        "--workdir",
        "/tmp/spec-repo/./.",
        "--entrypoint",
    ]

    @pytest.mark.parametrize(
        "cmd, cwd, vars, functions, env_override, call",
        [
            # simple basic test
            (
                ConfigCommand(commandline=["echo", "1"]),
                ".",
                {},
                {},
                {},
                (
                    EXPECTED_DOCKER_INVOCATION + ["echo", DEFAULT_CONTAINER_IMAGE, "1"],
                    {},
                ),
            ),
            # test a system command
            (
                ConfigCommand(
                    commandline=["echo", "1"], container_opts={"system": True}
                ),
                ".",
                {},
                {},
                {},
                (["echo", "1"], {"additional_env": {}, "cwd": "."}),
            ),
            # test chevron vars rendering on a more complex command
            (
                ConfigCommand(
                    commandline=[
                        "echo",
                        "{{chevron_var}}",
                        {"function": "myecho", "args": ["{{chevron_var}}"]},
                    ]
                ),
                ".",
                {"chevron_var": "hello"},
                {"myecho": lambda x: x},
                {},
                (
                    EXPECTED_DOCKER_INVOCATION
                    + ["echo", DEFAULT_CONTAINER_IMAGE, "hello", "hello"],
                    {},
                ),
            ),
        ],
    )
    def test_run_config_command(self, cmd, cwd, vars, functions, env_override, call):
        # make sure container_opts are fully populated
        cmd.container_opts = utils.inherit_container_opts(
            cmd.container_opts, ContainerOpts()
        )
        flexmock(command).should_receive("run_command").with_args(call[0], **call[1])
        MyCommand(None, None).run_config_command(
            cmd, "testing", cwd, vars, functions, env_override
        )

    def test_run_config_command_with_image_build(self):
        cmd = ConfigCommand(
            commandline=["echo", "1"],
            container_opts={
                "image": {"dockerfile": "Dockerfile", "context": os.getcwd()}
            },
        )
        cmd.container_opts = utils.inherit_container_opts(
            cmd.container_opts, ContainerOpts()
        )
        flexmock(command).should_receive("run_command").with_args(
            [
                "docker",
                "build",
                os.getcwd(),
                "-t",
                "apigentools-test-java-v1",
                "-f",
                "Dockerfile",
            ]
        )
        flexmock(command).should_receive("run_command").with_args(
            self.EXPECTED_DOCKER_INVOCATION + ["echo", "apigentools-test-java-v1", "1"]
        )
        MyCommand(None, None).run_config_command(cmd, "java-v1", ".", {}, {}, {})

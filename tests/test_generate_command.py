# Unless explicitly stated otherwise all files in this repository are licensed
# under the 3-clause BSD style license (see LICENSE).
# This product includes software developed at Datadog (https://www.datadoghq.com/).
# Copyright 2019-Present Datadog, Inc.

import logging
import sys

from flexmock import flexmock
import pytest

from apigentools import __version__
from apigentools.commands.generate import GenerateCommand, run_command
from apigentools.config import ConfigCommand


class TestGenerateCommand:
    default_generate_function_result = [
        "openapi-generator",
        "generate",
        "--http-user-agent",
        "{{user_agent_client_name}}/{{library_version}}/{{language_name}}",
        "-g",
        "{{language_name}}",
        "-c",
        "{{language_config}}",
        "-i",
        "{{full_spec_path}}",
        "-o",
        "{{version_output_dir}}",
        "--additional-properties",
        "apigentoolsStamp='{{stamp}}'",
    ]

    def test_get_default_generate_function(self):
        assert (
            GenerateCommand(None, None).get_default_generate_function(True)()
            == self.default_generate_function_result
        )
        assert GenerateCommand(None, None).get_default_generate_function(
            False
        )() == self.default_generate_function_result + ["-t", "{{templates_dir}}"]

    @pytest.mark.parametrize(
        "language, version, cwd, chevron_vars, commands",
        [
            ("java", "v1", ".", {}, []),
            ("java", "v1", ".", {}, [ConfigCommand(commandline=["echo", "1"])]),
            (
                "java",
                "v1",
                ".",
                {},
                [
                    ConfigCommand(commandline=["echo", "1"]),
                    ConfigCommand(commandline=["echo", "2"]),
                ],
            ),
        ],
    )
    def test_run_language_commands(
        self, language, version, cwd, chevron_vars, commands
    ):
        class AdditionalFunctionsComparator:
            def __eq__(myself, other):
                assert len(other) == 1
                return (
                    other["openapi_generator_generate"]()
                    == self.default_generate_function_result
                )

        lc = flexmock(
            commands_for=lambda x: commands if x == version else None,
            templates_config_for=lambda x: None,
        )
        cfg = flexmock(get_language_config=lambda x: lc if x == language else None)
        gc = GenerateCommand(cfg, None)
        for c in commands:
            flexmock(gc).should_receive("run_config_command").with_args(
                c,
                "{l}/{v}".format(l=language, v=version),
                cwd,
                chevron_vars,
                additional_functions=AdditionalFunctionsComparator(),
            )
        gc.run_language_commands(language, version, cwd, chevron_vars)

    @pytest.mark.parametrize(
        "lc, vars",
        [
            (flexmock(downstream_templates={}, language="java"), {}),
            (
                flexmock(downstream_templates={"foo": "bar"}, language="java"),
                {"key": "value"},
            ),
        ],
    )
    def test_render_downstream_templates(self, tmpdir, caplog, lc, vars):
        caplog.set_level(logging.INFO)
        lc.generated_lang_dir = str(tmpdir)
        gc = GenerateCommand(None, None)

        if not lc.downstream_templates:
            gc.render_downstream_templates(lc, vars)
            assert (
                "apigentools.commands.generate",
                20,
                "No downstream templates for java",
            ) in caplog.record_tuples
        else:
            expected = []
            # create all downstream templates
            for f in lc.downstream_templates.keys():
                with open(str(tmpdir.join(f)), "w") as fp:
                    for k, v in sorted(vars.items()):
                        fp.write(f"{{{{ {k} }}}}")
                        expected.append(v)

            with tmpdir.as_cwd():
                gc.render_downstream_templates(lc, vars)

            # verify all templates have been rendered correctly
            expected = "".join(expected)
            for f in lc.downstream_templates.values():
                with open(str(tmpdir.join(f))) as fp:
                    assert fp.read() == expected

    @pytest.mark.parametrize(
        "args, expected",
        [
            ({}, f"Generated with: apigentools version {__version__}"),
            (
                {"additional_stamp": ("STAMP!",)},
                f"Generated with: apigentools version {__version__}; STAMP!",
            ),
        ],
    )
    def test_get_stamp(self, args, expected):
        gc = GenerateCommand(None, args)
        assert gc.get_stamp() == expected

    @pytest.mark.parametrize(
        "lc, branch, args, expected",
        [
            (
                flexmock(
                    generated_lang_dir="/path/",
                    github_org="myorg",
                    github_repo="myrepo",
                ),
                None,
                {"git_via_https": True, "git_via_https_oauth_token": "mytoken"},
                [
                    (
                        [
                            "git",
                            "clone",
                            "--depth=2",
                            {
                                "item": "https://mytoken:x-oauth-basic@github.com/myorg/myrepo.git",
                                "secret": True,
                            },
                            "/path/",
                        ],
                        {"sensitive_output": True},
                    ),
                ],
            ),
            (
                flexmock(
                    generated_lang_dir="/path/",
                    github_org="myorg",
                    github_repo="myrepo",
                ),
                None,
                {
                    "git_via_https": True,
                    "git_via_https_installation_access_token": "mytoken",
                },
                [
                    (
                        [
                            "git",
                            "clone",
                            "--depth=2",
                            {
                                "item": "https://x-access-token:mytoken@github.com/myorg/myrepo.git",
                                "secret": True,
                            },
                            "/path/",
                        ],
                        {"sensitive_output": True},
                    ),
                ],
            ),
            (
                flexmock(
                    generated_lang_dir="/path/",
                    github_org="myorg",
                    github_repo="myrepo",
                ),
                None,
                {},
                [
                    (
                        [
                            "git",
                            "clone",
                            "--depth=2",
                            {
                                "item": "git@github.com:myorg/myrepo.git",
                                "secret": False,
                            },
                            "/path/",
                        ],
                        {"sensitive_output": False},
                    ),
                ],
            ),
            (
                flexmock(
                    generated_lang_dir="/path/",
                    github_org="myorg",
                    github_repo="myrepo",
                ),
                "prodbranch",
                {},
                [
                    (
                        [
                            "git",
                            "clone",
                            "--depth=2",
                            {
                                "item": "git@github.com:myorg/myrepo.git",
                                "secret": False,
                            },
                            "/path/",
                        ],
                        {"sensitive_output": False},
                    ),
                    (["git", "fetch", "origin", "prodbranch"], {"cwd": "/path/"}),
                    (["git", "branch", "prodbranch", "FETCH_HEAD"], {"cwd": "/path/"}),
                    (["git", "checkout", "prodbranch"], {"cwd": "/path/"}),
                ],
            ),
            (
                flexmock(
                    generated_lang_dir="/path/",
                    github_org="myorg",
                    github_repo="myrepo",
                ),
                "prodbranch",
                {"is_ancestor": "master"},
                [
                    (
                        [
                            "git",
                            "clone",
                            "--depth=2",
                            {
                                "item": "git@github.com:myorg/myrepo.git",
                                "secret": False,
                            },
                            "/path/",
                        ],
                        {"sensitive_output": False},
                    ),
                    (["git", "fetch", "origin", "prodbranch"], {"cwd": "/path/"}),
                    (["git", "branch", "prodbranch", "FETCH_HEAD"], {"cwd": "/path/"}),
                    (["git", "checkout", "prodbranch"], {"cwd": "/path/"}),
                    (
                        ["git", "merge-base", "--is-ancestor", "master", "prodbranch"],
                        {"cwd": "/path/"},
                    ),
                ],
            ),
        ],
    )
    def test_pull_repository(self, lc, branch, args, expected):
        for cmd in expected:
            # we can't do `from apigentools.commands import generate` and than do `flexmock(generate)`,
            # as that is the actual command class, not the module
            flexmock(sys.modules["apigentools.commands.generate"]).should_receive(
                "run_command"
            ).with_args(cmd[0], **cmd[1])
        gc = GenerateCommand(None, args)
        gc.pull_repository(lc, branch)

import os
import subprocess

import pytest
import py

HERE = os.path.dirname(os.path.abspath(__file__))
EXAMPLES = os.path.join(HERE, "..", "..", "examples")
BAD = os.path.join(EXAMPLES, "bad")
GOOD = os.path.join(EXAMPLES, "good")


def run_apigentools(command):
    subprocess.run(["apigentools", "command"])


@pytest.mark.parametrize(
    "example, should_pass, should_fail",
    [
        (
            os.path.join(GOOD, "openapi-generator-java"),
            ["validate", "templates", "generate", "test"],
            [],
        ),
        (os.path.join(BAD, "openapi-generator-java-fail-validate"), [], ["validate"]),
        (
            os.path.join(BAD, "openapi-generator-java-fail-templates"),
            ["validate"],
            ["templates"],
        ),
        (
            os.path.join(BAD, "openapi-generator-java-fail-generate"),
            ["validate", "templates"],
            ["generate"],
        ),
        (
            os.path.join(BAD, "openapi-generator-java-fail-tests"),
            ["validate", "templates", "generate"],
            ["test"],
        ),
    ],
)
def test_examples(tmpdir, script_runner, example, should_pass, should_fail):
    p = py.path.local(example)
    p.copy(tmpdir)
    with tmpdir.as_cwd() as p:
        for p in should_pass:
            ret = script_runner.run("apigentools", p)
            assert ret.success
        for f in should_fail:
            ret = script_runner.run("apigentools", f)
            assert not ret.success

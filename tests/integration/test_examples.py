import copy
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
            ["validate", "templates", "generate", "test", "push"],
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
        # create a testing git repo to try pushing to
        reponame = "thisIsATestClientRepo"
        repo = tmpdir.mkdir(reponame)
        generated = tmpdir.join("generated", "my-java-client")
        if generated.check():
            generated.remove()
        with repo.as_cwd():
            subprocess.run(["git", "init", "--bare"])
            subprocess.run(
                ["git", "clone", os.path.join("..", reponame), "my-java-client"],
                cwd=os.path.join("..", "generated"),
            )
        env = copy.deepcopy(os.environ)
        # for some reason, Git tends to ignore gpgSign = false in the overriden GIT_CONFIG if
        # user's GIT_CONFIG sets it to true; therefore we also set HOME to the tempdir
        # so that user's .gitconfig is not found at all and the one we have provided is used
        env["GIT_CONFIG_NOSYSTEM"] = "1"
        env["HOME"] = str(tmpdir)

        for p in should_pass:
            ret = script_runner.run("apigentools", "--verbose", p, env=env)
            assert ret.success
            if p == "push":
                log = subprocess.run(
                    ["git", "log"], cwd=reponame, capture_output=True, encoding="utf-8"
                )
                assert "Regenerate client from commit" in log.stdout
        for f in should_fail:
            ret = script_runner.run("apigentools", "--verbose", f)
            assert not ret.success

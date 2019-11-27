import pytest

from click.testing import CliRunner


@pytest.fixture
def isolated_runner():
    """Create a runner on isolated filesystem."""
    runner_ = CliRunner()
    with runner_.isolated_filesystem():
        yield runner_


@pytest.fixture
def invoke(isolated_runner):
    """Return a invokation factory."""
    from apigentools.cli import cli

    def run(args, **kwargs):
        return isolated_runner.invoke(cli, args, **kwargs)
    return run


@pytest.fixture(scope='module')
def repository():
    """Yield a API spec repository."""
    from apigentools.cli import cli
    runner = CliRunner()

    with runner.isolated_filesystem() as project_path:
        result = runner.invoke(cli, ['init', 'test'], catch_exceptions=False)
        assert 0 == result.exit_code

        yield project_path

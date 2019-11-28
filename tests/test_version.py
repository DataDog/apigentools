def test_version():
    """Check the version import works."""
    from apigentools import __version__
    from pkg_resources import get_distribution

    assert __version__ == get_distribution("apigentools").version

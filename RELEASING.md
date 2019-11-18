# Releasing apigentools

This document summarizes the process of doing a new release of apigentools.

## Make Sure Everything Works

* Make sure tests are passing
* Make sure [Docker builds](https://hub.docker.com/r/apigentools/apigentools/builds) are passing
* Make sure [documentation](https://apigentools.readthedocs.io/en/latest/) is up-to-date and building correctly
* Build the package locally (e.g. `python3 setup.py sdist`), install it into a fresh virtualenv and try playing around with it for a bit

## Release

Note that once the release process is started, nobody should be merging/pushing anything. Once the version is changed from `X.Y.Z.devN` to `X.Y.Z`, we don't want to trigger multiple rebuilds of docs and Docker images with that official final release version and different content - this would only create confusion.

Accepting new code should only be allowed after the [post release](#post-release) steps are done.

* Create a PR that bumps version from `X.Y.Z.devN` to `X.Y.Z` and get it reviewed and merged in
  * You need to change the version both in `setup.py` and `apigentools/__init__.py`
  * Also include any relevant user-facing changes in `docs/changelog.md`
* Pull the merged PR locally and tag the latest commit: `git tag -a "vX.Y.Z" -m "Version X.Y.Z"`
  * Note that the `v` in `-a "vX.Y.Z"` is important, our Dockerhub setup recognizes a tag like this and automatically builds image `apigentools/apigentools:X.Y.X` from it
  * Push the tag with `git push --tags`
* Do a release on PyPI. Since this is a simple non-binary-extension package, we can do source releases only:
  * Run `python3 setup.py sdist`
  * Run `twine upload dist/apigentools-X.Y.Z.tar.gz` - note that we're using [twine](https://github.com/pypa/twine/) to upload to PyPI because it's more secure than plain `python3 setup.py upload`
* Go to [readthedocs dashboard](https://readthedocs.org/projects/apigentools/versions/) and add the newly released `X.Y.Z` version to "Active Versions"
* The Dockerhub builds for tagged version are automated, so just make sure that everything went ok

## Post Release

* Create a PR that bumps version from `X.Y.Z` to `A.B.C.dev1` (choose `A`, `B` and `C` appropriately) and get it reviewed and merged in
  * You need to change the version both in `setup.py` and `apigentools/__init__.py`
* Everything is done now and you can start accepting PRs again.

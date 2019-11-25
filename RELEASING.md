# Releasing apigentools

This document summarizes the process of doing a new release of apigentools.

## Make Sure Everything Works

* Make sure tests are passing
* Make sure [Docker builds](https://hub.docker.com/r/apigentools/apigentools/builds) are passing
* Make sure [documentation](https://apigentools.readthedocs.io/en/latest/) is up-to-date and building correctly
* Build the package locally (e.g. `python3 setup.py sdist`), install it into a fresh virtualenv and try playing around with it for a bit

## Update Changelog

* Create a PR that summarizes any relevant user-facing changes in `docs/changelog.md`
* Wait until PR is approved and merged to master.

## Release

Note that once the release process is started, nobody should be merging/pushing anything. We don't want to trigger multiple rebuilds of docs and Docker images with that official final release version and different content - this would only create confusion.

* Pull the merged PR locally and tag the latest commit: `git tag -a "vX.Y.Z" -m "Version X.Y.Z"`
  * Note that the `v` in `-a "vX.Y.Z"` is important, our Dockerhub setup recognizes a tag like this and automatically builds image `apigentools/apigentools:X.Y.X` from it
  * Push the tag with `git push --tags`
* Do a release on PyPI. Since this is a simple non-binary-extension package, we can do source releases only:
  * Clean old builds `python setup.py clean`
  * Run `python3 setup.py sdist`
  * Run `twine upload dist/apigentools-X.Y.Z.tar.gz` - note that we're using [twine](https://github.com/pypa/twine/) to upload to PyPI because it's more secure than plain `python3 setup.py upload`
* Go to [readthedocs dashboard](https://readthedocs.org/projects/apigentools/versions/) and add the newly released `X.Y.Z` version to "Active Versions"
* The Dockerhub builds for tagged version are automated, so just make sure that everything went ok

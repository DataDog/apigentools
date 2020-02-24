# Releasing

This document summarizes the process of doing a new release of this project.
Release can only be performed by Datadog maintainers of this repository.

## Schedule
This project does not have a strict release schedule. However, we would make a release at least every 2 months.
  - No release will be done if no changes got merged to the `master` branch during the above mentioned window.
  - Releases may be done more frequently than the above mentioned window.

## Make Sure Everything Works

* Make sure tests are passing.
* Make sure Docker builds are passing.
* Make sure documentation is up-to-date and building correctly.
* Build the package locally (e.g. `python3 setup.py sdist`), install it into a fresh virtualenv and try playing around with it for a bit.
  - Use the manual testing guide.

## Update Changelog

### Prerequisite

- Install [datadog_checks_dev](https://datadog-checks-base.readthedocs.io/en/latest/datadog_checks_dev.cli.html#installation) using Python 3

### Commands

- See changes ready for release by running `ddev release show changes .` at the root of this project. Add any missing labels to PRs if needed.
- Run `ddev release changelog . <NEW_VERSION> -o docs/changelog.md` to update the changelog.
- Commit the changes to the repository in a release branch and get it approved/merged.
- Tag the repository with the new version number.

## Release

Note that once the release process is started, nobody should be merging/pushing anything.
We don't want to trigger multiple rebuilds of docs and Docker images with that official final release version and different content - this would only create confusion.

* Pull the merged PR locally and tag the latest commit: `git tag -a "vX.Y.Z" -m "Version X.Y.Z"`
  * Note that the `v` in `-a "vX.Y.Z"` is important, our Dockerhub setup recognizes a tag like this and automatically builds image `datadog/apigentools:X.Y.X` from it
  * Push the tag with `git push --tags`
* Do a release on PyPI. Since this is a simple non-binary-extension package, we can do source releases only:
  * Clean old builds `python setup.py clean`
  * Run `python3 setup.py sdist`
  * Run `twine upload dist/apigentools-X.Y.Z.tar.gz` - note that we're using [twine](https://github.com/pypa/twine/) to upload to PyPI because it's more secure than plain `python3 setup.py upload`
* Go to [readthedocs dashboard](https://readthedocs.org/projects/apigentools/versions/) and add the newly released `X.Y.Z` version to "Active Versions"
* The Dockerhub builds for tagged version are automated, so just make sure that everything went ok

# Releasing

This document summarizes the process of doing a new release of this project.
Release can only be performed by Datadog maintainers of this repository.

## Schedule
This project does not have a strict release schedule. However, we would make a release at least every 2 months.
  - No release will be done if no changes got merged to the `master` branch during the above mentioned window.
  - Releases may be done more frequently than the above mentioned window.

## Update Changelog

### Prerequisite

- Install [datadog_checks_dev](https://datadog-checks-base.readthedocs.io/en/latest/datadog_checks_dev.cli.html#installation) using Python 3

### Commands

- See changes ready for release by running `ddev release show changes . --tag-prefix v` at the root of this project. Add any missing labels to PRs if needed.
- Run `ddev release changelog . <NEW_VERSION> -o docs/changelog.md` to update the changelog.
- Commit the changes to the repository in a release branch and get it approved/merged.
    * Make sure CI is passing. This is the commit that will be released!
    * Make sure the most recent Docker [builds](https://hub.docker.com/r/datadog/apigentools/builds) are passing.
    * Make sure recent documentation [builds](https://readthedocs.org/projects/apigentools/builds/) are succeeding.

## Release

Note that once the release process is started, nobody should be merging/pushing anything.
We don't want to trigger multiple rebuilds of docs and Docker images with that official final release version and different content - this would only create confusion.

* Create the release on GitHub using the format: `"vX.Y.Z"`
  * Note that the `v` in `-a "vX.Y.Z"` is important, our Dockerhub setup recognizes a tag like this and automatically builds image `datadog/apigentools:X.Y.X` from it
* A github action will kick off that builds and publishes this tag to PyPI. Confirm the release is [available](https://pypi.org/project/apigentools/#history)
* Go to [readthedocs dashboard](https://readthedocs.org/projects/apigentools/versions/) and add the newly released `X.Y.Z` version to "Active Versions"
* The Dockerhub builds for tagged version are automated, so just make sure the [build succeeded](https://hub.docker.com/r/datadog/apigentools/builds)

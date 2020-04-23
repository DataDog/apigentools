# Changelog

## 1.0.0b1 / 2020-04-23

* *NOTE* This is the first beta release for the new major version. Major changes are documented at [upgrading](upgrading.md#from-0x-series-to-1x-series). List of new features not related to the 1.0.0 release follows:
* [Added] Introduce config validation using pydantic. See [#169](https://github.com/DataDog/apigentools/pull/169).
* [Added] Check apigentools version compatibility using config. See [#163](https://github.com/DataDog/apigentools/pull/163).
* [Added] Add a `--version` flag to the root command. See [#162](https://github.com/DataDog/apigentools/pull/162).
* [Added] Enable removing generated files between generations. See [#153](https://github.com/DataDog/apigentools/pull/153).
* [Added] Add a `glob_re` function to use in config. See [#149](https://github.com/DataDog/apigentools/pull/149).
* [Added] Upgrade openapi-generator to 4.3.0. See [#148](https://github.com/DataDog/apigentools/pull/148).
* [Added] Make it possible to provide different operations for the same path in different spec sections. See [#144](https://github.com/DataDog/apigentools/pull/144).
* [Added] Add pre-commit hook definition. See [#139](https://github.com/DataDog/apigentools/pull/139).
* [Added] Include node 12 (LTS) in the base image. See [#137](https://github.com/DataDog/apigentools/pull/137).
* [Added] Add new `config` command. See [#132](https://github.com/DataDog/apigentools/pull/132).
* [Added] Choose only necessary combinations of lang and versions. See [#131](https://github.com/DataDog/apigentools/pull/131).
* [Added] Support `{{spec_version}}` in all commands. See [#127](https://github.com/DataDog/apigentools/pull/127).
* [Changed] Don't log all the command outputs by default. See [#161](https://github.com/DataDog/apigentools/pull/161).
* [Changed] Docker image was moved from apigentools/apigentools to datadog/apigentools. See [#130](https://github.com/DataDog/apigentools/pull/130).
* [Fixed] Fail code generation when preparing templates fails. See [#145](https://github.com/DataDog/apigentools/pull/145).
* [Fixed] Fix args retrieveing `is_ancestor`. See [#140](https://github.com/DataDog/apigentools/pull/140).

## 0.10.0 / 2020-01-31

* [Added] Make it possible to add custom validation commands. See [#124](https://github.com/DataDog/apigentools/pull/124).
* [Added] Make template preparation part of code generation by default. See [#123](https://github.com/DataDog/apigentools/pull/123).
* [Fixed] Fix git cwd in push command. See [#122](https://github.com/DataDog/apigentools/pull/122).
* [Fixed] Fix merging when clone --depth=2. See [#120](https://github.com/DataDog/apigentools/pull/120).
* [Fixed] Configure git before merging. See [#119](https://github.com/DataDog/apigentools/pull/119).
* [Added] Sort OpenAPI tags alphabetical. See [#118](https://github.com/DataDog/apigentools/pull/118).
* [Fixed] Merge --is-ancestor branch to --branch. See [#117](https://github.com/DataDog/apigentools/pull/117).
* [Fixed] Fix ancestor error message. See [#116](https://github.com/DataDog/apigentools/pull/116).
* [Changed] [ITL-182] Use specific image openapitools/openapi-generator@sha256:xxx. See [#114](https://github.com/DataDog/apigentools/pull/114).

## 0.9.2

* [Improvement] Adds an optional check to ensure that a branch specified in `--branch` option is an ancestor of the branch given in `--is-ancestor` option in `generate` command.

## 0.9.1

* [Improvement] Make `server_base_url` optional and possibly deprecated in the future version.
* [Bugfix] Fetch branch before checkout in `generate` command with `--branch` option.
* [Bugfix] Make container-apigentools properly accept arguments to pass inside the container
* [Bugfix] Mount local SSH keys to container to make `generate --clone-repo` work
* [Bugfix] Properly record used image in `.apigentools-info`

## 0.9.0

* [Feature] Allow using specific branch as base for generation
* [Improvement] Bump openapi-generator in container image to 4.2.2
* [Improvement] The `container-apigentools` script no longer requires a positional argument with image to use, e.g. `container-apigentools apigentools/apigentools:0.8.0 validate`. From now on, the image to be used is read either from `APIGENTOOLS_IMAGE` environment variable or from [config](spec_repo.md#configconfigjson) `container_apigentools_image` value.

## 0.8.0

* [Feature] Allow overriding spec sections for individual languages
* [Feature] Add `generate_extra_args` as top level config value in `config.json`
* [Improvement] Many documentation fixes/tweaks

## 0.7.0

* [Improvement] Bump openapi-generator in container image to 4.2.0

## 0.6.0

* [Improvement] Bump openapi-generator in container image to 4.1.3

## 0.5.0

* [Feature] When patching upstream templates, run `patch` with `--fuzz 0` to prevent unexpected/hard to debug errors.
* [Feature] Allow setting author name and email on commits created by `apigentools push`.

## 0.4.0

* [Security] OAuth tokens and installation access tokens are no longer logged.

## 0.3.0

* [Feature] Added `--dry-run` option to the `push` command
* [Feature] Made it possible to add extra arguments to `openapi-generator` subprocess
* [Feature] The `push` command will now push to the default branch, if it doesn't exist
* [Feature] Allow skipping pushes for repos with on changes via `push` command
* [Feature] Allow authenticating via OAuth token or installation access token for git operations via https
* [Bugfix] Fixed recognizing list of languages to process from the `APIGENTOOLS_LANG` environment variable
* [Bugfix] When rendering downstream templates, make sure the whole directory structure containing them exists
* [Bugfix] Fixed docs and environment variable name for `apigentools generate --clone-repo` argument

## 0.2.0

* Added `apigentools push` command that creates and pushes new branch after code generation
* Added `--clone-repo` option to `apigentools generate` command to allow cloning repos from Github before running code generation
* Added env var for `openapi_jar` path when using `apigentools templates openapi_jar`
* All OpenAPI spec `components` members are now correctly preserved while generating full spec
* Error is now raised if duplicate fields are found in multiple spec sections while generating full spec
* [Docker] Images are now correctly tagged with `:git-{shortrev}`
* [Docker] Images now store git commit hash inside them during build, thus correctly stamping `apigentools-info` with `:git-{shortrev}` image tag even if running from `apigentools/apigentools:latest`
* [Docker] Updated openapi-generator to 4.1.1

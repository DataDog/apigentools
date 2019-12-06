# Changelog

## 0.9.1

* [Improvement] Make `server_base_url` optional and possibly deprecated in the future version.
* [Bugfix] Fetch branch before checkout in `generate` command with `--branch` option.a
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

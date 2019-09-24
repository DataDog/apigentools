# Changelog

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

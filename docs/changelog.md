# Changelog

## 0.2.0

* Added `apigentools push` command that creates and pushes new branch after code generation
* Added `--clone-repo` option to `apigentools generate` command to allow cloning repos from Github before running code generation
* Added env var for `openapi_jar` path when using `apigentools templates openapi_jar`
* All OpenAPI spec `components` members are now correctly preserved while generating full spec
* Error is now raised if duplicate fields fields are found in multiple spec sections while generating full spec
* [Docker] Images are now correctly tagged with `:git-{shortrev}`
* [Docker] Images now store git commit hash inside them during build, thus correctly stamping `apigentools-info` with `:git-{shortrev}` image tag even if running from `apigentools/apigentools:latest`
* [Docker] Updated openapi-generator to 4.1.1
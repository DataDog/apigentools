# apigentools CLI Reference

Basic usage:

```
apigentools <apigentools-args> <SUBCOMMAND> <subcommand args>
```

Note that a lot of arguments can take their value from environment variables and coded-in defaults. In this case, the actual value is obtained like this:

* If the commandline argument is provided, it is used.
* If the commandline argument is not provided and the environment variable exists, its content is used.
* If the commandline argument is not provided and the enviromnent variable doesn't exist, the coded-in default is used.

Throughout this document, arguments with this behaviour have a value both in their "Environment Variable" column as well as in their "Default" column.

Argument | Description | Environment Variable | Default
---------|-------------|----------------------|--------
`-av API_VERSIONS, --api-versions API_VERSIONS` | The API version to run the specified action against. These must match what the config in the spec repo contains. Example: `apigentools -av v1 -av v2 test` | `APIGENTOOLS_API_VERSION` | `None` to run against all
`-c CONFIG_DIR, --config-dir CONFIG_DIR` | Path to config directory | `APIGENTOOLS_CONFIG_DIR` | `config`
`-g GENERATED_CODE_DIR, --generated-code-dir GENERATED_CODE_DIR` | Path to directory where to save the generated source code | `APIGENTOOLS_GENERATED_CODE_DIR` | `generated`
`-h, --help` | Show help message and exit
`-l LANGUAGES, --languages LANGUAGES` | Languages to run the specified action against. These must match what the config in the spec repo contains. Example: `apigentools -l go -l java test` | `APIGENTOOLS_LANG` | `None` to run against all
`-r SPEC_REPO_DIR, --spec-repo-dir SPEC_REPO_DIR` | Switch to this directory before doing anything else | `APIGENTOOLS_SPEC_REPO_DIR` | `.`
`--git-via-https` | Whether to use https (or ssh) for git actions | `APIGENTOOLS_GIT_VIA_HTTPS` | `false`
`--git-via-https-installation-access-token` | Use installation access token (authenticating a Github app) for git actions. Mutually exclusive with `--git-via-https-oauth-token`. | `APIGENTOOLS_GIT_VIA_HTTPS_INSTALLATION_ACCESS_TOKEN` |
`--git-via-https-oauth-token` | Use OAuth over HTTPS passing this token for git actions. Mutually exclusive with `--git-via-https-installation-access-token`. | `APIGENTOOLS_GIT_VIA_HTTPS_OAUTH_TOKEN` |
`-v, --verbose` | Whether or not to log the generation in verbose mode

## `apigentools generate`

Generates client code. When specified with the `--clone-repo` flag, the `generated-code-dir` for that client must be empty.

Argument | Description | Environment Variable | Default
---------|-------------|----------------------|--------
`--additional-stamp [ADDITIONAL_STAMP [ADDITIONAL_STAMP ...]]` | Additional components to add to the `apigentoolsStamp` variable passed to templates | `APIGENTOOLS_ADDITIONAL_STAMP` | `[]`
`--builtin-templates` | Use unpatched upstream templates | | `false`
`-d DOWNSTREAM_TEMPLATES_DIR, --downstream-templates-dir DOWNSTREAM_TEMPLATES_DIR` | Path to directory with downstream templates | `APIGENTOOLS_DOWNSTREAM_TEMPLATES_DIR` | `downstream-templates`
`-f FULL_SPEC_FILE, --full-spec-file FULL_SPEC_FILE` | Name of the OpenAPI full spec file to write | `APIGENTOOLS_FULL_SPEC_FILE` | `full_spec.yaml`
`-h, --help` | Show help message and exit
`-i GENERATED_WITH_IMAGE, --generated-with-image GENERATED_WITH_IMAGE` | Override the tag of the image with which the client code was generated | `APIGENTOOLS_IMAGE` | `None`
`-s SPEC_DIR, --spec-dir SPEC_DIR` | Path to directory with OpenAPI specs | `APIGENTOOLS_SPEC_DIR` | `spec`
`-t TEMPLATE_DIR, --template-dir TEMPLATE_DIR` | Path to directory with processed upstream templates | `APIGENTOOLS_TEMPLATES_DIR` | `templates`
`--clone-repo` | Whether to pull the remote github repository when generating the client | `APIGENTOOLS_PULL_REPO` | `true`

## `apigentools init`

Initializes a new [Spec Repo](spec_repo.md).

Argument | Description | Environment Variable | Default
---------|-------------|----------------------|--------
`-g, --no-git-repo` | Don't initialize a git repository in the project directory
`-h, --help` | Show help message and exit

## `apigentools push`

Pushes the content of the generated directory to its target git repository
The generated directory is left in the branch that was checked out to push the code.

Argument | Description | Environment Variable | Default
---------|-------------|----------------------|--------
`-h, --help` | Show help message and exit
`--default-branch` | Default branch of client repo - if it doesn't exist, it will be created and pushed to instead of a new feature branch | `APIGENTOOLS_DEFAULT_PUSH_BRANCH` | `master`
`--dry-run` | Do a dry run (do not actualy create branches/commits or push) | | `False`
`--push-commit-msg` | Commit message to use when pushing the generated clients. | `APIGENTOOLS_COMMIT_MSG` | `Regenerate client from commit <XYZ> of spec repo`

## `apigentools split`

Splits an existing one-file OpenAPI spec into multiple sections suitable for usage with apigentools. Useful when doing a first-time batch import of an already existing spec.

Argument | Description | Environment Variable | Default
---------|-------------|----------------------|--------
`-h, --help` | Show help message and exit
`-i INPUT_FILE, --input-file INPUT_FILE` | Path to the OpenAPI full spec file to split
`-s SPEC_DIR, --spec-dir SPEC_DIR` | Path to directory with OpenAPI specs | `APIGENTOOLS_SPEC_DIR` | `spec`
`-v API_VERSION, --api-version API_VERSION` | Version of API that the input spec describes | `APIGENTOOLS_SPLIT_SPEC_VERSION` | `v1`

## `apigentools templates`

Obtains upstream openapi-generator templates, applies template patches and saves them to templates directory.

Argument | Description | Environment Variable | Default
---------|-------------|----------------------|--------
`-h, --help` | Show help message and exit
`-o OUTPUT_DIR, --output-dir OUTPUT_DIR` | Path to directory where to put processed upstream templates | `APIGENTOOLS_TEMPLATES_DIR` | `templates`
`-p TEMPLATE_PATCHES_DIR, --template-patches-dir TEMPLATE_PATCHES_DIR` | Directory with patches for upstream templates | `APIGENTOOLS_TEMPLATE_PATCHES_DIR` | `template-patches`

### `apigentools templates local-dir`

Obtains upstream templates from a given local directory.

Argument | Description | Environment Variable | Default
---------|-------------|----------------------|--------
`-h, --help` | Show help message and exit

Positional Argument | Description | Environment Variable | Default
--------------------|-------------|----------------------|--------
`local_path` | Path to directory with openapi-generator upstream templates

### `apigentools templates openapi-git`

Obtains upstream templates from openapi-generator git repository.

Argument | Description | Environment Variable | Default
---------|-------------|----------------------|--------
`-h, --help` | Show help message and exit
`-u REPO_URL, --repo_url REPO_URL` | URL of the openapi-generator repo | | `https://github.com/OpenAPITools/openapi-generator`

Positional Argument | Description | Environment Variable | Default
--------------------|-------------|----------------------|--------
`git_committish` | Git 'committish' to check out before obtaining templates | | `master`

### `apigentools templates openapi-jar`

Obtains upstream templates from an openapi-generator jar file.

Argument | Description | Environment Variable | Default
---------|-------------|----------------------|--------
`-h, --help` | Show help message and exit

Positional Argument | Description | Environment Variable | Default
--------------------|-------------|----------------------|--------
`jar_path` | Path to openapi-generator jar file | `APIGENTOOLS_OPENAPI_JAR` | `openapi-generator.jar`

## `apigentools test`

Runs tests of generated clients.

Argument | Description | Environment Variable | Default
---------|-------------|----------------------|--------
`--container-env [CONTAINER_ENV [CONTAINER_ENV ...]]` | Additional environment variables to pass to containers running the tests, for example `--container-env API_KEY=123 OTHER_KEY=234`. Note that apigentools contains additional logic to treat these values as sensitive and avoid logging them during runtime. (NOTE: if the testing container itself prints this value, it *will* be logged as part of the test output by apigentools).
`-g GENERATED_CODE_DIR, --generated-code-dir GENERATED_CODE_DIR` | Path to directory where the generated source code is | `APIGENTOOLS_GENERATED_CODE_DIR` | `generated`
`-h, --help` | Show help message and exit
`--no-cache` | Build test image with --no-cache option | `APIGENTOOLS_TEST_BUILD_NO_CACHE` | `False`

# Containerized Version

The apigentools PyPI package ships with two scripts - `apigentools` and `container-apigentools`. The containerized version will execute all commands in a container created from given image. Additionally, all `APIGENTOOLS_*` environment variables from current environment are passed inside the container. Basic usage:

`container-apigentools IMAGE [--spec-repo-volume SPEC_REPO_VOLUME] [APIGENTOOLS_ARG ...]`

Argument | Description | Environment Variable | Default
---------|-------------|----------------------|--------
`--spec-repo-volume SPEC_REPO_VOLUME` | Path to directory with the Spec Repo | | `.`

Positional Argument | Description | Environment Variable | Default
--------------------|-------------|----------------------|--------
`IMAGE` | apigentools image to use, e.g. `apigentools:1.2.3`
`APIGENTOOLS_ARGS` | arguments to pass to apigentools running inside container, see the help for apigentools above

Note that if `APIGENTOOLS_ARGS` is not provided, a [full automated workflow](workflow.md#run-all-automated-parts-of-the-workflow) will be run.

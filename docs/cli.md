# apigentools CLI Reference

Basic usage:

```
apigentools <apigentools-args> <SUBCOMMAND> <subcommand args>
```

Note that a lot of arguments can take their value from environment variables and coded-in defaults. In this case, the actual value is obtained like this:

* If the commandline argument is provided, it is used.
* If the commandline argument is not provided and the environment variable exists, its content is used.
* If the commandline argument is not provided and the enviromnent variable doesn't exist, the coded-in default is used.

Throughout this document, arguments with this behaviour have their default specified as "Default: `APIGENTOOLS_XXX` or `coded-in-value`".

Apigentools arguments:

* `-av API_VERSIONS, --api-versions API_VERSIONS` - The API version to run the specified action against. These must match what the config in the spec repo contains. Example: `apigentools -av v1 -av v2 test` (Default: `APIGENTOOLS_API_VERSION` or `None` to run against all)
* `-c CONFIG_DIR, --config-dir CONFIG_DIR` - Path to config directory (Default: `APIGENTOOLS_CONFIG_DIR` or `config`)
* `-g GENERATED_CODE_DIR, --generated-code-dir GENERATED_CODE_DIR` - Path to directory where to save the generated source code (default: `APIGENTOOLS_GENERATED_CODE_DIR` or `generated`)
* `-h, --help` - Show help message and exit
* `-l LANGUAGES, --languages LANGUAGES` - Languages to run the specified action against. These must match what the config in the spec repo contains. Example: `apigentools -l go -l java test` (Default: `APIGENTOOLS_LANG` or `None` to run against all)
* `-r SPEC_REPO_DIR, --spec-repo-dir SPEC_REPO_DIR` - Switch to this directory before doing anything else (Default: `APIGENTOOLS_SPEC_REPO_DIR` or `.`)
* `-v, --verbose` - Whether or not to log the generation in verbose mode

## `apigentools generate`

Generates client code.

* `--additional-stamp [ADDITIONAL_STAMP [ADDITIONAL_STAMP ...]]` - Additional components to add to the `apigentoolsStamp` variable passed to templates (Default: `APIGENTOOLS_ADDITIONAL_STAMP` or `[]`)
* `--builtin-templates` - Use unpatched upstream templates (Default: `false`)
* `-d DOWNSTREAM_TEMPLATES_DIR, --downstream-templates-dir DOWNSTREAM_TEMPLATES_DIR` - Path to directory with downstream templates (Default: `APIGENTOOLS_DOWNSTREAM_TEMPLATES_DIR` or `downstream-templates`)
* `-f FULL_SPEC_FILE, --full-spec-file FULL_SPEC_FILE` - Name of the OpenAPI full spec file to write (Default: `APIGENTOOLS_FULL_SPEC_FILE` or `full_spec.yaml`)
* `-h, --help` - Show help message and exit
* `-i GENERATED_WITH_IMAGE, --generated-with-image GENERATED_WITH_IMAGE` - Override the tag of the image with which the client code was generated (Default: `APIGENTOOLS_IMAGE` or `None`)
* `-s SPEC_DIR, --spec-dir SPEC_DIR` - Path to directory with OpenAPI specs (Default: `APIGENTOOLS_SPEC_DIR` or `spec`)
* `-t TEMPLATE_DIR, --template-dir TEMPLATE_DIR` - Path to directory with processed upstream templates (Default: `APIGENTOOLS_TEMPLATES_DIR` or `templates`)

## `apigentools init`

Initializes a new [Spec Repo](spec_repo.md).

Arguments:

* `-g, --no-git-repo` - Don't initialize a git repository in the project directory
* `-h, --help` - Show help message and exit

## `apigentools push`

Currently not operational, please don't use.

## `apigentools split`

Splits an existing one-file OpenAPI spec into multiple sections suitable for usage with apigentools. Useful when doing a first-time batch import of an already existing spec.

* `-h, --help` - Show help message and exit
* `-i INPUT_FILE, --input-file INPUT_FILE` - Path to the OpenAPI full spec file to split
* `-s SPEC_DIR, --spec-dir SPEC_DIR` - Path to directory with OpenAPI specs (Default: `APIGENTOOLS_SPEC_DIR` or `spec`)
* `-v API_VERSION, --api-version API_VERSION` - Version of API that the input spec describes (Default: `APIGENTOOLS_SPLIT_SPEC_VERSION` or `v1`)

## `apigentools templates`

Obtains upstream openapi-generator templates, applies template patches and saves them to templates directory.

Arguments:

* `-h, --help` - Show help message and exit
* `-o OUTPUT_DIR, --output-dir OUTPUT_DIR` - Path to directory where to put processed upstream templates (Default: `APIGENTOOLS_TEMPLATES_DIR` or `templates`)
* `-p TEMPLATE_PATCHES_DIR, --template-patches-dir TEMPLATE_PATCHES_DIR` - Directory with patches for upstream templates (Default: `APIGENTOOLS_TEMPLATE_PATCHES_DIR` or `template-patches`)

### `apigentools templates local-dir`

Obtains upstream templates from a given local directory.

Arguments:

* `-h, --help` - Show help message and exit

Positional arguments:

* `local_path` - Path to directory with openapi-generator upstream templates

### `apigentools templates openapi-git`

Obtains upstream templates from openapi-generator git repository.

Arguments:

* `-h, --help` - Show help message and exit
* `-u REPO_URL, --repo_url REPO_URL` - URL of the openapi-generator repo (Default: `https://github.com/OpenAPITools/openapi-generator`)

Positional arguments:

* `git_committish` - Git 'committish' to check out before obtaining templates (Default: `master`)

### `apigentools templates openapi-jar`

Obtains upstream templates from an openapi-generator jar file.

Arguments:

* `-h, --help` - Show help message and exit

Positional arguments:

* `jar_path` - Path to openapi-generator jar file

## `apigentools test`

Runs tests of generated clients.

* `--container-env [CONTAINER_ENV [CONTAINER_ENV ...]]` - Additional environment variables to pass to containers running the tests, for example `--container-env API_KEY=123 OTHER_KEY=234`. Note that these values are considered secret by apigentools and thus will never be logged.
* `-g GENERATED_CODE_DIR, --generated-code-dir GENERATED_CODE_DIR` - Path to directory where the generated source code is (Default: `APIGENTOOLS_GENERATED_CODE_DIR` or `generated`)
* `-h, --help` - Show help message and exit
* `--no-cache` - Build test image with --no-cache option (Default: `APIGENTOOLS_TEST_BUILD_NO_CACHE` or `False`)

# Containerized Version

The apigentools PyPI package ships with two scripts - `apigentools` and `container-apigentools`. The containerized version will execute all commands in a container created from given image. Additionally, all `APIGENTOOLS_*` environment variables from current environment are passed inside the container. Basic usage:

`container-apigentools IMAGE [--spec-repo-volume SPEC_REPO_VOLUME] [APIGENTOOLS_ARG ...]`

Arguments:

* `--spec-repo-volume SPEC_REPO_VOLUME` - Path to directory with the Spec Repo (Default: `.`)

Positional arguments:

* `IMAGE` - apigentools image to use, e.g. `apigentools:1.2.3`
* `APIGENTOOLS_ARGS` - arguments to pass to apigentools running inside container, see the help for apigentools above

Note that if `APIGENTOOLS_ARGS` is not provided, a [full automated workflow](workflow.md#run-all-automated-parts-of-the-workflow) will be run.
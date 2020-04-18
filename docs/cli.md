# apigentools CLI Reference

!!! note
    This is documentation for apigentools major version 1, which has significant differences from the 0.X series. Refer to [upgrading docs](upgrading.md) for further details.

## Basic Usage

```
apigentools <APIGENTOOLS_ARGS> <SUBCOMMAND> <SUBCOMMAND_ARGS>
```

Many arguments take values from environment variables and coded-in defaults. In this case, the actual value is obtained like this:

* If the command line argument is provided, it is used.
* If the command line argument is **not** provided, and the environment variable exists, the environment variable is used.
* If the command line argument is **not** provided, and the enviromnent variable does **not** exist, the coded-in default is used.

Throughout this document, arguments with this behavior have a value both in their "Environment Variable" column as well as in their "Default" column.

Argument | Description | Environment Variable | Default
---------|-------------|----------------------|--------
`-av API_VERSIONS, --api-versions API_VERSIONS` | The API version to run the specified action against. These must match what the config in the spec repo contains. Example: `apigentools -av v1 -av v2 test` | `APIGENTOOLS_API_VERSION` | `None` to run against all
`--help` | Show help message and exit.
`-l LANGUAGES, --languages LANGUAGES` | Languages to run the specified action against. These must match what the config in the spec repo contains. Example: `apigentools -l go -l java test` | `APIGENTOOLS_LANG` | `None` to run against all
`-r SPEC_REPO_DIR, --spec-repo-dir SPEC_REPO_DIR` | Switch to this directory before doing anything else. | `APIGENTOOLS_SPEC_REPO_DIR` | `.`
`--git-via-https` | Whether to use HTTPS (or SSH) for git actions. | `APIGENTOOLS_GIT_VIA_HTTPS` | `false`
`--git-via-https-installation-access-token` | Use installation access token (authenticating a Github app) for git actions. Mutually exclusive with `--git-via-https-oauth-token`. | `APIGENTOOLS_GIT_VIA_HTTPS_INSTALLATION_ACCESS_TOKEN` |
`--git-via-https-oauth-token` | Use OAuth over HTTPS, passing this token for git actions. Mutually exclusive with `--git-via-https-installation-access-token`. | `APIGENTOOLS_GIT_VIA_HTTPS_OAUTH_TOKEN` |
`--verbose` | Log generation in verbose mode.
`--delete-generated-files` | Delete generated files in output_dir before generation | NA | `False`
`--skip-version-check` | Skip the check that the apigentools version is in range of whats supported in the spec config file. | `APIGENTOOLS_SKIP_VERSION_CHECK` | `False`

## `apigentools generate`

Generates client code. When specified with the `--clone-repo` flag, the directory with generated code for that language must be empty.

Argument | Description | Environment Variable | Default
---------|-------------|----------------------|--------
`--additional-stamp [ADDITIONAL_STAMP [ADDITIONAL_STAMP ...]]` | Additional components to add to the `apigentoolsStamp` variable passed to templates. | `APIGENTOOLS_ADDITIONAL_STAMP` | `[]`
`--branch` | When specified, changes the client repository branch before running code generation. | `APIGENTOOLS_PULL_REPO_BRANCH` | `None`
`--clone-repo` | Whether to clone the client Github repositories before running code generation. | `APIGENTOOLS_PULL_REPO` | `False`
`-f FULL_SPEC_FILE, --full-spec-file FULL_SPEC_FILE` | Name of the OpenAPI full spec file to write. Note that if some languages override config's spec_sections, additional files will be generated with name pattern `full_spec.<lang>.yaml`. | `APIGENTOOLS_FULL_SPEC_FILE` | `full_spec.yaml`
`--is-ancestor` | Checks that the --branch is ancestor of specified branch. Useful to enforce in CI that the feature branch is on top of master branch: '-branch feature --is-ancestor master'. | `APIGENTOOLS_IS_ANCESTOR` | `None`
`--help` | Show help message and exit.
`--skip-templates` | Skip template preparation step. | `APIGENTOOLS_SKIP_TEMPLATES` | `False`

## `apigentools init`

Initializes a new [spec repo](spec_repo.md).

Argument | Description | Environment Variable | Default
---------|-------------|----------------------|--------
`-g, --no-git-repo` | Don't initialize a git repository in the project directory.
`--help` | Show help message and exit.

## `apigentools push`

Pushes the content of the generated directory to its target git repository. The generated directory is left in the branch that was checked out to push the code.

Argument | Description | Environment Variable | Default
---------|-------------|----------------------|--------
`--default-branch` | Default branch of client repo. If this branch does not exist, it is created and pushed to instead of a new feature branch | `APIGENTOOLS_DEFAULT_PUSH_BRANCH` | `master`
`--dry-run` | Do a dry run (do not actualy create branches/commits or push). | | `False`
`--git-email` | Email of the git commit author. | `APIGENTOOLS_GIT_AUTHOR_EMAIL` | `None`
`--git-name` | Name of the git commit author. | `APIGENTOOLSGIT_AUTHOR_NAME` | `None`
`--help` | Show help message and exit.
`--push-commit-msg` | Commit message to use when pushing the generated clients. | `APIGENTOOLS_COMMIT_MSG` | `Regenerate client from commit <COMMIT_ID> of spec repo`
`--skip-if-no-changes` | Skip committing/pushing for all repositories where only `.apigentools-info` has changed. | `APIGENTOOLS_SKIP_IF_NO_CHANGES` | `False`

**Note** Specifying the `--git-*` flags modifies the `.git/config` settings of each local repository that you push to to via apigentools. This does not modify the global `.git/config`.

## `apigentools split`

Splits an existing one-file OpenAPI spec into multiple sections suitable for usage with apigentools. This is useful when doing a first-time batch import of an already existing spec.

Argument | Description | Environment Variable | Default
---------|-------------|----------------------|--------
`--help` | Show help message and exit.
`-i INPUT_FILE, --input-file INPUT_FILE` | Path to the OpenAPI full spec file to split.
`-v API_VERSION, --api-version API_VERSION` | Version of API that the input spec describes. | `APIGENTOOLS_SPLIT_SPEC_VERSION` | `v1`

## `apigentools templates`

Obtains upstream `openapi-generator` templates, applies template patches, and saves them to a templates directory.

Argument | Description | Environment Variable | Default
---------|-------------|----------------------|--------
`--help` | Show help message and exit.

## `apigentools test`

Runs tests of generated clients.

Argument | Description | Environment Variable | Default
---------|-------------|----------------------|--------
`--container-env [CONTAINER_ENV [CONTAINER_ENV ...]]` | Additional environment variables to pass to containers running the tests, for example `--container-env API_KEY=123 OTHER_KEY=234`. Note that apigentools contains additional logic to treat these values as sensitive and avoid logging them during runtime. (**NOTE**: if the testing container itself prints this value, it *will* be logged as part of the test output by apigentools).
`--help` | Show help message and exit.
`--no-sensitive-output` | By default, it is considered that the environment values provided through `--container-env` may contain sensitive values and the whole command and its output is therefore hidden. You can override this behaviour by using this flag. | `APIGENTOOLS_NO_SENSITIVE_OUTPUT` | `False`

## `apigentools config`

Displays information about the configuration for the spec being worked on, including supported languages, api versions, and the paths to the generated api yaml.
These languages and api versions can be directly passed to the `--languages` and `--api-versions` flags of the supported commands.

Argument | Description | Environment Variable | Default
---------|-------------|----------------------|--------
`-f FULL_SPEC_FILE, --full-spec-file FULL_SPEC_FILE` | Name of the OpenAPI full spec file to write. Note that if some languages override config's spec_sections, additional files will be generated with name pattern `full_spec.<lang>.yaml`. | `APIGENTOOLS_FULL_SPEC_FILE` | `full_spec.yaml`
`-L, --list-languages` | Whether to only list the languages supported by this spec. Example: `apigentools -l` | `NA` | `None` to list both languages and versions
`-V, --list-versions` | Whether to only list the API versions supported by this spec. Example: `apigentools -av` | `NA` | `None` to list both languages and versions
`--help` | Show help message and exit.

## `apigentools validate`

Runs validation steps defined in `config/config.yaml`.

Argument | Description | Environment Variable | Default
---------|-------------|----------------------|--------
`-f FULL_SPEC_FILE, --full-spec-file FULL_SPEC_FILE` | Name of the OpenAPI full spec file to write. Note that if some languages override config's spec_sections, additional files will be generated with name pattern `full_spec.<lang>.yaml`. | `APIGENTOOLS_FULL_SPEC_FILE` | `full_spec.yaml`
`--help` | Show help message and exit.

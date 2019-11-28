# Typical apigentools Workflow

This page summarizes the typical workflow for making changes to your spec and regenerating your client code:

## Overview

* First time setup:
    1. Get set up
    2. Create "Spec Repo"
* Repeated:
    1. (If necessary) Modify the OpenAPI spec sections
    2. (If necessary) Modify apigentools configuration
    3. Validate specs (locally or using Docker)
    4. (If necessary) Add template patches
    5. (If necessary) Add downstream templates
    6. (If necessary) Prepare templates (locally or using Docker)
    7. Generate client code (locally or using Docker)
    8. Run tests
    9. (WIP) Push code

The following sections explain the individual steps.

## Get Set Up

Install apigentools from PyPI:

```
pip install apigentools
```

Note that apigentools ships with 2 executables: `apigentools` and `container-apigentools`. Consult the [CLI documentation](cli.md) on how these are used. While the following sections provide examples using both of these, we recommend using the container version to ensure reproducibility and presence of all necessary tools.

Note that up until version 0.8.0, the `container-apigentools` required a positional argument with image to use, e.g. `container-apigentools apigentools/apigentools:0.8.0 validate`. Since 0.9.0, the image to be used is read either from `APIGENTOOLS_IMAGE` environment variable or from [config](spec_repo.md#configconfigjson) `container_apigentools_image` value.

## Create a "Spec Repo"

To create a scaffold [spec repo](spec_repo.md) structure in `myapispec` directory, run:

```
apigentools init myapispec
```

## Modify the OpenAPI Spec Sections

To add or change the behavior of your generated clients, modify the [spec sections](spec_repo.md#section-files) for the relevant major version of your API under `spec/<MAJOR_VERSION>`.

If you are adding new section files, also add them in `spec_sections` in `config/config.json`.

If you are adding a new major API version, also add it in the top-level `spec_versions` and then in per-language `spec_versions` in `config/config.yaml`. With this, you can choose which languages generate code for which major API versions.

## Modify apigentools Configuration

When adding new languages to generate clients, adding major API versions, or adding spec sections, you must make corresponding changes to [config/config.yaml](spec_repo.md#configconfigjson).

## Validate Specs

To check the basic validity of your specs, use the [validate command](cli.md#apigentools-validate).

### Locally

Run `apigentools validate`.

### Docker

Run `container-apigentools validate`.

## Add Template Patches

Templates that are built into openapi-generator are used to generate API clients. To modify these templates, include the `template-patches` directory in your repository with patches that get applied to the upstream templates. You can create these patches by making changes in a checked out openapi-generator repo:

```
git clone git@github.com:OpenAPITools/openapi-generator.git
cd openapi-generator
# do changes in modules/openapi-generator/src/main/resources/<language>
git diff --relative=modules/openapi-generator/src/main/resources/ > /path/to/spec/repo/template-patches/java-0001-my-functionality.patch
```

All files with the `.patch` extension from `template-patches` directory are applied.

## Add Downstream Templates

If you wish to add your own templates that need to be rendered in a different context, and have different usages than those provided in openapi-generator upstream, you can add these in the `downstream-templates/<LANGUAGE>` directory. This is best used to add files that are top-level for each of the generated repositories, as the openapi-generator is used to render only per-major-API-version subdirectories with the actual code.

Note that downstream templates are rendered after the code generation is done, and may overwrite files written by previous code generation. Downstream templates are [mustache templates](https://mustache.github.io/).

## Prepare Templates

Preparing templates means obtaining templates from openapi-generator upstream (either from a git repo, JAR file, or local dir) and applying template patches on top of them.

### Locally

Example: `apigentools templates local-dir /path/to/base/templates`

### Docker

Example: `container-apigentools templates openapi-git v4.1.0`

## Generate Client Code

To generate actual client code with the [generate command](cli.md#apigentools-generate), you need [templates prepared](#prepare-templates).

### Locally

Run `apigentools generate`.

### Docker

Run `container-apigentools generate`.

## Run Tests

openapi-generator pre-creates unit test files for most of the languages supported. The tests themselves need to be implemented by hand, but apigentools still allows running them as an optional part of the process. The [test command](cli.md#apigentools-test) looks for `Dockerfile.test` and `Dockerfile.test.{major_api_version}` files in the *top level directory* of the generated repo (*not* in the subdirectory with code for that specific major API version). For example, if a specific language in `config.json` has `"github_repo_name": "my-client-java"` and `"spec_versions": ["v1", "v2"]`, apigentools will be looking for `generated/my-client-java/Dockerfile.test`, `generated/my-client-java/Dockerfile.test.v1` and `generated/my-client-java/Dockerfile.test.v2`. For each of these files found, it is built and then executed without arguments. These Dockerfiles would need to be put in the repos manually or added via the [downstream templates](#add-downstream-templates) mechanism.

### Locally

Run `apigentools test`.

### Docker

Run `container-apigentools test`.

## Push Code

The [push command](cli.md#apigentools-push) allows for taking the generated client code and pushing it up to the remote target directory, so that you can create and merge a quick pull request.

Note that when using the `push` command, the generated directory must be empty, and you must run the `generate` command with the `--clone-repo` flag. This ensure that the latest master of the client repository is cloned into the generated directory, and that the generated client is generated on top of this—while respecting any ignore rules.

# Run All Automated Parts of the Workflow

Note that you can run all the above commands (`validate`, `templates`, `generate`, and `test`) in sequence with Docker with just one command by passing no additional arguments to `container-apigentools`:

Run `container-apigentools`.
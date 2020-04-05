# Typical apigentools Workflow

!!! note
    This is documentation for apigentools major version 1, which has significant differences from the 0.X series. Refer to [upgrading docs](upgrading.md) for further details.

This page summarizes the typical workflow for making changes to your spec and regenerating your client code:

## Overview

* First time setup:
    1. Get set up
    2. Create "Spec Repo"
* Repeated:
    1. (If necessary) Modify the OpenAPI spec sections
    2. (If necessary) Modify apigentools configuration
    3. Validate specs
    4. (If necessary) Add template patches
    5. (If necessary) Add downstream templates
    6. (If necessary) Prepare templates
    7. Generate client code
    8. Run tests
    9. (WIP) Push code

The following sections explain the individual steps.

## Get Set Up

Install apigentools from PyPI:

```
pip install apigentools
```

## Create a "Spec Repo"

To create a scaffold [spec repo](spec_repo.md) structure in `myapispec` directory, run:

```
apigentools init myapispec
```

## Modify the OpenAPI Spec Sections

To add or change the behavior of your generated clients, modify the [spec sections](spec_repo.md#section-files) for the relevant major version of your API under `spec/<MAJOR_VERSION>`.

If you are adding new section files, also add them in `spec_sections` in `config/config.yaml`.

If you are adding a new major API version, also add it in the top-level `spec_versions` and then in per-language `spec_versions` in `config/config.yaml`. With this, you can choose which languages generate code for which major API versions.

## Modify apigentools Configuration

When adding new languages to generate clients, adding major API versions, or adding spec sections, you must make corresponding changes to [config/config.yaml](spec_repo.md#configconfigjson).

## Validate Specs

To check the basic validity of your specs, use the [validate command](cli.md#apigentools-validate).

Run `apigentools validate`.

## Add Template Patches

Templates that are built into openapi-generator (or other code generators) are used to generate API clients. To modify these templates, include the `template-patches` directory in your repository with patches that get applied to the upstream templates. For example, for openapi-generator you can create these patches by making changes in a checked out openapi-generator repo:

```
git clone git@github.com:OpenAPITools/openapi-generator.git
cd openapi-generator
# do changes in modules/openapi-generator/src/main/resources/<language>
git diff --relative=modules/openapi-generator/src/main/resources/ > /path/to/spec/repo/template-patches/java-0001-my-functionality.patch
```

The patch files must be listed in `config/config.yaml` [templates section](spec_repo.md#preprocess-templates).

## Add Downstream Templates

If you wish to add your own templates that need to be [rendered in a different context](spec_repo.md#downstream-templates) , and have different usages than those provided in openapi-generator upstream, you can add these in the `downstream-templates/<LANGUAGE>` directory.

Note that downstream templates are rendered after the code generation is done, and may overwrite files written by previous code generation. Downstream templates are [mustache templates](https://mustache.github.io/).

Downstream templates must be listed in `config/config.yaml` [downstream_templates section](spec_repo.md#downstream-templates).

## Prepare Templates

*NOTE:* [preparing templates](spec_repo.md#preprocess-templates) is done as part of `apigentools generate` step. The individual `apigentools templates` command is mostly useful for debugging/creating template patches.

Run: `apigentools templates`.

## Generate Client Code

You can generate actual client code with the [generate command](cli.md#apigentools-generate).

Run: `apigentools generate`.

## Run Tests

openapi-generator pre-creates unit test files for most of the languages supported. The tests themselves need to be implemented by hand, but apigentools still allows running them as an optional part of the process.

The [test command](cli.md#apigentools-test) looks for `Dockerfile.test` and `Dockerfile.test.{major_api_version}` files in the *top level directory* of the generated repo (*not* in the subdirectory with code for that specific major API version).

For example, if a specific language in `config/config.yaml` has `"github_repo_name": "my-client-java"` and `"spec_versions": ["v1", "v2"]`, apigentools will be looking for `generated/my-client-java/Dockerfile.test`, `generated/my-client-java/Dockerfile.test.v1` and `generated/my-client-java/Dockerfile.test.v2`. For each of these files found, it is built and then executed without arguments. These Dockerfiles would need to be put in the repos manually or added via the [downstream templates](#add-downstream-templates) mechanism.

### Locally

Run `apigentools test`.

## Push Code

The [push command](cli.md#apigentools-push) allows for taking the generated client code and pushing it up to the remote target directory, so that you can create and merge a quick pull request.

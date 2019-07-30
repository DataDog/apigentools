# Typical apigentools Workflow

This page summarizes the typical workflow that you would use when doing changes to your spec and regenerating your client code:

## Overview

Generally, the workflow steps are:

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
TODO: not available yet
```

Note that apigentools are shipped with 2 executables - `apigentools` and `container-apigentools`. Consult [CLI documentation](cli.md) on how these are used. The following sections will provide examples using both of these.

## Create "Spec Repo"

To create a scaffold [Spec Repo](spec_repo.md) structure in `myapispec` directory, run:

```
apigentools init myapispec
```

## Modify the OpenAPI Spec Sections

When you want to add/change behaviour of your generated clients, you need to modify the [spec sections](file_formats.md#section-files) for the relevant major version of your API under `spec/<MAJOR_VERSION>`. If you're adding new section files, don't forget to also add them in `spec_sections` in `config/config.json`. If you're adding a new major API version, don't forget to add it in top-level `spec_versions` and then in per-language `spec_versions` in `config/config.yaml` (thanks to this, you can choose which languages generate code for which major API versions).

## Modify apigentools Configuration

When adding new languages to generate clients for, adding major API version or adding spec sections, you'll need to do the corresponding changes to [config/config.yaml](file_formats.md#configconfigjson).

## Validate Specs

To check basic validity of your specs, use the [validate command](cli.md#apigentools-validate).

### Locally

Run `apigentools validate`.

### Docker

Run `container-apigentools apigentools:latest validate`

## Add Template Patches

Templates that are built into openapi-generator are used to generate API clients. Sometimes it's necessary to modify these templates. To achieve that, you can include `template-patches` directory in yout repository with patches that get applied to the upstream templates. You can create such patches by doing changes in a checked out openapi-generator repo:

```
git clone git@github.com:OpenAPITools/openapi-generator.git
cd openapi-generator
# do changes in modules/openapi-generator/src/main/resources/<language>
git diff --relative=modules/openapi-generator/src/main/resources/ > /path/to/spec/repo/template-patches/java-0001-my-functionality.patch
```

All files with `.patch` extension from `template-patches` directory are applied

## Add Downstream Templates

Sometimes you may need to add our own templates that need to be rendered in a completely different context and have different usage than those provided in openapi-generator upstream. These can be added to the `downstream-templates/<language>` directory. This is best used to add files that are top-level for each of the generated repositories, as the openapi-generator is used to render only per-major-API-version subdirectories with the actual code.

Note that downstream templates are rendered after the code generation is done; take this into consideration should they overwrite files written by previous code generation. Downstream templates are [mustache templates](https://mustache.github.io/).

## Prepare Templates

Preparing templates means obtaining templates from openapi-generator upstream (either from git repo, jar file or a local dir) and applying template patches on top of them.

### Locally

Run e.g. `apigentools templates local-dir /path/to/base/templates`

### Docker

Run e.g. `container-apigentools apigentools:latest templates openapi-git v4.0.2`

## Generate Client Code

To generate actual client code with the [generate command](cli.md#apigentools-generate), you need [templates prepared](#prepare-templates).

### Locally

Run `apigentools generate`

### Docker

Run `container-apigentools apigentools:latest generate`

## Run Tests

openapi-generator pre-creates unittest files for most of the languages supported. The tests themselves need to be implemented by hand, but apigentools still allows running them as an optional part of the process. The [test command](cli.md#apigentools-test) will look for `Dockerfile.test.{major_api_version}` file in the *top level directory* of the generated repo (*not* in the subdirectory with code for that specific major API version) - for example, if a specific language in `config.json` has `"github_repo_name": "my-client-java"` and `"spec_versions": ["v1", "v2"]`, apigentools will be looking for `generated/my-client-java/Dockerfile.test.v1` and `generated/my-client-java/Dockerfile.test.v2`. For each of these files found, it is built and then executed without arguments. These Dockerfiles would need to be put in the repos manually or added via the [downstream templates](#add-downstream-templates) mechanism.

### Locally

Run `apigentools test`

### Docker

Run `container-apigentools apigentools:latest test`

## Push Code

The [push command](cli.md#apigentools-push) is currently unstable, please don't use it.

# Run All Automated Parts of the Workflow

Note that all the above commands (`validate`, `templates`, `generate` and `test`) can be run in sequence with Docker in just one command by passing no additional arguments to `container-apigentools`:

Run `container-apigentools apigentools:local`

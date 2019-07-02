#  apigentools - Generate API Clients with Ease

## Purpose

The purpose of the apigentools package is providing an easy way to generate API clients from [OpenAPI v3 specification](https://github.com/OAI/OpenAPI-Specification/) for multiple languages using [openapi-generator](https://github.com/OpenAPITools/openapi-generator).

*Note on "downstream/upstream" nomenclature*: Throughout the code and documentation of this repository, the words "*downstream*" and "*upstream*" are used when talking about certain pieces of functionality and/or templates. In this context, "*upstream*" is used to reference functionality/templates coming from openapi-generator or other external tools used; "*downstream*" is used to reference configuration and modifications that you will be providing as inputs to apigentools.

## Basic Workflow

This section summarizes the basic workflow from creating the OpenAPI specs to generating client code.

In general, the workflow is as follows:

1. Get set up
2. Create "Spec Repo"
   1. Create the OpenAPI specs
   2. Create apigentools configuration, patches and downstream templates
3. Validate specs (locally or using Docker)
4. (Optional) Add template patches
5. (Optional) Add downstream templates
6. Prepare templates (locally or using Docker)
7. Generate client code (locally or using Docker)
8. Run tests

See the below sections for descriptions of the above steps.

### Get Set Up

#### Local Setup

If you want to do the execution steps locally, you'll need to [install openapi-generator](https://openapi-generator.tech/docs/installation), preferrably using `npm`. See the `Dockerfile` for a version used there to get the same result. Using local option is mostly useful when trying different versions of openapi-generator and/or other changes that would require rebuilding the image and thus would be time consuming.

You will also need to install some Python dependencies with `pip3 install --user -r requirements.txt`.

#### Docker Setup

If you want to do the execution steps using Docker, you'll just need Docker. Build the tools image using `docker build . -t apigentools:local`. You can of course create your own image with all the tooling that you might require to generate your API clients.

The `apigentools` package contains a convenience wrapper script called `container-apigentools` that can be used to execute `apigentools` inside a container. Examples are provided below. Note that while all the examples explicitly pass `--spec-repo-volume /absolute/path/to/spec/repo`, you can omit this if running the command from the spec repo directory.

This repository contains a simple Dockerfile that can be used to build an image that works fine with `container-apigentools` script. We intend to keep it as minimal as possible, therefore we recommend that you build your own image (either on top of our one or from scratch) if you need any special tools run before/after code generation.

### Create "Spec Repo"

apigentools expects you to have a separate repository containing various configuration files, openapi specs and other artifacts. We call it the "Spec Repo". The expected layout is as follows:

```
.
├── .gitignore
├── config
│   ├── config.json                 # general config for apigentools
│   └── languages
│       └── java_v1.json            # openapi-generator config for Java client for v1 API
├── downstream-templates
│   └── java
│       └── LICENSE                 # a file/template to add to generated client
├── generated                       # generated code will end up in this directory
│   └── .gitkeep
├── spec
│   └── v1                          # directory with spec of v1 of the API
│       ├── accounts.yaml           # example: spec of the accounts API
│       ├── header.yaml             # header of the OpenAPI spec
│       └── shared.yaml             # entities shared between multiple parts of the OpenAPI spec
├── template-patches
│   └── java-01-minor-change.patch  # a patch to apply to openapi-generator template
└── templates                       # openapi-generator templates with applied patches end up here
    └── .gitkeep
```

Most of the paths in this layout can be overriden by commandline arguments passed to apigentools executable. More details about files from the above structure can be found in following sections.

#### Create the OpenAPI Specs

Since OpenAPI specs quickly grow large, apigentools allows splitting them into multiple files (see the `spec/v1` directory above). While any files with `.yaml` extension will be picked up, apigentools recommends putting at least:

* `header.yaml` file with information like `info` and `openapi` required by OpenAPI spec
* `shared.yaml` file with entities shared between multiple files in this directory (e.g. common schemas)

All of the files in this directory have structure defined by the OpenAPI specification, e.g. contain `paths`, `components`, `tags`, `security`, etc. apigentools can merge these files into a single file which is required by openapi-generator to work.

Note that for now, we intentionally only generate client code into per-major-API-version subdirectories to be able to have clients that support side-by-side importable modules for multiple major API versions.

#### Create apigentools Configuration, Patches and Downstream Templates

Following files are used by apigentools or are otherwise useful in the Spec Repo:

* `.gitignore` (optional) - Usually you would want to add everything under `generated/` and `templates/` ignored from this git repository
* `config/config.json` - Configuration file for apigentools, see [configuration format](#configconfigjson).
* `config/languages/{language}_{spec_version}.json` - Files in the `config/languages` directory are openapi-generator configuration files. A configuration file must exist for each combination of `language` and each of its `spec_versions`.
* `downstream-templates` (optional) - A directory with downstream-added templates that you might need. Note that these are [mustache templates](https://mustache.github.io/), but are rendered with variables from your `config/config.json` file's language sections.
* `template-patches` (optional) - A directory with your downstream template patches; these are applied to openapi-generator templates before the generation process, thus allowing you to customize the upsteam templates.

### Validate Specs

To generate an all-in-one OpenAPI spec file from all the specs in `spec` directory, you can either use `apigentools` directly or image built from the included `Dockerfile`.

#### Locally

Run `apigentools -b path/to/spec/repo validate`.

#### Docker

Run `container-apigentools apigentools:local --spec-repo-volume /absolute/path/to/spec/repo validate`.

### Add Template Patches

Templates that are built into openapi-generator are used to generate API clients. Sometimes it's necessary to modify these templates. To achieve that, you can include `template-patches` directory in yout repository with patches that get applied to the upstream templates. You can create such patches by doing changes in a checked out openapi-generator repo:

```
git clone git@github.com:OpenAPITools/openapi-generator.git
cd openapi-generator
# do changes in modules/openapi-generator/src/main/resources/<language>
git diff --relative=modules/openapi-generator/src/main/resources/
```

### Add Downstream Templates

Sometimes you may need to add our own templates that need to be rendered in a completely different context and have different usage than those provided in openapi-generator upstream. These can be added to the `downstream-templates/<language>` directory, Currently this is only used to add files that are top-level for each of the generated repositories, as the openapi-generator is used to render only per-major-version subdirectories with the actual code.

Note that downstream templates are rendered after the code generation is done; they must not overwrite any files written by previous code generation.

### Prepare Templates

Templates need to be prepared before first code generation and then every time template patches are added/changed/deleted.

Preparation of templates takes a base (IOW templates taken from openapi-generator) and downstream patches from `template-patches` directory.

The base for the templates can be taken from an openapi-generator jar file, from local directory or from an openapi-generator checkout at a specific commit. See `apigentools templates --help` for all options and their description.

#### Locally

Run e.g. `apigentools -b path/to/spec/repo templates local-dir /path/to/base/templates`

#### Docker

Run e.g. `container-apigentools apigentools:local --spec-repo-volume /absolute/path/to/spec/repo templates openapi-git v4.0.2`.

### Generate Client Code

To generate actual client code, you need templates prepared (see the above step).

#### Locally

Run `apigentools -b path/to/spec/repo generate`

#### Docker

Run `container-apigentools apigentools:local --spec-repo-volume /absolute/path/to/spec/repo generate`.

### Run Tests

openapi-generator pre-creates unittest files for most of the languages supported. The tests themselves need to be implemented by hand, but apigentools still allows running them as a part of the process. The `apigentools test` command will look for `Dockerfile.test.{major_api_version}` file in the *top level directory* of the generated repo (*not* in the subdirectory with code for that specific major API version). If such a file is found, it is built and then executed without arguments.

#### Locally

Run `apigentools -b path/to/spec/repo test`

#### Docker

Run `container-apigentools apigentools:local --spec-repo-volume /absolute/path/to/spec/repo test`.

### Running the Whole Workflow

Note that all the above commands can be run in sequence with Docker in just one command by passing no additional arguments:

Run `container-apigentools apigentools:local --spec-repo-volume /absolute/path/to/spec/repo`.

## File Formats

### config/config.json

Example:

```
{
    "codegen_exec": "openapi-generator",
    "languages": {
        "java": {
            "github_org_name": "my-github-org",
            "github_repo_name": "my-java-client",
            "spec_versions": ["v1"],
            "version_path_template": "myapi_{{spec_version}}"
        }
    },
    "server_base_urls": {
        "v1": "https://api.myserver.com/v1"
    },
    "spec_sections": {
        "v1": ["accounts.yaml"]
    },
    "spec_versions": ["v1"]
}
```

The structure of the general config file is as follows (starting with top-level keys):

* `codegen_exec` - name of the executable of the code generating tool
* `languages` - settings for individual languages, contains a mapping of language names to their settings
  * individual language settings:
    * `commands` - commands to execute before/after code generation; commands are executed in two *phases* - `pre` (executed before code generation) or `post` (executed after code generation); note that each command is run once for each of the langauge's `spec_versions` and inside the directory with code for that spec version
       * *phase* commands - each phase can contain a list of commands to be executed; each command is represented as a map:
         * `description` - a description of the command
         * `commandline` - the command itself, the items in the list are strings and potentially *functions* that represent callbacks to the Python code; each function is represented as a map:
            * `function` - name of the function (see below for list of recognized functions)
            * `args` - list of args to pass to the function in Python code (as in `*args`)
            * `kwargs` - mapping of args to pass to the function in Python code (as in `**kwargs`)
            * result of the *function* call is then used in the actual commandline call
    * `command_env` - additional environment values with which both commands from `commands` and code generation itself will be executed (mapping of environment variable names to their values)
    * `github_org_name` - name of the Github organization of the client for this language
    * `github_repo_name` - name of the Github repository of the client for this language
    * `spec_versions` - list of spec versions to generate client modules for, has to be subset of top-level `spec_versions`
    * `upstream_templates_dir` - name of the directory in openapi-generator that holds templates for this language; this is optional and by default the name of the language is used
    * `version_path_template` - Mustache template for the name of the subdirectory in the Github repo where code for individual major versions of the API will end up, e.g. with `myapi_{{spec_version}}` as value and `github_repo_name` of value `my-java-client`, the code for `v1` of the API will end up in `myapi-java-client/myapi_v1`
* `server_base_urls` - mapping of major spec versions (these have to be in `spec_versions`) to URLs of servers that provide them
* `spec_sections` - mapping of major spec versions (these have to be in `spec_versions`) to lists of files with paths/tags/components definitions to merge when creating full spec (files not explicitly listed here will be ignored)
* `spec_versions` - list of major versions currently known and operated on (these have to be subdirectories of `spec` directory)

#### Functions in Language Phase Commands

This section lists currently recognized functions for language phase commands as described in the section above:

* `glob` - runs Python's `glob.glob`
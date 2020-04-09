#  apigentools

!!! note
    This is documentation for apigentools major version 1, which has significant differences from the 0.X series. Refer to [upgrading docs](upgrading.md) for further details.

## Purpose

The purpose of the apigentools package is to provide an easy way to generate API clients from an [OpenAPI v3 specification](https://github.com/OAI/OpenAPI-Specification/) for multiple languages using [openapi-generator](https://github.com/OpenAPITools/openapi-generator) or other tools that work with the OpenAPI Specification.

*Note on "downstream/upstream" nomenclature*: Throughout the code and documentation of this project, the words "*downstream*" and "*upstream*" are used when talking about certain pieces of functionality and/or templates. In this context, "*upstream*" is used to reference functionality/templates coming from openapi-generator or other external tools used; "*downstream*" is used to reference configuration and modifications that you will be providing as inputs to apigentools.

## Quickstart

*Note*: This quickstart opts for the easiest approach possible. To access advanced features of apigentools, refer to the rest of this documentation.

### Installation

Install apigentools with

```
pip install apigentools
```

You will also need a [docker](https://www.docker.com/) environment available locally.

### Setup Spec Repo

A [spec repo](spec_repo.md) is a repository that holds the [OpenAPI spec](https://www.openapis.org/) of your API, configuration for both apigentools and [openapi-generator](https://github.com/OpenAPITools/openapi-generator) (or a different code generator of your choice), and some optional additional files, such as [downstream templates](workflow.md#add-downstream-templates) and [template patches](workflow.md#add-template-patches). Apigentools work with this repo to perform various tasks, such as validating your spec or generating client code. To get set up, run:

```
apigentools init myspecrepo
cd myspecrepo
```

This creates an apigentools supported directory, `myspecrepo`, where you can start defining your API spec.

### Writing the OpenAPI Specification

One of the apigentools core ideas is being able to generate clients that can access multiple major versions of your API (e.g. `v1`, `v2`, ...). This means it also expects you to have a separate spec for each of the major versions. The `init` command, by default, generates a directory structure holding `spec/v1` directories for `v1` of your API.

Since OpenAPI specification files can grow very large, apigentools allow you to split them into multiple "sections". Initially, only two files are created. These are also files that are expected to exist for each major version of your API:

* `spec/v1/header.yaml` - A header file that should only contain the OpenAPI keys `openapi`, `info`, `externalDocs` and `servers`.
* `spec/v1/shared.yaml` - A file containing any OpenAPI objects that are referenced from more than one "section"—`components` (which includes `schemas` and `security_schemes`), `security`, and `tags`.

Add a file `spec/v1/users.yaml` with the following content:

```
paths:
  /api/v1/users:
    get:
      description: Get all registered users
      summary: Get all users
      operationId: GetAllUsers
      responses:
        '200':
          description: OK
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Users'
        '400':
          description: Bad Request
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error400'
components:
  schemas:
    Users:
      type: object
      properties:
        users:
          type: array
          items:
            $ref: '#/components/schemas/User'
    User:
      type: object
      properties:
        name:
          type: string
        email:
          type: string
          format: email
```

Note that you didn't add the `Error400` entity in the file. Assume that this would be a generic error response returned by all API endpoints and put it in the `spec/v1/shared.yaml` file:

```yaml
components:
  callbacks: {}
  examples: {}
  headers: {}
  links: {}
  parameters: {}
  requestBodies: {}
  responses: {}
  schemas:
    Error400:
      type: object
      properties:
        errors:
          type: array
          items:
            type: string
  securitySchemes: {}
security: []
tags: []
```

Now you just need to add the `users.yaml` spec section to `config/config.yaml`. Add it to `spec_sections.v1` like this:

```
container_opts:
  image: datadog/apigentools:latest
languages: {}
spec_sections:
  v1: ["header.yaml", "shared.yaml", "users.yaml"]
spec_versions:
- v1
```

Now that you have a complete spec with a single API endpoint and all schemas defined for it, you can start using apigentools to process it.

### Add a Language Configuration

Configure apigentools to actually generate code for one language. Try doing this for Go. First, add it to `config/config.yaml`:

```
container_opts:
  image: datadog/apigentools:latest
languages:
  go:
    generation:
      default:
        commands:
          - commandline:
            - function: openapi_generator_generate
            description: Generate code using openapi-generator
    github_repo_name: my-api-client-go
    github_org_name: myorg
    library_version: "0.0.1"
    spec_versions: ["v1"]
    version_path_template: "myapi_{{spec_version}}"
spec_sections:
  v1: ["header.yaml", "shared.yaml", "users.yaml"]
spec_versions:
- v1
```

This will make sure that Go client will be generated with the following aspects:

* It will be generated inside `generated/my-api-client-go` directory.
* Only the `v1` client will be generated. If you ever add another version of this API, you'll need to also explicitly add it to its `spec_versions`.
* The code for `v1` of the API will reside under `generated/my-api-client-go/myapi_v1`. See [config.yaml format](spec_repo.md#configconfigyaml) for information on how the `version_path_template` works.
* Thanks to using the `generation.default` section, all of your major API versions will use the same process for generating their code. You can override this behaviour later on per major API version if you wish.
* The command uses a [builtin function](spec_repo.md#functions-in-commands) that expands to the proper command using openapi-generator to generate your code.

Next, add an openapi-generator configuration file for Go, called `config/languages/go_v1.json`:

```
{
    "gitUserId": "myorg",
    "gitRepoId": "my-api-client-go",
    "isGoSubmodule": true,
    "packageName": "myapi_v1",
    "packageVersion": "0.0.1",
    "withGoCodegenComment": true
}
```

You're finished configuring apigentools, and you can now start generating code!

### Generating Client Code

To generate client code using the configuration you've created, run:

```
apigentools generate
```

Note that by default, openapi generator will be invoked to generate code, using its builtin templates. See [config.yaml format](spec_repo.md#configconfigyaml) for information on how to change this behaviour.

If using non-builtin templates and/or [template patches](workflow.md#add-template-patches), apigentools preprocesses the templates and runs the code generation as part of `apigentools generate`.

You can now browse the generated code under `generated/my-api-client-go/myapi_v1`. Note that if you want to make this a proper Go module with per-major-API-version submodules, you need to also add top-level `go.mod` and `go.sum` files.

Also note that not all language templates included in openapi-generator are compatible with apigentools' per-major-API-version submodules approach. If you find a language for which this is not possible, consider contributing this as a feature to openapi-generator to make the project better for everyone!

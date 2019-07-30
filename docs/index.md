#  apigentools

## Purpose

The purpose of the apigentools package is providing an easy way to generate API clients from [OpenAPI v3 specification](https://github.com/OAI/OpenAPI-Specification/) for multiple languages using [openapi-generator](https://github.com/OpenAPITools/openapi-generator).

*Note on "downstream/upstream" nomenclature*: Throughout the code and documentation of this project, the words "*downstream*" and "*upstream*" are used when talking about certain pieces of functionality and/or templates. In this context, "*upstream*" is used to reference functionality/templates coming from openapi-generator or other external tools used; "*downstream*" is used to reference configuration and modifications that you will be providing as inputs to apigentools.

## Quickstart

*Note*: For purposes of this quickstart, we'll choose the easiest approach possible. To access advanced features of apigentools, refer to the rest of this documentation.

### Installation

Install apigentools with

```
pip install apigentools
```

### Setup Spec Repo

[Spec Repo](spec_repo.md) is a repository that holds the [OpenAPI spec](https://www.openapis.org/) of your API, configuration for both apigentools and [openapi-generator](https://github.com/OpenAPITools/openapi-generator) as well as some additional files, such as [downstream templates](workflow.md#add-downstream-templates) and [template patches](workflow.md#add-template-patches). Apigentools work with this repo to perform various tasks such as validating your spec or generating client code. To get set up, run:

```
apigentools init myspecrepo
cd myspecrepo
```

This will create a `myspecrepo` directory with a directory structure inside that apigentools expect.

### Writing the OpenAPI Specification

One of the apigentools core ideas is being able to generate clients that can access multiple major versions of your API (e.g. `v1`, `v2`, ...). This means it also expects you to have a separate spec for each of the major versions. The `init` command by default generates a directory structure holding `spec/v1` directories for `v1` of your API.

Since OpenAPI specification files can grow very large, apigentools allow you to split them into multiple "sections". Initially, only two files are created. These are also files that are expected to exist for each major version of your API:

* `spec/v1/header.yaml` - A header file that should only contain OpenAPI keys `openapi`, `info`, `externalDocs` (note that `servers` is filled in dynamically by apigentools based on your `config/config.yaml`).
* `spec/v1/shared.yaml` - A file containing any OpenAPI objects that are referenced from more than one "section" - `components` (which includes `schemas` and `security_schemes`), `security` and `tags`.

Let's add a file `spec/v1/users.yaml` with the following content:

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

Note that we didn't add the `Error400` entity in the file. We're assuming that this would be a generic error response returned by all API endpoints, so we'll put it in the `spec/v1/shared.yaml` file:

```
components:
  securitySchemes: {}
  schemas:
    Error400:
      type: object
      properties:
        errors:
          type: array
          items:
            type: string
tags: []
security: []
```

Now you just need to add the `users.yaml` spec section to `config/config.json`. Add it to `spec_sections.v1` like this:

```
{
    "codegen_exec": "openapi-generator",
    "languages": {},
    "server_base_urls": {
        "v1": "https://api.myserver.com/v1"
    },
    "spec_sections": {
        "v1": ["users.yaml"]
    },
    "spec_versions": [
        "v1"
    ]
}
```

Now we have a complete spec with a single API endpoint and all schemas defined for it, so we can start using apigentools to process it.

### Validating the OpenAPI Spec

Run:

```
apigentools validate
```

if you did everything right, the command will exit successfully. If not, it should print a meaningful error message telling you where the problem is. It will also create a `spec/v1/full_spec.yaml`, which is a single file containing the whole OpenAPI spec definition of your API.

### Add a Language Configuration

Now we want to configure apigentools to actually generate code for one language. Let's try doing this for Go. First, let's add it to `config/config.json`:

```
{
    "codegen_exec": "openapi-generator",
    "languages": {
        "go": {
            "github_repo_name": "my-api-client-go",
            "github_org_name": "myorg",
            "spec_versions": ["v1"],
            "version_path_template": "myapi_{{spec_version}}"
        }
    },
    "server_base_urls": {
        "v1": "https://api.myserver.com/v1"
    },
    "spec_sections": {
        "v1": ["users.yaml"]
    },
    "spec_versions": [
        "v1"
    ]
}
```

This will make sure that Go client will be generated with the following aspects:

* It will be generated inside `generated/my-api-client-go` directory.
* Only `v1` client will be generated. If you ever add another version of API, you'll need to also explicitly add it to its `spec_versions`.
* The code for `v1` of the API will reside under `generated/my-api-client-go/myapi_v1` (see [config.json format](file_formats.md#configconfigjson) for information on how the `version_path_template` works).

Next, we need to add openapi-generator configuration file for Python, called `config/languages/go_v1.json`:

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

We're finished configuring apigentools and we can start generating code now!

### Generating Client Code

To generate client code using the configuration we've created, run:

```
apigentools generate --builtin-templates
```

Note that we're using the `--builtin-templates` argument here to tell apigentools to use templates that are built in to openapi-generator. By default, apigentools expects you to pregenerate the templates using the [templates command](cli.md#apigentools-templates) - but you really only need to do this when you need to change openapi-generator included templates.

You can now browse the generated code under `generated/my-api-client-go/myapi_v1`. Note that if we wanted to make this a proper go module with per-major-API-version submodules, we'd need to also add top-level `go.mod` and `go.sum` that would be placed in `generated/my-api-client-go`. If you want to continue working on this example, see [downstream templates](workflow.md#add-downstream-templates) documentation for instructions on how to do that.

Also note that not all language templates included in openapi-generator are compatible with apigentools' per-major-API-version submodules approach. This is something that we (authors of apigentools) will continue working on together with openapi-generator authors.
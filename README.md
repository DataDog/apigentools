#  apigentools - Generate API Clients with Ease

![Build status](https://travis-ci.com/DataDog/apigentools.svg?branch=master)

## Purpose

The purpose of the apigentools package is providing an easy way to generate API clients from [OpenAPI v3 specification](https://github.com/OAI/OpenAPI-Specification/) for multiple languages using [openapi-generator](https://github.com/OpenAPITools/openapi-generator).

## Key Concepts

* Definition of structure of [Spec Repo](https://apigentools.readthedocs.io/en/latest/spec_repo/) - A repository with all the configuration for apigentools and openapi-generator as well as the actual OpenAPI spec of your API
* [Reproducible](https://apigentools.readthedocs.io/en/latest/reproducible/) code generation
* A recommended [workflow](https://apigentools.readthedocs.io/en/latest/workflow/)
* Ability to [patch openapi-generator templates](https://apigentools.readthedocs.io/en/latest/workflow/#add-template-patches) as well as [add your own templates](https://apigentools.readthedocs.io/en/latest/workflow/#add-downstream-templates)

## Get It

* Documentation: https://apigentools.readthedocs.io
* Install from PyPI: `pip install apigentools`
* Run it in Docker container: `docker run apigentools/apigentools:latest`

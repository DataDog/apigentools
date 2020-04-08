# Upgrading

## From 0.X Series to 1.X Series

Apigentools major version 1 is somewhat different from the 0.X series. It reflects the experience obtained by the apigentools developers through several months of using apigentools 0.X.

### Design Challenges

Before apigentools 1.X release, there were two ways to run apigentools - in container or outside of a container. While this allowed for reproducibility by pinning the container tag/sha, it had its own problems:

* It didn't allow for detaching of openapi-generator version used from apigentools version used when using containerized version.
* It didn't allow for (easily) using different versions of openapi-generator to generate different libraries/major spec versions for libraries.
* It didn't allow for using different code generating tools, such as [restful-react](https://github.com/contiamo/restful-react).
* It required building and maintaining custom image to achieve any of the above. The alternative was using a local environment that would be hard to reproduce among developers of a single Spec Repo.
* It posed problems with passphrase protected SSH keys and handling them inside used container.
* And more...

Apigentools 1.X takes a different approach described in sections below.

### Containerized Commands

Apigentools 1.X code is expected to run outside of container, while executed subprocesses (which are considered to be environment specific) run in containers.

### openapi-generator No Longer Built In 

openapi-generator, while still the default code generation tool, is not required. A [different code generation](spec_repo.md#commands) tool might be used by providing a custom command.

### Overriding Container Options for Commands

Each [command](spec_repo.md#commands) is executed in an individual container and can use a different environment for the container, including specification of individual image. This is achieved through the [container_opts](spec_repo.md#container_opts) argument that can be specified on multiple levels of the configuration and implements simple inheritance.

### Detaching Code Generation Process of Major API Versions for Languages

The new [config file syntax](spec_repo.md#configconfigyaml) allows specifying different ways to generate code for different major API versions for a single language, including usage of different pre/post commands, different generation command, different [template patches](spec_repo.md#template-patches).

### Spec Repo structure

The [Spec Repo](spec_repo.md) structure now has less assumptions. [Downstream templates](spec_repo.md#downstream-templates) and [template patches](spec_repo.md#template-patches) can be placed in arbitrary places inside the Spec Repo.

### Template Preprocessing

[Template preprocessing](spec_repo.md#preprocess-templates) is now configured in the configuration file, including specifying the templates source, list of template patches (and their order, which is implied by their position in the list).

### Tests

Apigentools no longer automatically searches for Dockerfiles to build and run tests in. There is now a `tests` section in the [configuration file](spec_repo.md#configconfigyaml) where you can define a list of commands that constitute tests.

### New Configuration File Syntax

The [configuration file](spec_repo.md#configconfigyaml) now uses Yaml as a markup language. It's been overhauled to support the above usecases, but should look very familiar to existing apigentools users.

### Default Spec Sections

Apigentools 1.X code doesn't have any special treatment for `spec/<version>/header.yaml` and `spec/<version>/shared.yaml` files. While they are stil recommended for `openapi`/`info`/`servers`/... resp. shared components, they have to be explicitly listed in `spec_sections`.
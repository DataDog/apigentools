# Reproducibility

One of the core concepts of apigentools is reproducible code generation. In order to allow for debugging the generated client code and tracking how exactly it was generated, apigentools provides two special features:

* A file called `.apigentools-info` gets written into the top-level directory of each language client. For example:

        {
            "additional_stamps": [],
            "apigentools_version": "0.1.0.dev1",
            "codegen_version": "4.0.1",
            "image": "apigentools:local",
            "info_version": "1"
            "spec_repo_commit": "36cefa8",
        }

    * `additional_stamps` is a list of strings given through the `--additional-stamp` argument (empty if none are given)
        * As an example, you might want to use additional stamps when using a post-processing tool (such as a `post` command in [config/config.json](spec_repo.md#configconfigjson)) on the generated code, which makes actual changes to the code. For example, if you decided to use [black](https://black.readthedocs.io/en/stable/) on generated Python code, you could specify `--additional-stamp black=1.2.3` to record its version.
    * `apigentools_version` is the version of apigentools used to generate code
    * `codegen_version` is the version of the used code generation tool (openapi-generator)
    * `image` is a name and tag of the Docker image in which code generation happened (`null` if outside of Docker image)
    * `info_version` is the format version of this document
    * `spec_repo_commit` is a commit of the spec repo (`null` if it's not a git repository)

* All the templates rendered with openapi-generator get an additional key in context, `apigentoolsStamp`, which contains the same set of information as `.apigentools-info` in a condensed form, for example: `Generated with: apigentools version 0.1.0.dev1 (image: apigentools:local); spec repo commit 36cefa8; codegen version 4.0.1`. You can use this in your template patches and/or downstream templates as `{{apigentoolsStamp}}` tag.
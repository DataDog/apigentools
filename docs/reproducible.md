# Reproducibility

!!! note
    This is documentation for apigentools major version 1, which has significant differences from the 0.X series. Refer to [upgrading docs](upgrading.md) for further details.

One of the core concepts of apigentools is reproducible code generation. In order to allow for debugging the generated client code and tracking how exactly it was generated, apigentools provides two special features:

* A file called `.apigentools-info` gets written into the top-level directory of each language client. For example:

        {
            "additional_stamps": [],
            "info_version": "2",
            "spec_versions": {
                "v2": {
                    "apigentools_version": "1.0.0",
                    "regenerated": "2020-04-05 19:54:29.870015",
                    "spec_repo_commit": "70c45c5"
                },
                "v1": {
                    "apigentools_version": "1.0.0",
                    "regenerated": "2020-04-05 19:54:19.287951",
                    "spec_repo_commit": "70c45c5"
                }
            }
        }

    * `additional_stamps` is a list of strings given through the `--additional-stamp` argument (empty if none are given)
    * `info_version` is the format version of this document
    * `spec_versions` is an object containing more detailed information about code generation run for specific major API versions:
        * `apigentools_version` is the version of apigentools used to generate code
        * `regenerated` is the datetime of code generation of code for this major API version
        * `spec_repo_commit` is a commit of the spec repo (`null` if it's not a git repository)

* All the templates rendered with openapi-generator get an additional key in context, `apigentoolsStamp`, which contains the same set of information as `.apigentools-info` in a condensed form, for example: `Generated with: apigentools version 1.0.0; spec repo commit abcd123;`. You can use this in your template patches and/or downstream templates as `{{apigentoolsStamp}}` tag.

If you need to ensure reproducibility, we recommend pinning versions of all used container images in your `config/config.yaml`. This will ensure that you can reconstruct your code generation environment from looking at `spec_repo_commit`.
# Examples

This directory contains two subdirectories - `good` and `bad`. While all of these are used in integration tests, you can also use the `good` examples as real life samples to C&P to kickstart work on your Spec Repo.

* `good` examples:
  * `openapi-generator-java` - An example that validates the input spec and generates code with `openapi-generator`. The `jersey2` library is used as client library.
* `bad` examples:
  * `openapi-generator-java-fail-validate` - example that fails `apigentools validate`
  * `openapi-generator-java-fail-templates` - example that passes `apigentools validate`, but fails `apigentools templates`
  * `openapi-generator-java-fail-generate` - example that passes `apigentools validate` and `apigentools templates`, but fails `apigentools generate`

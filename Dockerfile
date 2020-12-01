# https://github.com/OpenAPITools/openapi-generator/commit/64ade2ce8f4ff0ce3c970d5a09a9ca48379d8887
FROM openapitools/openapi-generator@sha256:a08f5b6bd2998738398526c21249b0bfe8b620e07bb95def37d5fde71e8c1758 AS jar
# Ensure the jar file is build
RUN /usr/local/bin/docker-entrypoint.sh version

FROM fedora:30

ENV OPENAPI_GENERATOR_VERSION=5.0.0-SNAPSHOT \
    PACKAGES="docker findutils git golang-googlecode-tools-goimports java jq maven nodejs patch python3 python3-pip unzip"

RUN dnf install -y gcc-c++ make && \
    curl -sL https://rpm.nodesource.com/setup_12.x | bash - && \
    dnf install -y ${PACKAGES} && \
    dnf clean all && \
    curl https://raw.githubusercontent.com/OpenAPITools/openapi-generator/master/bin/utils/openapi-generator-cli.sh > /usr/bin/openapi-generator && \
    chmod +x /usr/bin/openapi-generator

# for manipulating html docs
RUN pip3 install beautifulsoup4

COPY --from=jar /opt/openapi-generator/modules/openapi-generator-cli/target/openapi-generator-cli.jar /usr/bin/openapi-generator-cli-${OPENAPI_GENERATOR_VERSION}.jar
# make an unversioned JAR for "templates" command
COPY --from=jar /opt/openapi-generator/modules/openapi-generator-cli/target/openapi-generator-cli.jar /usr/bin/openapi-generator-cli.jar

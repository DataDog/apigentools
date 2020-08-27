# https://github.com/OpenAPITools/openapi-generator/commit/b4edfe477a300558624c235f8b5b83f1bc8a02ae
FROM openapitools/openapi-generator-cli@sha256:10fdbf4fc389576306f46c213504168b700d26ed6a041d7571d43e0651a220e5 AS jar
# Ensure the jar file is build
RUN /usr/local/bin/docker-entrypoint.sh version

FROM fedora:30

ENV OPENAPI_GENERATOR_VERSION=4.3.1-SNAPSHOT \
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

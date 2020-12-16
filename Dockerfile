# https://github.com/OpenAPITools/openapi-generator/commit/afa750f2491337e6d95c0a39085ad75246fb4889
FROM openapitools/openapi-generator@sha256:0970a33b5c6e70f9dab387d261318055b9e9c7a741ae6427c0f6be59d959706c AS jar
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

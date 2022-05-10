# https://github.com/OpenAPITools/openapi-generator/commit/21c399f2b88e2ba824648d749025880ed5359cd3
FROM openapitools/openapi-generator-cli@sha256:bda9ca9b2d4ad50a41e1b2cdfbb84d7c21ce0e4d9e9b0061718315d9a7321443 AS jar
# Ensure the jar file is build
RUN /usr/local/bin/docker-entrypoint.sh version

FROM fedora:35

ENV OPENAPI_GENERATOR_VERSION=5.0.0-SNAPSHOT \
    PACKAGES="docker findutils git golang-x-tools-goimports java jq maven nodejs patch python3 python3-pip unzip"

RUN dnf install -y gcc-c++ make && \
    curl -sL https://rpm.nodesource.com/setup_16.x | bash - && \
    dnf install -y ${PACKAGES} && \
    dnf clean all && \
    curl https://raw.githubusercontent.com/OpenAPITools/openapi-generator/master/bin/utils/openapi-generator-cli.sh > /usr/bin/openapi-generator && \
    chmod +x /usr/bin/openapi-generator

# for manipulating html docs
RUN pip3 install beautifulsoup4

COPY --from=jar /opt/openapi-generator/modules/openapi-generator-cli/target/openapi-generator-cli.jar /usr/bin/openapi-generator-cli-${OPENAPI_GENERATOR_VERSION}.jar
# make an unversioned JAR for "templates" command
COPY --from=jar /opt/openapi-generator/modules/openapi-generator-cli/target/openapi-generator-cli.jar /usr/bin/openapi-generator-cli.jar

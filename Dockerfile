# Built from upstream commit 928d065bbfc8e3bb620934c6c6a6d8540cce1974
# contains PR https://github.com/OpenAPITools/openapi-generator/pull/5414 that fixes Go nullables
FROM openapitools/openapi-generator@sha256:121e3a56be10156fff90eb9875f0d35513dbe7dc081085cbd45cd3e936d990f1 AS jar
# Ensure the jar file is build
RUN /usr/local/bin/docker-entrypoint.sh version

FROM fedora:30

ENV APIGENTOOLS_BASE_DIR=/var/lib/apigentools

# _APIGENTOOLS_GIT_HASH_FILE is only for internal use, which is why it's prefixed with "_"
ENV APIGENTOOLS_SPEC_REPO_DIR=${APIGENTOOLS_BASE_DIR}/spec-repo \
    APIGENTOOLS_TEMPLATES_SOURCE=openapi-jar \
    _APIGENTOOLS_GIT_HASH_FILE=${APIGENTOOLS_BASE_DIR}/git-hash

ENV OPENAPI_GENERATOR_VERSION=4.2.3-SNAPSHOT \
    PACKAGES="docker findutils git golang-googlecode-tools-goimports java jq maven nodejs patch python3 python3-pip unzip"

VOLUME ${APIGENTOOLS_SPEC_REPO_DIR}

ENTRYPOINT ["/usr/bin/docker-entrypoint.sh"]

RUN mkdir -p ${APIGENTOOLS_SPEC_REPO_DIR}

RUN dnf install -y gcc-c++ make && \
    curl -sL https://rpm.nodesource.com/setup_12.x | bash - && \
    dnf install -y ${PACKAGES} && \
    dnf clean all && \
    curl https://raw.githubusercontent.com/OpenAPITools/openapi-generator/master/bin/utils/openapi-generator-cli.sh > /usr/bin/openapi-generator && \
    chmod +x /usr/bin/openapi-generator

COPY --from=jar /opt/openapi-generator/modules/openapi-generator-cli/target/openapi-generator-cli.jar /usr/bin/openapi-generator-cli-${OPENAPI_GENERATOR_VERSION}.jar

ENV APIGENTOOLS_OPENAPI_JAR "/usr/bin/openapi-generator-cli-${OPENAPI_GENERATOR_VERSION}.jar"

COPY docker-entrypoint.sh /usr/bin/
COPY . /tmp/apigentools

ARG APIGENTOOLS_SOURCE=/tmp/apigentools
RUN pip3 install --prefix /usr ${APIGENTOOLS_SOURCE}

ARG APIGENTOOLS_COMMIT=""
RUN echo ${APIGENTOOLS_COMMIT} > ${_APIGENTOOLS_GIT_HASH_FILE}

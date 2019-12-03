FROM fedora:30

ENV APIGENTOOLS_BASE_DIR=/var/lib/apigentools

# _APIGENTOOLS_GIT_HASH_FILE is only for internal use, which is why it's prefixed with "_"
ENV APIGENTOOLS_SPEC_REPO_DIR=${APIGENTOOLS_BASE_DIR}/spec-repo \
    _APIGENTOOLS_GIT_HASH_FILE=${APIGENTOOLS_BASE_DIR}/git-hash

ENV OPENAPI_GENERATOR_VERSION=4.2.2 \
    PACKAGES="docker findutils git golang-googlecode-tools-goimports java npm patch python3 python3-pip unzip"

VOLUME ${APIGENTOOLS_SPEC_REPO_DIR}

ENTRYPOINT ["/usr/bin/docker-entrypoint.sh"]

RUN mkdir -p ${APIGENTOOLS_SPEC_REPO_DIR}

RUN dnf install -y ${PACKAGES} && \
    dnf clean all && \
    npm install @openapitools/openapi-generator-cli@cli-${OPENAPI_GENERATOR_VERSION} -g

ENV APIGENTOOLS_OPENAPI_JAR "/usr/lib/node_modules/@openapitools/openapi-generator-cli/bin/openapi-generator.jar"

COPY docker-entrypoint.sh /usr/bin/
COPY . /tmp/apigentools

ARG APIGENTOOLS_SOURCE=/tmp/apigentools
RUN pip3 install --prefix /usr ${APIGENTOOLS_SOURCE}

ARG APIGENTOOLS_COMMIT=""
RUN echo ${APIGENTOOLS_COMMIT} > ${_APIGENTOOLS_GIT_HASH_FILE}

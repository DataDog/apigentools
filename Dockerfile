FROM fedora:30

ENV APIGENTOOLS_SPEC_REPO_DIR=/var/lib/apigentools/spec-repo

ENV OPENAPI_GENERATOR_VERSION=4.0.2 \
    PACKAGES="docker findutils git golang-googlecode-tools-goimports java npm patch python3 python3-pip unzip"

VOLUME ${APIGENTOOLS_SPEC_REPO_DIR}

ENTRYPOINT ["/usr/bin/docker-entrypoint.sh"]

RUN mkdir -p ${APIGENTOOLS_SPEC_REPO_DIR}

RUN dnf install -y ${PACKAGES} && \
    dnf clean all && \
    npm install @openapitools/openapi-generator-cli@cli-${OPENAPI_GENERATOR_VERSION} -g

COPY docker-entrypoint.sh /usr/bin/
COPY . /tmp/apigentools

ARG APIGENTOOLS_SOURCE=/tmp/apigentools
RUN pip3 install --prefix /usr ${APIGENTOOLS_SOURCE}

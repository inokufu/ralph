# -- Base image --
FROM python:3.12.8-slim AS base

# Set pip specific var env to reduce docker image size
ENV PIP_NO_CACHE_DIR=1 PYTHONDONTWRITEBYTECODE=1

# Upgrade pip to its latest release to speed up dependencies installation and install uv
RUN pip install --upgrade pip && pip install uv 

# set venv environment variables
ENV UV_PROJECT_ENVIRONMENT=/venv
ENV PATH="$UV_PROJECT_ENVIRONMENT/bin:$PATH"

# Upgrade system packages to install security updates
RUN apt-get update && \
    apt-get -y upgrade && \
    rm -rf /var/lib/apt/lists/*


# -- Builder --
FROM base AS builder

WORKDIR /build

COPY . /build/

RUN apt-get update && \
    apt-get install -y \
        build-essential \
        gcc \
        libc6-dev \
        libffi-dev && \
    rm -rf /var/lib/apt/lists/*


# -- Core --
FROM base AS core

RUN apt-get update && \
    apt-get install -y \
        curl \
        jq \
        wget && \
    rm -rf /var/lib/apt/lists/*

COPY --from=builder /usr/local /usr/local

WORKDIR /app


# -- Development --
FROM core AS development

# Copy all sources, not only runtime-required files
COPY . /app/

# Only the M1 Mac images need these packages installed
ARG TARGETPLATFORM
RUN if [ "$TARGETPLATFORM" = "linux/arm64" ]; \
    then apt-get update && \
        apt-get install -y \
            build-essential \
            gcc && \
        rm -rf /var/lib/apt/lists/*; \
    fi;

# Install git for documentation deployment
RUN apt-get update && \
    apt-get install -y \
        git && \
    rm -rf /var/lib/apt/lists/*;

# Install dependencies and project as editable
RUN uv sync --extra full --extra dev --frozen

# Un-privileged user running the application
ARG DOCKER_USER=1000
USER ${DOCKER_USER}


# -- Production --
FROM core AS production

# Install dependencies and project as not editable
RUN uv sync --extra full --no-editable --frozen

# Un-privileged user running the application
ARG DOCKER_USER=1000
USER ${DOCKER_USER}

CMD ["ralph"]

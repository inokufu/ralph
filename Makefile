# -- General
SHELL := /bin/bash

# -- Docker
# Get the current user ID to use for docker run and docker exec commands
DOCKER_UID           = $(shell id -u)
DOCKER_GID           = $(shell id -g)
DOCKER_USER          = $(DOCKER_UID):$(DOCKER_GID)
COMPOSE              = DOCKER_USER=$(DOCKER_USER) docker compose
COMPOSE_RUN          = $(COMPOSE) run --rm
COMPOSE_TEST_RUN     = $(COMPOSE_RUN)
COMPOSE_TEST_RUN_APP = $(COMPOSE_TEST_RUN) app
COMPOSE_EXEC         = $(COMPOSE) exec
COMPOSE_EXEC_APP     = $(COMPOSE) exec app


# -- Documentation
MKDOCS               = $(COMPOSE_RUN) --no-deps --publish "8000:8000" app mkdocs

# -- Elasticsearch
ES_PROTOCOL = http
ES_HOST     = localhost
ES_PORT     = 9200
ES_INDEX    = statements
ES_URL      = $(ES_PROTOCOL)://$(ES_HOST):$(ES_PORT)

# -- RALPH
RALPH_IMAGE_NAME         ?= ralph
RALPH_IMAGE_TAG          ?= development
RALPH_IMAGE_BUILD_TARGET ?= development
RALPH_LRS_AUTH_USER_NAME  = ralph
RALPH_LRS_AUTH_USER_PWD   = secret
RALPH_LRS_AUTH_USER_SCOPE = all
RALPH_LRS_AUTH_USER_AGENT_MBOX = mailto:ralph@example.com

# ==============================================================================
# RULES

default: help

.env:
	cp .env.dist .env

.ralph/auth.json:
	@$(COMPOSE_RUN) app ralph \
		auth \
		-u $(RALPH_LRS_AUTH_USER_NAME) \
		-p $(RALPH_LRS_AUTH_USER_PWD) \
		-s $(RALPH_LRS_AUTH_USER_SCOPE) \
		-M $(RALPH_LRS_AUTH_USER_AGENT_MBOX) \
		-w


# -- Docker/compose
bootstrap: ## bootstrap the project for development
bootstrap: \
  .env \
  build \
  .ralph/auth.json \
  es-index
.PHONY: bootstrap

build: ## build the app container
build: .env
	RALPH_IMAGE_BUILD_TARGET=$(RALPH_IMAGE_BUILD_TARGET) \
	RALPH_IMAGE_NAME=$(RALPH_IMAGE_NAME) \
	RALPH_IMAGE_TAG=$(RALPH_IMAGE_TAG) \
	  $(COMPOSE) build app
.PHONY: build

docs-build: ## build documentation site
	@$(MKDOCS) build
.PHONY: docs-build

docs-serve: ## run mkdocs live server for dev docs
	@$(MKDOCS) serve --dev-addr 0.0.0.0:8000
.PHONY: docs-serve

docs-serve-pages: ## run mike live server for versioned docs
	@$(MIKE) serve --dev-addr 0.0.0.0:8001
.PHONY: docs-serve-pages

down: ## stop and remove backend containers
	@$(COMPOSE) down
.PHONY: down

es-index: ## create elasticsearch index
es-index: run-es
	@echo "Creating $(ES_INDEX) index..."
	curl -X PUT $(ES_URL)/$(ES_INDEX)
	@echo -e "\nConfiguring $(ES_INDEX) index..."
	curl -X PUT $(ES_URL)/$(ES_INDEX)/_settings -H 'Content-Type: application/json' -d '{"index": {"number_of_replicas": 0}}'
.PHONY: es-index

lint: ## lint back-end python sources
lint: \
	lint-black \
	lint-ruff
.PHONY: lint

lint-mypy: ## lint back-end python sources with mypy
	@echo 'lint:mypy started…'
	@$(COMPOSE_TEST_RUN_APP) mypy
.PHONY: lint-mypy

lint-black: ## lint back-end python sources with black
	@echo 'lint:black started…'
	@$(COMPOSE_TEST_RUN_APP) black src/ralph tests
.PHONY: lint-black

lint-ruff: ## lint python sources with ruff
	@echo 'lint:ruff started…'
	@$(COMPOSE_TEST_RUN_APP) ruff check .
.PHONY: lint-ruff

lint-ruff-fix: ## lint python sources with ruff with fix option
	@echo 'lint:ruff-fix started…'
	@$(COMPOSE_TEST_RUN_APP) ruff check . --fix
.PHONY: lint-ruff-fix

logs: ## display app logs (follow mode)
	@$(COMPOSE) logs -f app
.PHONY: logs

run: ## run LRS server with the runserver backends (development mode)
run: \
	run-databases
	@$(COMPOSE) up -d app
.PHONY: run

run-all: ## start all supported local backends
run-all: run-databases 
.PHONY: run-all

run-databases: ## alias for running databases services
run-databases: \
	run-es \
	run-mongo \
	run-cozy-stack
.PHONY: run-databases

run-es: ## start elasticsearch backend
	@echo "Waiting for elasticsearch to be up and running..."
	@$(COMPOSE) up -d --wait elasticsearch
.PHONY: run-es

run-mongo: ## start mongodb backend
	@echo "Waiting for mongo to be up and running..."
	@$(COMPOSE) up -d --wait mongo
.PHONY: run-mongo

run-cozy-stack: ## start cozystack backend
	@echo "Waiting for cozy-stack to be up and running..."
	@$(COMPOSE) up -d --wait cozy-stack
.PHONY: run-cozy-stack

status: ## an alias for "docker compose ps"
	@$(COMPOSE) ps
.PHONY: status

stop: ## stops backend servers
	@$(COMPOSE) stop
.PHONY: stop

test: ## run back-end tests
test: run
	bin/pytest
.PHONY: test

diff-cover: coverage.xml 
	@$(COMPOSE_EXEC_APP) diff-cover coverage.xml --fail-under 100 

# -- Misc
help:
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
.PHONY: help

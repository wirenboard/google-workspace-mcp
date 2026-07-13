# Makefile — single entry point for every repeated action in this deploy repo.
# Run `make` (or `make help`) to list targets.
#
# This repo has no first-party code: the application is the pinned upstream
# `workspace-mcp` package baked into our image. Routine actions are therefore
# docker-compose operations, wrapped here so they stay consistent and documented.

COMPOSE ?= docker compose

.DEFAULT_GOAL := help

.PHONY: help
help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

.PHONY: env
env: ## Create .env from the template if it does not exist
	@test -f .env || cp .env.example .env

.PHONY: config
config: env ## Validate and render the compose file (checks .env substitution)
	$(COMPOSE) config

.PHONY: build
build: ## Build the image locally (CI builds and pushes the real one)
	$(COMPOSE) build

.PHONY: pull
pull: ## Pull the latest image from ghcr.io
	$(COMPOSE) pull

.PHONY: net
net: ## Create the shared external Traefik network if it is missing
	docker network inspect docker_main_net >/dev/null 2>&1 || docker network create docker_main_net

.PHONY: up
up: net env ## Start the server (detached)
	$(COMPOSE) up -d

.PHONY: down
down: ## Stop the server
	$(COMPOSE) down

.PHONY: restart
restart: ## Recreate the container with the current image/config
	$(COMPOSE) up -d --force-recreate

.PHONY: logs
logs: ## Follow container logs
	$(COMPOSE) logs -f --tail=100

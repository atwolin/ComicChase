# Variables for creating non-root user
UID ?= $(shell id -u)
GID ?= $(shell id -g)

# Define docker-compose command with production config
COMPOSE = UID=$(UID) GID=$(GID) docker compose -f docker-compose.prod.yaml -p comicchase-prod

.PHONY: build up down logs shell clean help

.DEFAULT_GOAL := help

# -------------------------------
up: ## Start the Docker containers in detached mode. Usage: make up UP_OPTIONS="<options>"
	@echo "🚀 Starting services with UID=$(UID) GID=$(GID)..."
	$(COMPOSE) up -d $(UP_OPTIONS)

down: ## Stop and remove the Docker containers
	@echo "🛑 Stopping services..."
	$(COMPOSE) down

build: ## Build the Docker images. Usage: make build UP_OPTIONS="<options>"
	@echo "🔨 Building Docker images with UID=$(UID) GID=$(GID)..."
	$(COMPOSE) up --build -d $(UP_OPTIONS)

logs: ## View logs of the Docker containers
	@echo "📜 Viewing logs..."
	$(COMPOSE) logs -f

shell: ## Access the shell of the app container
	@echo "🐚 Accessing app container shell..."
	$(COMPOSE) exec backend bash

manage: ## Run a Django manage.py command inside the app container. Usage: make manage cmd=<command>
	$(COMPOSE) exec backend python manage.py $(cmd)

clean: ## Remove all Docker containers and volumes
	@echo "🧹 Cleaning up Docker containers and volumes..."
	$(COMPOSE) down -v --remove-orphans

help: ## Show this help message
	@echo "Usage: make [command]"
	@echo ""
	@echo "Commands:"
	@echo "  up      Start the application (detached mode). Pass options with UP_OPTIONS."
	@echo "  down    Stop the application"
	@echo "  build   Rebuild and start the application. Pass options with UP_OPTIONS."
	@echo "  logs    Follow log output"
	@echo "  shell   Enter the 'backend' container shell"
	@echo "  manage  Run django manage.py command (e.g., make manage cmd=migrate)"
	@echo "  clean   Stop and remove containers, networks, and volumes"

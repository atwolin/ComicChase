# Variables for creating non-root user
UID ?= $(shell id -u)
GID ?= $(shell id -g)

# Environment selection (default: local)
ENV ?= local

# Define docker-compose commands for different environments
ifeq ($(ENV),vm)
    COMPOSE = UID=$(UID) GID=$(GID) docker compose -f docker-compose-vm.yaml -p comicchase-vm
else ifeq ($(ENV),gcr-test)
    COMPOSE = UID=$(UID) GID=$(GID) docker compose -f docker-compose-gcr-test.yaml -p comicchase-gcr-test
else ifeq ($(ENV),local)
    COMPOSE = UID=$(UID) GID=$(GID) docker compose -f docker-compose.yml -p comicchase-local
else
    $(error Invalid ENV value: $(ENV). Use 'local', 'vm', or 'gcr-test')
endif

.PHONY: all up down restart build rebuild logs shell manage test clean help env-info

all: rebuild ## Build and start everything (alias for rebuild)

.DEFAULT_GOAL := help

# -------------------------------
env-info: ## Show current environment configuration
	@echo "📋 Environment: $(ENV)"
	@echo "🆔 UID=$(UID) GID=$(GID)"
	@echo "🐳 Compose command: $(COMPOSE)"
	@echo ""
up: env-info ## Start the Docker containers in detached mode. Usage: make up [ENV=local|vm|gcr-test] [UP_OPTIONS="<options>"]
	@echo "🚀 Starting services..."
	$(COMPOSE) up -d $(UP_OPTIONS)

down: ## Stop and remove the Docker containers. Usage: make down [ENV=local|vm|gcr-test]
	@echo "🛑 Stopping services..."
	$(COMPOSE) down

restart: ## Restart the Docker containers. Usage: make restart [ENV=local|vm|gcr-test] [SERV=service_name]
	@echo "🔄 Restarting $(if $(SERV),$(SERV),all services)..."
	$(COMPOSE) restart $(SERV)

build: env-info ## Build the Docker images without starting. Usage: make build [ENV=local|vm|gcr-test]
	@echo "🔨 Building Docker images..."
	$(COMPOSE) build

rebuild: env-info ## Rebuild and start the Docker containers. Usage: make rebuild [ENV=local|vm|gcr-test] [UP_OPTIONS="<options>"]
	@echo "♻️ Rebuilding and starting services..."
	$(COMPOSE) up --build -d $(UP_OPTIONS)

logs: ## View logs of the Docker containers. Usage: make logs [SERV=service_name] [LINES=20]
	@echo "📜 Viewing logs for $(if $(SERV),$(SERV),all services)..."
	$(COMPOSE) logs --tail=$(if $(LINES),$(LINES),20) $(SERV)

shell: ## Access the shell of the app container. Usage: make shell [ENV=local|vm|gcr-test]
	@echo "🐚 Accessing app container shell..."
	$(COMPOSE) exec backend bash

manage: ## Run a Django manage.py command inside the app container. Usage: make manage cmd=<command> [ENV=local|vm|gcr-test]
	@if [ -z "$(cmd)" ]; then \
		echo "❗ Please provide a command to run. Usage: make manage cmd=\"<command>\""; \
		exit 1; \
	fi
	@echo "⚙️ Running manage.py command: $(cmd)"
	$(COMPOSE) exec backend python manage.py $(cmd)

test: ## Run tests inside the app container. Usage: make test [ENV=local|vm|gcr-test]
	@echo "🧪 Running tests..."
	$(COMPOSE) exec backend python manage.py test

clean: ## Remove all Docker containers and volumes. Usage: make clean [ENV=local|vm|gcr-test]
	@echo "🧹 Cleaning up Docker containers and volumes..."
	$(COMPOSE) down -v --remove-orphans

help: ## Show this help message
	@echo "Usage: make [target] [ENV=local|vm|gcr-test]"
	@echo ""
	@echo "Environments:"
	@echo "  ENV=local     - Use docker-compose.yml (default)"
	@echo "  ENV=vm        - Use docker-compose-vm.yaml"
	@echo "  ENV=gcr-test  - Use docker-compose-gcr-test.yaml (test GCR locally)"
	@echo ""
	@echo "Examples:"
	@echo "  make up                 # Start local environment"
	@echo "  make up ENV=vm          # Start VM environment"
	@echo "  make up ENV=gcr-test    # Test GCR Dockerfile locally"
	@echo "  make rebuild ENV=gcr-test # Rebuild and start GCR test environment"
	@echo ""
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-10s %s\n", $$1, $$2}'

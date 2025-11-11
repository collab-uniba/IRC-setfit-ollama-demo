.PHONY: venv activate install-ui install-setfit install-all setup-ollama run-ui run-setfit run-all dev clean docker-build docker-run docker-compose-up docker-compose-down

# Load environment variables if .env file exists
ifneq (,$(wildcard .env))
    include .env
    export
endif

# Default values if not set in .env
UI_PORT ?= 7860
SETFIT_PORT ?= 8000
OLLAMA_PORT ?= 11434
VECTOR_STORE_PORT ?= 8001
UI_HOST ?= 0.0.0.0
SETFIT_HOST ?= 0.0.0.0
OLLAMA_HOST ?= 0.0.0.0
VECTOR_STORE_HOST ?= 0.0.0.0
OLLAMA_BASE_URL ?= http://localhost:11434
SETFIT_BASE_URL ?= http://localhost:8000
VECTOR_STORE_BASE_URL ?= http://localhost:8001

# Environment setup target
setup-env:
	@if [ ! -f .env ]; then \
		echo "Creating .env file..."; \
		echo "UI_PORT=${UI_PORT}" > .env; \
		echo "SETFIT_PORT=${SETFIT_PORT}" >> .env; \
		echo "OLLAMA_PORT=${OLLAMA_PORT}" >> .env; \
		echo "VECTOR_STORE_PORT=${VECTOR_STORE_PORT}" >> .env; \
		echo "UI_HOST=${UI_HOST}" >> .env; \
		echo "SETFIT_HOST=${SETFIT_HOST}" >> .env; \
		echo "OLLAMA_HOST=${OLLAMA_HOST}" >> .env; \
		echo "VECTOR_STORE_HOST=${VECTOR_STORE_HOST}" >> .env; \
		echo "OLLAMA_BASE_URL=${OLLAMA_BASE_URL}" >> .env; \
		echo "SETFIT_BASE_URL=${SETFIT_BASE_URL}" >> .env; \
		echo "VECTOR_STORE_BASE_URL=${VECTOR_STORE_BASE_URL}" >> .env; \
		echo "DOCKER_OLLAMA_BASE_URL=http://ollama:11434" >> .env; \
		echo "DOCKER_SETFIT_BASE_URL=http://setfit:8000" >> .env; \
		echo "DOCKER_VECTOR_STORE_BASE_URL=http://vector-store:8001" >> .env; \
	fi

# Python version check target
python_version_check:
	@python3 -c 'import sys; assert sys.version_info >= (3, 12), "Python 3.12 or higher is required"'

# Virtual environment setup
venv: python_version_check
	python3 -m venv venv
	@echo "Virtual environment created. Use 'make activate' to activate it."

activate: venv
	@echo "To activate the virtual environment, run: source venv/bin/activate"

# Installation targets (updated paths)
install-ui: activate
	. venv/bin/activate && pip install -r services/ui/requirements.txt

install-setfit: activate
	. venv/bin/activate && pip install -r services/setfit/requirements.txt

install-all: install-ui install-setfit

# Ollama setup
setup-ollama:
	@if ! command -v ollama >/dev/null 2>&1; then \
		echo "Installing Ollama..."; \
		curl -fsSL https://ollama.com/install.sh | sh; \
	else \
		echo "Ollama is already installed."; \
	fi
	@if ! pgrep ollama >/dev/null; then \
		echo "Starting Ollama service..."; \
		OLLAMA_HOST=${OLLAMA_HOST} ollama serve > /dev/null 2>&1 & \
		echo "Waiting for Ollama to start..."; \
		sleep 5; \
	else \
		echo "Ollama is already running."; \
	fi

# Run services locally
run-ui: install-ui setup-ollama setup-env
	. venv/bin/activate && HOST=${UI_HOST} PORT=${UI_PORT} \
		OLLAMA_BASE_URL=${OLLAMA_BASE_URL} \
		SETFIT_BASE_URL=${SETFIT_BASE_URL} \
		python -m services.ui.app

run-setfit: install-setfit setup-env
	. venv/bin/activate && HOST=${SETFIT_HOST} PORT=${SETFIT_PORT} \
		uvicorn services.setfit.setfit_api:app --host ${SETFIT_HOST} --port ${SETFIT_PORT}

run-all: install-all setup-ollama setup-env
	@echo "Starting all services..."
	@echo "Starting SetFit service..."
	. venv/bin/activate && HOST=${SETFIT_HOST} PORT=${SETFIT_PORT} \
		uvicorn services.setfit.setfit_api:app --host ${SETFIT_HOST} --port ${SETFIT_PORT} & \
	echo "Starting UI service..." && \
	. venv/bin/activate && HOST=${UI_HOST} PORT=${UI_PORT} \
		OLLAMA_BASE_URL=${OLLAMA_BASE_URL} \
		SETFIT_BASE_URL=${SETFIT_BASE_URL} \
		python -m services.ui.app

# Docker commands with environment variables
docker-compose-up: setup-env
	docker-compose up --build -d

docker-compose-down:
	docker-compose down

# Clean up
clean:
	docker-compose down -v
	-docker rmi github-issue-classifier-ui github-issue-classifier-setfit github-issue-classifier-ollama
	-rm -rf venv
	-rm .env
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type f -name "*.pyc" -delete

# Help target
help:
	@echo "Available targets:"
	@echo "  setup-env         - Create .env file with default values"
	@echo "  venv              - Create Python virtual environment"
	@echo "  activate          - Activate virtual environment (must be sourced)"
	@echo "  install-ui        - Install UI requirements"
	@echo "  install-setfit    - Install SetFit requirements"
	@echo "  install-all       - Install all requirements"
	@echo "  setup-ollama      - Install and start Ollama service"
	@echo "  run-ui            - Run UI service locally"
	@echo "  run-setfit        - Run SetFit service locally"
	@echo "  run-all           - Run all services locally"
	@echo "  docker-compose-up - Start all services with Docker Compose"
	@echo "  docker-compose-down - Stop all services"
	@echo "  clean             - Remove all generated files and Docker resources"
	@echo ""
	@echo "Current configuration:"
	@echo "  UI_PORT:          ${UI_PORT}"
	@echo "  SETFIT_PORT:      ${SETFIT_PORT}"
	@echo "  OLLAMA_PORT:      ${OLLAMA_PORT}"
	@echo "  VECTOR_STORE_PORT:${VECTOR_STORE_PORT}"

.PHONY: install run-api run-frontend test lint clean docker-build docker-up docker-down help

VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

$(VENV):
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip

install: $(VENV) ## Install Python dependencies
	$(PIP) install -r requirements.txt

run-api: ## Run the FastAPI server
	$(PYTHON) -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --reload-exclude "$(VENV)/*" --reload-exclude "data/*" --reload-exclude "logs/*"

run-frontend: ## Run the Flask frontend
	export FLASK_APP=frontend/flask_app/app.py && $(VENV)/bin/flask run --port 8501

test: ## Run tests with coverage
	$(VENV)/bin/pytest tests/ -v --cov=app --cov-report=term-missing

test-unit: ## Run unit tests only
	$(VENV)/bin/pytest tests/test_services.py -v

test-api: ## Run API integration tests
	$(VENV)/bin/pytest tests/test_api.py -v

lint: ## Run code linting
	$(VENV)/bin/ruff check app/ tests/ frontend/
	$(VENV)/bin/ruff format --check app/ tests/ frontend/

format: ## Format code
	$(VENV)/bin/ruff format app/ tests/ frontend/

docker-build: ## Build Docker images
	docker compose build

docker-up: ## Start Docker containers
	docker compose up -d

docker-down: ## Stop Docker containers
	docker compose down

docker-logs: ## View Docker logs
	docker compose logs -f

clean: ## Clean temporary files and caches
	rm -rf data/uploads/*
	rm -rf data/chroma_db/*
	rm -rf __pycache__ .pytest_cache htmlcov .coverage
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	touch data/uploads/.gitkeep data/chroma_db/.gitkeep

.PHONY: help build up up-dev down logs test seed shell clean

help:
	@echo "Annotation Quality Guardian — Docker Commands"
	@echo "  make build      Build all production Docker images"
	@echo "  make up         Start production stack in background"
	@echo "  make up-dev     Start development stack with hot-reloading"
	@echo "  make down       Stop all containers"
	@echo "  make logs       View logs from all containers"
	@echo "  make test       Run test suite inside backend container"
	@echo "  make seed       Seed demo data inside backend container"
	@echo "  make shell      Open a bash shell inside the backend container"
	@echo "  make clean      Stop containers and remove volumes"

build:
	docker compose build

up:
	docker compose up -d

up-dev:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml up

down:
	docker compose down

logs:
	docker compose logs -f

test:
	docker compose exec backend pytest

seed:
	docker compose exec backend python -m app.core.seed_demo_data

shell:
	docker compose exec backend bash

clean:
	docker compose down -v --remove-orphans

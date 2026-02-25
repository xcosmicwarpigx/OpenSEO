.PHONY: up down build logs backend frontend test

# Docker commands
up:
	docker-compose up -d

up-build:
	docker-compose up --build -d

down:
	docker-compose down

logs:
	docker-compose logs -f

# Individual services
backend:
	docker-compose up -d backend redis worker

frontend:
	docker-compose up -d frontend

# Development (without Docker)
dev-backend:
	cd backend && uvicorn main:app --reload

dev-frontend:
	cd frontend && npm run dev

# Install dependencies
install-backend:
	cd backend && pip install -r requirements.txt && playwright install chromium

install-frontend:
	cd frontend && npm install

# Cleanup
clean:
	docker-compose down -v
	docker system prune -f

# Testing
test:
	cd backend && python -m pytest

# Setup
setup:
	cp .env.example .env
	@echo "Edit .env to add your Google PageSpeed API key (optional)"

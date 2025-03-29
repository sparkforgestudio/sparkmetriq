# Makefile - Musai MuseMgmt Platform

# Variables
PROJECT_NAME=musai-musemgmt-platform

# --- Commands ---
.PHONY: help install lint test build docker-up docker-down clean

help:
	@echo "Usage:"
	@echo "  make install       => Install all dependencies"
	@echo "  make lint          => Run linters on all services"
	@echo "  make test          => Run tests on all services"
	@echo "  make build         => Build all services"
	@echo "  make docker-up     => Start docker-compose"
	@echo "  make docker-down   => Stop docker-compose"
	@echo "  make clean         => Clean build artifacts"

install:
	pnpm install || npm install

lint:
	npx eslint ./services ./packages

test:
	npm run test

build:
	npm run build

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

clean:
	rm -rf dist build node_modules

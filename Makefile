SHELL := /bin/bash

.PHONY: up down rebuild worker logs api metrics smoke alembic-up

up:
	docker-compose up -d

down:
	docker-compose down

rebuild:
	docker-compose build --no-cache api && docker-compose up -d --force-recreate api

worker:
	docker-compose up -d --force-recreate worker

logs:
	docker-compose logs --tail=200 api worker

api:
	curl -s http://localhost:8000/ready | jq

metrics:
	curl -s http://localhost:8000/metrics | head

smoke:
	bash scripts/smoke.sh

alembic-up:
	alembic upgrade head

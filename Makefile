.PHONY: dev prod test audit generate clean docker-build docker-up

VENV = .venv
PYTHON = $(VENV)/bin/python
ifeq ($(OS),Windows_NT)
    PYTHON = $(VENV)\Scripts\python.exe
endif

all: test audit

generate:
	$(PYTHON) tools/generate_instance.py --seed "0x4B5552554B534845545241" --flag "KCTF{DRONA_CHAKRAVYUHA_SEAL_UNBROKEN_TRUTH}"

test:
	$(PYTHON) -m pytest backend/tests/ -v

audit:
	$(PYTHON) tools/audit_strings.py

study:
	$(PYTHON) tools/solvability_study.py

dev-backend:
	$(PYTHON) -m uvicorn backend.app.main:app --reload --port 8000

dev-frontend:
	cd frontend && npm run dev

build-frontend:
	cd frontend && npm run build

prod: build-frontend
	$(PYTHON) -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000

docker-build:
	docker compose build

docker-up:
	docker compose up -d

clean:
	rm -rf frontend/dist .pytest_cache backend/app/__pycache__ backend/tests/__pycache__

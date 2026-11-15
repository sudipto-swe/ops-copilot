.PHONY: up down test lint type-check demo smoke clean

VENV = .venv/bin

up:
	bash scripts/start_services.sh

down:
	bash scripts/stop_services.sh

test:
	$(VENV)/pytest apps/api/tests/ -v --cov=apps/api/app --cov-report=term-missing

lint:
	$(VENV)/ruff check .

type-check:
	$(VENV)/mypy --explicit-package-bases apps/api/app target

smoke:
	bash scripts/smoke.sh

demo:
	$(VENV)/python -m scripts.run_demo

clean:
	rm -rf .cache .pytest_cache logs/*.log .pids

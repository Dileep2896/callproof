.PHONY: install api web dev test build seed snapshot audit gate impact

install:
	cd engine && uv sync
	cd web && pnpm install

api:
	cd engine && uv run uvicorn callproof.api:app --host 127.0.0.1 --port 8761 --reload

web:
	cd web && pnpm dev

dev:
	$(MAKE) -j2 api web

test:
	cd engine && uv run pytest -q && uv run ruff check .
	cd web && pnpm test && pnpm typecheck

build:
	cd web && pnpm build

seed:
	cd engine && uv run python scripts/make_seed.py

snapshot:
	cd engine && uv run python -m callproof.cli snapshot ../web/public/snapshot.json

audit:
	cd engine && uv run python -m callproof.cli audit --version v14

gate:
	cd engine && uv run python -m callproof.cli gate --baseline v14 --candidate $(or $(CANDIDATE),v15)

impact:
	cd engine && uv run python -m callproof.cli impact

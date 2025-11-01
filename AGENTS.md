# Repository Guidelines

## Project Structure & Module Organization
Backend source lives under `api/` (FastAPI entrypoint), `services/` (scraping, LLM, security, persistence layers), and `core/` plus `db/` for Pydantic settings and SQLAlchemy session helpers. Database migrations are in `alembic/` with generated versions in `alembic/versions/`. Frontend assets are in `frontend/` (Vite + React + TypeScript). Shared configuration such as `requirements.txt`, `Makefile`, and deployment assets (e.g., `Dockerfile`) sit at the repository root. Add new tests beneath a top-level `tests/` package to keep discovery simple.

## Build, Test, and Development Commands
Create and activate a virtualenv, then `pip install -r requirements.txt` to prepare the backend. Run the API with `python -m uvicorn api.main_api:app --host 0.0.0.0 --port 8000 --reload`. Apply migrations via `alembic upgrade head`. Frontend setup uses `npm install` followed by `npm run dev`; bundle builds with `npm run build`. Helpful make targets include `make lint`, `make test`, `make format`, and `make install-playwright` (installs browsers for the advanced scraper).

## Coding Style & Naming Conventions
Python code follows Black formatting (4-space indents, 88-character target) and isort import ordering; enforce with `make format`. Lint with Flake8 and type-check with MyPy (`make lint`). Prefer descriptive module names (`snake_case.py`), PascalCase classes, snake_case functions, and typed signatures. React components use PascalCase filenames (`frontend/src/components/HeroSection.tsx`), hooks stay camelCase, and props should be typed via interfaces or `type` aliases. Keep environment keys in `.env` files, never in source.

## Testing Guidelines
Use Pytest for backend tests; mirror the `make test` command locally to ensure coverage and HTML reports match CI expectations. Name test modules `test_*.py` and colocate fixtures in `tests/conftest.py`. For frontend, rely on Vite-compatible testing (add Vitest/Playwright as needed) and keep scenario files under `frontend/src/__tests__/`. Ensure new features ship with at least one automated check.

## Commit & Pull Request Guidelines
Write commits in imperative mood (`Add health check endpoint`) and keep them focused; amend or squash noisy WIP commits before sharing. Link issues in PR descriptions, summarize scope, call out migrations or config changes, and attach screenshots for UI updates. Confirm lint/test runs are green prior to requesting review, and note any deliberate omissions or follow-up tasks explicitly.

## Security & Configuration Tips
Provide required secrets (`GROQ_API_KEY`, `JWT_SECRET`, `REDIS_HOST`, optional `DATABASE_URL`) through environment variables or `.env`, and avoid committing real credentials. When running locally, start Redis before the API (e.g., `redis-server` or Docker). Review scraping targets’ robots.txt policies and throttle requests via `ScrapingConfig` to stay compliant.

# Orchestra

An AI agent orchestration platform: submit a complex task, an LLM planner breaks it into a dependency graph of subtasks, specialized agents (research/writing/analysis/code) execute them — in parallel where possible — and a synthesizer combines the results into one final output with provenance.

This README grows alongside the implementation (see [`DECISIONS.md`](DECISIONS.md) for the phase-by-phase build plan). Right now it covers **Phase 1: infrastructure** — Postgres, migrations, and the LLM client abstraction. API endpoints and agents land in later phases.

## Prerequisites

- Docker + Docker Compose. On Windows, Docker Desktop isn't required — WSL2 with Docker installed directly inside the Linux distro works too (that's what's used below). Run all commands from inside WSL (`wsl`), not PowerShell.
- Python 3.11+ (only needed for the local `.venv` below, for editor/IDE support — running the app itself only needs Docker)
- An Anthropic API key (only needed once real LLM calls start in later phases — not required to run Phase 1)

## First-time setup

From inside WSL, in the project directory (e.g. `/mnt/c/Users/<you>/Desktop/code/Orchestra`):

```bash
# 1. Local virtualenv, for editor/IDE support only (type checking, autocomplete) —
#    the app itself runs in Docker, this isn't required for that.
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"

# 2. Env file — APP_ENV=dev by default (see below for prod)
cp .env.example .env          # fill in ANTHROPIC_API_KEY when you have one

# 3. Start Postgres + the app
docker compose up -d --build

# 4. Create tables, seed the 4 agent rows
docker compose exec app alembic upgrade head
```

Verify it's up: `curl http://localhost:8000/health` → `{"status":"ok"}`.

Every port and Postgres credential comes from `.env` (see `.env.example`) — nothing is hardcoded in `docker-compose.yml`. Setting `APP_ENV=prod` in `.env` before `docker compose up -d --build` builds `Dockerfile.prod` instead of `Dockerfile.dev` (no dev dependencies, no `--reload`) — see `CLAUDE.md`'s "Docker: dev vs. prod" section.

If `python3 -m venv .venv` fails with a missing `ensurepip` error (some minimal WSL distros don't ship it and installing `python3-venv` needs `sudo`), fall back to `virtualenv`:
```bash
python3 -m pip install --user --break-system-packages virtualenv
python3 -m virtualenv .venv
```

## Running tests

```bash
docker compose exec app pytest
```

Tests run against a real Postgres database (a separate `orchestra_test` database on the same instance, created automatically) with the actual Alembic migrations applied — not a fake in-memory DB. No test ever calls a real LLM; every LLM call goes through `FakeLLMClient` (see `tests/conftest.py`).

**Verified working end-to-end** (Phase 1, all 5 tests passing): infrastructure build, migrations, and test suite have all actually been run against real Docker/Postgres — not just reviewed. See [`DECISIONS.md`](DECISIONS.md) for two bugs that only surfaced once tests actually ran.

## Project structure

See [`CLAUDE.md`](CLAUDE.md) for the full folder layout and the conventions this codebase follows.

## Status

- [x] Phase 1 — Postgres + Alembic migrations, SQLAlchemy async models, `LLMClient` abstraction
- [ ] Phase 2 — Task submission API + first agent (vertical slice)
- [ ] Phase 3 — Planner + dependency-based execution engine (sequential + parallel)
- [ ] Phase 4 — Synthesis, failure recovery, monitoring, cancellation
- [ ] Phase 5 — Docs finalized, full end-to-end verification

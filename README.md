# Orchestra

An AI agent orchestration platform: submit a complex task, an LLM planner breaks it into a dependency graph of subtasks, specialized agents (research/writing/analysis/code) execute them — in parallel where possible — and a synthesizer combines the results into one final output with provenance.

This README grows alongside the implementation (see [`DECISIONS.md`](DECISIONS.md) for the phase-by-phase build plan). It currently covers **Phase 1: infrastructure** (Postgres, migrations, LLM client abstraction), **Phase 2: task submission API**, and **Phase 3: planner + execution engine** — a submitted goal is decomposed by the LLM into a dependency graph of steps, routed across 4 agents (research/writing/analysis/code), and executed respecting dependencies, in parallel where the graph allows.

### API (Phase 3)

- `POST /tasks` — `{"goal": "...", "constraints": {}, "output_format": "markdown"}` → creates a task, has the planner decompose it into a `Plan`, executes the plan's steps (parallel where independent), and returns the completed task with its composed result. Returns `422` if the planner can't produce a structurally valid plan after retrying; the task itself is left `failed`. A step that exhausts its retries is marked failed and any step depending on it is skipped — the task still completes if at least one step succeeded.
- `GET /tasks/{id}` — fetch a task by id (404 if missing).
- `GET /agents` — lists the 4 seeded agent rows and their capabilities.

Result composition today is a placeholder — each completed step's output, concatenated in plan order. A real synthesis pass (weighing partial results, explaining what failed, provenance) is Phase 4's job. See [`DECISIONS.md`](DECISIONS.md) for the planner/dependency/parallel-execution design decisions.

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

**Verified working end-to-end** (Phase 1 + 2 + 3): infrastructure build, migrations, the task/agent API, the planner, the execution engine, and the full test suite have all actually been run against real Docker/Postgres — not just reviewed. See [`DECISIONS.md`](DECISIONS.md) for bugs that only surfaced once tests actually ran.

## Development

Everything below runs through the `app` container (`docker compose exec app ...`) — there's no need to run anything on the host except editor tooling.

### Daily loop

```bash
docker compose up               # start db + app (already built once)
docker compose logs -f app      # tail app logs
```

`Dockerfile.dev` runs Uvicorn with `--reload`, and `./app`, `./tests`, `./alembic` are bind-mounted (see `docker-compose.yml`), so editing a file on the host is picked up immediately — no rebuild needed. A rebuild (`docker compose up -d --build`) is only required after changing a dependency in `pyproject.toml` or either `Dockerfile.*`.

### Database migrations

Schema changes always go: **edit a model in `app/models/` → autogenerate a migration → review it → apply it.** Never hand-write the schema operations in a migration file yourself:

```bash
docker compose exec app alembic revision --autogenerate -m "add task result column"
docker compose exec app alembic upgrade head
```

Open the generated file in `alembic/versions/` before applying — autogenerate is good but not perfect (renames and some index changes need a manual nudge). The one legitimate exception to "never hand-write" is a pure *data* migration (like seeding the `agents` table), since there's no model diff for Alembic to detect; that gets written against the plain template instead:

```bash
docker compose exec app alembic revision -m "seed something"
```

Other useful commands:

```bash
docker compose exec app alembic current    # what revision is the DB on
docker compose exec app alembic history    # full migration chain
docker compose exec app alembic downgrade -1
```

### Tests

```bash
docker compose exec app pytest                        # full suite
docker compose exec app pytest tests/test_api_tasks.py # one file
docker compose exec app pytest -k missing_id           # by name
```

Every test hits a real, disposable Postgres database (`orchestra_test`) with actual migrations applied, but never a real LLM — `FakeLLMClient` (`tests/conftest.py`) stands in everywhere, wired in for API tests via `app.dependency_overrides`.

### Formatting & linting

```bash
docker compose exec app black app tests
docker compose exec app ruff check app tests
docker compose exec app ruff check --fix app tests   # auto-fix what's fixable
```

Both are enforced — CI-equivalent expectation is zero findings from either before merging.

### Running against a prod-built image locally

```bash
# in .env:
APP_ENV=prod
```
```bash
docker compose up -d --build
```

Builds `Dockerfile.prod` instead (frozen install, no dev deps, no `--reload`, no `tests/` copied in) — useful for sanity-checking the production image locally. Switch `APP_ENV` back to `dev` afterwards for the normal edit-and-reload workflow.

### Local `.venv` (editor support only)

The app always runs in Docker; the venv from [First-time setup](#first-time-setup) exists purely so your editor can resolve imports and type-check. It needs Python 3.11+ specifically — a mismatched local Python will still show false errors for 3.11+ syntax (`StrEnum`, `str | None` unions) even with all packages installed.

## Project structure

See [`CLAUDE.md`](CLAUDE.md) for the full folder layout and the conventions this codebase follows.

## Status

- [x] Phase 1 — Postgres + Alembic migrations, SQLAlchemy async models, `LLMClient` abstraction
- [x] Phase 2 — Task submission API + first agent (vertical slice)
- [x] Phase 3 — Planner + dependency-based execution engine (sequential + parallel)
- [ ] Phase 4 — Synthesis, failure recovery, monitoring, cancellation
- [ ] Phase 5 — Docs finalized, full end-to-end verification

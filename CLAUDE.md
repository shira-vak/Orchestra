# CLAUDE.md

Source of truth for all code generation in this project.
**Priority: CLAUDE.md → project structure → framework defaults.**

---

## Before Generating Code

1. Does this conflict with CLAUDE.md?
2. Are all types explicit (full type hints, no bare `dict`/`Any`)?
3. Is the solution simpler than what I first thought of?
4. Is this value a magic number/string that belongs in `constants.py` or `config.py` instead?
5. Is this logic non-obvious enough that a future reader (including the author) would need a comment or docstring to follow it? If yes, write one. If the comment would just restate the code, rename instead.

---

## Project

**Orchestra** — an AI agent orchestration platform. Backend-only service: submits complex tasks, decomposes them via an LLM planner into a dependency graph of subtasks, routes subtasks to specialized agents (research/writing/analysis/code), executes the graph respecting dependencies (parallel where possible), and synthesizes the results into one final output with provenance.

## Tech Stack

- **Language:** Python 3.11+
- **Web framework:** FastAPI + Uvicorn (async)
- **Validation / schemas:** Pydantic v2
- **Database:** PostgreSQL 16 via Docker
- **ORM:** SQLAlchemy 2.0 (async, `asyncpg` driver)
- **Migrations:** Alembic
- **LLM provider:** Anthropic SDK, behind an `LLMClient` interface (swappable, mockable)
- **Retry/backoff:** plain hand-written retry loop (no dedicated library) — see `app/execution/retry.py`
- **Testing:** `pytest` + `pytest-asyncio` + `httpx.AsyncClient`
- **Formatting/linting:** `black` + `ruff`

**Library policy:** every dependency above is already load-bearing for the assignment's required stack. Don't add a new third-party library for something a short hand-written function can do just as clearly — the author needs to be able to read and explain every piece of this code.

## Development Commands

### First-time setup

```bash
cp .env.example .env                            # APP_ENV=dev by default
docker compose up -d --build                     # starts Postgres + the app (dev image)
docker compose exec app alembic upgrade head     # runs migrations (creates + seeds tables)

# Local .venv, for editor/IDE support only (import resolution, type checking) —
# the app always runs in Docker, this isn't required for that. Needs Python 3.11+.
python3.11 -m venv .venv
.venv/bin/pip install -e ".[dev]"
```

### Daily dev

```bash
docker compose up                 # app (port from .env's APP_PORT) + postgres
docker compose logs -f app        # tail app logs
docker compose exec app alembic revision --autogenerate -m "message"   # new migration after a models/ change
```

### Running against a prod-built image locally

```bash
# In .env: APP_ENV=prod
docker compose up -d --build      # builds Dockerfile.prod instead of Dockerfile.dev
```

`APP_ENV` in `.env` selects which Dockerfile `docker-compose.yml` builds (`Dockerfile.dev` or `Dockerfile.prod` — see [Docker: dev vs. prod](#docker-dev-vs-prod)). A real deployment doesn't use this compose file at all — it pushes the `Dockerfile.prod` image to a registry and runs it directly, without the dev bind-mounts this compose file adds for convenience.

### Tests

```bash
docker compose exec app pytest              # full suite
docker compose exec app pytest -k planner   # scoped run
```

Tests never hit a real LLM, but do hit a real (separate, disposable) Postgres database — see [Testing](#testing).

---

## Python

- Every function and method has explicit parameter types and an explicit return type. No relying on inference for signatures.
- No bare `dict`, `list`, or `Any` in signatures. Use a Pydantic model, a `TypedDict`, or a precise generic (`dict[str, int]`) — reserve `Any` for the one true unknown boundary (raw LLM JSON before validation), and narrow it immediately.
- Use `enum.StrEnum` for closed value sets (`TaskStatus`, `StepStatus`, `AgentName`) instead of raw strings — this is the Python equivalent of TS `as const` unions and is how we avoid magic strings for anything used more than once.
- Use `Literal[...]` only for small, truly local one-off constraints; prefer `StrEnum` for anything that appears in more than one file or crosses the API boundary.
- Use `from __future__ import annotations` is unnecessary on 3.11+ — write native `str | None` unions directly.
- Prefer `dataclasses` only for internal, non-serialized structures. Anything crossing an API boundary, stored in the DB as JSON, or returned by the LLM is a Pydantic model.

---

## Clean Code

- Clear names over comments. If a function name plus its signature doesn't explain what it does, rename before reaching for a comment.
- **Exception: write a docstring or inline comment whenever the logic itself is non-obvious** — e.g. the DAG topological-sort/cycle-detection algorithm, the parallel-layer scheduling logic, the retry/skip-propagation rules, the context-truncation heuristic. This project exists to be understood, not just to pass review — err on the side of explaining *why*, not *what*.
- One function = one responsibility.
- No over-engineering, no speculative abstraction. A shared helper needs a real second caller before it's extracted.
- Prefer simple, predictable code over clever code.
- **Function length:** no function should exceed ~60 lines. Python is terser than TS/NestJS, so this is a tighter budget than a typical TS project's 100 — if a function is creeping past it, extract a named helper.
- Async functions only where they actually await something (an LLM call, a DB call). Don't mark something `async def` just because it's called from async code.

---

## No Magic Values

Never use inline literal numbers, strings, or config objects whose meaning isn't obvious from context.

| Value type | Where it lives |
|---|---|
| Domain constant (retry count, concurrency limit, token-truncation cap, timeout) | `app/config.py` `Settings` (if env-overridable) or `app/constants.py` (if fixed) |
| Closed value set (task status, step status, agent name, action name) | `StrEnum` in the nearest `enums.py` (or on the model file if only used there) |
| API route paths | Defined once on the router (`@router.post("/tasks")`) — never duplicated as a literal elsewhere (tests import the router's path constant) |
| Prompt templates | `app/planner/prompts.py`, `app/agents/*/prompts.py` — never an inline f-string built ad hoc inside business logic |
| Pydantic schema | `app/schemas/` — never a bare `dict` passed across a function boundary |

A value defined once must not be re-typed anywhere else — import it.

---

## Configuration & Environment

- `.env` holds **atomic values only** — a host, a port, a username, a single number. Never a pre-assembled connection string. `app/config.py`'s `Settings` composes those into things like `database_url` via a `@property`, so there is exactly one place that string is ever built. If you catch yourself writing `postgresql://...` as a literal anywhere outside that one property, stop — read the pieces from `Settings` instead.
- `docker-compose.yml` reads the **same** `.env` (Compose auto-loads it for `${VAR}` interpolation) for ports and Postgres credentials — it never hardcodes a value that also appears in `.env` or in `Settings`' defaults. If `db`'s credentials and the app's `database_url` ever need to agree, they're reading the same `POSTGRES_*` vars, not two independently-typed copies.
- Ports are never a bare number in `Dockerfile.*`, `docker-compose.yml`, or app code — `APP_PORT` in `.env`, threaded through as a build `ARG`/`ENV` in the Dockerfiles and as `${APP_PORT}` in compose.
- Config that's only relevant to **tests** does not belong in `app/config.py`'s `Settings` — see `tests/settings.py`. The production config model should never carry a field nothing in `app/` actually reads.
- Config that's fixed regardless of environment (ID prefixes, default formats) stays in `app/constants.py`, not `.env` — `.env` is for things a deployer might legitimately need to change.

---

## Docker: dev vs. prod

Two Dockerfiles, chosen by `.env`'s `APP_ENV` (`dockerfile: Dockerfile.${APP_ENV}` in `docker-compose.yml`):

| | `Dockerfile.dev` | `Dockerfile.prod` |
|---|---|---|
| Install | `pip install -e ".[dev]"` (editable, dev extras) | `pip install .` (frozen, runtime-only) |
| `tests/` copied in | Yes | No |
| Uvicorn | `--reload` | no `--reload` |
| Expects bind-mounted source | Yes (docker-compose.yml mounts `./app` etc.) | No — self-contained image |

Keep both Dockerfiles minimal and let them diverge only where dev/prod genuinely need different behavior — don't add a flag to one Dockerfile to fake what the other already does natively.

---

## Architecture

### Folder Structure

```
orchestra/
├── app/
│   ├── main.py                 # FastAPI app, router mounting, startup hooks
│   ├── config.py                # Settings (pydantic-settings): DB URL, API key, concurrency limit, retry count
│   ├── constants.py             # fixed, non-env constants
│   ├── api/
│   │   ├── tasks_router.py      # POST /tasks, GET /tasks/{id}, GET /tasks/{id}/result, POST /tasks/{id}/cancel
│   │   └── agents_router.py     # GET /agents
│   ├── schemas/                 # Pydantic request/response models (API contract)
│   │   ├── task.py
│   │   ├── plan.py
│   │   └── agent_output.py
│   ├── models/                  # SQLAlchemy ORM tables
│   │   ├── task.py
│   │   ├── execution_plan.py
│   │   ├── execution_step.py
│   │   └── agent.py
│   ├── db/
│   │   ├── session.py           # async engine + sessionmaker, FastAPI dependency
│   │   └── repository.py        # TaskRepository — all persistence access goes through here
│   ├── planner/
│   │   ├── planner.py           # decompose(task) -> ExecutionPlan
│   │   ├── prompts.py           # planning prompt templates
│   │   └── validation.py        # schema check, cycle detection, unknown-reference check
│   ├── agents/
│   │   ├── base.py              # BaseAgent ABC
│   │   ├── research_agent.py
│   │   ├── writing_agent.py
│   │   ├── analysis_agent.py
│   │   ├── code_agent.py
│   │   └── registry.py          # agent name -> instance, capability metadata for GET /agents
│   ├── execution/
│   │   ├── engine.py            # topological layering, asyncio.gather + semaphore, step lifecycle
│   │   ├── context.py           # builds each step's input from its dependencies' outputs
│   │   └── retry.py             # plain retry loop (for/try-except) around agent calls
│   ├── synthesis/
│   │   └── synthesizer.py       # combine outputs + provenance + final compose call
│   ├── llm/
│   │   └── client.py            # LLMClient ABC + AnthropicClient
│   └── core/
│       ├── task_manager.py      # lifecycle facade: plan → execute → synthesize → persist
│       └── exceptions.py        # domain exceptions, mapped to HTTP errors in one place
├── alembic/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/                # every file here is generated (or, for pure data
│                                 # migrations like seeding, hand-written against
│                                 # the template) — never a hand-authored schema diff
├── tests/
│   ├── conftest.py              # FakeLLMClient, test DB session, FastAPI test client fixtures
│   ├── settings.py               # test-only config (test DB name) — kept out of app/config.py
│   ├── consts.py                # shared test constants (IDs, timestamps, mock plan JSON)
│   ├── test_api_tasks.py
│   ├── test_planner.py
│   ├── test_execution_sequential.py
│   ├── test_execution_parallel.py
│   ├── test_error_handling.py
│   └── test_synthesis.py
├── docker-compose.yml
├── Dockerfile.dev
├── Dockerfile.prod
├── pyproject.toml
├── .env.example
├── README.md
├── DECISIONS.md
└── AI_USAGE.md
```

### Naming

- Files: `snake_case` (`tasks_router.py`, `research_agent.py`)
- Classes: `PascalCase` (`TaskManager`, `ExecutionEngine`, `TaskStatus`)
- Functions/variables: `snake_case`
- No `__init__.py` re-export barrels that hide where something is actually defined — import from the real module path.

### API Layer

- Routers do request/response wiring only — parse input, call `TaskManager`, return the response schema. No business logic, no DB access, no LLM calls in a router function.
- Every handler has an explicit response model (`response_model=...`) and explicit param/body types.
- Domain exceptions raised in the service layer are translated to HTTP errors in **one place** (an exception handler registered in `main.py`), not with scattered `try/except` in routers.

### Service-equivalent Layer (Planner / Engine / Synthesizer / TaskManager)

- All orchestration logic lives here, not in routers or models.
- Public methods are `async def` with explicit return types.
- Return Pydantic schemas or ORM models as appropriate — never a bare `dict`.
- Cross-component calls go through the component's public interface (`Planner.decompose(...)`), never by reaching into another component's internals.

### Schemas (Pydantic)

- Every field has an explicit type; use `Field(...)` for constraints (`max_length`, `ge`, `le`) instead of validating manually where Pydantic already supports it.
- Naming: `<Action><Resource>Request` for input (`CreateTaskRequest`), `<Resource>Response` for output (`TaskResponse`).
- Use `field_validator` only for checks Pydantic's declarative constraints can't express (cross-field checks, DAG structure).

### SQLAlchemy / Alembic

- All DB access goes through `TaskRepository` — no `session.execute(...)` calls outside `app/db/`.
- Use `async with session.begin():` for any operation that writes to more than one table, so it's atomic.
- **The SQLAlchemy models in `app/models/` are the schema.** Never hand-write a migration's `op.create_table`/`op.add_column`/etc. calls — change the model, then run `alembic revision --autogenerate -m "..."` and let Alembic diff the models against the DB to generate the migration file. Review the generated file (autogenerate isn't perfect for renames, index changes, etc.) but don't author schema operations by hand.
- **Exception:** pure data migrations (seeding fixed rows, like `agents`) can't be autogenerated — those are legitimately hand-written against the plain `alembic revision -m "..."` template, since there's no model diff to detect.
- Never hand-edit a migration that has already been applied anywhere — generate a new one.
- Load relationships explicitly (`selectinload`) where needed; never rely on implicit lazy-loading in async code (it will error).

### Error Handling

| Situation | Exception |
|---|---|
| Task/step/agent not found | `TaskNotFoundError` → 404 |
| Planner returns an invalid/unparseable plan after retry | `InvalidPlanError` → 422 |
| Cycle or unknown reference detected in a plan | `InvalidPlanError` → 422 |
| Action attempted on a task in the wrong state (e.g. cancel a completed task) | `InvalidTaskStateError` → 409 |
| Step exhausts retries | not an HTTP error — recorded on the step, task proceeds per the failure-recovery policy in `DECISIONS.md` |

All domain exceptions live in `app/core/exceptions.py` and are mapped to HTTP responses in a single FastAPI exception handler — never inline `HTTPException` raises deep in business logic.

---

## Security

- `goal` and `constraints` from the client are untrusted: enforce max lengths via Pydantic `Field` constraints before they ever reach a prompt.
- The LLM's plan JSON is untrusted: it is always parsed through the Pydantic `ExecutionPlan` schema and passed through `validation.py` (cycle + reference checks) before a single step is executed. Never execute an unvalidated plan.
- The Code Agent generates and explains code — it never executes model-generated code.
- API keys are read from environment variables only (`.env`, not committed); never logged, never returned in any API response.
- Research Agent output is LLM-generated, not live-fetched — sources are labeled as such, never presented as verified.

---

## Testing

### What to test

- Every new component gets tests in the same phase it's built in — not deferred to a final "testing phase."
- Planner: valid plan parses correctly; a plan with a cycle or an unknown step reference is rejected.
- Execution engine: sequential ordering + dependency data passing; parallel steps genuinely overlap in time (assert on timing, not just on output).
- Failure handling: a step that exhausts retries is marked failed, and its dependents are skipped, not silently executed.
- API endpoints: submit → status → result → cancel, happy path and one failure path each.

### Naming

```
test_<module>.py → def test_<behavior>_<condition>_<expected_result>()
```

Group with a `class Test<Component>` only when it meaningfully clusters related cases — not required for every file.

### No magic values in tests

Every ID, timestamp, and domain literal is a named constant, not an inline literal:

```python
# correct
MOCK_TASK_ID = "task_123"
MOCK_CREATED_AT = datetime(2024, 6, 1, 8, 0, tzinfo=UTC)

# wrong — independent literals that can drift
task_id = "task_123"
```

### Mocks

- **Shared** constants and mock objects (IDs, mock plan JSON, mock DB rows) live in `tests/consts.py`.
- **Feature-specific** constants used by a single test file are defined at the top of that file.
- All LLM calls in tests go through `FakeLLMClient` (fixture in `conftest.py`), which returns fixed, deterministic responses. No test ever calls a real LLM or a real database outside the test Postgres/session fixture.
- Test-only configuration (the test database name) lives in `tests/settings.py`, not `app/config.py` — `app/config.py`'s `Settings` should never gain a field that nothing in `app/` reads.

---

## Formatting

- `black` (line length 100) + `ruff` for linting, both enforced — no PR/commit with lint or format failures.
- Double quotes (black default).
- Trailing commas in multi-line collections.

"""Purpose: validates a Plan's structure and computes its parallel execution layers in one pass."""

from app.exceptions import InvalidPlanError
from app.planner.schemas.plan import Plan
from app.planner.schemas.plan_step import PlanStep


def validate_plan(plan: Plan) -> list[list[str]]:
    return _build_parallel_groups(plan.steps)


def _build_parallel_groups(steps: list[PlanStep]) -> list[list[str]]:
    """Kahn's-algorithm layering: a cycle leaves steps that never reach an
    empty dependency set, which doubles as cycle detection."""
    step_ids = {step.id for step in steps}
    unknown_refs = {dep for step in steps for dep in step.dependencies if dep not in step_ids}
    if unknown_refs:
        raise InvalidPlanError(f"plan references unknown step id(s): {sorted(unknown_refs)}")

    remaining = {step.id: set(step.dependencies) for step in steps}
    groups: list[list[str]] = []

    while remaining:
        ready = sorted(step_id for step_id, deps in remaining.items() if not deps)
        if not ready:
            raise InvalidPlanError(
                f"plan has a dependency cycle among step(s): {sorted(remaining)}"
            )
        groups.append(ready)
        for step_id in ready:
            del remaining[step_id]
        for deps in remaining.values():
            deps.difference_update(ready)

    return groups

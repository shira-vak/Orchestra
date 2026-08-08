from app.planner.schemas.plan_step import PlanStep


def build_step_input(step: PlanStep, outputs: dict[str, str]) -> str:
    if not step.dependencies:
        return step.input

    context = "\n\n".join(
        f"### Output of {dep_id}\n{outputs[dep_id]}" for dep_id in step.dependencies
    )
    return f"{step.input}\n\nContext from prior steps:\n{context}"

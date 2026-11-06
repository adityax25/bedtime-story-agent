"""One function per agent. Each pairs a system prompt with its inputs and output contract."""

from storyteller.llm import call_model, call_structured
from storyteller.prompts import load_prompt
from storyteller.schemas import StoryBrief, StoryPlan


def classify(request: str) -> StoryBrief:
    return call_structured(
        f"<request>\n{request}\n</request>",
        StoryBrief,
        system=load_prompt("classifier"),
        effort="low",
    )


def plan(brief: StoryBrief) -> StoryPlan:
    # Only the strategy for this category is sent, so the planner is not
    # distracted by guidance meant for other kinds of stories.
    strategy = load_prompt(f"strategies/{brief.category}")
    prompt = (
        f"<brief>\n{brief.model_dump_json(indent=2)}\n</brief>\n\n"
        f"<category_strategy>\n{strategy}\n</category_strategy>"
    )
    return call_structured(prompt, StoryPlan, system=load_prompt("planner"), effort="medium")


def write(brief: StoryBrief, story_plan: StoryPlan) -> str:
    prompt = (
        f"<brief>\n{brief.model_dump_json(indent=2)}\n</brief>\n\n"
        f"<plan>\n{story_plan.model_dump_json(indent=2)}\n</plan>"
    )
    return call_model(prompt, system=load_prompt("storyteller"), effort="medium")

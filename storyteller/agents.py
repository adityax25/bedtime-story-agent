"""One function per agent. Each pairs a system prompt with its inputs and output contract."""

from storyteller.llm import call_model, call_structured
from storyteller.prompts import load_prompt
from storyteller.schemas import Judgement, PairwiseVerdict, StoryBrief, StoryPlan


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


def _review_context(request: str, brief: StoryBrief) -> str:
    # Reviewers see the request and audience but never the writer's prompts or plan,
    # so they judge the story on its own merits.
    return (
        f"<request>\n{request}\n</request>\n\n"
        f"<age_band>{brief.age_band}</age_band>\n\n"
        f"<safety_adjustment>\n{brief.safety_note or 'None'}\n</safety_adjustment>"
    )


def judge(request: str, brief: StoryBrief, story: str) -> Judgement:
    prompt = f"{_review_context(request, brief)}\n\n<story>\n{story}\n</story>"
    return call_structured(prompt, Judgement, system=load_prompt("judge"), effort="high")


def revise(brief: StoryBrief, story: str, notes: list[str]) -> str:
    numbered = "\n".join(f"{i}. {note}" for i, note in enumerate(notes, start=1))
    prompt = (
        f"<brief>\n{brief.model_dump_json(indent=2)}\n</brief>\n\n"
        f"<draft>\n{story}\n</draft>\n\n"
        f"<revision_notes>\n{numbered}\n</revision_notes>"
    )
    return call_model(prompt, system=load_prompt("reviser"), effort="medium")


def compare(request: str, brief: StoryBrief, story_a: str, story_b: str) -> PairwiseVerdict:
    prompt = (
        f"{_review_context(request, brief)}\n\n"
        f"<story_a>\n{story_a}\n</story_a>\n\n"
        f"<story_b>\n{story_b}\n</story_b>"
    )
    return call_structured(prompt, PairwiseVerdict, system=load_prompt("pairwise"), effort="high")

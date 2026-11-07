"""One function per agent. Each pairs a system prompt with its inputs and output contract."""

from storyteller.checks import TARGET_WORDS, word_count
from storyteller.llm import call_model, call_structured
from storyteller.prompts import load_prompt
from storyteller.schemas import FeedbackInterpretation, Judgement, PairwiseVerdict, StoryBrief, StoryPlan


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


def _numbered(notes: list[str]) -> str:
    return "\n".join(f"{i}. {note}" for i, note in enumerate(notes, start=1))


def revise(brief: StoryBrief, story: str, notes: list[str]) -> str:
    prompt = (
        f"<brief>\n{brief.model_dump_json(indent=2)}\n</brief>\n\n"
        f"<draft>\n{story}\n</draft>\n\n"
        f"<revision_notes>\n{_numbered(notes)}\n</revision_notes>"
    )
    return call_model(prompt, system=load_prompt("reviser"), effort="medium")


def compare(
    request: str, brief: StoryBrief, story_a: str, story_b: str, notes: list[str]
) -> PairwiseVerdict:
    # Word counts are computed in code and stated explicitly; an abstract warning
    # alone did not stop the judge from favoring the longer version.
    low, high = TARGET_WORDS
    lengths = (
        f"Target length: {low} to {high} words.\n"
        f"Story A: {word_count(story_a)} words.\n"
        f"Story B: {word_count(story_b)} words."
    )
    prompt = (
        f"{_review_context(request, brief)}\n\n"
        f"<lengths>\n{lengths}\n</lengths>\n\n"
        f"<revision_notes>\n{_numbered(notes)}\n</revision_notes>\n\n"
        f"<story_a>\n{story_a}\n</story_a>\n\n"
        f"<story_b>\n{story_b}\n</story_b>"
    )
    # Comparing two near-identical drafts needs less deliberation than a full review.
    return call_structured(prompt, PairwiseVerdict, system=load_prompt("pairwise"), effort="medium")


def interpret(story: str, feedback: str) -> FeedbackInterpretation:
    prompt = (
        f"<current_story>\n{story}\n</current_story>\n\n"
        f"<listener_message>\n{feedback}\n</listener_message>"
    )
    return call_structured(prompt, FeedbackInterpretation, system=load_prompt("interpreter"), effort="low")

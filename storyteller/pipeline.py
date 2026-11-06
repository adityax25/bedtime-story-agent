"""Orchestrates the agents in order. Holds no prompts or API details itself."""

from collections.abc import Callable
from dataclasses import dataclass

from storyteller import agents
from storyteller.schemas import StoryBrief, StoryPlan


@dataclass
class StoryResult:
    brief: StoryBrief
    plan: StoryPlan
    story: str


def generate_story(request: str, on_step: Callable[[str], None] = lambda _: None) -> StoryResult:
    on_step("Understanding the request")
    brief = agents.classify(request)

    if brief.safety != "safe":
        on_step(f"Safety {brief.safety}: {brief.safety_note}")

    on_step(f"Planning the story (category: {brief.category}, ages {brief.age_band})")
    story_plan = agents.plan(brief)

    on_step("Writing the story")
    story = agents.write(brief, story_plan)

    return StoryResult(brief=brief, plan=story_plan, story=story)

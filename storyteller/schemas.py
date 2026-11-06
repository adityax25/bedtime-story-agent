"""Contracts between agents. Each model is the structured output of one agent."""

from typing import Literal

from pydantic import BaseModel, Field

Category = Literal[
    "adventure",
    "friendship_feelings",
    "funny_silly",
    "animals_nature",
    "calm_cozy",
]
AgeBand = Literal["5-7", "8-10", "5-10"]
SafetyVerdict = Literal["safe", "reframe", "redirect"]


class Character(BaseModel):
    name: str = Field(description="Name exactly as the requester gave it, or a fitting new name.")
    description: str = Field(description="Who or what the character is, e.g. 'a girl', 'a talking cat'.")


class StoryBrief(BaseModel):
    """Classifier output: what the requester wants and how safe it is."""

    category: Category
    age_band: AgeBand
    characters: list[Character] = Field(description="Characters named or implied in the request. Empty if none.")
    setting: str = Field(description="Where the story takes place, or an empty string if unspecified.")
    must_include: list[str] = Field(description="Concrete elements the requester explicitly asked for.")
    safety: SafetyVerdict
    safety_note: str = Field(
        description="For 'reframe' or 'redirect': exactly what to change and what to keep. Empty for 'safe'."
    )


class Beat(BaseModel):
    name: str = Field(description="Short label for the beat, e.g. 'The Spark'.")
    summary: str = Field(description="One or two sentences on what happens in this beat.")


class StoryPlan(BaseModel):
    """Planner output: the story's structure, written before any prose."""

    title: str
    beats: list[Beat] = Field(description="Five to seven beats in story order, ending with the wind-down.")
    refrain: str = Field(description="A short, rhythmic line repeated through the story.")
    gentle_lesson: str = Field(description="The quiet takeaway, to be shown through events, never stated as a moral.")
    wind_down: str = Field(description="How the final scene settles into calm, safe sleepiness.")

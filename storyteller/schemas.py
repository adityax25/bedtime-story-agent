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


Score = Literal[1, 2, 3, 4, 5]


class GateCheck(BaseModel):
    # Evidence is declared before the verdict so the model reasons before deciding.
    evidence: str = Field(description="Quote the relevant passages, or explain why none exist.")
    passed: bool


class DimensionScore(BaseModel):
    critique: str = Field(description="Specific strengths and weaknesses, quoting the story.")
    score: Score


class Gates(BaseModel):
    no_frightening_content: GateCheck
    no_heavy_themes: GateCheck
    calm_ending: GateCheck


class Scores(BaseModel):
    faithfulness: DimensionScore
    coherence: DimensionScore
    reading_level: DimensionScore
    engagement: DimensionScore
    bedtime_quality: DimensionScore


class Judgement(BaseModel):
    """Judge output: pass/fail safety gates, anchored quality scores, and fixes."""

    gates: Gates
    scores: Scores
    revision_notes: list[str] = Field(
        description="One specific, actionable fix per failed gate or score below 4. Empty if none."
    )

    def failed_gates(self) -> list[str]:
        return [name for name, gate in self.gates if not gate.passed]

    def lowest_score(self) -> int:
        return min(dimension.score for _, dimension in self.scores)


class PairwiseVerdict(BaseModel):
    reasoning: str = Field(description="Compare the two stories against the criteria before choosing.")
    winner: Literal["A", "B", "tie"]


class StoryPlan(BaseModel):
    """Planner output: the story's structure, written before any prose."""

    title: str
    beats: list[Beat] = Field(description="Five to seven beats in story order, ending with the wind-down.")
    refrain: str = Field(description="A short, rhythmic line repeated through the story.")
    gentle_lesson: str = Field(description="The quiet takeaway, to be shown through events, never stated as a moral.")
    wind_down: str = Field(description="How the final scene settles into calm, safe sleepiness.")

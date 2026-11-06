"""Orchestrates the agents in order. Holds no prompts or API details itself."""

from collections.abc import Callable
from dataclasses import dataclass, replace

from storyteller import agents
from storyteller.checks import length_issue, word_count
from storyteller.schemas import Judgement, StoryBrief, StoryPlan

MAX_REVISION_ROUNDS = 2
# Every dimension must reach this score; the minimum is used rather than the
# average so that one weak dimension cannot hide behind strong ones.
PASS_SCORE = 4

StepCallback = Callable[[str], None]


@dataclass
class Evaluation:
    judgement: Judgement
    words: int
    length_note: str | None

    @property
    def passed(self) -> bool:
        return (
            not self.judgement.failed_gates()
            and self.judgement.lowest_score() >= PASS_SCORE
            and self.length_note is None
        )

    @property
    def notes(self) -> list[str]:
        extra = [self.length_note] if self.length_note else []
        return self.judgement.revision_notes + extra

    def summary(self) -> str:
        gates = ", ".join(
            f"{name}={'ok' if gate.passed else 'FAIL'}" for name, gate in self.judgement.gates
        )
        scores = ", ".join(f"{name}={dim.score}" for name, dim in self.judgement.scores)
        verdict = "PASS" if self.passed else "NEEDS REVISION"
        return f"Judge: {verdict} | {gates} | {scores} | {self.words} words"


@dataclass
class StoryResult:
    request: str
    brief: StoryBrief
    plan: StoryPlan
    story: str
    evaluation: Evaluation
    revisions: int


def _evaluate(request: str, brief: StoryBrief, story: str) -> Evaluation:
    return Evaluation(
        judgement=agents.judge(request, brief, story),
        words=word_count(story),
        length_note=length_issue(story),
    )


def _revision_wins(request: str, brief: StoryBrief, old: str, new: str) -> bool:
    """Ask the pairwise judge twice with the order swapped to cancel position bias."""
    new_second = agents.compare(request, brief, old, new).winner
    new_first = agents.compare(request, brief, new, old).winner
    votes = (new_second == "B") + (new_first == "A") - (new_second == "A") - (new_first == "B")
    return votes > 0


def _refine(
    request: str, brief: StoryBrief, story: str, on_step: StepCallback
) -> tuple[str, Evaluation, int]:
    """Judge the story and revise it until it passes or the round limit is reached."""
    on_step("Judging the story")
    evaluation = _evaluate(request, brief, story)
    on_step(evaluation.summary())

    accepted = 0
    for round_number in range(1, MAX_REVISION_ROUNDS + 1):
        if evaluation.passed:
            break
        count = len(evaluation.notes)
        on_step(f"Revising, round {round_number} ({count} note{'s' if count != 1 else ''})")
        candidate = agents.revise(brief, story, evaluation.notes)

        if not _revision_wins(request, brief, story, candidate):
            on_step("Revision was not better than the current draft; keeping the current draft")
            continue

        story = candidate
        accepted += 1
        evaluation = _evaluate(request, brief, story)
        on_step(evaluation.summary())

    if not evaluation.passed:
        on_step("Revision limit reached; showing the best draft so far")
    return story, evaluation, accepted


def generate_story(request: str, on_step: StepCallback = lambda _: None) -> StoryResult:
    on_step("Understanding the request")
    brief = agents.classify(request)
    if brief.safety != "safe":
        on_step(f"Safety {brief.safety}: {brief.safety_note}")

    on_step(f"Planning the story (category: {brief.category}, ages {brief.age_band})")
    story_plan = agents.plan(brief)

    on_step("Writing the story")
    draft = agents.write(brief, story_plan)

    story, evaluation, revisions = _refine(request, brief, draft, on_step)
    return StoryResult(request, brief, story_plan, story, evaluation, revisions)


def apply_feedback(
    result: StoryResult, feedback: str, on_step: StepCallback = lambda _: None
) -> StoryResult:
    """Revise a finished story to honor listener feedback, then re-run the judge loop.

    The listener's change is applied directly rather than gated by the pairwise
    judge, since the listener's preference is the point; the judge loop still
    enforces safety and quality on the result.
    """
    on_step("Applying the requested changes")
    revised = agents.revise(result.brief, result.story, [f"Listener request: {feedback}"])
    story, evaluation, revisions = _refine(result.request, result.brief, revised, on_step)
    return replace(result, story=story, evaluation=evaluation, revisions=result.revisions + revisions)

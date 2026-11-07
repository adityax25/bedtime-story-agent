"""Orchestrates the agents in order. Holds no prompts, API details, or display text.

Progress is reported as (event, detail) pairs so that the caller decides how to
present it: playful narration for listeners, or full internals for debugging.

Safety guarantee: a story that fails any safety gate is never returned. Quality
may degrade gracefully when the revision limit is reached; safety may not.
"""

from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, replace
from typing import Literal

from storyteller import agents
from storyteller.checks import exceeds_length_limit, length_issue, word_count
from storyteller.schemas import Judgement, StoryBrief, StoryPlan

MAX_REVISION_ROUNDS = 2
# Every dimension must reach this score; the minimum is used rather than the
# average so that one weak dimension cannot hide behind strong ones.
PASS_SCORE = 4

Event = Literal[
    "classify",
    "safety",
    "plan",
    "write",
    "judge",
    "verdict",
    "revise",
    "revision_accepted",
    "revision_rejected",
    "limit_reached",
    "fresh_draft",
    "interpret",
    "interpretation",
    "feedback",
    "safety_fallback",
]
StepCallback = Callable[[Event, str], None]


def _ignore(event: Event, detail: str) -> None:
    pass


class UnsafeStoryError(RuntimeError):
    """Raised when no draft passes the safety gates, so no story can be shown."""


@dataclass
class Evaluation:
    judgement: Judgement
    words: int
    length_note: str | None

    @property
    def safe(self) -> bool:
        return not self.judgement.failed_gates()

    @property
    def passed(self) -> bool:
        return self.safe and self.judgement.lowest_score() >= PASS_SCORE and self.length_note is None

    @property
    def notes(self) -> list[str]:
        extra = [self.length_note] if self.length_note else []
        return self.judgement.revision_notes + extra

    def report(self) -> str:
        """Multi-line scorecard with evidence for failed gates and every revision note."""
        verdict = "PASS" if self.passed else "NEEDS REVISION"
        scores = ", ".join(f"{name}={dim.score}" for name, dim in self.judgement.scores)
        lines = [f"{verdict} | {scores} | {self.words} words"]
        for name, gate in self.judgement.gates:
            lines.append(f"  gate {name}: {'ok' if gate.passed else 'FAIL'}")
            if not gate.passed:
                lines.append(f"    evidence: {gate.evidence}")
        lines.extend(f"  note {i}: {note}" for i, note in enumerate(self.notes, start=1))
        return "\n".join(lines)


@dataclass
class StoryResult:
    request: str
    brief: StoryBrief
    plan: StoryPlan
    story: str
    evaluation: Evaluation
    revisions: int


@dataclass
class FeedbackOutcome:
    result: StoryResult
    applied: bool
    # The Story Owl's reply, shown only when the story was not changed.
    reply: str | None


def _evaluate(request: str, brief: StoryBrief, story: str) -> Evaluation:
    return Evaluation(
        judgement=agents.judge(request, brief, story),
        words=word_count(story),
        length_note=length_issue(story),
    )


def _revision_wins(
    request: str, brief: StoryBrief, old: str, new: str, notes: list[str]
) -> tuple[bool, str]:
    """Ask the pairwise judge twice with the order swapped to cancel position bias.

    Returns whether the revision wins on net, and both verdicts' reasoning.
    """
    with ThreadPoolExecutor(max_workers=2) as pool:
        new_as_b = pool.submit(agents.compare, request, brief, old, new, notes)
        new_as_a = pool.submit(agents.compare, request, brief, new, old, notes)
        verdict_b, verdict_a = new_as_b.result(), new_as_a.result()

    votes = (
        (verdict_b.winner == "B")
        + (verdict_a.winner == "A")
        - (verdict_b.winner == "A")
        - (verdict_a.winner == "B")
    )
    reasoning = (
        f"revision as B: winner={verdict_b.winner}: {verdict_b.reasoning}\n"
        f"  revision as A: winner={verdict_a.winner}: {verdict_a.reasoning}"
    )
    return votes > 0, reasoning


def _refine(
    request: str, brief: StoryBrief, story: str, on_step: StepCallback
) -> tuple[str, Evaluation, int]:
    """Judge and revise until the story passes or the round limit is reached.

    If the final draft fails a safety gate but an earlier draft passed every
    gate, the earlier draft is returned instead.
    """
    on_step("judge", "draft")
    evaluation = _evaluate(request, brief, story)
    on_step("verdict", evaluation.report())
    best_safe = (story, evaluation) if evaluation.safe else None

    accepted = 0
    for round_number in range(1, MAX_REVISION_ROUNDS + 1):
        if evaluation.passed:
            break
        on_step("revise", f"round {round_number}")
        candidate = agents.revise(brief, story, evaluation.notes)

        candidate_evaluation: Evaluation | None = None
        if evaluation.safe and exceeds_length_limit(candidate) and not exceeds_length_limit(story):
            # Length is a fact, so code decides it; asking a model to weigh it
            # against other criteria produced inconsistent verdicts.
            wins, reasoning = False, f"revision grew to {word_count(candidate)} words, past the length limit"
        elif evaluation.safe:
            wins, reasoning = _revision_wins(request, brief, story, candidate, evaluation.notes)
        else:
            # The gate judge is the single source of truth for safety, so an
            # unsafe draft's revision is accepted on the gate judge's re-check
            # rather than on the pairwise judge's separate sense of safety.
            on_step("judge", "safety re-check of the revision")
            candidate_evaluation = _evaluate(request, brief, candidate)
            on_step("verdict", candidate_evaluation.report())
            wins = len(candidate_evaluation.judgement.failed_gates()) < len(evaluation.judgement.failed_gates())
            reasoning = (
                "gate judge: the revision fails fewer safety gates"
                if wins
                else "gate judge: the revision does not fix the failing safety gates"
            )

        if not wins:
            on_step("revision_rejected", reasoning)
            continue
        on_step("revision_accepted", reasoning)

        story = candidate
        accepted += 1
        if candidate_evaluation is None:
            on_step("judge", f"revision {accepted}")
            candidate_evaluation = _evaluate(request, brief, story)
            on_step("verdict", candidate_evaluation.report())
        evaluation = candidate_evaluation
        if evaluation.safe:
            best_safe = (story, evaluation)

    if not evaluation.passed:
        on_step("limit_reached", "using the best draft so far")
    if not evaluation.safe and best_safe:
        on_step("safety_fallback", "final draft failed a gate; using the last draft that passed all gates")
        story, evaluation = best_safe
    return story, evaluation, accepted


def generate_story(request: str, on_step: StepCallback = _ignore) -> StoryResult:
    on_step("classify", request)
    brief = agents.classify(request)
    if brief.safety != "safe":
        on_step("safety", f"{brief.safety}: {brief.safety_note}")

    on_step("plan", brief.category)
    story_plan = agents.plan(brief)

    on_step("write", f"category={brief.category}, ages={brief.age_band}, title={story_plan.title}")
    draft = agents.write(brief, story_plan)
    story, evaluation, revisions = _refine(request, brief, draft, on_step)

    if not evaluation.safe:
        on_step("fresh_draft", "no draft passed the safety gates; writing a fresh draft from the plan")
        draft = agents.write(brief, story_plan)
        story, evaluation, revisions = _refine(request, brief, draft, on_step)
        if not evaluation.safe:
            raise UnsafeStoryError("No draft passed the safety gates.")

    return StoryResult(request, brief, story_plan, story, evaluation, revisions)


def apply_feedback(result: StoryResult, feedback: str, on_step: StepCallback = _ignore) -> FeedbackOutcome:
    """Interpret listener feedback, then revise and re-judge the story if appropriate.

    Raw feedback never reaches the reviser: the interpreter turns it into a
    vetted instruction, asks for clarification, or declines it. An applied
    change is not gated by the pairwise judge, since the listener's preference
    is the point, but it must still pass the safety gates or the previous
    story is kept.
    """
    on_step("interpret", feedback)
    interpretation = agents.interpret(result.story, feedback)
    on_step(
        "interpretation",
        f"kind={interpretation.kind}, safety={interpretation.safety}, "
        f"instruction={interpretation.instruction or 'None'}",
    )

    if interpretation.kind == "unclear" or interpretation.safety == "redirect":
        return FeedbackOutcome(result, applied=False, reply=interpretation.reply)
    if interpretation.safety == "reframe":
        on_step("safety", f"reframe: {interpretation.instruction}")

    on_step("feedback", interpretation.instruction)
    revised = agents.revise(result.brief, result.story, [f"Listener request: {interpretation.instruction}"])
    story, evaluation, revisions = _refine(result.request, result.brief, revised, on_step)

    if not evaluation.safe:
        on_step("safety_fallback", "changed story failed a safety gate; keeping the previous story")
        return FeedbackOutcome(result, applied=False, reply=None)

    updated = replace(result, story=story, evaluation=evaluation, revisions=result.revisions + revisions)
    # The updated story is the response; the interpreter's acknowledgement was
    # written before the editor chose details and could contradict them.
    return FeedbackOutcome(updated, applied=True, reply=None)

"""Tests for the deterministic logic around the model calls. No API access needed."""

from unittest.mock import patch

from storyteller import pipeline
from storyteller.checks import TARGET_WORDS, length_issue, reading_grade, word_count
from storyteller.narration import friendly_message
from storyteller.prompts import load_prompt
from storyteller.schemas import (
    Category,
    DimensionScore,
    FeedbackInterpretation,
    GateCheck,
    Gates,
    Judgement,
    PairwiseVerdict,
    Scores,
)


def make_judgement(gate_passed: bool = True, score: int = 4, notes: list[str] | None = None) -> Judgement:
    gate = GateCheck(evidence="quoted passage", passed=gate_passed)
    dim = DimensionScore(critique="critique", score=score)
    return Judgement(
        gates=Gates(no_frightening_content=gate, no_heavy_themes=gate, calm_ending=gate),
        scores=Scores(faithfulness=dim, coherence=dim, reading_level=dim, engagement=dim, bedtime_quality=dim),
        revision_notes=notes or [],
    )


def make_evaluation(judgement: Judgement, words: int = 500) -> pipeline.Evaluation:
    story = "word " * words
    return pipeline.Evaluation(judgement, word_count(story), length_issue(story))


def make_result(story: str) -> pipeline.StoryResult:
    return pipeline.StoryResult(
        request="request", brief=None, plan=None, story=story,
        evaluation=make_evaluation(make_judgement()), revisions=0,
    )


def make_interpretation(kind: str = "change", safety: str = "safe") -> FeedbackInterpretation:
    return FeedbackInterpretation(
        analysis="", kind=kind, safety=safety, instruction="add a friendly dragon", reply="Hoo!"
    )


class TestPassRule:
    def test_passes_when_gates_pass_scores_meet_bar_and_length_fits(self):
        assert make_evaluation(make_judgement()).passed

    def test_fails_on_any_gate_regardless_of_scores(self):
        assert not make_evaluation(make_judgement(gate_passed=False, score=5)).passed

    def test_fails_when_one_dimension_is_below_bar(self):
        judgement = make_judgement(score=5)
        judgement.scores.coherence.score = 3
        assert not make_evaluation(judgement).passed

    def test_fails_when_too_long(self):
        assert not make_evaluation(make_judgement(score=5), words=800).passed

    def test_length_note_is_added_to_judge_notes(self):
        evaluation = make_evaluation(make_judgement(notes=["fix the bridge"]), words=800)
        assert evaluation.notes[0] == "fix the bridge"
        assert "800 words" in evaluation.notes[1]


class TestLengthCheck:
    def test_within_tolerance_is_fine(self):
        low, high = TARGET_WORDS
        assert length_issue("w " * low) is None
        assert length_issue("w " * int(high * 1.05)) is None

    def test_flags_short_and_long(self):
        assert "Expand" in length_issue("w " * 100)
        assert "Tighten" in length_issue("w " * 900)


class TestReadingGrade:
    def test_simple_text_scores_lower_than_complex_text(self):
        simple = "The cat sat. The cat was big. It had a hat."
        complex_ = "Notwithstanding considerable meteorological uncertainty, the expedition proceeded."
        assert reading_grade(simple) < reading_grade(complex_)


class TestPositionSwappedPairwise:
    """The two pairwise calls run in parallel, so fakes answer by argument, not call order."""

    def run(self, judge) -> bool:
        with patch.object(pipeline.agents, "compare", side_effect=judge):
            wins, _ = pipeline._revision_wins("request", None, "old", "new", ["note"])
        return wins

    @staticmethod
    def verdict(winner: str) -> PairwiseVerdict:
        return PairwiseVerdict(reasoning="", winner=winner)

    def test_accepts_when_new_wins_both_orders(self):
        assert self.run(lambda req, brief, a, b, notes: self.verdict("A" if a == "new" else "B"))

    def test_rejects_pure_position_bias(self):
        # A judge that always prefers one position cancels out.
        assert not self.run(lambda *args: self.verdict("A"))
        assert not self.run(lambda *args: self.verdict("B"))

    def test_accepts_a_win_plus_a_tie(self):
        assert self.run(lambda req, brief, a, b, notes: self.verdict("A" if a == "new" else "tie"))

    def test_rejects_when_old_wins(self):
        assert not self.run(lambda req, brief, a, b, notes: self.verdict("A" if a == "old" else "B"))


class TestSafetyGuarantee:
    """A story that fails a safety gate must never be returned."""

    def test_refine_falls_back_to_last_safe_draft(self):
        # Draft is safe but low quality; both accepted revisions then fail a gate.
        unsafe = make_judgement(gate_passed=False, score=5)
        judgements = iter([make_judgement(score=3), unsafe, unsafe])
        with (
            patch.object(pipeline.agents, "judge", side_effect=lambda *a: next(judgements)),
            patch.object(pipeline.agents, "revise", return_value="unsafe revision"),
            patch.object(pipeline, "_revision_wins", return_value=(True, "")),
        ):
            story, evaluation, _ = pipeline._refine("request", None, "safe draft", lambda *a: None)
        assert story == "safe draft"
        assert evaluation.safe

    def test_unsafe_draft_revision_is_decided_by_gate_judge_not_pairwise(self):
        safe_revision = "calm " * 500
        judgements = iter([make_judgement(gate_passed=False), make_judgement()])
        with (
            patch.object(pipeline.agents, "judge", side_effect=lambda *a: next(judgements)),
            patch.object(pipeline.agents, "revise", return_value=safe_revision),
            patch.object(pipeline, "_revision_wins") as pairwise,
        ):
            story, evaluation, accepted = pipeline._refine("request", None, "scary " * 500, lambda *a: None)
        pairwise.assert_not_called()
        assert story == safe_revision
        assert evaluation.passed
        assert accepted == 1

    def test_revision_that_breaks_length_limit_is_rejected_without_pairwise(self):
        with (
            patch.object(pipeline.agents, "judge", return_value=make_judgement(score=3)),
            patch.object(pipeline.agents, "revise", return_value="word " * 900),
            patch.object(pipeline, "_revision_wins") as pairwise,
        ):
            story, _, accepted = pipeline._refine("request", None, "word " * 500, lambda *a: None)
        pairwise.assert_not_called()
        assert accepted == 0
        assert story == "word " * 500

    def test_feedback_that_ends_unsafe_keeps_previous_story(self):
        previous = make_result("previous story")
        with (
            patch.object(pipeline.agents, "interpret", return_value=make_interpretation()),
            patch.object(pipeline.agents, "revise", return_value="changed story"),
            patch.object(pipeline.agents, "judge", return_value=make_judgement(gate_passed=False)),
            patch.object(pipeline, "_revision_wins", return_value=(False, "")),
        ):
            outcome = pipeline.apply_feedback(previous, "add a dragon")
        assert not outcome.applied
        assert outcome.result.story == "previous story"

    def test_unclear_feedback_asks_instead_of_rewriting(self):
        previous = make_result("previous story")
        with (
            patch.object(pipeline.agents, "interpret", return_value=make_interpretation(kind="unclear")),
            patch.object(pipeline.agents, "revise") as revise,
        ):
            outcome = pipeline.apply_feedback(previous, "Otto says Pickle is right")
        revise.assert_not_called()
        assert not outcome.applied
        assert outcome.reply

    def test_redirected_feedback_never_reaches_the_reviser(self):
        previous = make_result("previous story")
        with (
            patch.object(pipeline.agents, "interpret", return_value=make_interpretation(safety="redirect")),
            patch.object(pipeline.agents, "revise") as revise,
        ):
            outcome = pipeline.apply_feedback(previous, "something inappropriate")
        revise.assert_not_called()
        assert outcome.result.story == "previous story"


class TestPrompts:
    def test_every_agent_prompt_loads(self):
        for name in ["classifier", "planner", "storyteller", "judge", "reviser", "pairwise", "interpreter"]:
            assert load_prompt(name)

    def test_every_category_has_a_strategy_and_plan_message(self):
        for category in Category.__args__:
            assert load_prompt(f"strategies/{category}")
            assert friendly_message("plan", category)

    def test_internal_events_stay_hidden_from_listeners(self):
        for event in ["verdict", "revision_accepted", "revision_rejected", "limit_reached", "safety_fallback"]:
            assert friendly_message(event, "detail") is None

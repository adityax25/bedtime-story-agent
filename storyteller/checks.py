"""Deterministic checks that code performs better than a model, such as counting."""

TARGET_WORDS = (400, 600)
# Small overshoots are not worth a revision round.
TOLERANCE = 0.1


def word_count(text: str) -> int:
    return len(text.split())


def length_issue(story: str) -> str | None:
    """Return a revision note when the story is clearly outside the target length."""
    words = word_count(story)
    low, high = TARGET_WORDS
    if words < low * (1 - TOLERANCE):
        return (
            f"The story is {words} words. Expand it to {low} to {high} words by deepening "
            "existing scenes with dialogue and sensory detail, not by adding new plot."
        )
    if words > high * (1 + TOLERANCE):
        return (
            f"The story is {words} words. Tighten it to {low} to {high} words by trimming the "
            "least essential sentences and scenes, keeping every beat and the refrain."
        )
    return None

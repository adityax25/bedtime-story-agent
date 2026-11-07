"""Deterministic checks that code performs better than a model, such as counting."""

import re

TARGET_WORDS = (400, 700)
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


def exceeds_length_limit(story: str) -> bool:
    """True when the story is longer than the target plus tolerance."""
    return word_count(story) > TARGET_WORDS[1] * (1 + TOLERANCE)


def _syllables(word: str) -> int:
    # Vowel-group heuristic; accurate enough to compare texts, not to grade one word.
    word = word.lower()
    groups = len(re.findall(r"[aeiouy]+", word))
    if word.endswith("e") and not word.endswith("le") and groups > 1:
        groups -= 1
    return max(groups, 1)


def reading_grade(text: str) -> float:
    """Flesch-Kincaid grade level: an objective reading-difficulty signal beside the judge."""
    words = re.findall(r"[A-Za-z']+", text)
    sentences = max(len(re.findall(r"[.!?]+", text)), 1)
    if not words:
        return 0.0
    syllables = sum(_syllables(w) for w in words)
    return round(0.39 * len(words) / sentences + 11.8 * syllables / len(words) - 15.59, 1)

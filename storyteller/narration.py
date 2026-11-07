"""Listener-facing messages. Internals stay hidden unless verbose mode is on."""

import random

from storyteller.pipeline import Event

UNSAFE_CHANGE_MESSAGE = (
    "🦉 Hoo! I tried, but I couldn't make that change and keep the story cozy for bedtime. "
    "Want to try a different idea?"
)
NO_SAFE_STORY_MESSAGE = (
    "🦉 Hoo! The Story Owl couldn't find a cozy enough way to tell that one tonight. "
    "Could you try a different story wish?"
)

_MESSAGES: dict[str, list[str]] = {
    "classify": [
        "🌙 Listening carefully to your story wish...",
        "🌙 Tucking your idea under the story pillow...",
    ],
    "safety": [
        "🧸 Making this one extra cozy for bedtime...",
        "🧸 Sprinkling in some gentleness so it is just right for tonight...",
    ],
    "write": [
        "✏️  Dipping the quill in moonlight and writing your story...",
        "✏️  Writing your story, one twinkly word at a time...",
    ],
    "fresh_draft": [
        "✏️  Hmm, starting a fresh page to make it just right...",
    ],
    "judge": [
        "🦉 The wise old Story Owl is reading it over...",
        "🦉 The Story Owl is checking every page...",
    ],
    "revise": [
        "🪄 Polishing a few sparkly bits...",
        "🪄 The Story Owl suggested a little touch-up...",
    ],
    "interpret": [
        "🦉 The Story Owl is thinking about your idea...",
    ],
    "feedback": [
        "🎨 Stirring your ideas into the story...",
        "🎨 Rewriting with your changes...",
    ],
}

_PLAN_BY_CATEGORY: dict[str, str] = {
    "adventure": "🗺️  Packing a map, a lantern, and a brave heart...",
    "friendship_feelings": "🤝 Gathering some very good friends...",
    "funny_silly": "🤪 Tickling the silly bone...",
    "animals_nature": "🦔 Waking up the forest critters...",
    "calm_cozy": "☁️  Fluffing the pillows and dimming the lights...",
}


def friendly_message(event: Event, detail: str) -> str | None:
    """Return a playful message for an event, or None for events listeners need not see."""
    if event == "plan":
        return _PLAN_BY_CATEGORY.get(detail, "🗺️  Sketching out the story...")
    options = _MESSAGES.get(event)
    return random.choice(options) if options else None

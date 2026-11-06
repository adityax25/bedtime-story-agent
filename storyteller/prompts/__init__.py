"""Prompt files live beside this module so they can be reviewed without reading code."""

from pathlib import Path

_PROMPT_DIR = Path(__file__).parent


def load_prompt(name: str) -> str:
    """Load a prompt by path relative to this directory, without the .md suffix."""
    return (_PROMPT_DIR / f"{name}.md").read_text(encoding="utf-8").strip()

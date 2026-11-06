"""Single gateway to the Anthropic API. Every agent calls the model through here."""

from typing import Literal, TypeVar

import anthropic
from pydantic import BaseModel

# Fixed by the assignment: every agent, including the judge, runs on this model.
MODEL = "claude-haiku-5-5"

Effort = Literal["low", "medium", "high"]
SchemaT = TypeVar("SchemaT", bound=BaseModel)

_client: anthropic.Anthropic | None = None


class ModelOutputError(RuntimeError):
    """Raised when the model stops without producing a usable answer."""


def _get_client() -> anthropic.Anthropic:
    # Lazy so that importing the package never requires an API key.
    global _client
    if _client is None:
        _client = anthropic.Anthropic()
    return _client


def _check_stop_reason(response: anthropic.types.Message) -> None:
    if response.stop_reason == "refusal":
        raise ModelOutputError("The model declined this request.")
    if response.stop_reason == "max_tokens":
        raise ModelOutputError("The response hit max_tokens and was cut off.")


def call_model(
    prompt: str,
    *,
    system: str | None = None,
    effort: Effort = "medium",
    max_tokens: int = 16000,
) -> str:
    """Return the model's plain-text reply to a single user prompt.

    Sampling parameters such as temperature are rejected by Haiku 5.5, so
    behavior is steered through the prompt and the effort level instead.
    """
    kwargs = {"system": system} if system else {}
    response = _get_client().messages.create(
        model=MODEL,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
        output_config={"effort": effort},
        **kwargs,
    )
    _check_stop_reason(response)
    # Adaptive thinking adds thinking blocks to the content; only text blocks are the answer.
    return "".join(block.text for block in response.content if block.type == "text").strip()


def call_structured(
    prompt: str,
    schema: type[SchemaT],
    *,
    system: str | None = None,
    effort: Effort = "medium",
    max_tokens: int = 16000,
) -> SchemaT:
    """Return the model's reply parsed and validated against a Pydantic schema."""
    kwargs = {"system": system} if system else {}
    response = _get_client().messages.parse(
        model=MODEL,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
        output_format=schema,
        output_config={"effort": effort},
        **kwargs,
    )
    _check_stop_reason(response)
    if response.parsed_output is None:
        raise ModelOutputError(f"The model returned no valid {schema.__name__}.")
    return response.parsed_output

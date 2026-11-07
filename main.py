"""Bedtime story generator for children aged 5 to 10, with an LLM judge in the loop.

Usage: python main.py [--verbose]

Before submitting the assignment, describe here in a few sentences what you would have built next if you spent 2 more hours on this project:

"""

import argparse
import sys

import anthropic
from dotenv import load_dotenv

from storyteller.llm import ModelOutputError
from storyteller.narration import NO_SAFE_STORY_MESSAGE, UNSAFE_CHANGE_MESSAGE, friendly_message
from storyteller.pipeline import Event, StepCallback, UnsafeStoryError, apply_feedback, generate_story

example_requests = "A story about a girl named Alice and her best friend Bob, who happens to be a cat."


def make_reporter(verbose: bool) -> StepCallback:
    # Progress goes to stderr so stdout carries only the story.
    def report(event: Event, detail: str) -> None:
        message = f"[{event}] {detail}" if verbose else friendly_message(event, detail)
        if message:
            print(message, file=sys.stderr)

    return report


def ask(prompt: str) -> str:
    try:
        return input(prompt).strip()
    except EOFError:
        return ""


def run(verbose: bool) -> None:
    report = make_reporter(verbose)
    request = ask("What kind of story would you like tonight? ")
    if not request:
        request = example_requests
        print(f"No idea yet? Here is one: {request}", file=sys.stderr)

    try:
        result = generate_story(request, on_step=report)
    except UnsafeStoryError:
        print(f"\n{NO_SAFE_STORY_MESSAGE}\n")
        return
    print(f"\n{result.story}\n")

    while feedback := ask("Want to change anything? Tell me, or press Enter to say goodnight: "):
        try:
            outcome = apply_feedback(result, feedback, on_step=report)
        except (anthropic.APIError, ModelOutputError) as err:
            # Keep the session and the current story alive; the listener can retry.
            print("Oops, the story elves dropped their pencils. Could you ask that again?", file=sys.stderr)
            if verbose:
                print(f"[error] {err}", file=sys.stderr)
            continue

        if outcome.reply:
            print(f"\n🦉 {outcome.reply}")
        if outcome.applied:
            result = outcome.result
            print(f"\n{result.story}\n")
        elif not outcome.reply:
            print(f"\n{UNSAFE_CHANGE_MESSAGE}\n")
        else:
            print()

    print("Goodnight! 🌙")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="show judge scores, evidence, and revision notes"
    )
    args = parser.parse_args()
    load_dotenv()

    try:
        run(args.verbose)
    except anthropic.AuthenticationError:
        print("Authentication failed. Check ANTHROPIC_API_KEY in .env.", file=sys.stderr)
        return 1
    except anthropic.APIConnectionError:
        print("Could not reach the Anthropic API. Check the network connection.", file=sys.stderr)
        return 1
    except (anthropic.APIStatusError, ModelOutputError) as err:
        print(f"Story generation failed: {err}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nGoodnight! 🌙", file=sys.stderr)
        return 130
    return 0


if __name__ == "__main__":
    sys.exit(main())

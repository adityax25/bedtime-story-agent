import sys

import anthropic
from dotenv import load_dotenv

from storyteller.llm import ModelOutputError
from storyteller.pipeline import apply_feedback, generate_story

"""
Before submitting the assignment, describe here in a few sentences what you would have built next if you spent 2 more hours on this project:

"""

example_requests = "A story about a girl named Alice and her best friend Bob, who happens to be a cat."


def show_step(message: str) -> None:
    # Progress goes to stderr so stdout carries only the story.
    print(f"... {message}", file=sys.stderr)


def ask(prompt: str) -> str:
    try:
        return input(prompt).strip()
    except EOFError:
        return ""


def run() -> None:
    request = ask("What kind of story do you want to hear? ")
    if not request:
        request = example_requests
        show_step(f"No request given, using the example: {request}")

    result = generate_story(request, on_step=show_step)
    print(f"\n{result.story}\n")

    while feedback := ask("Want any changes? Describe them, or press Enter to finish: "):
        result = apply_feedback(result, feedback, on_step=show_step)
        print(f"\n{result.story}\n")

    print("Goodnight!")


def main() -> int:
    load_dotenv()
    try:
        run()
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
        print("\nGoodnight!", file=sys.stderr)
        return 130
    return 0


if __name__ == "__main__":
    sys.exit(main())

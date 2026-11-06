import sys

import anthropic
from dotenv import load_dotenv

from storyteller.llm import ModelOutputError, call_model

"""
Before submitting the assignment, describe here in a few sentences what you would have built next if you spent 2 more hours on this project:

"""

example_requests = "A story about a girl named Alice and her best friend Bob, who happens to be a cat."


def main() -> int:
    load_dotenv()
    user_input = input("What kind of story do you want to hear? ")
    try:
        response = call_model(user_input)
    except anthropic.AuthenticationError:
        print("Authentication failed. Check ANTHROPIC_API_KEY in .env.", file=sys.stderr)
        return 1
    except anthropic.APIConnectionError:
        print("Could not reach the Anthropic API. Check the network connection.", file=sys.stderr)
        return 1
    except (anthropic.APIStatusError, ModelOutputError) as err:
        print(f"Story generation failed: {err}", file=sys.stderr)
        return 1
    print(response)
    return 0


if __name__ == "__main__":
    sys.exit(main())

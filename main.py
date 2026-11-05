import argparse
from urllib.error import URLError

from agent import run_agent
from ollama_model import OllamaModel


def chat():
    history = []

    while True:
        try:
            question = input("> ").strip()
        except EOFError:
            return

        if not question or question.casefold() in {"exit", "quit"}:
            return

        # A new model per turn: its queued tool calls must not leak into the next question.
        print(run_agent(question, OllamaModel(), history=history))


def main():
    parser = argparse.ArgumentParser(
        description="CityWheels AI help desk",
    )
    parser.add_argument(
        "question",
        nargs="?",
        help="Your question for CityWheels; omit it to start a chat",
    )
    args = parser.parse_args()

    try:
        if args.question is None:
            chat()
        else:
            print(run_agent(args.question, OllamaModel()))
    except (URLError, TimeoutError) as error:
        print(f"Could not connect to Ollama: {error}")
        print("Make sure Ollama is running and the model is downloaded.")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
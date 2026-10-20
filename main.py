import argparse
from urllib.error import URLError

from agent import run_agent
from ollama_model import OllamaModel


def main():
    parser = argparse.ArgumentParser(
        description="CityWheels AI help desk",
    )
    parser.add_argument(
        "question",
        help="Your question for CityWheels",
    )
    args = parser.parse_args()

    try:
        answer = run_agent(args.question, OllamaModel())
    except (URLError, TimeoutError) as error:
        print(f"Could not connect to Ollama: {error}")
        print("Make sure Ollama is running and the model is downloaded.")
        return 1

    print(answer)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
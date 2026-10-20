import json
from pathlib import Path

from agent import run_agent
from ollama_model import OllamaModel


ROOT = Path(__file__).resolve().parent


class TrackedModel:
    def __init__(self):
        self.model = OllamaModel()
        self.tool_calls = []

    def respond(self, messages):
        response = self.model.respond(messages)

        if response["type"] == "tool_call":
            self.tool_calls.append(response["name"])

        return response


def main():
    questions = json.loads(
        (ROOT / "eval" / "questions.json").read_text(encoding="utf-8")
    )

    passed = 0
    report = [
        "# Agent evaluation",
        "",
        "Automated checks are partial; answers need semantic review.",
        "",
    ]

    for case in questions:
        print(f"Running: {case['id']}", flush=True)
        model = TrackedModel()
        failures = []

        try:
            answer = run_agent(case["question"], model)
            normalized = answer.casefold()

            for text in case["required"]:
                if text.casefold() not in normalized:
                    failures.append(f"Missing required text: {text}")

            for text in case["forbidden"]:
                if text.casefold() in normalized:
                    failures.append(f"Contains forbidden text: {text}")

            expected_tool = case["expected_tool"]

            if expected_tool and expected_tool not in model.tool_calls:
                failures.append(f"Expected tool not called: {expected_tool}")

        except Exception as error:
            answer = ""
            failures.append(f"{type(error).__name__}: {error}")

        status = "FAIL" if failures else "PASS"
        passed += not failures

        report.extend([
            f"## {case['id']}: {status}",
            "",
            f"Question: {case['question']}",
            "",
            f"Expected meaning: {case['review']}",
            "",
            f"Tools: {', '.join(model.tool_calls) or 'none'}",
            "",
            "Answer:",
            "",
            answer or "(No answer)",
            "",
            f"Checks: {'; '.join(failures) if failures else 'Passed automated checks'}",
            "",
            "Manual review: PENDING",
            "",
        ])

        print(f"  {status}", flush=True)

    report.insert(2, f"Automated checks passed: {passed}/{len(questions)}")
    report.insert(3, "")
    report.insert(4, f"Model: {OllamaModel().model}")
    report.insert(5, "")

    output = ROOT / "eval" / "results.md"
    output.write_text("\n".join(report), encoding="utf-8")

    print(f"\nAutomated checks passed: {passed}/{len(questions)}")
    print(f"Report saved to: {output}")

    return 0 if passed == len(questions) else 1


if __name__ == "__main__":
    raise SystemExit(main())
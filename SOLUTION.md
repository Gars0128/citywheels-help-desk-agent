# CityWheels help desk

## Setup and commands

Install Python 3.10+ and Ollama first. I used only the Python standard library, so there are no pip packages to install.

Run these commands from the project folder:

```powershell
ollama pull qwen3:4b
# If Ollama is not running, start `ollama serve` in another terminal.
python main.py "What is the total refund for CW-1002?"
python -m unittest -v
python evaluate.py
```

The agent accepts one question per run. The tests work offline. The evaluation needs Ollama and the downloaded model.

I also kept `check_ollama.py` as an early debugging script. Run `python check_ollama.py` to check a refund tool call directly with `qwen2.5:3b` at `localhost:11434`. It prints the request, tool result and model response.

Local Ollama does not need an API key. `.env.example` lists the optional settings. To change them, set environment variables in your shell:

```powershell
$env:OLLAMA_MODEL = "qwen3:4b"
$env:OLLAMA_URL = "http://localhost:11434/api/chat"
```

The app does not load `.env` files automatically. No keys are included in the project. I kept the fixed time from the supplied README: **2026-06-10 09:00 +02:00**, Europe/Warsaw. Refunds use this time instead of the computer's clock.

## Model and how it works

I used Ollama because I could run it locally without paying for an API. I started with `qwen2.5:3b`. It made mistakes on the age rules, even when it received the correct policy section. I later switched to `qwen3:4b`, which handled the age and helmet questions better. It is now the default model, although its answers are slower.

I called Ollama's HTTP API directly. A framework did not seem necessary for this small loop: the model chooses a tool, Python runs it, and the result goes back to the model. This continues until the model gives a final answer or reaches the limit of eight steps.

There are three tools:

- `get_booking` reads the booking JSON. If the ID does not exist, it returns a clear not-found result.
- `calculate_refund` calculates the amount in Python using `Decimal`, not the model. For confirmed bookings, the rental refund is 100% at least 48 hours before the start, 50% from 24 to less than 48 hours, and 0% below 24 hours. It adds the full deposit but excludes the booking fee. Voucher payments stay vouchers. Other booking statuses get no additional refund.
- `search_policies` finds matching words in Markdown sections. It handles a few word variants and gives heading matches more weight. It returns up to three sections with their source filenames.

The system instructions tell the model to use these tools, keep the conditions from the policies, and send unsupported questions to staff. They also say not to claim that a booking was cancelled or a refund was sent. Weather exceptions need a staff decision. The tools only read data and calculate amounts.

If the model answers without calling a tool, or after only empty policy searches, the code returns a fixed refusal with the staff contact. This helps, but it cannot catch every wrong answer based on an irrelevant result.

## Tests, results and fixes

The latest test run passed **23 offline tests**. They cover the tools, refund rules and exact time boundaries, fake-model agent loops, the Ollama adapter, and mistakes in the evaluation checks.

`eval/questions.json` contains 11 questions, including three refund calculations and two questions the agent should not answer. The evaluation checks tool calls, required facts and forbidden claims. It saves answers to `eval/results.md` and returns exit code 1 if any automated check fails. Running it again replaces the report and resets the review notes.

An earlier saved report for `qwen2.5:3b` showed **9/11 automated checks passed**, but that score was misleading. It included wrong answers about age limits and an already cancelled booking. The fixes included better search ranking, returning the actual booking status, and clearer instructions about age rules and refund processing. The evaluation also needed stricter checks for incorrect claims.

The latest `qwen3:4b` run passed **11/11 automated checks**, but only **10/11 in the AI-assisted review of meaning**. The voucher answer correctly says 73 EUR, but adds that this refund is available if the customer cancels before the start. This suggests the amount stays the same until then, although it changes at the 48/24-hour boundaries. The calculation is correct for the fixed current time; the extra condition added by the model is the problem. This failure is still recorded in the report.

## AI assistance

I used Codex during development to help with writing and reviewing code, debugging, tests and documentation. The suggestions were checked against the task requirements, and the changes were tested instead of assuming they were correct.

For example, an earlier evaluation passed a wrong answer about the minimum age for renting an e-bike. The answer mentioned 16, but still incorrectly allowed a 14-year-old to rent one. Comparing the actual answer with the rental policy showed the mistake. With Codex's help, I updated the evaluation checks and added a regression test for this case.

This was a useful reminder that passing automated checks does not always mean the answer is correct. I also used AI to help review the final answers, so I recorded that separately from the automated test results. This was an AI-assisted review, not an independent human review.

## Limitations and what I would do next

This is a read-only demo with example bookings. Word matching can miss questions written in a different way, and the model can add details that are not in the documents. The fixed refusal is in English. Connection errors are reported, but malformed model responses and tool calls are not automatically repaired. There is no conversation memory or authentication.

With more time, I would add questions about changing refund amounts over time and more ways of asking the same question. I would also improve handling of invalid tool calls and compare a stronger model or a more restricted format for refund answers. Real booking data would need authentication before the agent could be used by customers.

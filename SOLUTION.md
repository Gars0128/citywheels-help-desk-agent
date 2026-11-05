# CityWheels help desk

## Setup and commands

Install Python 3.10+ and Ollama first. I used only the Python standard library, so there are no pip packages to install.

Run these commands from the project folder:

```powershell
ollama pull qwen3:4b
# If Ollama is not running, start `ollama serve` in another terminal.
python main.py "What is the total refund for CW-1002?"
python main.py
python -m unittest -v
python evaluate.py
```

With a question, the agent answers once. Without one, it starts a chat that keeps the conversation, so a customer can follow up with "And if I cancel tomorrow?". An empty line or `exit` ends the chat, and the conversation is not saved. The tests work offline, and GitHub Actions runs them on every push. The evaluation needs Ollama and the downloaded model.

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
- `calculate_refund` calculates the amount in Python using `Decimal`, not the model. For confirmed bookings, the rental refund is 100% at least 48 hours before the start, 50% from 24 to less than 48 hours, and 0% below 24 hours. It adds the full deposit but excludes the booking fee. Voucher payments stay vouchers. Other booking statuses get no additional refund. An optional `cancel_at` argument calculates the refund for a future cancellation time. Past or invalid times return an error, and a time after the rental starts returns no refund.
- `search_policies` finds matching words in Markdown sections. It handles a few word variants and gives heading matches more weight. It returns up to three sections with their source filenames.

The system instructions tell the model to use these tools, keep the conditions from the policies, and send unsupported questions to staff. They also say not to claim that a booking was cancelled or a refund was sent. Weather exceptions need a staff decision. The tools only read data and calculate amounts.

If the model answers without calling a tool, or after only empty policy searches, the code returns a fixed refusal with the staff contact. This helps, but it cannot catch every wrong answer based on an irrelevant result. With conversation memory, this check looks only at tool results from the current question. Otherwise, one earlier booking lookup would allow an answer to "What is the capital of Australia?". The cost is that a follow-up answered without calling a tool also gets the refusal, so the instructions tell the model to call the tools again.

Some models print a tool call as JSON text instead of using `tool_calls`. The adapter runs this as a tool call if the tool name is known, so the customer does not see raw JSON.

## Tests, results and fixes

The latest test run passed **31 offline tests**. They cover the tools, refund rules and exact time boundaries, future cancellation times, fake-model agent loops, conversation memory, the Ollama adapter, and mistakes in the evaluation checks.

`eval/questions.json` contains 13 cases, including three refund calculations, two questions the agent should not answer, and two follow-ups that run after an earlier question. The evaluation checks tool calls, required facts and forbidden claims. It saves answers to `eval/results.md` and returns exit code 1 if any automated check fails. Running it again replaces the report and resets the review notes.

An earlier saved report for `qwen2.5:3b` showed **9/11 automated checks passed**, but that score was misleading. It included wrong answers about age limits and an already cancelled booking. The fixes included better search ranking, returning the actual booking status, and clearer instructions about age rules and refund processing. The evaluation also needed stricter checks for incorrect claims.

The previous `qwen3:4b` run, with 11 questions, passed 11/11 automated checks but only 10/11 in the AI-assisted review of meaning. The voucher answer said 73 EUR was available until the start, although the amount changes at the 48/24-hour boundaries. The instructions now say the amount depends on the cancellation time, and the latest voucher answer ties the amount to the current time.

The latest `qwen3:4b` run passed **13/13 automated checks**, but only **12/13 in the AI-assisted review of meaning**. The follow-up answer gives the correct 300 EUR and states the assumed time, but explains it incorrectly: it says there is no rental refund because the cancellation is before the start, when the real reason is that it is less than 24 hours before the start. This failure is still recorded in the report. Another answer is correct but repeats itself inside a stray `<final_answer>` tag.

## Model comparison

I compared the two models with the same code, instructions and 13 cases. Each model ran once, with temperature 0, on one machine with an RTX 3060. The reports are `eval/results.md` and `eval/results_qwen2.5_3b.md`.

| | `qwen3:4b` | `qwen2.5:3b` |
| --- | --- | --- |
| Automated checks | 13/13 | 11/13 |
| AI-assisted review of meaning | 12/13 | 9/13 |
| Total time | 457 s (about 35 s per case) | 79 s (about 6 s per case) |
| Size on disk | 2.5 GB | 1.9 GB |

- **Which model I kept:** `qwen3:4b` stays the default. It is about 6 times slower, but a slow answer is better than telling a customer that a 14-year-old can rent an e-bike, which `qwen2.5:3b` still does.
- **Instructions were not enough:** `qwen2.5:3b` got the improved instructions and search and still failed the age question. So the earlier improvement in this question did come from changing the model.
- **Refund amounts were the same:** both models gave the correct amount in all four refund calculations, because Python calculates them. The differences are in reading policy text and in claims the model adds. `qwen2.5:3b` invented a processing time in two answers that passed the automated checks.
- **How far to trust this:** 13 cases and one run per model are enough to show these specific failures, but not to measure small differences. The times also include loading the model and the earlier questions in the follow-up cases.

## AI assistance

I used  Claude Code for the CI workflow, conversation memory and model comparison, to help with writing and reviewing code, debugging, tests and documentation. The suggestions were checked against the task requirements, and the changes were tested instead of assuming they were correct.

For example, an earlier evaluation passed a wrong answer about the minimum age for renting an e-bike. The answer mentioned 16, but still incorrectly allowed a 14-year-old to rent one. Comparing the actual answer with the rental policy showed the mistake. With Codex's help, I updated the evaluation checks and added a regression test for this case.

This was a useful reminder that passing automated checks does not always mean the answer is correct. I also used AI to help review the final answers, so I recorded that separately from the automated test results. This was an AI-assisted review, not an independent human review.

## Limitations and what I would do next

This is a read-only demo with example bookings. Word matching can miss questions written in a different way, and the model can add details that are not in the documents. The fixed refusal is in English. Connection errors are reported, but other malformed model responses and invalid tool arguments are not automatically repaired. Conversation memory lasts only for one chat and has no size limit. There is no authentication.

With more time, I would add more questions about changing refund amounts over time and more ways of asking the same question. I would also improve handling of invalid tool calls and try a more restricted format for refund answers, because both models add claims that the tools did not return. Real booking data would need authentication before the agent could be used by customers.

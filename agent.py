import json

from tools import get_booking, calculate_refund, search_policies


TOOLS = {
    "get_booking": get_booking,
    "calculate_refund": calculate_refund,
    "search_policies": search_policies,
}


def run_agent(question: str, model, max_steps: int = 8, history: list | None = None) -> str:
    messages = [] if history is None else history
    turn_start = len(messages)
    messages.append({"role": "user", "content": question})

    def finish(answer: str) -> str:
        messages.append({"role": "assistant", "content": answer})
        return answer

    for _ in range(max_steps):
        response = model.respond(messages)

        if response["type"] == "final":
            # Only this turn counts: old tool results must not ground an unrelated question.
            has_tool_result = any(
                message["role"] == "tool"
                and json.loads(message["content"]) != {"matches": []}
                for message in messages[turn_start:]
            )

            if not has_tool_result:
                return finish(
                    "I can only answer CityWheels questions using "
                    "the shop's policies and booking data. "
                    "Please provide a booking ID for booking questions, "
                    "or contact help@citywheels.example."
                )

            return finish(response["content"])

        if response["type"] != "tool_call":
            raise ValueError("Unknown model response type")

        tool_name = response["name"]
        arguments = response["arguments"]

        if tool_name not in TOOLS:
            raise ValueError(f"Unknown tool: {tool_name}")

        tool_result = TOOLS[tool_name](**arguments)

        messages.append({
            "role": "assistant",
            "content": response,
        })
        messages.append({
            "role": "tool",
            "name": tool_name,
            "content": json.dumps(tool_result, ensure_ascii=False),
        })

    return finish("I could not finish the request. Please contact CityWheels staff.")

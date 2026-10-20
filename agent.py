import json

from tools import get_booking, calculate_refund, search_policies


TOOLS = {
    "get_booking": get_booking,
    "calculate_refund": calculate_refund,
    "search_policies": search_policies,
}


def run_agent(question: str, model, max_steps: int = 8) -> str:
    messages = [
        {"role": "user", "content": question},
    ]

    for _ in range(max_steps):
        response = model.respond(messages)

        if response["type"] == "final":
            has_tool_result = any(
                message["role"] == "tool"
                and json.loads(message["content"]) != {"matches": []}
                for message in messages
            )

            if not has_tool_result:
                return (
                    "I can only answer CityWheels questions using "
                    "the shop's policies and booking data. "
                    "Please provide a booking ID for booking questions, "
                    "or contact help@citywheels.example."
                )

            return response["content"]

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

    return "I could not finish the request. Please contact CityWheels staff."

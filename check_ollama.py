import json
from urllib.request import Request, urlopen
from tools import calculate_refund

payload = {
    "model": "qwen2.5:3b",
    "messages": [
        {
            "role": "system",
            "content": (
                "You are a CityWheels help desk assistant. "
                "For refund questions, call calculate_refund. "
                "Never invent refund amounts."
            ),
        },
        {
            "role": "user",
            "content": "What is the refund for booking CW-1002?",
        },
    ],
    "tools": [
        {
            "type": "function",
            "function": {
                "name": "calculate_refund",
                "description": (
                    "Calculate the cancellation refund for a CityWheels booking."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "booking_id": {
                            "type": "string",
                            "description": "Booking ID, for example CW-1002.",
                        },
                    },
                    "required": ["booking_id"],
                },
            },
        },
    ],
    "stream": False,
    "options": {"temperature": 0},
}
print("REQUEST:", payload)

request = Request(
    "http://localhost:11434/api/chat",
    data=json.dumps(payload).encode("utf-8"),
    headers={"Content-Type": "application/json"},
    method="POST",
)

with urlopen(request, timeout=120) as response:
    result = json.load(response)

print(json.dumps(result["message"], indent=2, ensure_ascii=False))

message = result["message"]
tool_calls = message.get("tool_calls", [])

if not tool_calls:
    raise RuntimeError("Expected the model to request a tool")

payload["messages"].append(message)

for tool_call in tool_calls:
    function = tool_call["function"]

    if function["name"] != "calculate_refund":
        raise ValueError(f"Unexpected tool: {function['name']}")

    tool_result = calculate_refund(**function["arguments"])

    print("TOOL RESULT:", tool_result)

    payload["messages"].append({
        "role": "tool",
        "tool_name": function["name"],
        "content": json.dumps(tool_result),
    })

follow_up_request = Request(
    "http://localhost:11434/api/chat",
    data=json.dumps(payload).encode("utf-8"),
    headers={"Content-Type": "application/json"},
    method="POST",
)

with urlopen(follow_up_request, timeout=120) as response:
    final_result = json.load(response)

print("MODEL RESPONSE:")
print(json.dumps(final_result["message"], indent=2, ensure_ascii=False))
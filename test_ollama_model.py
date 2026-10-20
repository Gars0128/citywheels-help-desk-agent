import io
import json
import unittest
from unittest.mock import patch

from ollama_model import OllamaModel, SYSTEM_PROMPT


class OllamaProtocolTests(unittest.TestCase):
    def test_tool_call_and_result_round_trip(self):
        tool_call = {"function": {"name": "get_booking",
                                  "arguments": {"booking_id": "CW-9999"}}}
        responses = [
            io.BytesIO(json.dumps({"message": {"tool_calls": [tool_call]}}).encode()),
            io.BytesIO(json.dumps({"message": {"content": "Booking not found."}}).encode()),
        ]
        messages = [{"role": "user", "content": "Show CW-9999"}]
        model = OllamaModel()
        with patch("ollama_model.urlopen", side_effect=responses) as request:
            call = model.respond(messages)
            self.assertEqual(call, {"type": "tool_call", **tool_call["function"]})
            messages.extend([
                {"role": "assistant", "content": call},
                {"role": "tool", "name": "get_booking",
                 "content": '{"found": false, "booking_id": "CW-9999"}'},
            ])
            final = model.respond(messages)
            self.assertEqual(final, {"type": "final", "content": "Booking not found."})
            payload = json.loads(request.call_args.args[0].data)
            self.assertEqual(payload["messages"][0]["content"], SYSTEM_PROMPT)
            self.assertEqual(payload["messages"][2]["tool_calls"], [tool_call])
            self.assertEqual(payload["messages"][3]["tool_name"], "get_booking")
            self.assertFalse(json.loads(payload["messages"][3]["content"])["found"])

    def test_all_calls_from_one_model_turn_are_executed(self):
        calls = [{"function": {"name": "get_booking", "arguments": {"booking_id": key}}}
                 for key in ["CW-1001", "CW-1002"]]
        response = io.BytesIO(json.dumps({"message": {"tool_calls": calls}}).encode())
        with patch("ollama_model.urlopen", return_value=response) as request:
            model = OllamaModel()
            first = model.respond([])
            second = model.respond([])
            self.assertEqual(first["arguments"]["booking_id"], "CW-1001")
            self.assertEqual(second["arguments"]["booking_id"], "CW-1002")
            request.assert_called_once()

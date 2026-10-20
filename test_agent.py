import json
import unittest

from agent import run_agent


class FakeRefundModel:
    def __init__(self):
        self.calls = 0
        self.received_result = None

    def respond(self, messages):
        self.calls += 1

        if self.calls == 1:
            return {
                "type": "tool_call",
                "name": "calculate_refund",
                "arguments": {"booking_id": "CW-1002"},
            }

        last_message = messages[-1]

        if last_message["role"] != "tool":
            raise AssertionError("Expected a tool result")

        self.received_result = json.loads(last_message["content"])
        amount = self.received_result["total_refund_eur"]

        return {
            "type": "final",
            "content": f"Your refund is {amount} EUR.",
        }


class AgentLoopTests(unittest.TestCase):
    def test_refund_tool_call_and_final_answer(self):
        model = FakeRefundModel()

        answer = run_agent(
            "How much will I get back for CW-1002?",
            model,
        )

        self.assertEqual(model.calls, 2)
        self.assertEqual(model.received_result["booking_id"], "CW-1002")
        self.assertEqual(model.received_result["total_refund_eur"], "340.00")
        self.assertEqual(answer, "Your refund is 340.00 EUR.")

class EndlessToolModel:
    def __init__(self):
        self.calls = 0

    def respond(self, messages):
        self.calls += 1

        return {
            "type": "tool_call",
            "name": "get_booking",
            "arguments": {"booking_id": "CW-1002"},
        }

class AgentLimitTests(unittest.TestCase):
    def test_stops_after_step_limit(self):
        model = EndlessToolModel()

        answer = run_agent(
            "Show my booking CW-1002",
            model,
            max_steps=3,
        )

        self.assertEqual(model.calls, 3)
        self.assertIn("contact CityWheels staff", answer)          

class UnsupportedAnswerModel:
    def respond(self, messages):
        return {
            "type": "final",
            "content": "The capital of Australia is Canberra.",
        }


class AgentGroundingTests(unittest.TestCase):
    def test_blocks_answer_without_tool_results(self):
        answer = run_agent(
            "What is the capital of Australia?",
            UnsupportedAnswerModel(),
        )

        self.assertNotIn("Canberra", answer)
        self.assertIn("help@citywheels.example", answer)       
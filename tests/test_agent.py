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


class AgentMemoryTests(unittest.TestCase):
    def test_follow_up_sees_earlier_turn(self):
        history = []
        run_agent("How much for CW-1002?", FakeRefundModel(), history=history)

        class FollowUpModel(FakeRefundModel):
            def respond(self, messages):
                self.seen = list(messages)
                return super().respond(messages)

        model = FollowUpModel()
        answer = run_agent("And again?", model, history=history)

        self.assertEqual(answer, "Your refund is 340.00 EUR.")
        self.assertEqual(model.seen[0]["content"], "How much for CW-1002?")
        self.assertEqual(history[3], {"role": "assistant", "content": "Your refund is 340.00 EUR."})
        self.assertEqual(history[-1]["content"], answer)

    def test_old_tool_results_do_not_ground_unrelated_follow_up(self):
        history = []
        run_agent("How much for CW-1002?", FakeRefundModel(), history=history)

        answer = run_agent("What is the capital of Australia?", UnsupportedAnswerModel(), history=history)

        self.assertNotIn("Canberra", answer)
        self.assertEqual(history[-1]["content"], answer)


class AgentGroundingTests(unittest.TestCase):
    def test_blocks_answer_without_tool_results(self):
        answer = run_agent(
            "What is the capital of Australia?",
            UnsupportedAnswerModel(),
        )

        self.assertNotIn("Canberra", answer)
        self.assertIn("help@citywheels.example", answer)

    def test_empty_search_is_not_evidence_for_invented_answer(self):
        class EmptySearchModel:
            calls = 0

            def respond(self, messages):
                self.calls += 1
                if self.calls == 1:
                    return {"type": "tool_call", "name": "search_policies",
                            "arguments": {"query": "owner name CityWheels"}}
                return {"type": "final", "content": "The owner is Alice."}

        answer = run_agent("Who owns CityWheels?", EmptySearchModel())
        self.assertNotIn("Alice", answer)
        self.assertIn("help@citywheels.example", answer)

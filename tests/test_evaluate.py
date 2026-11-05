import json
import unittest

from evaluate import ROOT, check_answer


class EvaluationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = {case["id"]: case for case in json.loads(
            (ROOT / "eval/questions.json").read_text(encoding="utf-8"))}

    def test_rejects_old_false_passes(self):
        answers = {
            "cancelled_booking": "You cannot cancel this booking as it is a confirmed booking.",
            "ebike_age": "Helmets are for under 16. A 14-year-old can rent an electric bike. There's no specific age restriction.",
            "refund_voucher": "73 EUR as a voucher, sent to the email address associated with your account.",
        }
        for key, answer in answers.items():
            with self.subTest(case=key):
                case = self.cases[key]
                self.assertTrue(check_answer(case, answer, [case["expected_tool"]]))

    def test_accepts_equivalent_not_found_wording(self):
        self.assertEqual(check_answer(self.cases["unknown_booking"],
                         "I couldn't find any booking with the ID CW-9999.", ["get_booking"]), [])

    def test_correct_answers_still_require_tools(self):
        case = self.cases["ebike_age"]
        answer = "No. Minimum age is 16. Riders under 18 need a guardian signature."
        self.assertEqual(check_answer(case, answer, ["search_policies"]), [])
        self.assertTrue(check_answer(case, answer, []))

    def test_parent_signature_wording_is_accepted(self):
        self.assertEqual(check_answer(self.cases["ebike_age"],
                         "No. From 16 only; under 18 requires a parent signature.",
                         ["search_policies"]), [])

    def test_cancelled_status_does_not_prove_refund_processing(self):
        self.assertTrue(check_answer(self.cases["cancelled_booking"],
                        "Already cancelled; cannot cancel again. Refunds are processed automatically.",
                        ["calculate_refund"]))

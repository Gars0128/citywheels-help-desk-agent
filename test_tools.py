import unittest
from tools import get_booking, calculate_refund, search_policies
from tools import get_booking, calculate_refund
from datetime import timedelta
from unittest.mock import patch

from tools import CURRENT_TIME

class GetBookingTests(unittest.TestCase):
    def test_existing_booking(self):
        result = get_booking("CW-1002")

        self.assertTrue(result["found"])
        self.assertEqual(result["booking"]["id"], "CW-1002")
        self.assertEqual(result["booking"]["deposit_eur"], 300.0)

    def test_unknown_booking(self):
        result = get_booking("CW-9999")

        self.assertEqual(
            result,
            {"found": False, "booking_id": "CW-9999"},
        )


class CalculateRefundTests(unittest.TestCase):


    
    def test_refund_amounts(self):
        cases = [
            ("CW-1001", "40.00", "50.00", "90.00"),
            ("CW-1002", "40.00", "300.00", "340.00"),
            ("CW-1003", "0.00", "50.00", "50.00"),
            ("CW-1007", "36.00", "150.00", "186.00"),
            ("CW-1010", "20.00", "150.00", "170.00"),
        ]

        for booking_id, rental, deposit, total in cases:
            with self.subTest(booking_id=booking_id):
                result = calculate_refund(booking_id)

                self.assertTrue(result["can_cancel"])
                self.assertEqual(result["rental_refund_eur"], rental)
                self.assertEqual(result["deposit_refund_eur"], deposit)
                self.assertEqual(result["total_refund_eur"], total)

    def test_non_confirmed_bookings(self):
        for booking_id in ["CW-1005", "CW-1006", "CW-1008"]:
            with self.subTest(booking_id=booking_id):
                result = calculate_refund(booking_id)

                self.assertFalse(result["can_cancel"])
                self.assertEqual(result["total_refund_eur"], "0.00")

    def test_voucher_refund(self):
        result = calculate_refund("CW-1004")

        self.assertTrue(result["can_cancel"])
        self.assertEqual(result["refund_method"], "voucher")
        self.assertEqual(result["total_refund_eur"], "73.00")

    def test_unknown_booking(self):
        result = calculate_refund("CW-9999")

        self.assertEqual(
            result,
            {"found": False, "booking_id": "CW-9999"},
        )

    def test_just_below_refund_boundaries(self):
        cases = [
            ("CW-1007", "18.00", "168.00"),
            ("CW-1010", "0.00", "150.00"),
        ]

        later = CURRENT_TIME + timedelta(seconds=1)

        with patch("tools.CURRENT_TIME", later):
            for booking_id, rental, total in cases:
                with self.subTest(booking_id=booking_id):
                    result = calculate_refund(booking_id)

                    self.assertEqual(result["rental_refund_eur"], rental)
  
                    self.assertEqual(result["total_refund_eur"], total)



class SearchPoliciesTests(unittest.TestCase):
    def test_finds_helmet_policy(self):
        result = search_policies("helmet")

        self.assertTrue(result["matches"])

        helmet_rules = [
            match
            for match in result["matches"]
            if match["source"] == "faq.md"
            and "required for riders under 16" in match["text"]
        ]

        self.assertTrue(helmet_rules)

    def test_unknown_word(self):
        result = search_policies("xyznonexistent")

        self.assertEqual(result, {"matches": []})

    def test_empty_query(self):
        result = search_policies("")

        self.assertEqual(result, {"matches": []})                    


                    
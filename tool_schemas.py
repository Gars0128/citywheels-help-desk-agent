TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "get_booking",
           "description": (
                "Look up a CityWheels booking by its booking ID. "
                "Use this tool whenever a customer asks about a specific "
                "booking, its existence, status, or details. "
                "Always look up the booking even if the ID may be invalid. "
                "Never assume a booking exists or does not exist without "
                "checking this tool."
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
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_refund",
            "description": (
                "Check cancellation eligibility and calculate the refund, now "
                "or for a future cancellation time. "
                "Use for all booking refund questions, including whether a "
                "cancelled booking qualifies for another refund. "
                "It only calculates a refund; it does not cancel the booking."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "booking_id": {
                        "type": "string",
                        "description": "Booking ID, for example CW-1002.",
                    },
                    "cancel_at": {
                        "type": "string",
                        "description": (
                            "Future cancellation time in ISO 8601, for example "
                            "2026-06-11T09:00:00+02:00. Omit it for cancelling now."
                        ),
                    },
                },
                "required": ["booking_id"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_policies",
            "description": (
                "Search CityWheels policies for rental rules, prices, "
                "opening hours, age restrictions, helmet requirements, "
                "cancellations, refunds, weather conditions and exceptions. "
                "Use this tool for questions about what CityWheels allows "
                "or requires, including storm-warning refund exceptions. "
                "Use concise English keywords because the policy "
                "documents are in English."
                " Include the topic and constraint, e.g. 'electric bike age limits' "
                "for an age eligibility question."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "English search keywords, for example helmet.",
                    },
                },
                "required": ["query"],
                "additionalProperties": False,
            },
        },
    },
]

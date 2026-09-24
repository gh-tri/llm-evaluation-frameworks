"""
Tiny, presentation-friendly sample inputs for the live framework demos.

Deliberately NOT this project's Northwind Robotics dataset - that's a
fictional company's SEC filing, which needs context to even parse. Both
sample sets below live in the same delayed-package customer-support world,
so a presenter can move between frameworks without re-explaining the
scenario.

SAMPLES / DEFAULT_CRITERIA: for the "define a metric" demo (#1) on every
framework's page. Three answers to the exact same question, spanning good,
mediocre, and bad, so running a metric across all three visibly
discriminates - the whole point of a live demo is that the audience can
see the score actually mean something.

RAG_SAMPLE: for the RAG-specific demo (#2) on Ragas's and TruLens's pages
- a tiny retrieval scenario with a grounded answer and a hallucinated one,
so metrics that check groundedness/faithfulness visibly discriminate too.
"""

CUSTOMER_SUPPORT_QUESTION = (
    "My package was supposed to arrive 5 days ago and the tracking page hasn't "
    "updated since. What should I do?"
)

SAMPLES = {
    "good": {
        "label": "Good answer",
        "input": CUSTOMER_SUPPORT_QUESTION,
        "actual_output": (
            "I'm sorry for the delay - that's frustrating. I checked your order and "
            "the carrier shows it's been stuck at the regional hub since Tuesday. "
            "I've filed a trace request with them and queued a free reshipment that "
            "goes out automatically if there's no tracking update within 48 hours. "
            "You'll get an email either way."
        ),
        "expected_output": (
            "Acknowledge the delay, check the actual tracking status, take a concrete "
            "next step (trace request or reshipment), and tell the customer what "
            "happens next."
        ),
    },
    "mediocre": {
        "label": "Mediocre answer",
        "input": CUSTOMER_SUPPORT_QUESTION,
        "actual_output": (
            "Sorry about that. Shipping delays can happen sometimes. Please keep "
            "checking the tracking link for updates."
        ),
        "expected_output": (
            "Acknowledge the delay, check the actual tracking status, take a concrete "
            "next step (trace request or reshipment), and tell the customer what "
            "happens next."
        ),
    },
    "bad": {
        "label": "Bad / off-topic answer",
        "input": CUSTOMER_SUPPORT_QUESTION,
        "actual_output": (
            "Thanks for reaching out! Did you know we have a summer sale on all "
            "backpacks right now? Check out our new arrivals!"
        ),
        "expected_output": (
            "Acknowledge the delay, check the actual tracking status, take a concrete "
            "next step (trace request or reshipment), and tell the customer what "
            "happens next."
        ),
    },
}

DEFAULT_CRITERIA = (
    "Determine whether the response directly addresses the customer's problem, "
    "takes a concrete next step, and stays on-topic. Penalize vague reassurance "
    "with no action, and penalize responses that ignore the question entirely."
)

RAG_SAMPLE = {
    "question": (
        "Will I get a refund if my package doesn't arrive within 10 days of the "
        "promised delivery date?"
    ),
    "contexts": [
        "Delayed Delivery Policy: If a package is not delivered within 10 days of "
        "its promised delivery date, the customer is eligible for a full refund or "
        "a free reshipment, whichever they prefer. Customers should contact support "
        "to initiate either option.",
        "Shipping Insurance: All orders over $50 include free shipping insurance, "
        "which covers loss or damage during transit but does not cover delays "
        "caused by the carrier.",
    ],
    "reference": (
        "Yes. If your package is more than 10 days late against its promised "
        "delivery date, you can choose either a full refund or a free reshipment - "
        "just contact support to start one of those."
    ),
    "answers": {
        "grounded": {
            "label": "Grounded answer",
            "text": (
                "Yes - since your package hasn't arrived within 10 days of the "
                "promised date, you're eligible for a full refund or a free "
                "reshipment. Just contact support to start one."
            ),
        },
        "hallucinated": {
            "label": "Hallucinated answer",
            "text": (
                "Yes, and on top of the refund you'll also get an automatic $20 "
                "store credit for the inconvenience, no need to contact anyone."
            ),
        },
    },
}

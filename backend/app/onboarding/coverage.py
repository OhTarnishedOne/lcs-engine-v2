"""
Coverage state machine for conversational onboarding.

Tracks which topics have been covered in the conversation using
keyword/regex heuristics on user messages.
"""

import re

REQUIRED_TOPICS = ["experience", "goals", "risk", "interests", "learning_style"]

# Keyword patterns per topic (matched against user messages, case-insensitive)
TOPIC_KEYWORDS: dict[str, list[str]] = {
    "experience": [
        "invest", "stock", "trade", "beginner", "never", "started",
        "years", "portfolio", "etf", "crypto", "401k", "brokerage",
        "new to", "first time", "no experience", "some experience",
    ],
    "goals": [
        "goal", "want to", "hope to", "retire", "save", "grow",
        "wealth", "learn", "financial", "freedom", "income",
        "planning", "future", "long term", "short term",
    ],
    "risk": [
        "risk", "lose", "drop", "conservative", "aggressive",
        "comfortable", "nervous", "volatile", "safe", "scared",
        "worry", "crash", "decline", "stomach",
    ],
    "interests": [
        "interest", "stocks", "etf", "bond", "crypto", "real estate",
        "retirement", "curious about", "want to learn about",
        "fascinated", "drawn to", "index fund",
    ],
    "learning_style": [
        "learn", "read", "watch", "video", "hands-on", "practice",
        "discuss", "explain", "examples", "do", "tutorial",
        "article", "course", "prefer",
    ],
}

# Pre-compile patterns for each topic
_TOPIC_PATTERNS: dict[str, re.Pattern] = {
    topic: re.compile(
        "|".join(re.escape(kw) for kw in keywords),
        re.IGNORECASE,
    )
    for topic, keywords in TOPIC_KEYWORDS.items()
}


def compute_coverage(messages: list[dict]) -> dict[str, bool]:
    """
    Scan user messages and determine which topics have been covered.

    Args:
        messages: List of {"role": "user"|"assistant", "content": "..."} dicts

    Returns:
        Dict mapping each required topic to True/False
    """
    user_text = " ".join(
        msg.get("content", "")
        for msg in messages
        if msg.get("role") == "user"
    )

    return {
        topic: bool(_TOPIC_PATTERNS[topic].search(user_text))
        for topic in REQUIRED_TOPICS
    }


def get_completion_status(coverage: dict[str, bool], turn_count: int) -> str:
    """
    Determine whether the conversation should continue or wrap up.

    Args:
        coverage: Dict from compute_coverage()
        turn_count: Number of user messages so far

    Returns:
        "wrap_up" if all 5 topics covered OR turn_count >= 6, else "continue"
    """
    all_covered = all(coverage.get(topic, False) for topic in REQUIRED_TOPICS)
    if all_covered or turn_count >= 6:
        return "wrap_up"
    return "continue"

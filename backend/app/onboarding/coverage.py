"""
Coverage state machine for conversational onboarding.

Tracks which topics have been covered in the conversation using
keyword/regex heuristics on user messages.

With the hybrid tap+chat flow, the tap screens cover experience, goals,
risk, interests, and learning_style. The chat phase explores deeper:
motivation, life_context, and emotional_relationship.
"""

import re

REQUIRED_TOPICS = ["motivation", "life_context", "emotional_relationship"]

# Keyword patterns per topic (matched against user messages, case-insensitive)
TOPIC_KEYWORDS: dict[str, list[str]] = {
    "motivation": [
        "why", "reason", "motivated", "inspired", "because", "decided",
        "sparked", "moment", "started thinking", "got interested",
        "made me want", "prompted", "pushed me", "finally",
    ],
    "life_context": [
        "family", "kids", "children", "debt", "job", "income", "student",
        "career", "mortgage", "rent", "salary", "wife", "husband", "partner",
        "work", "busy", "time", "schedule", "retire", "promotion",
    ],
    "emotional_relationship": [
        "feel", "afraid", "scared", "excited", "anxious", "confident",
        "nervous", "overwhelmed", "comfortable", "worry", "stress", "hope",
        "frustrated", "confused", "uncertain", "optimistic", "cautious",
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


def get_completion_status(coverage: dict[str, bool], turn_count: int, messages: list[dict] | None = None) -> str:
    """
    Determine whether the conversation should continue or wrap up.

    Args:
        coverage: Dict from compute_coverage()
        turn_count: Number of user messages so far
        messages: Optional full message list for disengagement detection

    Returns:
        "wrap_up" if all 3 topics covered OR turn_count >= 5 OR disengaged, else "continue"
    """
    all_covered = all(coverage.get(topic, False) for topic in REQUIRED_TOPICS)
    if all_covered or turn_count >= 5:
        return "wrap_up"

    # Detect disengagement: 2+ consecutive short user responses (<10 words)
    if messages and turn_count >= 2:
        user_messages = [
            msg.get("content", "")
            for msg in messages
            if msg.get("role") == "user"
        ]
        if len(user_messages) >= 2:
            last_two = user_messages[-2:]
            if all(len(m.split()) < 10 for m in last_two):
                return "wrap_up"

    return "continue"

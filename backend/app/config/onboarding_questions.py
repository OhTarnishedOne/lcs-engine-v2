"""
Onboarding Questions Configuration

Store questions as configuration, not hardcoded in routes.
This allows easy updates without code changes.

Target audience: Adult learners - workforce development programs, HBCU students,
first-time investors. People who are intimidated by investing and don't know where to start.

Core value prop: LCS removes the fear and creates a safe space. The onboarding should
feel like a conversation, not a form.
"""

from typing import Any, Optional

ONBOARDING_SECTIONS: list[dict[str, Any]] = [
    {
        "section": 1,
        "title": "Where You Are",
        "subtitle": "Let's understand your current relationship with investing.",
        "questions": [
            {
                "key": "experience_level",
                "text": "How would you describe your investing experience?",
                "type": "single_select",
                "required": True,
                "order": 1,
                "options": [
                    {"value": "never", "label": "I've never invested", "emoji": "🌱"},
                    {"value": "curious", "label": "I've read about it but never tried", "emoji": "📚"},
                    {"value": "beginner", "label": "I've made a few investments", "emoji": "🚀"},
                    {"value": "intermediate", "label": "I invest regularly", "emoji": "📈"},
                    {"value": "advanced", "label": "I'm experienced and want to level up", "emoji": "🎯"}
                ]
            },
            {
                "key": "current_situation",
                "text": "What best describes where you are in life?",
                "type": "single_select",
                "required": True,
                "order": 2,
                "options": [
                    {"value": "student", "label": "Student", "emoji": "🎓"},
                    {"value": "early_career", "label": "Early career (0-5 years working)", "emoji": "💼"},
                    {"value": "mid_career", "label": "Mid-career", "emoji": "📊"},
                    {"value": "career_change", "label": "Career transition", "emoji": "🔄"},
                    {"value": "pre_retirement", "label": "Approaching retirement", "emoji": "🌅"}
                ]
            },
            {
                "key": "has_investment_account",
                "text": "Do you have a brokerage account (like Robinhood, Fidelity, etc.)?",
                "type": "boolean",
                "required": True,
                "order": 3,
                "options": [
                    {"value": True, "label": "Yes"},
                    {"value": False, "label": "No"}
                ]
            },
            {
                "key": "has_retirement_account",
                "text": "Do you have a retirement account (401k, IRA, pension)?",
                "type": "boolean",
                "required": True,
                "order": 4,
                "options": [
                    {"value": True, "label": "Yes"},
                    {"value": False, "label": "No, or I'm not sure"}
                ]
            }
        ]
    },
    {
        "section": 2,
        "title": "What's Holding You Back",
        "subtitle": "No judgment here — we've all felt these. Understanding your hesitations helps us help you.",
        "questions": [
            {
                "key": "barriers",
                "text": "What has kept you from investing (or investing more)? Select all that apply.",
                "type": "multi_select",
                "required": True,
                "order": 1,
                "options": [
                    {"value": "dont_know_where_to_start", "label": "I don't know where to start", "emoji": "🤷"},
                    {"value": "fear_of_losing_money", "label": "I'm afraid of losing money", "emoji": "😰"},
                    {"value": "not_enough_money", "label": "I don't think I have enough to invest", "emoji": "💸"},
                    {"value": "too_complicated", "label": "It all seems too complicated", "emoji": "🤯"},
                    {"value": "dont_trust_markets", "label": "I don't trust the stock market", "emoji": "🎰"},
                    {"value": "no_time", "label": "I don't have time to learn", "emoji": "⏰"},
                    {"value": "bad_experience", "label": "I've had a bad experience before", "emoji": "😔"},
                    {"value": "none", "label": "Nothing — I'm ready to go!", "emoji": "🚀"}
                ]
            },
            {
                "key": "biggest_barrier",
                "text": "If you had to pick ONE thing that's held you back the most, what would it be?",
                "type": "single_select",
                "required": False,
                "order": 2,
                "conditional": {"depends_on": "barriers", "not_contains": "none"},
                "options": "dynamic"  # Populated from barriers selection
            }
        ]
    },
    {
        "section": 3,
        "title": "What You Want",
        "subtitle": "Let's talk about your goals.",
        "questions": [
            {
                "key": "primary_goal",
                "text": "What's your main reason for wanting to learn about investing?",
                "type": "single_select",
                "required": True,
                "order": 1,
                "options": [
                    {"value": "learn_basics", "label": "I just want to understand how it works", "emoji": "🧠"},
                    {"value": "start_investing", "label": "I want to start investing for the first time", "emoji": "🌱"},
                    {"value": "grow_wealth", "label": "I want to grow my money over time", "emoji": "📈"},
                    {"value": "retirement", "label": "I'm focused on retirement savings", "emoji": "🏖️"},
                    {"value": "specific_goal", "label": "I have a specific goal in mind", "emoji": "🎯"}
                ]
            },
            {
                "key": "specific_goal_description",
                "text": "What's your specific goal?",
                "type": "text",
                "required": False,
                "order": 2,
                "placeholder": "e.g., Save for a house down payment, fund my kid's education...",
                "conditional": {"depends_on": "primary_goal", "equals": "specific_goal"}
            },
            {
                "key": "time_horizon",
                "text": "When do you think you'll need this money?",
                "type": "single_select",
                "required": True,
                "order": 3,
                "options": [
                    {"value": "less_than_1_year", "label": "Less than 1 year", "emoji": "📅"},
                    {"value": "1_to_3_years", "label": "1-3 years", "emoji": "📆"},
                    {"value": "3_to_5_years", "label": "3-5 years", "emoji": "🗓️"},
                    {"value": "5_to_10_years", "label": "5-10 years", "emoji": "📊"},
                    {"value": "10_plus_years", "label": "10+ years", "emoji": "🌳"},
                    {"value": "not_sure", "label": "I'm not sure yet", "emoji": "🤔"}
                ]
            }
        ]
    },
    {
        "section": 4,
        "title": "Risk & Comfort",
        "subtitle": "There are no wrong answers — just honest ones.",
        "questions": [
            {
                "key": "risk_tolerance",
                "text": "How would you describe your comfort with risk?",
                "type": "single_select",
                "required": True,
                "order": 1,
                "options": [
                    {"value": "very_conservative", "label": "I can't afford to lose anything", "emoji": "🛡️"},
                    {"value": "conservative", "label": "I prefer safety over growth", "emoji": "🔒"},
                    {"value": "moderate", "label": "I'm okay with some ups and downs", "emoji": "⚖️"},
                    {"value": "aggressive", "label": "I'm comfortable with volatility for higher returns", "emoji": "📈"},
                    {"value": "very_aggressive", "label": "I'm willing to take big risks", "emoji": "🎢"}
                ]
            },
            {
                "key": "loss_reaction",
                "text": "Imagine you invested $1,000 and it dropped to $800. What would you do?",
                "type": "single_select",
                "required": True,
                "order": 2,
                "options": [
                    {"value": "sell_immediately", "label": "Sell immediately to avoid more loss", "emoji": "🏃"},
                    {"value": "wait_and_see", "label": "Wait and see what happens", "emoji": "👀"},
                    {"value": "buy_more", "label": "Buy more while it's cheaper", "emoji": "🛒"},
                    {"value": "not_sure", "label": "I honestly don't know", "emoji": "🤷"}
                ]
            },
            {
                "key": "monthly_investable",
                "text": "How much could you realistically invest per month? (No judgment — $0 is okay!)",
                "type": "single_select",
                "required": True,
                "order": 3,
                "options": [
                    {"value": "nothing_yet", "label": "Nothing right now", "emoji": "🌱"},
                    {"value": "under_100", "label": "Under $100", "emoji": "💵"},
                    {"value": "100_to_500", "label": "$100-$500", "emoji": "💰"},
                    {"value": "500_to_1000", "label": "$500-$1,000", "emoji": "💎"},
                    {"value": "over_1000", "label": "Over $1,000", "emoji": "🏆"},
                    {"value": "not_sure", "label": "I'm not sure", "emoji": "🤔"}
                ]
            }
        ]
    },
    {
        "section": 5,
        "title": "How You Learn",
        "subtitle": "Last step — help us personalize your experience.",
        "questions": [
            {
                "key": "learning_preference",
                "text": "How do you prefer to learn new things?",
                "type": "single_select",
                "required": True,
                "order": 1,
                "options": [
                    {"value": "read", "label": "Reading articles and guides", "emoji": "📖"},
                    {"value": "watch", "label": "Watching videos", "emoji": "🎬"},
                    {"value": "do", "label": "Hands-on practice", "emoji": "🛠️"},
                    {"value": "discuss", "label": "Talking it through with someone", "emoji": "💬"}
                ]
            },
            {
                "key": "time_commitment",
                "text": "How much time can you dedicate to learning?",
                "type": "single_select",
                "required": True,
                "order": 2,
                "options": [
                    {"value": "5_min_daily", "label": "5 minutes a day", "emoji": "⚡"},
                    {"value": "15_min_daily", "label": "15 minutes a day", "emoji": "☕"},
                    {"value": "30_min_weekly", "label": "30 minutes a week", "emoji": "📅"},
                    {"value": "1_hour_weekly", "label": "1 hour a week", "emoji": "🗓️"},
                    {"value": "flexible", "label": "Flexible — I'll learn when I can", "emoji": "🌊"}
                ]
            },
            {
                "key": "interests",
                "text": "What topics are you most interested in? Select all that apply.",
                "type": "multi_select",
                "required": True,
                "order": 3,
                "options": [
                    {"value": "stocks", "label": "Individual stocks", "emoji": "📊"},
                    {"value": "etfs", "label": "ETFs & index funds", "emoji": "📦"},
                    {"value": "bonds", "label": "Bonds & fixed income", "emoji": "🔒"},
                    {"value": "crypto", "label": "Cryptocurrency", "emoji": "🪙"},
                    {"value": "real_estate", "label": "Real estate investing", "emoji": "🏠"},
                    {"value": "retirement", "label": "Retirement planning", "emoji": "🏖️"},
                    {"value": "all", "label": "All of the above — teach me everything!", "emoji": "🌟"}
                ]
            }
        ]
    }
]


# Barrier descriptions for personalized messaging
BARRIER_DESCRIPTIONS: dict[str, dict[str, str]] = {
    "dont_know_where_to_start": {
        "acknowledgment": "You mentioned you're not sure where to start",
        "encouragement": "That's exactly why we built LCS. We'll guide you step by step."
    },
    "fear_of_losing_money": {
        "acknowledgment": "You mentioned you're worried about losing money",
        "encouragement": "That's a valid concern. We'll help you understand risk and start small."
    },
    "not_enough_money": {
        "acknowledgment": "You mentioned you're not sure if you have enough to invest",
        "encouragement": "Good news: you can start investing with as little as $1. Let's explore your options."
    },
    "too_complicated": {
        "acknowledgment": "You mentioned investing seems too complicated",
        "encouragement": "We break everything down into simple, digestible pieces. No jargon, just clarity."
    },
    "dont_trust_markets": {
        "acknowledgment": "You mentioned you're skeptical about the markets",
        "encouragement": "Healthy skepticism is good. Let's look at the data and history together."
    },
    "no_time": {
        "acknowledgment": "You mentioned time is a constraint",
        "encouragement": "We respect your time. Our lessons are bite-sized and designed for busy people."
    },
    "bad_experience": {
        "acknowledgment": "You mentioned you've had a difficult experience before",
        "encouragement": "We're sorry to hear that. LCS is a safe space to learn at your own pace."
    }
}


# Persona definitions
PERSONA_DEFINITIONS: dict[str, dict[str, str]] = {
    "cautious_beginner": {
        "name": "Cautious Beginner",
        "description": "New to investing and risk-averse. Needs reassurance and small wins.",
        "approach": "Start with the basics, emphasize safety, celebrate small progress."
    },
    "eager_learner": {
        "name": "Eager Learner",
        "description": "Curious and ready to dive in. Wants hands-on practice.",
        "approach": "Provide interactive experiences, encourage exploration, offer challenges."
    },
    "goal_focused": {
        "name": "Goal Focused",
        "description": "Has a specific target. Practical and wants a clear path.",
        "approach": "Show the roadmap, connect actions to outcomes, track progress visibly."
    },
    "skeptical_explorer": {
        "name": "Skeptical Explorer",
        "description": "Has doubts about markets. Needs proof and appreciates data.",
        "approach": "Lead with evidence, show historical data, acknowledge uncertainties."
    },
    "time_pressed": {
        "name": "Time Pressed",
        "description": "Busy and wants efficiency. Prefers bite-sized learning.",
        "approach": "Keep it brief, prioritize high-impact info, offer quick wins."
    },
    "rebuilding_confidence": {
        "name": "Rebuilding Confidence",
        "description": "Had a bad experience. Needs a safe space to try again.",
        "approach": "Be gentle, go slow, emphasize paper trading and simulation."
    }
}


def get_section(section_number: int) -> Optional[dict[str, Any]]:
    """Get a specific section by number."""
    for section in ONBOARDING_SECTIONS:
        if section["section"] == section_number:
            return section
    return None


def get_question_by_key(key: str) -> Optional[tuple[dict[str, Any], int]]:
    """Get a question by its key. Returns (question, section_number) or None."""
    for section in ONBOARDING_SECTIONS:
        for question in section["questions"]:
            if question["key"] == key:
                return (question, section["section"])
    return None


def get_all_question_keys() -> list[str]:
    """Get all question keys in order."""
    keys = []
    for section in ONBOARDING_SECTIONS:
        for question in section["questions"]:
            keys.append(question["key"])
    return keys


def get_required_question_keys() -> list[str]:
    """Get all required question keys."""
    keys = []
    for section in ONBOARDING_SECTIONS:
        for question in section["questions"]:
            if question.get("required", False) and question.get("options") != "dynamic":
                # Skip conditional questions for base requirement
                if "conditional" not in question:
                    keys.append(question["key"])
    return keys


def get_option_label(question_key: str, value: Any) -> Optional[str]:
    """Get the display label for a question option value."""
    result = get_question_by_key(question_key)
    if not result:
        return None
    question, _ = result
    options = question.get("options", [])
    if options == "dynamic":
        return str(value)
    for option in options:
        if option["value"] == value:
            return option["label"]
    return str(value)


def get_total_questions() -> int:
    """Get total number of questions across all sections."""
    total = 0
    for section in ONBOARDING_SECTIONS:
        total += len(section["questions"])
    return total

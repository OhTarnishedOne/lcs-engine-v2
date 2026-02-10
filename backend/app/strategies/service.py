"""
Strategy Service

Core business logic for AI-generated investment strategies.
"""

import logging
from datetime import datetime, UTC
from typing import Optional

from sqlalchemy.orm import Session

from ..db.models import UserProfile, Strategy, StrategyComparison
from ..integrations import ResilientAIClient

logger = logging.getLogger(__name__)

# Valid strategy types
VALID_STRATEGY_TYPES = ["value", "growth", "income", "momentum", "balanced", "index"]


class StrategyService:
    """Service for generating and managing investment strategies."""

    # Maps onboarding profile to best-fit strategy type
    PROFILE_TO_STRATEGY = {
        ("very_conservative", "learn_basics"): "index",
        ("very_conservative", "save_for_retirement"): "income",
        ("very_conservative", "grow_wealth"): "balanced",
        ("conservative", "learn_basics"): "index",
        ("conservative", "save_for_retirement"): "income",
        ("conservative", "grow_wealth"): "balanced",
        ("moderate", "learn_basics"): "balanced",
        ("moderate", "save_for_retirement"): "balanced",
        ("moderate", "grow_wealth"): "growth",
        ("aggressive", "learn_basics"): "growth",
        ("aggressive", "save_for_retirement"): "growth",
        ("aggressive", "grow_wealth"): "momentum",
        ("very_aggressive", "learn_basics"): "growth",
        ("very_aggressive", "save_for_retirement"): "growth",
        ("very_aggressive", "grow_wealth"): "momentum",
    }

    def __init__(self, db: Session, ai_client: ResilientAIClient):
        self.db = db
        self.ai_client = ai_client

    def get_user_profile(self, user_id: str) -> Optional[UserProfile]:
        """Get user's onboarding profile."""
        return self.db.query(UserProfile).filter(
            UserProfile.user_id == user_id
        ).first()

    def get_default_strategy_type(self, profile: Optional[UserProfile]) -> str:
        """Auto-select strategy type from onboarding answers."""
        if not profile:
            return "balanced"

        risk = getattr(profile, 'risk_tolerance', 'moderate') or 'moderate'
        goal = getattr(profile, 'primary_goal', 'learn_basics') or 'learn_basics'

        # Normalize risk tolerance
        risk_map = {
            "very_conservative": "very_conservative",
            "conservative": "conservative",
            "moderate": "moderate",
            "aggressive": "aggressive",
            "very_aggressive": "very_aggressive",
        }
        risk = risk_map.get(risk, "moderate")

        key = (risk, goal)
        return self.PROFILE_TO_STRATEGY.get(key, "balanced")

    def build_generation_prompt(self, profile: Optional[UserProfile], strategy_type: str) -> str:
        """Build Claude prompt for strategy generation."""
        experience = getattr(profile, 'experience_level', 'never') or 'beginner'
        risk = getattr(profile, 'risk_tolerance', 'moderate') or 'moderate'
        goal = getattr(profile, 'primary_goal', 'learn about investing') or 'learn about investing'
        barrier = getattr(profile, 'biggest_barrier', 'unknown') or 'unknown'

        return f"""Generate an investment strategy for educational purposes.

USER PROFILE:
- Experience: {experience}
- Risk tolerance: {risk}
- Primary goal: {goal}
- Biggest barrier: {barrier}

STRATEGY TYPE REQUESTED: {strategy_type}

STRATEGY TYPE DEFINITIONS:
- value: Buy undervalued companies, hold long-term. Warren Buffett style.
- growth: Companies growing revenue/earnings fast. Higher risk, higher potential.
- income: Dividend-paying stocks and bonds. Steady cash flow.
- momentum: Stocks trending upward. Ride winners, cut losers.
- balanced: Mix of growth and stability. Middle road.
- index: Track the market with ETFs. Lowest effort, broadly diversified.

REQUIREMENTS:
1. Create a portfolio of 5-8 assets (stocks and/or ETFs)
2. Use REAL tickers that exist on major US exchanges
3. Allocations must sum to 100%
4. Match the risk level to the user's tolerance (1-5 scale, 1=conservative, 5=aggressive)
5. Rationale should be in plain English a beginner can understand
6. Risks should be honest — don't sugarcoat
7. Include 3-5 learning points (concepts this strategy teaches)

Respond ONLY with valid JSON in this exact format:
{{
    "name": "Strategy Name",
    "description": "2-3 sentence summary",
    "strategy_type": "{strategy_type}",
    "risk_level": 3,
    "time_horizon": "medium",
    "assets": [
        {{
            "ticker": "VTI",
            "name": "Vanguard Total Stock Market ETF",
            "allocation_pct": 40.0,
            "rationale": "Gives you broad exposure to the entire US stock market."
        }}
    ],
    "rationale": "Why this strategy fits you...",
    "risks": "What could go wrong...",
    "learning_points": ["Diversification", "Dollar-cost averaging", "..."]
}}

Do NOT include any text outside the JSON. No markdown, no code fences, no explanation."""

    def build_comparison_prompt(self, strategies: list[dict], profile: Optional[UserProfile]) -> str:
        """Build prompt for comparing strategies side by side."""
        experience = getattr(profile, 'experience_level', 'beginner') if profile else 'beginner'
        risk = getattr(profile, 'risk_tolerance', 'moderate') if profile else 'moderate'
        goal = getattr(profile, 'primary_goal', 'learn about investing') if profile else 'learn about investing'

        strategy_summaries = ""
        for i, s in enumerate(strategies, 1):
            assets = s.get('assets', [])
            tickers = ', '.join([a.get('ticker', 'N/A') for a in assets])
            strategy_summaries += f"""
Strategy {i}: {s.get('name', 'Unknown')}
- Type: {s.get('strategy_type', 'unknown')}
- Risk: {s.get('risk_level', '?')}/5
- Assets: {tickers}
- Time horizon: {s.get('time_horizon', 'unknown')}
"""

        return f"""Compare these investment strategies for a user who is a {experience}
with {risk} risk tolerance, aiming to {goal}.

{strategy_summaries}

Write a comparison in plain English that:
1. Highlights the key differences (risk, return potential, effort)
2. Explains which scenarios each strategy works best in
3. Gives the user enough info to choose confidently
4. Does NOT recommend one over the other — let them decide
5. Keeps it under 300 words

Be direct and practical. No fluff."""

    def build_explanation_prompt(self, strategy: dict, profile: Optional[UserProfile], question: str) -> str:
        """Build prompt for deeper explanation of a strategy."""
        experience = getattr(profile, 'experience_level', 'beginner') if profile else 'beginner'
        risk = getattr(profile, 'risk_tolerance', 'moderate') if profile else 'moderate'

        assets = strategy.get('assets', [])
        asset_summary = ', '.join([f"{a.get('ticker', 'N/A')} ({a.get('allocation_pct', 0)}%)" for a in assets])

        return f"""The user has a strategy called "{strategy.get('name', 'Unknown')}" ({strategy.get('strategy_type', 'unknown')}).
Assets: {asset_summary}

User profile: {experience}, {risk} risk tolerance.

They asked: "{question}"

Answer their question about this strategy. Be specific to THEIR portfolio.
Use simple language. If they're asking something advanced, bridge from basics.
Keep it concise — 2-3 paragraphs max."""

    async def generate_strategy(
        self,
        user_id: str,
        strategy_type: Optional[str] = None,
        preferences: Optional[dict] = None
    ) -> Strategy:
        """
        Generate a new AI-powered investment strategy.

        1. Load user profile
        2. Determine strategy type (explicit or auto from profile)
        3. Call Claude via ResilientAIClient for JSON generation
        4. Parse and validate response
        5. Save to DB
        6. Return strategy
        """
        # Check strategy limit
        existing_count = self.db.query(Strategy).filter(
            Strategy.user_id == user_id,
            Strategy.is_active == True
        ).count()
        if existing_count >= 10:
            raise ValueError("Maximum of 10 strategies reached. Delete some before creating new ones.")

        # Get user profile
        profile = self.get_user_profile(user_id)

        # Determine strategy type
        if strategy_type:
            if strategy_type not in VALID_STRATEGY_TYPES:
                raise ValueError(f"Invalid strategy type. Must be one of: {', '.join(VALID_STRATEGY_TYPES)}")
        else:
            strategy_type = self.get_default_strategy_type(profile)

        # Build prompt and call AI
        prompt = self.build_generation_prompt(profile, strategy_type)
        messages = [{"role": "user", "content": prompt}]
        system_prompt = "You are an investment education assistant. Generate investment strategies in valid JSON format only."

        try:
            strategy_data = await self.ai_client.chat_json(messages, system_prompt)
        except Exception as e:
            logger.error(f"Strategy generation failed: {e}")
            raise ValueError("Strategy generation failed, please try again.")

        # Validate required fields
        required_fields = ['name', 'description', 'strategy_type', 'risk_level', 'time_horizon', 'assets', 'rationale', 'risks']
        for field in required_fields:
            if field not in strategy_data:
                raise ValueError(f"Strategy generation failed: missing {field}")

        # Create strategy
        strategy = Strategy(
            user_id=user_id,
            name=strategy_data['name'],
            description=strategy_data['description'],
            strategy_type=strategy_data['strategy_type'],
            risk_level=strategy_data['risk_level'],
            time_horizon=strategy_data['time_horizon'],
            assets=strategy_data['assets'],
            rationale=strategy_data['rationale'],
            risks=strategy_data['risks'],
            learning_points=strategy_data.get('learning_points', [])
        )

        self.db.add(strategy)
        self.db.commit()
        self.db.refresh(strategy)

        return strategy

    def get_strategies(self, user_id: str) -> list[Strategy]:
        """Get all active strategies for a user."""
        return self.db.query(Strategy).filter(
            Strategy.user_id == user_id,
            Strategy.is_active == True
        ).order_by(Strategy.created_at.desc()).all()

    def get_strategy(self, user_id: str, strategy_id: str) -> Optional[Strategy]:
        """Get a specific strategy by ID."""
        return self.db.query(Strategy).filter(
            Strategy.id == strategy_id,
            Strategy.user_id == user_id
        ).first()

    def delete_strategy(self, user_id: str, strategy_id: str) -> bool:
        """Delete a strategy."""
        strategy = self.db.query(Strategy).filter(
            Strategy.id == strategy_id,
            Strategy.user_id == user_id
        ).first()

        if not strategy:
            return False

        self.db.delete(strategy)
        self.db.commit()
        return True

    async def compare_strategies(
        self,
        user_id: str,
        strategy_ids: list[str]
    ) -> StrategyComparison:
        """Compare 2-3 strategies with AI analysis."""
        if len(strategy_ids) < 2:
            raise ValueError("At least 2 strategies required for comparison")
        if len(strategy_ids) > 3:
            raise ValueError("Maximum 3 strategies can be compared at once")

        # Load strategies
        strategies = []
        for sid in strategy_ids:
            strategy = self.get_strategy(user_id, sid)
            if not strategy:
                raise ValueError(f"Strategy {sid} not found")
            strategies.append({
                'id': strategy.id,
                'name': strategy.name,
                'description': strategy.description,
                'strategy_type': strategy.strategy_type,
                'risk_level': strategy.risk_level,
                'time_horizon': strategy.time_horizon,
                'assets': strategy.assets,
                'rationale': strategy.rationale,
                'risks': strategy.risks,
                'learning_points': strategy.learning_points,
            })

        # Get user profile
        profile = self.get_user_profile(user_id)

        # Build prompt and call AI
        prompt = self.build_comparison_prompt(strategies, profile)
        messages = [{"role": "user", "content": prompt}]
        system_prompt = "You are an investment education assistant. Compare investment strategies clearly and objectively."

        try:
            comparison_text = await self.ai_client.chat(messages, system_prompt, max_tokens=1024)
        except Exception as e:
            logger.error(f"Strategy comparison failed: {e}")
            raise ValueError("Strategy comparison failed, please try again.")

        # Save comparison
        comparison = StrategyComparison(
            user_id=user_id,
            strategy_ids=strategy_ids,
            comparison_text=comparison_text
        )
        self.db.add(comparison)
        self.db.commit()
        self.db.refresh(comparison)

        return comparison

    async def explain_strategy(
        self,
        user_id: str,
        strategy_id: str,
        question: str
    ) -> str:
        """Get AI explanation for a specific strategy question."""
        strategy = self.get_strategy(user_id, strategy_id)
        if not strategy:
            raise ValueError("Strategy not found")

        strategy_dict = {
            'name': strategy.name,
            'strategy_type': strategy.strategy_type,
            'assets': strategy.assets,
            'risk_level': strategy.risk_level,
            'time_horizon': strategy.time_horizon,
            'rationale': strategy.rationale,
        }

        profile = self.get_user_profile(user_id)
        prompt = self.build_explanation_prompt(strategy_dict, profile, question)
        messages = [{"role": "user", "content": prompt}]
        system_prompt = "You are an investment education assistant. Answer questions about investment strategies clearly and helpfully."

        try:
            explanation = await self.ai_client.chat(messages, system_prompt, max_tokens=1024)
        except Exception as e:
            logger.error(f"Strategy explanation failed: {e}")
            raise ValueError("Failed to generate explanation, please try again.")

        return explanation

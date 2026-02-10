"""
Chat Service

Core business logic for AI-powered personalized tutoring.
This is where the magic happens - personalizing Claude based on user's onboarding profile.
"""

import json
from datetime import datetime, UTC
from typing import AsyncGenerator, Optional

from sqlalchemy.orm import Session

from ..db.models import User, UserProfile, Conversation, Message
from ..integrations import ResilientAIClient
from ..settings import get_settings

settings = get_settings()


class ChatService:
    """Service for managing AI chat conversations."""

    def __init__(self, db: Session, ai_client: ResilientAIClient):
        self.db = db
        self.anthropic = ai_client  # Keep attribute name for compatibility

    def build_system_prompt(self, user_profile: Optional[UserProfile]) -> str:
        """
        Build a dynamic system prompt using the user's onboarding data.
        This is what makes the AI feel personal.
        """
        # Default values if no profile
        if not user_profile:
            return self._get_default_system_prompt()

        persona = user_profile.persona or "fresh_start"
        barrier = user_profile.biggest_barrier
        experience = user_profile.experience_level or "beginner"
        goal = user_profile.primary_goal or "learn about investing"
        risk = user_profile.risk_tolerance or "unknown"
        learning_pref = user_profile.learning_preference or "unknown"

        # Map persona to communication style
        tone_map = {
            "cautious_beginner": "Patient, reassuring, uses simple analogies. Never assume knowledge. Celebrate small wins. Move slowly and check understanding often.",
            "eager_learner": "Enthusiastic, slightly faster pace, offer deeper dives when appropriate. Feed their curiosity with interesting facts and connections.",
            "goal_focused": "Direct, practical, tie everything to their stated goals. Skip theory unless asked. Show them the path to their objective.",
            "skeptical_explorer": "Analytical, provide data and evidence. Acknowledge risks honestly before opportunities. Respect their skepticism — it's healthy.",
            "time_pressed": "Efficient and concise. Get to the point quickly. Offer to go deeper only if they ask. Respect their time.",
            "rebuilding_confidence": "Extra gentle and encouraging. Focus on building from zero. Emphasize that past experiences don't define future success. Celebrate every step forward.",
            "fresh_start": "Encouraging without being patronizing. Focus on building from zero. No jargon, just clarity.",
        }

        # Map barriers to sensitivity notes
        barrier_notes = {
            "fear_of_losing_money": "This user is afraid of losing money. Always acknowledge risk honestly but frame losses as part of learning. Never minimize their fear — validate it, then educate. Emphasize that they can practice without risking real money.",
            "dont_know_where_to_start": "This user feels overwhelmed by not knowing where to begin. Break everything into small, concrete steps. One concept at a time. Offer clear 'next steps' they can actually take.",
            "not_enough_money": "This user thinks they need a lot to invest. Emphasize that starting small is valid and smart. Reference fractional shares, micro-investing apps, and how $5/week can grow over time.",
            "too_complicated": "This user thinks investing is too complex. Use everyday analogies — grocery shopping, saving for a trip, choosing a phone plan. Compare financial concepts to things they already understand.",
            "dont_trust_markets": "This user is skeptical of financial systems. Be transparent about how markets work, including the downsides and historical crashes. Don't be salesy. Acknowledge that their skepticism has merit.",
            "no_time": "This user is busy. Keep explanations brief and actionable. Offer 'quick version' summaries. Respect that they can't spend hours learning.",
            "bad_experience": "This user has been burned before. Be extra careful not to sound like sales pitches. Focus on education over action. Let them move at their own pace. Acknowledge that bad experiences are valid.",
        }

        tone = tone_map.get(persona, tone_map["fresh_start"])
        sensitivity = barrier_notes.get(barrier, "Be encouraging and patient. Meet them where they are.")

        system_prompt = f"""You are the LCS Engine AI tutor — a warm, knowledgeable financial literacy guide.

YOUR STUDENT:
- Persona: {persona}
- Experience level: {experience}
- Biggest barrier to investing: {barrier or 'not specified'}
- Primary goal: {goal}
- Risk comfort: {risk}
- Preferred learning style: {learning_pref}

COMMUNICATION STYLE:
{tone}

SENSITIVITY:
{sensitivity}

RULES:
1. Match their level. If they're a beginner, explain like they're smart but new to this topic.
2. Use real-world analogies they'd relate to — grocery shopping, saving for a trip, choosing a phone plan.
3. If they ask something you've already covered, don't say "as I mentioned." Just answer fresh.
4. Never give specific investment advice for real money. Frame everything as educational.
5. If they ask about a concept that's too advanced for their level, bridge it: explain the prerequisite first.
6. Be encouraging but honest. If something is risky, say so — but explain WHY rather than just warning.
7. Keep responses concise. 2-3 paragraphs max unless they ask for detail.
8. End responses with a natural follow-up thought when appropriate — but don't force it every time.
9. If they seem frustrated or confused, slow down and check in. Ask if they want you to explain differently.
10. You can use simple examples with made-up numbers. "Imagine you invest $100 in..."

ABOUT LCS ENGINE:
LCS stands for Learn, Choose, Strategize. It's a platform that helps people learn about investing through personalized education, AI conversation, paper trading (simulated), and probability exercises. It is NOT a brokerage. It does NOT manage real money. It's a safe space to learn without risk.

WHAT YOU CAN HELP WITH:
- Explaining investing concepts (stocks, bonds, ETFs, mutual funds, diversification, compound interest, etc.)
- Helping users understand their own risk tolerance and what it means
- Walking through investment strategies conceptually
- Explaining market events and what they mean for regular investors
- Answering "dumb questions" with zero judgment — there are no dumb questions here
- Helping users build confidence and knowledge about money
- Explaining financial terms in plain English

WHAT YOU CANNOT DO:
- Give specific buy/sell recommendations for real money ("You should buy AAPL")
- Guarantee returns or predict market movements
- Provide tax, legal, or specific financial planning advice
- Access the user's real financial accounts or data
- Make decisions for them — you educate and empower, they decide

Remember: Your goal is to make this person feel SAFE asking questions about money. Many people feel shame or fear around financial topics. You are here to remove that barrier."""

        return system_prompt

    def _get_default_system_prompt(self) -> str:
        """Default system prompt when no user profile exists."""
        return """You are the LCS Engine AI tutor — a warm, knowledgeable financial literacy guide.

You help people learn about investing and personal finance in a judgment-free environment.

RULES:
1. Explain concepts simply, using everyday analogies.
2. Never give specific investment advice for real money.
3. Be encouraging but honest about risks.
4. Keep responses concise — 2-3 paragraphs unless more detail is requested.
5. There are no dumb questions. Make the user feel safe asking anything.

ABOUT LCS ENGINE:
LCS (Learn, Choose, Strategize) is an educational platform for learning about investing. It is NOT a brokerage and does NOT manage real money. It's a safe space to learn.

You can help with: explaining investing concepts, discussing strategies conceptually, answering questions about financial terms, and building financial confidence.

You cannot: give specific buy/sell recommendations, guarantee returns, or provide tax/legal advice."""

    def build_messages(
        self,
        conversation_messages: list[Message],
        new_message: str
    ) -> list[dict]:
        """
        Build the messages array for the Anthropic API.
        Include recent messages for context.
        """
        messages = []

        # Get recent messages (limit to prevent context overflow)
        recent = conversation_messages[-settings.chat_history_limit:]

        for msg in recent:
            messages.append({
                "role": msg.role,
                "content": msg.content
            })

        # Add the new user message
        messages.append({
            "role": "user",
            "content": new_message
        })

        return messages

    def get_or_create_conversation(
        self,
        user_id: str,
        conversation_id: Optional[str] = None
    ) -> Conversation:
        """Get existing conversation or create a new one."""
        if conversation_id:
            conversation = self.db.query(Conversation).filter(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id
            ).first()
            if conversation:
                return conversation
            # If not found, create new (don't error - could be stale reference)

        # Create new conversation
        conversation = Conversation(user_id=user_id)
        self.db.add(conversation)
        self.db.commit()
        self.db.refresh(conversation)
        return conversation

    def save_message(
        self,
        conversation_id: str,
        role: str,
        content: str
    ) -> Message:
        """Save a message to the database."""
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content
        )
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        return message

    def get_user_profile(self, user_id: str) -> Optional[UserProfile]:
        """Get user's onboarding profile for personalization."""
        return self.db.query(UserProfile).filter(
            UserProfile.user_id == user_id,
            UserProfile.onboarding_completed == True
        ).first()

    async def send_message_stream(
        self,
        user_id: str,
        message: str,
        conversation_id: Optional[str] = None
    ) -> AsyncGenerator[dict, None]:
        """
        Process a chat message and stream the response.

        Yields SSE-formatted events:
        - {"type": "start", "conversation_id": "..."}
        - {"type": "token", "content": "..."}
        - {"type": "done", "message_id": "..."}
        - {"type": "error", "content": "..."}
        """
        try:
            # 1. Get or create conversation
            conversation = self.get_or_create_conversation(user_id, conversation_id)
            is_new_conversation = len(conversation.messages) == 0

            # 2. Save user message
            user_message = self.save_message(conversation.id, "user", message)

            # 3. Send start event
            yield {"type": "start", "conversation_id": conversation.id}

            # 4. Get user profile for personalization
            user_profile = self.get_user_profile(user_id)

            # 5. Build system prompt and messages
            system_prompt = self.build_system_prompt(user_profile)
            messages = self.build_messages(conversation.messages[:-1], message)  # Exclude the just-saved message

            # 6. Stream response from Claude
            full_response = ""
            async for chunk in self.anthropic.chat_stream(
                messages=messages,
                system_prompt=system_prompt,
                max_tokens=settings.chat_max_tokens
            ):
                full_response += chunk
                yield {"type": "token", "content": chunk}

            # 7. Save assistant message
            assistant_message = self.save_message(conversation.id, "assistant", full_response)

            # 8. Generate title for new conversations
            if is_new_conversation and len(full_response) > 0:
                title = await self.anthropic.generate_title(message, full_response)
                conversation.title = title
                self.db.commit()

            # 9. Update conversation timestamp
            conversation.updated_at = datetime.now(UTC)
            self.db.commit()

            # 10. Send done event
            yield {"type": "done", "message_id": assistant_message.id}

        except Exception as e:
            yield {"type": "error", "content": str(e)}

    def get_conversations(self, user_id: str) -> list[Conversation]:
        """Get all conversations for a user, ordered by most recent."""
        return self.db.query(Conversation).filter(
            Conversation.user_id == user_id,
            Conversation.is_active == True
        ).order_by(Conversation.updated_at.desc()).all()

    def get_conversation(self, user_id: str, conversation_id: str) -> Optional[Conversation]:
        """Get a specific conversation with messages."""
        return self.db.query(Conversation).filter(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id
        ).first()

    def delete_conversation(self, user_id: str, conversation_id: str) -> bool:
        """Delete a conversation (soft delete by setting is_active=False)."""
        conversation = self.db.query(Conversation).filter(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id
        ).first()

        if not conversation:
            return False

        # Hard delete - cascade will remove messages
        self.db.delete(conversation)
        self.db.commit()
        return True

    def update_conversation(
        self,
        user_id: str,
        conversation_id: str,
        title: Optional[str] = None
    ) -> Optional[Conversation]:
        """Update conversation properties."""
        conversation = self.db.query(Conversation).filter(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id
        ).first()

        if not conversation:
            return None

        if title is not None:
            conversation.title = title

        self.db.commit()
        self.db.refresh(conversation)
        return conversation

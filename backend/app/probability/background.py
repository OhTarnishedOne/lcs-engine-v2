"""
Background Market Automation Task

Runs in the FastAPI lifespan as an asyncio task. Checks for market resolutions
and generates new markets every 6 hours. Fails silently — logs errors but
never crashes.
"""

import asyncio
import logging

from ..database import SessionLocal
from ..integrations.fred import FredClient
from ..settings import get_settings
from .resolution import MarketAutomation

logger = logging.getLogger(__name__)


async def market_automation_loop():
    """Background loop that checks for resolutions and generates new markets.

    Runs immediately on startup, then every 6 hours. Catches all exceptions.
    """
    settings = get_settings()

    # Run first check after a short delay (let app finish startup)
    await asyncio.sleep(30)

    while True:

        db = None
        fred = None
        try:
            db = SessionLocal()
            fred = FredClient(api_key=settings.fred_api_key)
            automation = MarketAutomation(db, fred)

            # 1. Resolve any markets with available data
            result = await automation.check_and_resolve()
            if result["resolved"]:
                logger.info(
                    f"Auto-resolved {len(result['resolved'])} markets"
                )

            # 2. Generate next period's markets
            gen_result = await automation.generate_upcoming_markets()
            if gen_result["created"]:
                logger.info(
                    f"Created {len(gen_result['created'])} new markets"
                )

        except Exception as e:
            logger.error(f"Market automation error: {e}")
        finally:
            if db:
                db.close()
            if fred:
                await fred.close()

        # Wait 6 hours before next run
        await asyncio.sleep(6 * 60 * 60)

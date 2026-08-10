import logging
from typing import List, Optional
from urllib.parse import urlparse
from sqlmodel import select
from app.db.database import async_session_maker, init_db
from app.db.models import EpisodicMemoryRecord

logger = logging.getLogger(__name__)

class MemoryManager:
    """
    Episodic memory store that remembers successful route paths, dynamic locators,
    and form payloads across test runs to accelerate discovery and execution.
    """
    @staticmethod
    async def record_successful_action(route_url: str, action_type: str, selector: str, payload: Optional[str] = None):
        parsed = urlparse(route_url)
        domain = parsed.hostname or ""

        await init_db()

        async with async_session_maker() as session:
            statement = select(EpisodicMemoryRecord).where(
                EpisodicMemoryRecord.domain == domain,
                EpisodicMemoryRecord.route_url == route_url,
                EpisodicMemoryRecord.selector == selector
            )
            result = await session.execute(statement)
            existing = result.scalars().first()

            if existing:
                existing.success_count += 1
                session.add(existing)
            else:
                mem = EpisodicMemoryRecord(
                    domain=domain,
                    route_url=route_url,
                    action_type=action_type,
                    selector=selector,
                    successful_payload=payload
                )
                session.add(mem)
            await session.commit()
            logger.debug(f"EpisodicMemory recorded action '{action_type}' for {selector} on {route_url}")

    @staticmethod
    async def recall_domain_memory(target_url: str) -> List[EpisodicMemoryRecord]:
        parsed = urlparse(target_url)
        domain = parsed.hostname or ""

        await init_db()

        async with async_session_maker() as session:
            statement = select(EpisodicMemoryRecord).where(
                EpisodicMemoryRecord.domain == domain
            ).order_by(EpisodicMemoryRecord.success_count.desc())
            result = await session.execute(statement)
            memories = list(result.scalars().all())
            logger.info(f"Recalled {len(memories)} episodic memory records for domain: {domain}")
            return memories

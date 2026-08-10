import asyncio
from app.db.database import init_db, async_session_maker
from app.db.models import RunRecord
from app.models.state import ChaosPilotState
from app.api.runs import save_run_to_db

async def main():
    await init_db()
    state = ChaosPilotState(run_id="RUN-MYSQL-001", target_url="http://127.0.0.1:8888")
    await save_run_to_db(state)
    
    async with async_session_maker() as session:
        rec = await session.get(RunRecord, "RUN-MYSQL-001")
        if rec:
            print(f"VERIFIED MYSQL PERSISTENCE! Record ID: {rec.id}, Target: {rec.target_url}, Status: {rec.status}")

if __name__ == "__main__":
    asyncio.run(main())

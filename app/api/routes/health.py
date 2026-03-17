from fastapi import APIRouter
from sqlalchemy import text
from starlette.responses import JSONResponse

from app.core.database import ReadSessionLocal
from app.core.redis import redis_client

router = APIRouter(tags=["observability"])


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/readiness")
async def readiness() -> dict[str, str]:
    try:
        async with ReadSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        await redis_client.ping()
        return {"status": "ready"}
    except Exception:
        return JSONResponse(status_code=503, content={"status": "not_ready"})

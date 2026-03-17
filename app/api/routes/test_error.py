from fastapi import APIRouter

router = APIRouter(tags=["debug"])

@router.get("/test-500")
async def trigger_500():
    """Manually trigger a 500 error for debugging."""
    raise ValueError("Debug: Simulated 500 Internal Server Error")

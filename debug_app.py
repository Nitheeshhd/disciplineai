import uvicorn
import os
from app.core.config import get_settings

if __name__ == "__main__":
    settings = get_settings()
    
    # Development-ready uvicorn configuration
    # --reload: restarts on code change
    # --log-level debug: shows full details
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
        log_level="debug",
        access_log=True,
    )

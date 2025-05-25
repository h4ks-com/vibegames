import asyncio
from concurrent.futures import ThreadPoolExecutor

import uvicorn

from app.settings import settings

WORKERS = 4  # Number of worker threads for handling requests


if __name__ == "__main__":
    app_identifier = "app:app"
    asyncio.get_event_loop().set_default_executor(ThreadPoolExecutor(max_workers=WORKERS))

    uvicorn.run(
        app_identifier,
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.RELOAD,
        workers=WORKERS,
        timeout_keep_alive=15,
        log_level="info",
    )

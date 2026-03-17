import asyncio
import traceback
from app.main import app, lifespan

async def run_test():
    try:
        print("Starting lifespan test...")
        async with lifespan(app):
            print("Lifespan started successfully!")
    except Exception as e:
        with open('error_log.txt', 'w') as f:
            traceback.print_exc(file=f)

if __name__ == "__main__":
    asyncio.run(run_test())

import asyncio

from src.main import ResourceCollector

if __name__ == "__main__":
    c = ResourceCollector()
    asyncio.run(c.collect())

import asyncio
import logging

from collector.main import ResourceCollector

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    c = ResourceCollector()
    asyncio.run(c.collect())

"""
Detection module entry point.

Allows running the detection service with:
    python -m detection
"""

from detection.main import main
import asyncio

if __name__ == "__main__":
    asyncio.run(main())

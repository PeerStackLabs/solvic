import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from server import main
import asyncio

if __name__ == "__main__":
    asyncio.run(main())

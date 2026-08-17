"""Adds the project root to sys.path so `scripts/*.py` can `import src.*`
when run directly (e.g. `python scripts/generate_data.py`)."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

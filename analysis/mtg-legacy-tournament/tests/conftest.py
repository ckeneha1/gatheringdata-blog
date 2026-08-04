"""Make the mtg-legacy-tournament scripts importable from tests."""

import sys
from pathlib import Path

_TOURNAMENT_DIR = Path(__file__).resolve().parent.parent   # analysis/mtg-legacy-tournament
if str(_TOURNAMENT_DIR) not in sys.path:
    sys.path.insert(0, str(_TOURNAMENT_DIR))

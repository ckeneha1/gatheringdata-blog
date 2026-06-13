"""Make the mtg-primers scripts and the shared analysis modules importable."""

import sys
from pathlib import Path

_PRIMERS_DIR = Path(__file__).resolve().parent.parent   # analysis/mtg-primers
_ANALYSIS_DIR = _PRIMERS_DIR.parent                      # analysis/

for p in (str(_PRIMERS_DIR), str(_ANALYSIS_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

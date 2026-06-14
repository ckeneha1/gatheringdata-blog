"""Make value_model and the shared analysis modules importable from tests."""

import sys
from pathlib import Path

_MODEL_DIR = Path(__file__).resolve().parent.parent     # analysis/legacy-value-model
_ANALYSIS_DIR = _MODEL_DIR.parent                        # analysis/

for p in (str(_MODEL_DIR), str(_ANALYSIS_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

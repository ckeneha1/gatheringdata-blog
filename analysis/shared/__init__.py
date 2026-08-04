"""
shared — cross-analysis Python modules for gatheringdata.blog.

Modules here must be stdlib-only (no third-party imports) so that any
analysis subproject can use them regardless of its own dependency set.
Import pattern from a subproject script:

    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from shared.ability_features import card_feature_set
"""

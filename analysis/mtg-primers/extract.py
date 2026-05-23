"""
extract.py — LLM extraction pipeline for Legacy primer value signals.

Feeds each deck primer to Claude and extracts cards that are considered
disproportionately valuable in Legacy beyond raw ability-per-mana efficiency,
along with structured reasons why.

Uses the Batches API (50% cost savings) with JSON-schema structured outputs.

Usage:
    uv run python extract.py submit    # submit batch, saves batch ID to data/batch_id.txt
    uv run python extract.py poll      # check batch status
    uv run python extract.py collect   # collect results when batch is done
    uv run python extract.py run       # submit + poll every 60s + collect (blocking)
"""

import json
import re
import sys
import time
from pathlib import Path

import anthropic
from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
from anthropic.types.messages.batch_create_params import Request
from pydantic import BaseModel

# ── paths ──────────────────────────────────────────────────────────────────────
DATA_DIR = Path(__file__).parent / "data"
PRIMERS_JSON = DATA_DIR / "primers.json"
RAW_DIR = DATA_DIR / "raw"
BATCH_ID_FILE = DATA_DIR / "batch_id.txt"
RESULTS_FILE = DATA_DIR / "extractions.json"

# ── config ─────────────────────────────────────────────────────────────────────
MODEL = "claude-opus-4-6"
MAX_CHARS_PER_PRIMER = 20_000  # cap to first ~5K tokens — covers primer content, skips long thread tails
MAX_TOKENS = 4096
BATCH_CHUNK_SIZE = 20  # split into chunks to keep POST body under ~500KB

# ── value signal taxonomy ──────────────────────────────────────────────────────
# Each signal describes a dimension of Legacy power that ability-per-mana misses.
VALUE_SIGNALS = [
    "free_spell",          # cast for 0 mana or an alternative cost (Force of Will, Daze)
    "mana_denial",         # destroys or locks down opponent's mana (Wasteland, Rishadan Port)
    "mana_acceleration",   # produces more mana than it costs (Dark Ritual, Ancient Tomb, Gaea's Cradle)
    "cantrip",             # replaces itself while doing something else (Brainstorm, Ponder)
    "tutor",               # finds specific cards (Imperial Seal, Green Sun's Zenith)
    "combo_piece",         # critical enabling piece of a combo win
    "lock_piece",          # restricts opponent's options asymmetrically (Blood Moon, Chalice of the Void)
    "graveyard",           # leverages or enables graveyard as resource
    "resilience",          # hard to permanently deal with (recursion, protection, indestructible)
    "protection",          # shields your own key pieces (Mother of Runes, Veil of Summer)
    "hate_piece",          # specifically hates on prevalent Legacy strategies
    "card_advantage",      # generates more cards than its mana cost would predict
    "tempo",               # generates tempo disproportionate to mana spent
    "archetype_synergy",   # uniquely powerful in this specific archetype's engine
]

# ── schema ─────────────────────────────────────────────────────────────────────
class CardInsight(BaseModel):
    card_name: str
    value_signals: list[str]
    why_good: str  # 1-2 sentences: why it overperforms its mana cost in Legacy


class PrimerExtraction(BaseModel):
    archetype: str
    key_cards: list[CardInsight]
    format_insight: str  # what this deck exploits about Legacy's power structure


def _output_schema() -> dict:
    return {
        "type": "object",
        "properties": {
            "archetype": {"type": "string"},
            "key_cards": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "card_name": {"type": "string"},
                        "value_signals": {
                            "type": "array",
                            "items": {"type": "string", "enum": VALUE_SIGNALS},
                        },
                        "why_good": {"type": "string"},
                    },
                    "required": ["card_name", "value_signals", "why_good"],
                    "additionalProperties": False,
                },
            },
            "format_insight": {"type": "string"},
        },
        "required": ["archetype", "key_cards", "format_insight"],
        "additionalProperties": False,
    }


# ── system prompt ──────────────────────────────────────────────────────────────
SYSTEM_PROMPT = f"""You are analyzing Legacy Magic: the Gathering deck primers to extract structured information about which cards are considered disproportionately powerful relative to their mana cost, and why.

CONTEXT
We have an "ability-per-mana" metric that scores cards by how much raw ability they deliver per mana spent. This metric systematically undervalues certain cards that dominate Legacy for format-specific reasons. For example, Force of Will ranks in the bottom 5% by mana efficiency (it costs 3UU for a Counterspell effect), yet it appears in 55%+ of Legacy decks — because it can be cast for free. Your job is to identify and explain these overperformers per archetype.

WHAT TO EXTRACT
Focus on cards the primer author singles out as:
- Especially powerful, format-defining, or surprisingly good for their cost
- Strong because of *how* they're played, not just raw stats
- Exploiting specific Legacy power levers: free spells, mana denial, lock pieces, graveyard, etc.

DO NOT include:
- Cards mentioned only in decklists without author commentary
- Cards praised purely for raw power/stats ("this 4/4 for 4 is great")
- Cards that are simply generically good in any format without format-specific edge

VALUE SIGNALS (use only these):
{chr(10).join(f"- {s}" for s in VALUE_SIGNALS)}

NOTE: The primer text is raw-scraped from forum threads. It may contain navigation artifacts, pagination numbers, user profile text, and signatures. Focus on actual primer content — the strategic explanations of card choices.

Return key_cards for cards that genuinely overperform their mana cost in Legacy, and a format_insight summarizing what power lever this archetype exploits."""


# ── helpers ────────────────────────────────────────────────────────────────────
def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def _load_primers() -> dict[str, str]:
    """Load all primers: archetype -> text (truncated to MAX_CHARS_PER_PRIMER)."""
    meta = json.loads(PRIMERS_JSON.read_text())
    primers = {}
    for archetype in meta:
        path = RAW_DIR / f"{_slug(archetype)}.txt"
        if not path.exists():
            print(f"WARNING: missing raw file for '{archetype}' ({path.name})")
            continue
        text = path.read_text(encoding="utf-8")
        if len(text) > MAX_CHARS_PER_PRIMER:
            text = text[:MAX_CHARS_PER_PRIMER]
        primers[archetype] = text
    return primers


# ── commands ───────────────────────────────────────────────────────────────────
def _make_request(archetype: str, text: str, schema: dict) -> Request:
    return Request(
        custom_id=_slug(archetype),
        params=MessageCreateParamsNonStreaming(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=SYSTEM_PROMPT,
            messages=[{
                "role": "user",
                "content": f"Archetype: {archetype}\n\nPrimer text:\n{text}",
            }],
            output_config={
                "format": {
                    "type": "json_schema",
                    "schema": schema,
                }
            },
        ),
    )


def submit_batch() -> list[str]:
    client = anthropic.Anthropic()
    primers = _load_primers()
    schema = _output_schema()

    all_requests = [_make_request(arch, text, schema) for arch, text in primers.items()]

    # Split into chunks to keep each POST body manageable
    chunks = [
        all_requests[i : i + BATCH_CHUNK_SIZE]
        for i in range(0, len(all_requests), BATCH_CHUNK_SIZE)
    ]

    batch_ids = []
    for i, chunk in enumerate(chunks):
        print(f"Submitting chunk {i + 1}/{len(chunks)} ({len(chunk)} primers)...")
        batch = client.messages.batches.create(requests=chunk)
        print(f"  Batch ID: {batch.id}")
        batch_ids.append(batch.id)

    BATCH_ID_FILE.write_text("\n".join(batch_ids))
    print(f"\nAll {len(all_requests)} primers submitted across {len(chunks)} batch(es).")
    return batch_ids


def _load_batch_ids() -> list[str]:
    return [line.strip() for line in BATCH_ID_FILE.read_text().splitlines() if line.strip()]


def poll_batch(batch_ids: list[str] | None = None) -> bool:
    """Poll all batches. Returns True when all are done."""
    client = anthropic.Anthropic()
    if batch_ids is None:
        batch_ids = _load_batch_ids()
    all_done = True
    for batch_id in batch_ids:
        batch = client.messages.batches.retrieve(batch_id)
        c = batch.request_counts
        print(
            f"[{batch.id}] {batch.processing_status} — "
            f"processing={c.processing}  succeeded={c.succeeded}  errored={c.errored}"
        )
        if batch.processing_status != "ended":
            all_done = False
    return all_done


def collect_results(batch_ids: list[str] | None = None) -> None:
    client = anthropic.Anthropic()
    if batch_ids is None:
        batch_ids = _load_batch_ids()

    results = {}
    errors = []

    for batch_id in batch_ids:
        batch = client.messages.batches.retrieve(batch_id)
        if batch.processing_status != "ended":
            print(f"Batch {batch_id} not done yet (status: {batch.processing_status}).")
            sys.exit(1)

        for result in client.messages.batches.results(batch_id):
            if result.result.type == "succeeded":
                msg = result.result.message
                text = next((b.text for b in msg.content if b.type == "text"), "")
                try:
                    data = json.loads(text)
                    extraction = PrimerExtraction.model_validate(data)
                    results[result.custom_id] = extraction.model_dump()
                except Exception as e:
                    errors.append(f"{result.custom_id}: parse error — {e}\n  raw: {text[:200]}")
            else:
                errors.append(f"{result.custom_id}: {result.result.type}")

    if errors:
        print(f"\n{len(errors)} error(s):")
        for e in errors:
            print(f"  {e}")

    RESULTS_FILE.write_text(json.dumps(results, indent=2))
    print(f"\nSaved {len(results)} extractions → {RESULTS_FILE}")


def run_all() -> None:
    batch_ids = submit_batch()
    print("\nPolling every 60s until all batches done...")
    while True:
        time.sleep(60)
        if poll_batch(batch_ids):
            break
    collect_results(batch_ids)


# ── main ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "help"
    match cmd:
        case "submit":
            submit_batch()
        case "poll":
            poll_batch()
        case "collect":
            collect_results()
        case "run":
            run_all()
        case _:
            print(__doc__)

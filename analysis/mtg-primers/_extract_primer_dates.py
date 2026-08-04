"""Best-effort primer writing-date extractor for primer_dates.json.

Run `build_exclusions.py init-dates` first to generate the null template, then
this to populate it (review-first; pass --write to commit). Keys off the primer
slug (slugify of the primers.json key) -> data/raw/<slug>.txt.

Heuristics by source:
  mtgsalvation : earliest 'Mon DD, YYYY' post date ~ thread first post.
                 (Numeric MM/DD/YYYY there are user 'member since' dates -> ignored.)
                 A date within 30d of the scrape is scrape-time noise -> null.
  articles     : earliest dated token near the top (byline), any common format.
  wiki / yt    : usually undatable -> null (degrades to fetched_at + undated flag).

These dates are conditioning lower bounds (brief 2.4), not authoritative bylines;
date_basis records provenance per entry so any call is auditable/overridable.
"""
import json, re, sys
from datetime import date, timedelta
from pathlib import Path

BASE = Path(__file__).resolve().parent
RAW = BASE / "data" / "raw"
primers = json.load(open(BASE / "data" / "primers.json"))
DATES_PATH = BASE / "data" / "primer_dates.json"
pdates = json.load(open(DATES_PATH))

MON = {m: i for i, m in enumerate(
    ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], 1)}
RE_MON = re.compile(r"\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.? (\d{1,2}),? (20\d{2})\b")
RE_MDY = re.compile(r"\b(\d{1,2})/(\d{1,2})/(\d{2,4})\b")
RE_ISO = re.compile(r"\b(20\d{2})-(\d{2})-(\d{2})\b")


def slugify(s):
    return re.sub(r"_+", "_", re.sub(r"[^a-z0-9]+", "_", s.lower())).strip("_")


def _safe(y, m, d):
    try:
        return date(y, m, d)
    except ValueError:
        return None


def mon_dates(t):
    return [d for mt in RE_MON.finditer(t)
            if (d := _safe(int(mt.group(3)), MON[mt.group(1)], int(mt.group(2))))]


def all_dates(t):
    out = mon_dates(t)
    for mt in RE_MDY.finditer(t):
        mo, dd, y = int(mt.group(1)), int(mt.group(2)), int(mt.group(3))
        y = y + 2000 if y < 100 else y
        if (d := _safe(y, mo, dd)):
            out.append(d)
    for mt in RE_ISO.finditer(t):
        if (d := _safe(int(mt.group(1)), int(mt.group(2)), int(mt.group(3)))):
            out.append(d)
    return out


rows = []
for arch in [k for k in pdates if k != "_format"]:
    meta = primers.get(arch, {})
    source = meta.get("source", "")
    url = meta.get("url", "")
    fetched = (meta.get("fetched_at", "") or "")[:10]
    fetched_d = date.fromisoformat(fetched) if fetched else None
    page = re.search(r"page=(\d+)", url)
    raw = RAW / f"{slugify(arch)}.txt"
    chosen = basis = note = None
    if not raw.exists():
        rows.append((arch, source, None, f"RAW MISSING ({slugify(arch)}.txt)", "")); continue
    text = raw.read_text(errors="ignore")

    def ok(d):
        return d and d.year >= 2005 and (not fetched_d or d <= fetched_d)

    if source == "mtgsalvation":
        cands = [d for d in mon_dates(text) if ok(d)]
        if cands:
            chosen = min(cands)
            if fetched_d and chosen >= fetched_d - timedelta(days=30):
                chosen, basis = None, "only ~scrape-time dates found -> null (undated)"
            else:
                basis = "earliest forum post (Mon DD, YYYY) ~ thread first post"
                if page and page.group(1) != "1":
                    note = f"scrape is page {page.group(1)}; earliest post on that page, not thread start"
    else:
        cands = [d for d in all_dates(text[:4000]) if ok(d)]
        if cands:
            chosen = min(cands)
            basis = f"earliest dated token near top of {source or 'web'} article (byline)"
    if chosen is None and basis is None:
        basis = "no date found -> null (degrades to fetched_at)"
    rows.append((arch, source, chosen.isoformat() if chosen else None, basis, note or ""))

filled = sum(1 for r in rows if r[2])
print(f"{'ARCHETYPE':26} {'SOURCE':13} {'DATE':12} BASIS")
print("-" * 104)
for arch, source, d, basis, note in rows:
    print(f"{arch:26.26} {source:13.13} {str(d):12} {basis}{('  ['+note+']') if note else ''}")
print("-" * 104)
print(f"FILLED {filled}/{len(rows)}  |  NULL {len(rows)-filled}")

if "--write" in sys.argv:
    for arch, source, d, basis, note in rows:
        if isinstance(pdates.get(arch), dict):
            pdates[arch]["primer_date"] = d
            pdates[arch]["date_basis"] = basis
            pdates[arch]["notes"] = note
    DATES_PATH.write_text(json.dumps(pdates, indent=2) + "\n")
    print(f"\nWROTE {DATES_PATH}")

#!/usr/bin/env python3
"""
PongNews Research Radar — expanded study discovery for pongnews.com.

Problem: the daily generator searches only ("table tennis" OR "ping pong") on
PubMed, and after 76 articles that well is dry — daily sweeps have been
silent for days ("no new study"). Meanwhile adjacent literature (racket
sports, open-skill exercise, exergaming) is untapped.

This radar sweeps 4 tiers of queries, dedups against the research bank and
published articles, scores candidates, and emits a ranked story backlog
(JSON + SQLite) that the daily pipeline / writer sessions can draw from.

Usage:
  python3 research_radar.py scan     # run a full scan, print digest
  python3 research_radar.py list     # show current backlog from DB

Stdlib only. No secrets.
"""

import json
import re
import sqlite3
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

def _find_repo_root():
    """Walk up from this file to find the pongnews repo (has references/research-bank.md)."""
    for candidate in [Path(__file__).resolve().parent] + list(Path(__file__).resolve().parents):
        if (candidate / "references" / "research-bank.md").exists():
            return candidate
    return Path(__file__).resolve().parent.parent


PROJECT_DIR = _find_repo_root()
ARTICLES_DIR = PROJECT_DIR / "src" / "content" / "articles"
RESEARCH_BANK = PROJECT_DIR / "references" / "research-bank.md"
CANDIDATES_JSON = PROJECT_DIR / "references" / "radar-candidates.json"

# In-container path override (R10 deployment mounts ~/app-data/pongnews-radar)
DATA_DIR = Path("/app/data") if Path("/app/data").exists() else PROJECT_DIR / "data"
DB_PATH = DATA_DIR / "radar.db"

EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
UA = "Mozilla/5.0 (pongnews-research-radar; research discovery for pongnews.com)"

# Tier definitions: (tier, weight, query, days_back, note)
# Queries use PubMed [tiab] (title/abstract) field tags.
TIERS = [
    (
        1, 50,
        '("table tennis"[tiab] OR "ping pong"[tiab]) AND (health[tiab] OR cognit*[tiab] '
        'OR brain[tiab] OR aging[tiab] OR ageing[tiab] OR older[tiab] OR elderly[tiab] '
        'OR longevit*[tiab] OR mortalit*[tiab] OR rehabilitat*[tiab] '
        'OR parkinson*[tiab] OR stroke[tiab] OR dementia[tiab] OR depress*[tiab] '
        'OR anxiet*[tiab] OR "quality of life"[tiab] OR sedentary[tiab] OR obesity[tiab] '
        'OR wheelchair[tiab] OR "intellectual disability"[tiab] OR autism[tiab] OR "down syndrome"[tiab])',
        540,
        "Direct table tennis study — headline-ready",
    ),
    (
        2, 30,
        '("racket sport"[tiab] OR "racquet sport"[tiab] OR "racket sports"[tiab] '
        'OR "racquet sports"[tiab] OR badminton[tiab] OR tennis[tiab] OR squash[tiab]) '
        'AND (longevit*[tiab] OR mortalit*[tiab] OR cognit*[tiab] OR dementia[tiab] '
        'OR "healthy aging"[tiab] OR "healthy ageing"[tiab])',
        365,
        "Racket-sports evidence — frame as what it means for table tennis",
    ),
    (
        3, 25,
        '("open skill"[tiab] OR "open-skill"[tiab] OR "open motor skill"[tiab] '
        'OR "open loop sport"[tiab] OR "interceptive task"[tiab]) '
        'AND (cognit*[tiab] OR brain[tiab] OR aging[tiab] OR ageing[tiab] OR executive[tiab])',
        730,
        "Open-skill mechanism — explains WHY table tennis beats closed-skill exercise",
    ),
    (
        4, 20,
        '(exergam*[tiab] OR "virtual reality exercise"[tiab] OR "VR exercise"[tiab] '
        'OR "video game exercise"[tiab]) AND (older[tiab] OR elderly[tiab] '
        'OR parkinson*[tiab] OR dementia[tiab] OR cognit*[tiab]) '
        'AND (motor[tiab] OR balanc*[tiab] OR cognit*[tiab])',
        365,
        "Exergaming/VR — bridge to VR table tennis for home training",
    ),
]

CATEGORY_MAP = [
    ("Rehabilitation", r"parkinson|stroke|rehabilitat|recover|multiple sclerosis|cerebral palsy"),
    ("Cognitive Health", r"cognit|dementia|alzheimer|brain|memory|executive|attention"),
    ("Longevity", r"longevit|mortalit|lifespan|death|aging|ageing|survival"),
    ("Physical Health", r"balance|fall|bone|fitness|cardiovascular|heart|strength|obesity|sedentary"),
    ("Mental Health", r"depress|anxiet|stress|mood|psycholog|social|wellbeing|well-being|quality of life"),
]

PUBTYPE_BONUS = [
    (r"meta-?analysis", 30),
    (r"systematic review", 25),
    (r"randomized", 20),
    (r"clinical trial", 12),
    (r"review", 5),
]

HIGH_SIGNAL_KEYWORDS = [
    "dementia", "alzheimer", "parkinson", "mortality", "longevity",
    "cognition", "cognitive", "executive", "brain", "fall", "balance",
    "elderly", "older adults", "aging", "depression", "quality of life",
]

# Positive health-relevance gate: a study must match at least one pattern to
# be a candidate at all. PongNews is a health site, not a performance site.
HEALTH_RELEVANCE = re.compile(
    r"cognit|brain|dementia|alzheimer|parkinson|stroke|multiple sclerosis"
    r"|older adult|older people|elderly|aging|ageing|longevit|mortalit"
    r"|sedentary|obes|overweight|depress|anxiet|stress|quality of life"
    r"|well-?being|rehabilit|fall|bone mineral|cardiovascular|metabolic"
    r"|insulin|blood pressure|wheelchair|adaptive|intellectual disability"
    r"|autism|down syndrome|special need|mental health|sleep|executive function"
    r"|children|adolescen|youth|student",
    re.IGNORECASE,
)


def is_health_relevant(text):
    return bool(HEALTH_RELEVANCE.search(text))


# Hard rejects. "Ping-pong" appears in medicine for non-sport artifacts
# (ping-pong gaze, ping-pong catheter valves, ping-pong skull fractures).
CLINICAL_ARTIFACT = re.compile(
    r"catheter|perforation|gaze|valve|skull|unconscious|fracture|embolization"
    r"|tumor|carcinoma|surgery|surgical",
    re.IGNORECASE,
)
PURE_PERFORMANCE = re.compile(
    r"biomechanic|kinematic|synerg|topspin|counter-?movement jump|notational"
    r"|match analysis|serve performance|serve speed|reaction time in elite|wingate"
    r"|nutritional supplementation|dietary supplement",
    re.IGNORECASE,
)
HEALTH_POPULATION = re.compile(
    r"older|elderly|aging|ageing|parkinson|dementia|stroke patient|children"
    r"|adolescen|obese|obesity|sedentary|cognitive impairment|down syndrome"
    r"|intellectual disability|autism|wheelchair",
    re.IGNORECASE,
)


def is_offbrand(title, abstract):
    has_table_tennis = "table tennis" in (title + abstract).lower()
    if not has_table_tennis and CLINICAL_ARTIFACT.search(title):
        return "clinical artifact (ping-pong term, not the sport)"
    if PURE_PERFORMANCE.search(title) and not HEALTH_POPULATION.search(title + abstract):
        return "pure performance/biomechanics study"
    return None


def http_get_json(url, retries=3):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.load(resp)
        except Exception:
            if attempt == retries - 1:
                raise
            time.sleep(2 * (attempt + 1))


def http_get_text(url, retries=3):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except Exception:
            if attempt == retries - 1:
                raise
            time.sleep(2 * (attempt + 1))


def collect_covered_pmids():
    """PMIDs already cited by published articles or logged in the research bank.

    When the repo is absent (R10 container), falls back to a covered.json
    snapshot shipped at deploy time from the iMac."""
    covered = set()
    if RESEARCH_BANK.exists():
        text = RESEARCH_BANK.read_text(errors="replace")
        covered.update(re.findall(r"PMID:?\s*(\d{3,})", text))
    if ARTICLES_DIR.exists():
        for f in ARTICLES_DIR.glob("*.md"):
            text = f.read_text(errors="replace")
            covered.update(re.findall(r"pubmed\.ncbi\.nlm\.nih\.gov/(\d+)", text))
            covered.update(re.findall(r"PMID:?\s*(\d{3,})", text))
    if not covered:
        snapshot = DATA_DIR / "covered.json"
        if snapshot.exists():
            covered.update(json.loads(snapshot.read_text()))
    return covered


def search_tier(query, days_back, retmax=40):
    since = (datetime.now() - timedelta(days=days_back)).strftime("%Y/%m/%d")
    today = datetime.now().strftime("%Y/%m/%d")
    full = f"({query}) AND ({since}:{today}[dp])"
    url = (
        f"{EUTILS}/esearch.fcgi?db=pubmed&term={urllib.parse.quote(full)}"
        f"&retmode=json&retmax={retmax}&sort=relevance"
    )
    data = http_get_json(url)
    return data.get("esearchresult", {}).get("idlist", [])


def fetch_details(pmids):
    """Return {pmid: {title, journal, pubdate, pubtypes, abstract}} via efetch+esummary."""
    if not pmids:
        return {}
    joined = ",".join(pmids)
    summary = http_get_json(
        f"{EUTILS}/esummary.fcgi?db=pubmed&id={joined}&retmode=json"
    ).get("result", {})
    abstracts_raw = http_get_text(
        f"{EUTILS}/efetch.fcgi?db=pubmed&id={joined}&rettype=abstract&retmode=text"
    )
    # Split efetch text output into per-PMID chunks
    per_pmid = {}
    blocks = re.split(r"\n\n\n", abstracts_raw)
    for block in blocks:
        m = re.search(r"PMID:\s*(\d+)", block)
        if m:
            per_pmid[m.group(1)] = re.sub(r"\s+", " ", block).strip()

    out = {}
    for pmid in pmids:
        rec = summary.get(pmid, {})
        if not rec or rec.get("error"):
            continue
        pubtypes = " ".join(rec.get("pubtype", []))
        out[pmid] = {
            "pmid": pmid,
            "title": re.sub(r"\.$", "", rec.get("title", "").strip()),
            "journal": rec.get("source", ""),
            "pubdate": rec.get("pubdate", ""),
            "pubtypes": pubtypes,
            "abstract": per_pmid.get(pmid, "")[:1600],
        }
    return out


def guess_category(text):
    lowered = text.lower()
    for category, pattern in CATEGORY_MAP:
        if re.search(pattern, lowered):
            return category
    return "Physical Health"


def score_candidate(rec, tier, tier_weight, angle):
    text = (rec["title"] + " " + rec["abstract"]).lower()
    score = tier_weight
    for pattern, bonus in PUBTYPE_BONUS:
        if re.search(pattern, rec["pubtypes"].lower()):
            score += bonus
            break
    score += min(15, 3 * sum(1 for kw in HIGH_SIGNAL_KEYWORDS if kw in text))
    # Direct "table tennis" mention anywhere lifts an adjacent-tier study
    if "table tennis" in text or "ping pong" in text:
        score += 10
    # Recency: within 90 days gets a small boost
    try:
        year = int(rec["pubdate"][:4])
        if year >= datetime.now().year:
            score += 5
    except ValueError:
        pass
    # Human/older-adult relevance gate: studies on elite youth biomechanics are off-brand
    if re.search(r"elite|biomechanic|kinematic|match analysis|notational", text) and "older" not in text and "aging" not in text:
        score -= 15
    return score


def init_db():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS candidates (
            pmid TEXT PRIMARY KEY,
            tier INTEGER, score INTEGER, title TEXT, journal TEXT,
            pubdate TEXT, category TEXT, angle TEXT, pubtypes TEXT,
            abstract TEXT, discovered_at TEXT, updated_at TEXT,
            status TEXT DEFAULT 'new'
        );
        CREATE TABLE IF NOT EXISTS scans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ran_at TEXT, tier1_new INTEGER, tier2_new INTEGER,
            tier3_new INTEGER, tier4_new INTEGER, total_new INTEGER,
            covered_count INTEGER
        );
        """
    )
    conn.commit()
    return conn


def run_scan(covered=None, verbose=True):
    covered = covered if covered is not None else collect_covered_pmids()
    conn = init_db()
    existing = {r[0] for r in conn.execute("SELECT pmid FROM candidates")}
    tier_new = {1: 0, 2: 0, 3: 0, 4: 0}
    results = []
    seen_this_scan = set()

    for tier, weight, query, days_back, angle in TIERS:
        try:
            pmids = search_tier(query, days_back)
        except Exception as exc:
            if verbose:
                print(f"  tier {tier} search failed: {exc}")
            continue
        raw = len(pmids)
        pmids = [p for p in pmids if p not in covered]
        if verbose:
            print(f"  tier {tier}: {len(pmids)} uncovered of {raw} hits")
        if not pmids:
            continue
        details = fetch_details(pmids)
        for pmid, rec in details.items():
            if pmid in seen_this_scan:
                continue  # already captured from an earlier (higher-weight) tier
            if not rec["title"] or len(rec["abstract"]) < 200:
                continue  # no abstract = can't write an article from it
            full_text = rec["title"] + " " + rec["abstract"]
            if not is_health_relevant(full_text):
                continue  # performance/biomechanics-only study — off-brand
            reject = is_offbrand(rec["title"], rec["abstract"])
            if reject:
                continue
            score = score_candidate(rec, tier, weight, angle)
            if score < 40:
                continue
            seen_this_scan.add(pmid)
            entry = {
                **rec,
                "tier": tier,
                "score": score,
                "category": guess_category(rec["title"] + " " + rec["abstract"]),
                "angle": angle,
            }
            results.append(entry)
            now = datetime.now().isoformat(timespec="seconds")
            if pmid in existing:
                conn.execute(
                    "UPDATE candidates SET score=?, abstract=?, updated_at=? WHERE pmid=?",
                    (score, rec["abstract"], now, pmid),
                )
            else:
                tier_new[tier] += 1
                conn.execute(
                    "INSERT INTO candidates (pmid, tier, score, title, journal, pubdate,"
                    " category, angle, pubtypes, abstract, discovered_at, updated_at)"
                    " VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                    (pmid, tier, score, rec["title"], rec["journal"], rec["pubdate"],
                     entry["category"], angle, rec["pubtypes"], rec["abstract"], now, now),
                )
        time.sleep(0.5)  # NCBI rate limit courtesy

    conn.execute(
        "INSERT INTO scans (ran_at, tier1_new, tier2_new, tier3_new, tier4_new,"
        " total_new, covered_count) VALUES (?,?,?,?,?,?,?)",
        (datetime.now().isoformat(timespec="seconds"), tier_new[1], tier_new[2],
         tier_new[3], tier_new[4], sum(tier_new.values()), len(covered)),
    )
    conn.commit()

    backlog = [
        dict(r) for r in conn.execute(
            "SELECT * FROM candidates WHERE status='new' ORDER BY score DESC, pubdate DESC LIMIT 60"
        )
    ]
    if CANDIDATES_JSON.parent.parent.exists():
        CANDIDATES_JSON.parent.mkdir(parents=True, exist_ok=True)
        CANDIDATES_JSON.write_text(json.dumps(backlog, indent=2))
    conn.close()
    return backlog, tier_new, len(covered)


def list_backlog(limit=60):
    conn = init_db()
    rows = [
        dict(r) for r in conn.execute(
            "SELECT * FROM candidates WHERE status='new' ORDER BY score DESC, pubdate DESC LIMIT ?",
            (limit,),
        )
    ]
    conn.close()
    return rows


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "scan"
    if cmd == "scan":
        print(f"=== PongNews Research Radar — {datetime.now().isoformat(timespec='seconds')} ===")
        backlog, tier_new, covered = run_scan()
        print(f"covered PMIDs excluded: {covered}")
        print(f"new candidates: tier1={tier_new[1]} tier2={tier_new[2]} tier3={tier_new[3]} tier4={tier_new[4]}")
        print(f"backlog: {len(backlog)} stories ready")
        for c in backlog[:10]:
            print(f"  [{c['score']:>3}] T{c['tier']} {c['title'][:72]} ({c['journal']}, {c['pubdate']})")
    elif cmd == "list":
        for c in list_backlog():
            print(f"[{c['score']:>3}] T{c['tier']} PMID {c['pmid']} {c['title'][:70]}")
    else:
        print(__doc__)


if __name__ == "__main__":
    main()

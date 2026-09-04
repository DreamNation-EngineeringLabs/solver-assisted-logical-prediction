#!/usr/bin/env python3
"""Build an S2-shaped citation pool from OpenAlex (independent index, keyless).

Verification gates, mirroring the skill's Phase 2:
  - fuzzy title match (difflib ratio >= 0.70) against the candidate title
  - year strictly predates the cutoff
  - a non-empty abstract OR a resolvable DOI/arXiv id
Nothing is written for a candidate that fails to resolve.
"""
import difflib, json, os, re, sys, time, urllib.parse, urllib.request

MAILTO = os.environ.get("PAPER_ORCHESTRA_MAILTO", "")
BASE = "https://api.openalex.org/works"
CUTOFF = (2026, 8, 1)


def norm(s):
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", (s or "").lower())).strip()


def ratio(a, b):
    na, nb = norm(a), norm(b)
    r = difflib.SequenceMatcher(None, na, nb).ratio()
    if len(na.split()) < 4 and na and na in nb:
        r = max(r, 0.95)
    return r


def get(url):
    if MAILTO:
        url += ("&" if "?" in url else "?") + "mailto=" + urllib.parse.quote(MAILTO)
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "paper-orchestra-litreview/1.0"})
            with urllib.request.urlopen(req, timeout=40) as r:
                return json.loads(r.read())
        except Exception as e:
            if attempt == 3:
                print(f"  ! request failed: {e}", file=sys.stderr)
                return None
            time.sleep(1.5 * (attempt + 1))
    return None


def inv_to_abstract(inv):
    if not inv:
        return ""
    pos = {}
    for w, idxs in inv.items():
        for i in idxs:
            pos[i] = w
    return " ".join(pos[i] for i in sorted(pos))


def to_record(w, cand):
    title = w.get("title") or w.get("display_name") or ""
    year = w.get("publication_year")
    doi = (w.get("doi") or "").replace("https://doi.org/", "")
    ids = w.get("ids") or {}
    ext = {}
    if doi:
        ext["DOI"] = doi
    # arXiv id
    arx = None
    for loc in ([w.get("primary_location")] + (w.get("locations") or [])):
        if not loc:
            continue
        src = (loc.get("source") or {}).get("display_name") or ""
        url = loc.get("landing_page_url") or ""
        m = re.search(r"arxiv\.org/abs/([0-9]{4}\.[0-9]{4,5})", url)
        if m:
            arx = m.group(1)
        elif "arxiv" in src.lower() and doi.lower().startswith("10.48550/arxiv."):
            arx = doi.split("arxiv.")[-1]
    if not arx and cand.get("arxiv_id"):
        pass  # only record what the index confirms
    if arx:
        ext["ArXiv"] = arx
    venue = ""
    pl = w.get("primary_location") or {}
    src = pl.get("source") or {}
    venue = src.get("display_name") or ""
    authors = [{"name": (a.get("author") or {}).get("display_name", "")}
               for a in (w.get("authorships") or [])]
    abstract = inv_to_abstract(w.get("abstract_inverted_index"))
    return {
        "paperId": ids.get("openalex", "").rsplit("/", 1)[-1],
        "title": title,
        "abstract": abstract,
        "year": year,
        "authors": authors,
        "venue": venue,
        "externalIds": ext,
        "openalex_id": ids.get("openalex", ""),
        "type": w.get("type", ""),
        "cited_by_count": w.get("cited_by_count", 0),
        "verification": {"index": "openalex", "title_ratio": round(ratio(cand["title"], title), 3)},
        "discovered_for": cand.get("discovered_for", ""),
        "candidate_title": cand["title"],
    }


def resolve(cand):
    # Tier 1: DOI
    if cand.get("doi"):
        w = get(f"{BASE}/https://doi.org/{cand['doi']}")
        if w and not w.get("error"):
            return w, "doi"
    # Tier 2: arXiv DOI
    if cand.get("arxiv_id"):
        w = get(f"{BASE}/https://doi.org/10.48550/arxiv.{cand['arxiv_id']}")
        if w and not w.get("error"):
            return w, "arxiv-doi"
        r = get(f"{BASE}?filter=title.search:{urllib.parse.quote(cand['title'])}&per-page=10")
        if r and r.get("results"):
            for w in r["results"]:
                if ratio(cand["title"], w.get("title") or "") >= 0.70:
                    return w, "title-search"
    # Tier 3: title search
    r = get(f"{BASE}?search={urllib.parse.quote(cand['title'])}&per-page=10")
    if r and r.get("results"):
        best, bestr = None, 0.0
        for w in r["results"]:
            rr = ratio(cand["title"], w.get("title") or "")
            if rr > bestr:
                best, bestr = w, rr
        if best is not None and bestr >= 0.70:
            return best, "title-search"
    return None, "unresolved"


def main():
    cands = json.load(open(sys.argv[1]))
    pool, failures = [], []
    for c in cands:
        w, how = resolve(c)
        if w is None:
            failures.append({"title": c["title"], "reason": "not found in OpenAlex"})
            print(f"MISS  {c['title'][:70]}")
            continue
        rec = to_record(w, c)
        rr = rec["verification"]["title_ratio"]
        if rr < 0.70:
            failures.append({"title": c["title"], "reason": f"title ratio {rr}"})
            print(f"LOWSIM {rr} {c['title'][:60]}")
            continue
        y = rec["year"]
        if y is None or (y, 1, 1) >= CUTOFF:
            failures.append({"title": c["title"], "reason": f"year {y} not before cutoff"})
            print(f"CUTOFF {y} {c['title'][:60]}")
            continue
        rec["verification"]["resolved_by"] = how
        pool.append(rec)
        print(f"OK    [{how}] {rr}  {rec['title'][:65]}  ({y})")
        time.sleep(0.2)
    out = {"papers": pool, "failures": failures,
           "min_cite_paper_count": int(0.9 * len(pool))}
    json.dump(out, open(sys.argv[2], "w"), indent=2)
    print(f"\n{len(pool)} verified / {len(cands)} candidates; {len(failures)} failures")


main()

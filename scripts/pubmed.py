#!/usr/bin/env python3
"""PubMed literature search tool using NCBI E-utilities API.

Fetches top results by relevance or date, returns titles/PMIDs/DOIs/authors/years.
"""

import argparse
import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen


EUTILS_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
ENV_KEY_NAMES = ("NCBI_API_KEY", "EUTILS_API_KEY", "API_KEY")
DEFAULT_MAX_RESULTS = 5
TIMEOUT_SECONDS = 30
CACHE_DIR = Path("/tmp/pubmed_cache")
CACHE_TTL_SECONDS = 3600  # 1 hour


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Search PubMed and return the top most relevant results."
    )
    parser.add_argument(
        "--query",
        required=True,
        help='PubMed-formatted English query, e.g. ""long covid"[MeSH] AND 2025[DP]"',
    )
    parser.add_argument(
        "--api-key",
        dest="api_key",
        help="NCBI API key. If omitted, resolve from environment variables or .env.",
    )
    parser.add_argument(
        "--max-results",
        type=int,
        default=DEFAULT_MAX_RESULTS,
        help=f"Maximum number of results to return (default: {DEFAULT_MAX_RESULTS}).",
    )
    parser.add_argument(
        "--sort",
        choices=["relevance", "date"],
        default="relevance",
        help="Sort order: 'relevance' (default) or 'date' (newest first).",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Disable local result caching.",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# .env & API key resolution
# ---------------------------------------------------------------------------

def load_env_file(path: Path) -> Dict[str, str]:
    values: Dict[str, str] = {}
    if not path.is_file():
        return values

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()

        if (
            value
            and len(value) >= 2
            and value[0] == value[-1]
            and value[0] in {'"', "'"}
        ):
            value = value[1:-1]

        if key:
            values[key] = value

    return values


def resolve_api_key(cli_api_key: Optional[str]) -> Optional[str]:
    if cli_api_key:
        return cli_api_key

    for key_name in ENV_KEY_NAMES:
        value = os.environ.get(key_name)
        if value:
            return value

    # Search order: cwd → skill root → ~/.pubmed/
    cwd_env = Path.cwd() / ".env"
    skill_root_env = Path(__file__).resolve().parent.parent / ".env"
    home_env = Path.home() / ".pubmed" / ".env"

    for env_path in (cwd_env, skill_root_env, home_env):
        env_values = load_env_file(env_path)
        for key_name in ENV_KEY_NAMES:
            value = env_values.get(key_name)
            if value:
                return value

    return None


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def fetch_json(endpoint: str, params: Dict[str, str]) -> Dict:
    url = f"{EUTILS_BASE}/{endpoint}?{urlencode(params)}"
    try:
        with urlopen(url, timeout=TIMEOUT_SECONDS) as response:
            return json.load(response)
    except HTTPError as exc:
        raise RuntimeError(f"PubMed API HTTP error: {exc.code}") from exc
    except URLError as exc:
        raise RuntimeError(f"PubMed API connection error: {exc.reason}") from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError("PubMed API returned invalid JSON") from exc


# ---------------------------------------------------------------------------
# Cache helpers
# ---------------------------------------------------------------------------

def _cache_key(query: str, max_results: int, sort: str) -> str:
    raw = f"{query}|{max_results}|{sort}"
    return hashlib.sha256(raw.encode()).hexdigest()


def _cache_get(key: str) -> Optional[List[Dict[str, str]]]:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = CACHE_DIR / f"{key}.json"
    if not cache_file.is_file():
        return None
    try:
        data = json.loads(cache_file.read_text(encoding="utf-8"))
        if time.time() - data.get("ts", 0) > CACHE_TTL_SECONDS:
            return None  # expired
        return data.get("results")
    except (json.JSONDecodeError, KeyError):
        return None


def _cache_set(key: str, results: List[Dict[str, str]]) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = CACHE_DIR / f"{key}.json"
    payload = {"ts": time.time(), "results": results}
    cache_file.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


# ---------------------------------------------------------------------------
# PubMed API calls
# ---------------------------------------------------------------------------

def esearch(query: str, api_key: Optional[str], max_results: int, sort: str) -> List[str]:
    params: Dict[str, str] = {
        "db": "pubmed",
        "term": query,
        "retmode": "json",
        "retmax": str(max_results),
        "sort": sort,
    }
    if api_key:
        params["api_key"] = api_key

    payload = fetch_json("esearch.fcgi", params)
    return payload.get("esearchresult", {}).get("idlist", [])[:max_results]


def esummary(pmids: List[str], api_key: Optional[str]) -> List[Dict[str, str]]:
    if not pmids:
        return []

    params: Dict[str, str] = {
        "db": "pubmed",
        "id": ",".join(pmids),
        "retmode": "json",
    }
    if api_key:
        params["api_key"] = api_key

    payload = fetch_json("esummary.fcgi", params)
    result = payload.get("result", {})

    items: List[Dict[str, str]] = []
    for pmid in pmids:
        entry = result.get(pmid, {})

        # Extract DOI
        doi = ""
        for article_id in entry.get("articleids", []):
            if article_id.get("idtype") == "doi":
                doi = article_id.get("value", "")
                break

        # Extract first author
        authors = entry.get("authors", [])
        first_author = authors[0].get("name", "") if authors else ""

        # Extract publication year
        pubdate = entry.get("pubdate", "")
        year = pubdate.split()[0] if pubdate else ""

        items.append({
            "title": entry.get("title", "") or "",
            "pmid": pmid,
            "doi": doi,
            "first_author": first_author,
            "year": year,
            "link": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
        })

    return items


def efetch_abstract(pmids: List[str], api_key: Optional[str]) -> Dict[str, str]:
    """Fetch abstracts for given PMIDs. Returns {pmid: abstract_text}."""
    if not pmids:
        return {}

    params: Dict[str, str] = {
        "db": "pubmed",
        "id": ",".join(pmids),
        "retmode": "xml",
        "rettype": "abstract",
    }
    if api_key:
        params["api_key"] = api_key

    url = f"{EUTILS_BASE}/efetch.fcgi?{urlencode(params)}"
    try:
        with urlopen(url, timeout=TIMEOUT_SECONDS) as response:
            xml_text = response.read().decode("utf-8")
    except Exception:
        return {}

    # Simple XML parsing (no external deps)
    abstracts: Dict[str, str] = {}

    # Split by PubmedArticle blocks
    articles = re.findall(r"<PubmedArticle>(.*?)</PubmedArticle>", xml_text, re.DOTALL)
    for article in articles:
        pmid_match = re.search(r"<PMID[^>]*>(\d+)</PMID>", article)
        if not pmid_match:
            continue
        pmid = pmid_match.group(1)

        # Collect all AbstractText elements
        abstract_parts = re.findall(r"<AbstractText[^>]*>(.*?)</AbstractText>", article, re.DOTALL)
        if abstract_parts:
            abstract = " ".join(part.strip() for part in abstract_parts)
            # Strip any remaining XML tags
            abstract = re.sub(r"<[^>]+>", "", abstract).strip()
            abstracts[pmid] = abstract

    return abstracts


# ---------------------------------------------------------------------------
# Output formatting
# ---------------------------------------------------------------------------

def format_markdown(results: List[Dict[str, str]], abstracts: Optional[Dict[str, str]] = None) -> str:
    if not results:
        return "无相关文献"

    lines = []
    for item in results:
        author_info = f"  作者: {item['first_author']}\n" if item.get("first_author") else ""
        year_info = f"  年份: {item['year']}\n" if item.get("year") else ""

        block = (
            f"- Title: {item['title'] or 'N/A'}\n"
            f"{author_info}"
            f"{year_info}"
            f"  PMID: {item['pmid']}\n"
            f"  DOI: {item['doi'] or 'N/A'}\n"
            f"  PubMed link: {item['link']}"
        )

        # Append abstract if available
        if abstracts and item["pmid"] in abstracts:
            abstract_text = abstracts[item["pmid"]]
            # Truncate long abstracts to 300 chars
            if len(abstract_text) > 300:
                abstract_text = abstract_text[:297] + "..."
            block += f"\n  摘要: {abstract_text}"

        lines.append(block)

    return "\n\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    args = parse_args()
    api_key = resolve_api_key(args.api_key)

    try:
        # Check cache (unless disabled)
        cache_key = None
        if not args.no_cache:
            cache_key = _cache_key(args.query, args.max_results, args.sort)
            cached = _cache_get(cache_key)
            if cached is not None:
                # Still need abstracts for cached results
                pmids = [r["pmid"] for r in cached]
                abstracts = efetch_abstract(pmids, api_key)
                print(format_markdown(cached, abstracts))
                return 0

        # Search
        pmids = esearch(args.query, api_key, args.max_results, args.sort)
        if not pmids:
            print("无相关文献")
            return 0

        # Fetch metadata
        results = esummary(pmids, api_key)

        # Fetch abstracts
        abstracts = efetch_abstract(pmids, api_key)

        # Cache results
        if cache_key and not args.no_cache:
            _cache_set(cache_key, results)

        print(format_markdown(results, abstracts))
        return 0

    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

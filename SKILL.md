---
name: pubmed
description: "Search PubMed for biomedical literature via NCBI E-utilities API. Returns titles, authors, DOIs, abstracts."
version: 2.1.0
author: FFFold
license: MIT
compatibility: claude-code, opencode, openclaw, hermes-agent, aws-codex
platforms: [macos, linux, windows]
metadata:
  hermes:
    tags: [Research, PubMed, Medical, Literature, NCBI, MeSH, Biomedical]
    related_skills: [arxiv, ocr-and-documents]
  openclaw:
    requires:
      bins: [python3]
---

# PubMed Literature Search

Search and retrieve biomedical literature from PubMed via NCBI E-utilities API. Auto-converts natural language queries to PubMed syntax using MeSH Terms.

## When to Use

- User asks to search medical/biomedical literature
- User wants latest research on a specific medical topic
- User needs PMIDs, DOIs, or abstracts for academic references

## Quick Reference

| Action | Command |
|--------|---------|
| Basic search | `python3 scripts/pubmed.py --query '"diabetes"[MeSH]'` |
| By date | `python3 scripts/pubmed.py --query '"CRISPR"[MeSH]' --sort date` |
| More results | `python3 scripts/pubmed.py --query '"cancer"' --max-results 10` |
| No cache | `python3 scripts/pubmed.py --query '"vaccine"' --no-cache` |

## Workflow

1. Accept user's natural language search request (Chinese or English).
2. **Silently** convert to PubMed English query with MeSH Terms.
3. Call `scripts/pubmed.py` with the converted query.
4. Return results directly — no re-summarizing needed.

## Input Parameters

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `--query` | Yes | — | PubMed-formatted English query |
| `--api-key` | No | auto | NCBI API key (auto-resolved from env/.env) |
| `--max-results` | No | 5 | Number of results to return |
| `--sort` | No | relevance | `relevance` or `date` (newest first) |
| `--no-cache` | No | false | Disable local result caching |

## API Key Resolution

1. `--api-key` CLI argument
2. Environment: `NCBI_API_KEY` → `EUTILS_API_KEY` → `API_KEY`
3. `.env` files: cwd → skill root → `~/.pubmed/.env`

Free key: https://www.ncbi.nlm.nih.gov/account/settings/
Without key: 3 req/sec. With key: 10 req/sec.

## Output Format

Each result includes:
- **Title** — Article title
- **Author** — First author
- **Year** — Publication year
- **PMID** — PubMed ID
- **DOI** — Digital Object Identifier
- **PubMed link** — Direct URL
- **Abstract** — Abstract text (truncated to 300 chars)

## MeSH Query Syntax

| Syntax | Meaning | Example |
|--------|---------|---------|
| `"term"[MeSH]` | MeSH heading | `"diabetes mellitus"[MeSH]` |
| `"term"[Title/Abstract]` | Title or abstract | `"machine learning"[Title/Abstract]` |
| `YYYY[DP]` | Publication year | `2024[DP]` |
| `"last N years"[Date - Publication]` | Relative date | `"last 5 years"[Date - Publication]` |
| `Review[pt]` | Publication type | `Review[pt]` |
| `AND`, `OR`, `NOT` | Boolean operators | `"diabetes"[MeSH] AND "obesity"[MeSH]` |

### Common Patterns

```bash
# Recent reviews on a topic
"long covid"[MeSH] AND Review[pt] AND "last 3 years"[Date - Publication]

# Cross-topic intersection
"CRISPR"[MeSH] AND "cancer"[MeSH] AND 2024[DP]

# Broad keyword search (no MeSH)
"artificial intelligence in radiology"

# Specific journal
"Nature"[Journal] AND "gene therapy"[MeSH]
```

## Limitations & Pitfalls

### SSL Errors with Complex MeSH Queries

NCBI E-utilities occasionally returns `SSL: UNEXPECTED_EOF_WHILE_READING` for complex MeSH queries with multiple Boolean operators. Simple keyword queries are more reliable.

**Workaround**: If a complex MeSH query fails, simplify it or retry. The script handles this gracefully and returns an error message.

### Rate Limits

| API | Without Key | With Key | Auth |
|-----|-------------|----------|------|
| esearch/esummary | 3 req/s (5 burst) | 10 req/s | Optional |
| efetch | 3 req/s (5 burst) | 10 req/s | Optional |

HTTP 429 is returned on limit hit — the script does **not** auto-retry.

### efetch Abstract Parsing

The script uses regex-based XML parsing for abstracts (no external deps). Edge cases:
- Articles with no abstract return empty string
- Non-English abstracts are included as-is
- Structured abstracts (CONCLUSIONS:, METHODS:) are concatenated

### Date Sorting Quirk

`sort=date` returns the most recently indexed papers, not necessarily the most recently published. A paper published in 2024 but indexed in 2026 may appear first.

## Caching

- Default: local cache in `/tmp/pubmed_cache/`
- TTL: 1 hour
- Keyed on: query + max_results + sort
- Use `--no-cache` to bypass

## Verification

After running a search, verify:
- Results contain PMIDs and DOIs for cross-referencing
- Abstract text is present and readable (no raw XML artifacts)
- If no results are returned, try simplifying the query or removing MeSH qualifiers

## Script

Use `scripts/pubmed.py` for the full workflow. No external dependencies — Python stdlib only.

```bash
# Install (copy to a known location)
cp scripts/pubmed.py /usr/local/bin/pubmed-search

# Or run directly
python3 scripts/pubmed.py --query '"diabetes"[MeSH]' --sort date --max-results 5
```

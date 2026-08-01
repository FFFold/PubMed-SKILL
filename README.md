<p align="center">
  <h1 align="center">PubMed-SKILL</h1>
  <p align="center">Search PubMed for biomedical literature via NCBI E-utilities API — no external dependencies.</p>
</p>

<p align="center">
  <a href="./LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue" alt="License"></a>
  <img src="https://img.shields.io/badge/python-3.6+-blue" alt="Python 3.6+">
  <img src="https://img.shields.io/badge/dependencies-0-green" alt="Zero dependencies">
</p>

---

<div align="center">
  <a href="./README.zh.md">中文</a> | <b>English</b>
</div>

## Overview

PubMed-SKILL is a zero-dependency Python tool that searches and retrieves biomedical literature from [PubMed](https://pubmed.ncbi.nlm.nih.gov/) using the NCBI E-utilities API. It is compatible with major AI agent frameworks including **Claude Code**, **Opencode**, **OpenClaw**, **Hermes Agent**, **AWS Codex**, and other LLM agent tools — and works perfectly as a standalone CLI tool.

- No `pip install` required — pure Python standard library
- Supports Chinese and English natural language queries
- Local caching with 1-hour TTL
- Flexible API key resolution (CLI arg → env vars → `.env` files)

## Quick Start

### Install to AI Agent

Send the following command in an Agent session:

```
Please install this SKILL: https://github.com/FFFold/PubMed-SKILL
```

### Run Directly

```bash
python scripts/pubmed.py --query '"diabetes"[MeSH]'
python scripts/pubmed.py --query '"CRISPR"[MeSH]' --sort date --max-results 10
```

## Usage

```
python scripts/pubmed.py --query <query> [options]
```

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `--query` | Yes | — | PubMed-formatted query string |
| `--api-key` | No | auto-resolved | NCBI API key |
| `--max-results` | No | 5 | Number of results to return |
| `--sort` | No | `relevance` | Sort order: `relevance` or `date` |
| `--no-cache` | No | `false` | Bypass local result caching |

## API Key

Requests are rate-limited to **3 req/sec** without an API key and **10 req/sec** with one.

Get a free API key: https://www.ncbi.nlm.nih.gov/account/settings/

Resolution order:
1. `--api-key` CLI argument
2. Environment variables: `NCBI_API_KEY` → `EUTILS_API_KEY` → `API_KEY`
3. `.env` files: current directory → skill root → `~/.pubmed/.env`

See [.env.example](./.env.example) for the format.

## Query Syntax

| Syntax | Meaning | Example |
|--------|---------|---------|
| `"term"[MeSH]` | MeSH heading | `"diabetes mellitus"[MeSH]` |
| `"term"[Title/Abstract]` | Title or abstract | `"machine learning"[Title/Abstract]` |
| `YYYY[DP]` | Publication year | `2024[DP]` |
| `"last N years"[Date - Publication]` | Relative date | `"last 5 years"[Date - Publication]` |
| `Review[pt]` | Publication type | `Review[pt]` |
| `AND`, `OR`, `NOT` | Boolean operators | `"diabetes"[MeSH] AND "obesity"[MeSH]` |

### Examples

```bash
# Recent reviews
python scripts/pubmed.py --query '"long covid"[MeSH] AND Review[pt] AND "last 3 years"[Date - Publication]'

# Cross-topic
python scripts/pubmed.py --query '"CRISPR"[MeSH] AND "cancer"[MeSH] AND 2024[DP]'

# Broad keyword search
python scripts/pubmed.py --query 'artificial intelligence in radiology'

# Specific journal
python scripts/pubmed.py --query '"Nature"[Journal] AND "gene therapy"[MeSH]'
```

## Caching

Results are cached locally in `/tmp/pubmed_cache/` for 1 hour. The cache key is derived from the query, max results, and sort order. Use `--no-cache` to bypass.

## Output Format

Each result includes:

- **Title** — Article title
- **Author** — First author
- **Year** — Publication year
- **PMID** — PubMed ID
- **DOI** — Digital Object Identifier
- **PubMed link** — Direct URL
- **Abstract** — Abstract text (truncated to 300 characters)

## Install as CLI Tool

```bash
cp scripts/pubmed.py /usr/local/bin/pubmed-search
# or
python scripts/pubmed.py --query '"gene therapy"[MeSH]'
```

## License

[MIT](./LICENSE)

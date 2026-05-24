# NCBI E-utilities API Reference

## Endpoints

| Endpoint | Purpose | Format |
|----------|---------|--------|
| `esearch.fcgi` | Search, get PMIDs | JSON/XML |
| `esummary.fcgi` | Fetch metadata (title, authors, DOI) | JSON |
| `efetch.fcgi` | Fetch full records (abstract, full text) | XML |

## Base URL

```
https://eutils.ncbi.nlm.nih.gov/entrez/eutils
```

## Common Parameters

| Param | Values | Description |
|-------|--------|-------------|
| `db` | `pubmed` | Database to search |
| `term` | string | Search query (PubMed syntax) |
| `retmode` | `json`, `xml` | Response format |
| `retmax` | int | Max results (default 20) |
| `sort` | `relevance`, `date`, `pub_date`, `first_author` | Sort order |
| `api_key` | string | NCBI API key for higher rate limits |

## esearch Parameters

| Param | Description |
|-------|-------------|
| `usehistory` | `y` — return WebEnv for pagination |
| `retstart` | Offset for pagination |
| `datetype` | `edat` (entry date), `pdat` (publication date) |
| `reldate` | Relative date in days |
| `mindate`, `maxdate` | Date range (YYYY/MM/DD or YYYY) |

## esummary Response Fields

Key fields in `result.{pmid}`:
- `title` — Article title
- `authors` — Array of `{name: "..."}`
- `pubdate` — Publication date string
- `articleids` — Array of `{idtype: "doi", value: "..."}` and others
- `sortfirstauthor` — First author name
- `fulljournalname` — Journal full name
- `volume`, `issue` — Volume/issue numbers

## efetch Parameters

| Param | Description |
|-------|-------------|
| `rettype` | `abstract`, `full`, `medline`, `xml` |
| `retmode` | `xml`, `text` |

### Abstract XML Structure

```xml
<PubmedArticle>
  <MedlineCitation>
    <PMID>12345678</PMID>
    <Article>
      <Abstract>
        <AbstractText Label="BACKGROUND">...</AbstractText>
        <AbstractText Label="METHODS">...</AbstractText>
        <AbstractText Label="CONCLUSIONS">...</AbstractText>
      </Abstract>
    </Article>
  </MedlineCitation>
</PubmedArticle>
```

## MeSH Term Syntax

```
"term"[MeSH]              — Exact MeSH heading
"term"[MeSH Terms]        — MeSH heading + entry terms
"term"[Title/Abstract]    — Title or abstract text
"term"[Title]             — Title only
"term"[Author]            — Author name
"term"[Journal]           — Journal name
"term"[dp]                — Date of publication
"term"[pt]                — Publication type (Review, Clinical Trial, etc.)
```

## Date Filters

```
2024[dp]                          — Specific year
2020:2024[dp]                     — Date range
"last 5 years"[Date - Publication] — Relative
"last 30 days"[Date - Entry]      — Recent entries
```

## Boolean Operators

```
A AND B        — Both terms
A OR B         — Either term
A NOT B        — Exclude B
A AND NOT B    — Same as NOT
```

## Pagination

```bash
# First 20 results
curl "esearch.fcgi?db=pubmed&term=diabetes&retmax=20&retstart=0"

# Next 20 results
curl "esearch.fcgi?db=pubmed&term=diabetes&retmax=20&retstart=20"
```

## Rate Limits

| Auth | Rate | Burst |
|------|------|-------|
| Anonymous | 3/sec | 5/sec |
| With API key | 10/sec | 10/sec |

HTTP 429 = rate limited. No auto-retry in the script.

## Known Quirks

1. **SSL intermittent failures**: Complex MeSH queries with multiple布尔 operators may cause `SSL: UNEXPECTED_EOF_WHILE_READING`. Simple keyword queries are more reliable.

2. **sort=date ≠ sort by pub date**: `sort=date` sorts by modification/indexing date, not publication date. A paper published in 2024 but re-indexed in 2026 may appear first.

3. **MeSH auto-explosion**: `"diabetes"[MeSH]` automatically includes all narrower terms (diabetes mellitus type 1, type 2, etc.). Use `"diabetes"[MeSH:NoExp]` to disable.

4. **Empty abstracts**: Some records (especially older ones) have no abstract. The script returns empty string for these.

5. **Retraction notices**: Retracted papers still appear in results. Check for "Retraction of:" in the title or "Publication Type" field containing "Retraction".

## API Key Registration

1. Go to https://www.ncbi.nlm.nih.gov/account/settings/
2. Create free NCBI account
3. Generate API key in "API Key Management"
4. Set as env var or in `.env` file

## Useful Links

- E-utilities docs: https://www.ncbi.nlm.nih.gov/books/NBK25500/
- MeSH browser: https://meshb.nlm.nih.gov/
- PubMed search help: https://pubmed.ncbi.nlm.nih.gov/help/

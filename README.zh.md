<p align="center">
  <h1 align="center">PubMed-SKILL</h1>
  <p align="center">通过 NCBI E-utilities API 搜索 PubMed 生物医学文献 — 无外部依赖。</p>
</p>

<p align="center">
  <a href="./LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue" alt="License"></a>
  <img src="https://img.shields.io/badge/python-3.6+-blue" alt="Python 3.6+">
  <img src="https://img.shields.io/badge/dependencies-0-green" alt="零依赖">
</p>

---

<div align="center">
  <b>中文</b> | <a href="./README.md">English</a>
</div>

## 概述

PubMed-SKILL 是一个零依赖的 Python 工具，通过 NCBI E-utilities API 搜索和检索 [PubMed](https://pubmed.ncbi.nlm.nih.gov/) 生物医学文献。它兼容 **Claude Code**、**Opencode**、**OpenClaw**、**Hermes Agent**、**AWS Codex** 等主流 AI Agent 框架，也可以作为独立 CLI 工具使用。

- 无需 `pip install` — 纯 Python 标准库实现
- 支持中英文自然语言查询
- 本地缓存，1 小时 TTL
- 灵活的 API Key 解析（CLI 参数 → 环境变量 → `.env` 文件）

## 快速开始

```bash
python scripts/pubmed.py --query '"diabetes"[MeSH]'
python scripts/pubmed.py --query '"CRISPR"[MeSH]' --sort date --max-results 10
```

## 使用说明

```
python scripts/pubmed.py --query <查询语句> [选项]
```

| 参数 | 必填 | 默认值 | 说明 |
|----------|----------|---------|-------------|
| `--query` | 是 | — | PubMed 格式查询语句 |
| `--api-key` | 否 | 自动解析 | NCBI API 密钥 |
| `--max-results` | 否 | 5 | 返回结果数量 |
| `--sort` | 否 | `relevance` | 排序方式：`relevance`（相关度）或 `date`（日期） |
| `--no-cache` | 否 | `false` | 禁用本地缓存 |

## API 密钥

无 API 密钥时限制为 **3 次请求/秒**，使用密钥提升至 **10 次请求/秒**。

免费申请地址：https://www.ncbi.nlm.nih.gov/account/settings/

密钥解析顺序：
1. `--api-key` CLI 参数
2. 环境变量：`NCBI_API_KEY` → `EUTILS_API_KEY` → `API_KEY`
3. `.env` 文件：当前目录 → skill 根目录 → `~/.pubmed/.env`

格式参考 [.env.example](./.env.example)。

## 查询语法

| 语法 | 含义 | 示例 |
|--------|---------|---------|
| `"term"[MeSH]` | MeSH 主题词 | `"diabetes mellitus"[MeSH]` |
| `"term"[Title/Abstract]` | 标题或摘要 | `"machine learning"[Title/Abstract]` |
| `YYYY[DP]` | 出版年份 | `2024[DP]` |
| `"last N years"[Date - Publication]` | 相对日期 | `"last 5 years"[Date - Publication]` |
| `Review[pt]` | 文献类型 | `Review[pt]` |
| `AND`、`OR`、`NOT` | 布尔运算符 | `"diabetes"[MeSH] AND "obesity"[MeSH]` |

### 常用示例

```bash
# 近期综述
python scripts/pubmed.py --query '"long covid"[MeSH] AND Review[pt] AND "last 3 years"[Date - Publication]'

# 跨主题交叉
python scripts/pubmed.py --query '"CRISPR"[MeSH] AND "cancer"[MeSH] AND 2024[DP]'

# 宽泛关键词搜索
python scripts/pubmed.py --query 'artificial intelligence in radiology'

# 特定期刊
python scripts/pubmed.py --query '"Nature"[Journal] AND "gene therapy"[MeSH]'
```

## 缓存

结果默认缓存于 `/tmp/pubmed_cache/`，有效期为 1 小时。缓存键由查询语句、最大结果数和排序方式共同决定。使用 `--no-cache` 可跳过缓存。

## 输出格式

每条结果包含：

- **Title** — 文章标题
- **Author** — 第一作者
- **Year** — 出版年份
- **PMID** — PubMed ID
- **DOI** — 数字对象标识符
- **PubMed link** — 直达链接
- **Abstract** — 摘要（截断至 300 字符）

## 安装为 CLI 工具

```bash
cp scripts/pubmed.py /usr/local/bin/pubmed-search
# 或直接运行
python scripts/pubmed.py --query '"gene therapy"[MeSH]'
```

## 许可证

[MIT](./LICENSE)

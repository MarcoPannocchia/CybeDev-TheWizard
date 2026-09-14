# Roadmap

[← Index](20_Projects/Test_The-Wizard/index.md)

## 1. Persistence with `sqlite3`

Goal: replace/supplement `print()` calls with structured DB writes, to keep a history and compare scans over time.

Suggested starting schema (indicative, to be refined):

- `targets(id, url, first_seen, last_seen)`
- `ports(id, target_id, port, state, service, scanned_at)`
- `banners(id, target_id, port, banner, captured_at)`
- `cves(id, banner_id, cve_id, score, description)`
- `headers(id, target_id, header_name, present, checked_at)`
- `subdomains(id, target_id, subdomain, status, found_at)`
- `ssl_checks(id, target_id, issuer, subject, not_after, days_left, checked_at)` *(new, now that `SSL_TSL_CHECKER` is implemented and returns a structured dict)*

**Point of attention**: `self.banners` is currently reset on every `Port_Scanner(ip)` call (see [01_architecture.md](01_architecture.md)). Before introducing the DB, decide *when* to write: right after each `Port_Scanner` call, or at the end of `Cast_Spell` for that target — otherwise history is lost between targets.

## 2. UI

Library still to be decided. Options to weigh on a lightness/complexity tradeoff:

| Option | Pros | Cons |
|---|---|---|
| **TUI** (`Textual` or `Rich`) | lightweight, consistent with the already-async approach, no web deployment | less "demo-friendly" for a CS50 presentation |
| **Web app** (`Flask` / `FastAPI` + minimal frontend) | more presentable, browser-accessible | more complexity (routing, templates/API, possibly a separate frontend) |

Given the CS50X delivery goal, a lightweight web app (`Flask` + a few HTML pages) is probably the more "demo-friendly" tradeoff, but a TUI remains valid if you want to stay closer to the existing code.

## 3. Minimal demo (CS50X submission)

Suggested feature subset for the demo:
- Port scan (a single implementation, e.g. asyncio — avoid the triple redundancy during the demo)
- Subdomain scan
- Header analyzer
- CVE lookup
- SSL/TLS check (now available, a good demo candidate: structured, concise output)
- sqlite3 persistence of results
- Minimal UI to launch a scan on a target and view saved results

## 4. To complete / revisit

- `Exploitation_tool` / `Post_Exploitation_tool` — still just informational placeholders, to be evaluated whether and how to implement them (with strong emphasis on ethical use)
- NVD API rate limiting in `CVE_Lookup` — risks throttling on long banner lists
- Re-check the `TheWidzard` facade class (shared attributes, `Cast_Spell`) against the latest module version once it's available — see note in [06_thewidzard.md](06_thewidzard.md)

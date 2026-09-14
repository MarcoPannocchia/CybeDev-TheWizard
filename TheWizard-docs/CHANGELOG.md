# Changelog

[← Index](index.md)

This describes what changed to arrive at **Version 7**, the current codebase, compared to the previous version received. Earlier snapshots aren't individually numbered — they're referred to descriptively where relevant.

---

## What Version 7 changes vs the previous version

Targeted fixes for issues already flagged in earlier documentation passes, plus the SSL checker implementation. **Note:** Version 7 as received only includes the modules — not the `TheWidzard` facade class (see `06_thewidzard.md`).

| Area | Previous version | Version 7 |
|---|---|---|
| Class name | `Vulnerability_Assesment_Tool` (typo, missing an "s") | renamed to `Vulnerability_Assessment_Tool`; module-level alias keeps the old name working |
| `_port_scanner` / `Port_Scanner` | hardcoded 0.1s timeout | `timeout` becomes a configurable parameter (default 0.1s) |
| `Nmap_port_scanning` | `nm.scan()` called synchronously inside an `async` function — blocks the event loop | `nm.scan()` offloaded to a thread via `loop.run_in_executor(None, ...)` |
| `Recon_Spell` | calls `Socket_Port_Scanner`/`Socket_Banner_Grabber` (synchronous) directly — blocks the event loop | the same calls wrapped in `asyncio.to_thread(...)` |
| `CVE_Lookup` | opens a new `aiohttp.ClientSession` on every call (anti-pattern for connection pooling) | receives `session` as a parameter and reuses the shared one |
| `CVE_Lookup` — data access | `data["vulnerabilities"]` (KeyError if the field is missing) | `data.get("vulnerabilities", [])` |
| `CVE_Lookup` — per-CVE parsing | a malformed entry broke the whole `for` loop | each entry in its own `try/except (KeyError, IndexError)`, malformed entries are simply skipped with a dedicated log line |
| `CVE_Lookup` — CVSS score | only `cvssMetricV31[0]` | falls back through `cvssMetricV31` → `cvssMetricV30` → `cvssMetricV2`, otherwise `"N/A"` |
| `CVE_Lookup` — network errors | one generic `except Exception` | split into `aiohttp.ClientError`, `asyncio.TimeoutError`, `Exception` as fallback |
| `SSL_TSL_CHECKER` | non-functional stub, **signature missing `self`** (can't be called as an instance method) | implemented: checks the TLS certificate (issuer, subject, expiry), warns if it expires within 30 days; signature fixed with `self` |
| `Vuln_Asses_Spell` | `Header_Analyzer` + `CVE_Lookup` | + a call to `SSL_TSL_CHECKER(host)` as a third step, `host` extracted with `urlparse(url).netloc` |

---

## Earlier history (context)

Before reaching this point, the codebase went through a longer arc, roughly:

1. **Early prototype** — broken synchronous `Cast_Spell` (missing `self`), no banner collection, single test url, minimal error handling.
2. **First working iteration** — added banner grabbing and error handling across `fetch_info`/`Header_Analyzer`/`_word_scan`, fixed `Cast_Spell` to proper async, expanded to real test domains.
3. **CVE lookup added** — `insert_word` rewritten with `urlparse`/`urlunparse` instead of manual string manipulation, `CVE_Lookup` implemented against the NVD API for the first time.
4. **Facade completed** — every module (`Recon_Spell`, `Vuln_Asses_Spell`, `Exploit_Spell`, `Post_Exploit_Spell`, `Network_Spell`, `OSINT_Spell`) went from an empty stub to a real async orchestrator; a third, socket/thread-based port-scanning implementation was added alongside the asyncio- and nmap-based ones.
5. **Version 7 (current)** — the fixes detailed in the table above.

---

## Known issues resolved in Version 7

- ✅ `SSL_TSL_CHECKER` was missing `self` → fixed and implemented
- ✅ `CVE_Lookup` opened a new session per call → now reuses the shared session
- ✅ `Nmap_port_scanning` blocked the event loop → offloaded to a thread executor
- ✅ Inconsistent naming `Vulnerability_Assesment_Tool` → renamed, with a compatibility alias

Still **open** (or unverifiable pending the full file):
- ⏳ Naming consistency elsewhere in the class hierarchy — needs re-checking once the updated facade arrives
- ⏳ NVD API rate limiting in `CVE_Lookup` — still unhandled
- ⏳ `_port_scanner` timeout: now configurable, but the default remains 0.1s, aggressive on high-latency networks

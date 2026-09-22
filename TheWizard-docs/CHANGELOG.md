# Changelog

[← Index](index.md)

---

## v0.8.2 — current

Source files: `TheWizard_v082.py`, `ModulesTheWidzard_v082.py`, `Network_tool_v082.py`, `DatabaseTheWidzard_v082.py`.

By far the biggest jump since Version 7 (`v0.8.0`): the facade class itself arrived for the first time in a while (closing a gap flagged since the Version 7 pass), a real Postgres persistence layer was added, `Network_tool` and `OSINT_tool` went from thin wrappers/placeholders to fully implemented tools, `Exploitation_tool` gained a real (non-executing) implementation, and a new `AI_Suggestions` mixin was added.

**Note on v0.8.1:** no `v081` source was received/synced — this changelog jumps directly from `v0.8.0` (Version 7) to `v0.8.2`.

### 1. Persistence layer (new — `DatabaseTheWidzard_v082.py`)

| Area | Before | v0.8.2 |
|---|---|---|
| `wordlist` / `security_headers` / `urls` | hardcoded class attributes on the facade | start empty; loaded once from Postgres by `TheWizard._load_lists()` at the start of `Cast_Spell` |
| Config source of truth | the source file | Postgres tables `wizard_wordlist`, `wizard_security_headers`, `wizard_urls` |
| `add_word` / `add_header` / `add_url` | synchronous, appended to the in-memory list only | now `async classmethod`s: write to Postgres first (`db.add_word`/`add_security_header`/`add_url`), then append in-memory |
| DB unreachable / env vars missing | not applicable (no DB) | `_load_lists()` fails loudly — `db.init_pool()` raises and the process stops rather than scanning with an empty or stale list |
| Scan findings (emails, doc metadata, k6 configs, ZAP alerts, ARP hosts) | printed only, never persisted | saved to dedicated Postgres tables as they're produced |

See [modules/database.md](modules/database.md) for the full schema and the identifier-whitelisting approach used to keep table/column names out of caller-controlled input.

### 2. `Network_tool` — from thin wrapper to real tool (moved to `Network_tool_v082.py`)

| Before (Version 7 / v0.8.0) | v0.8.2 |
|---|---|
| `Network_Spell` only wrapped `fetch_info` | `Network_Spell` also starts/reuses an OWASP ZAP daemon and runs `ZAP_Scanner` (spider → active scan → alerts) against the target |
| No ZAP integration | `_start_zap_daemon`/`_zap_is_up`/`_stop_zap_daemon` manage the ZAP process lifecycle (reuses an already-running daemon, registers an `atexit` cleanup, polls readiness instead of a fixed sleep) |
| No LAN discovery | `ARP_Scanner(subnet)` (wraps the `arp-scan` binary) + `LAN_Recon_Spell` (ARP sweep → hands a bounded number of discovered hosts to `ZAP_Scanner`) + a facade-level `LAN_Scan(subnet)` entry point |
| — | `ZAP_Scanner` alerts saved to `wizard_zap_alerts`; ARP hosts saved to `wizard_arp_hosts` |
| — | Spider-discovered pages are fed into `Email_Harvester`/`Metadata_Extractor` (`_harvest_spidered_pages`), so OSINT findings aren't limited to the single entry-point URL |

**Safety notes carried over into the docs**: the ZAP active scan sends real attack payloads — same authorization requirement as `Exploitation_tool`. `max_lan_hosts_to_scan` and `max_spidered_pages_to_scan` cap how much an ARP sweep or a spider crawl can turn into automatically.

### 3. `OSINT_tool` — from one wrapper to three real tools

| Before | v0.8.2 |
|---|---|
| `OSINT_Spell` only wrapped `Subdomain_Scanner` | `OSINT_Spell` now also runs `Email_Harvester` and `Metadata_Extractor`, saving results to Postgres |
| No email harvesting | `Email_Harvester` — passive regex scan over the already-fetched page body, no extra requests |
| No document metadata extraction | `Metadata_Extractor` — finds `.pdf`/`.docx` links on the page, downloads a bounded number (`_MAX_DOCS_PER_TARGET = 5`, `_MAX_DOC_BYTES = 5 MB`, enforced against both `Content-Length` and the actual bytes read), and extracts embedded metadata (`pypdf`, `python-docx`) |

### 4. `Exploitation_tool` — from stub to (non-executing) k6 config builder

| Before | v0.8.2 |
|---|---|
| `Exploit_Spell(self)` — printed a placeholder message only | `Exploit_Spell(self, target)` — builds a `k6` load-test config + script for `target` via `build_k6_config` and persists it (`wizard_k6_configs`); **never shells out to the `k6` binary** — deliberately prepared for a future UI to review/trigger |

`Cast_Spell` now calls `self.Exploit_Spell(url)` (previously `Exploit_Spell()` with no argument).

### 5. `AI_Suggestions` — new mixin (Groq-backed triage)

- `AI_Suggest_Spell(session, findings, api_key=None)` sends aggregated scan findings to Groq's OpenAI-compatible chat completions API and expects back a structured JSON report: `risk_ranked_findings`, `summary`, `next_steps`.
- System prompt explicitly frames the findings block as **untrusted data**, instructing the model to ignore any text inside it that tries to redirect behavior — a prompt-injection guard, since findings can contain attacker-influenced strings (banners, page content).
- Client-side sliding-window rate limiter (`_GroqRateLimiter`) throttles requests/tokens per minute *before* Groq's own limits are hit, plus a warning when Groq's own `x-ratelimit-*` response headers drop below a threshold.
- Per-field/per-list truncation (`max_field_chars`, `max_list_items`, `max_input_chars`) before the prompt is built, so a noisy or hostile target can't blow up the request size or token bill.
- **Not yet wired into `Cast_Spell`** — will be invoked once a UI layer exists to drive when/how suggestions are requested. `TheWizard` already inherits `AI_Suggestions`, but nothing currently calls `AI_Suggest_Spell` during a normal run.

See [modules/ai_suggestions.md](modules/ai_suggestions.md).

### 6. Facade (`TheWizard_v082.py`) — first full copy received since Version 7

- Class renamed for good: it's `TheWizard` in source (not `TheWidzard`) — closes the naming inconsistency flagged since [facade.md](architecture/facade.md)'s first pass.
- Inherits `AI_Suggestions` in addition to the previous five mixins.
- `wordlist`/`security_headers`/`urls` start empty (see §1); `db_pool` is a new class attribute (`None` until `_load_lists()` runs).
- `Cast_Spell`: calls `_load_lists()` first; the whole url loop now runs inside `try/finally`, with `db.close_pool()` in `finally` so the pool is always released even if a target's scan raises.
- New: `clear_findings(target=None)` — empties the findings tables (emails, metadata, k6 configs, ZAP alerts; ARP hosts too when `target is None`), never touches the config lists.
- New: `LAN_Scan(subnet)` — standalone entry point for `LAN_Recon_Spell` outside the url-driven loop (a subnet isn't one of `self.urls`); lazily initializes the DB pool if needed.

### 7. Small fixes noticed while re-reading the actual source

- `_port_scanner`'s exception handling was previously documented as printing `"access denied"` / `"server unreachable"` for `ConnectionRefusedError`/`OSError`. The real source (confirmed again in v0.8.2) silently `pass`es on all three (`asyncio.TimeoutError`, `ConnectionRefusedError`, `OSError`) — a closed/filtered/unreachable port produces no output at all. [modules/reconnaissance.md](modules/reconnaissance.md) has been corrected to match.

---

## What Version 7 (v0.8.0) changed vs the previous version

Targeted fixes for issues already flagged in earlier documentation passes, plus the SSL checker implementation.

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

Before reaching Version 7, the codebase went through a longer arc, roughly:

1. **Early prototype** — broken synchronous `Cast_Spell` (missing `self`), no banner collection, single test url, minimal error handling.
2. **First working iteration** — added banner grabbing and error handling across `fetch_info`/`Header_Analyzer`/`_word_scan`, fixed `Cast_Spell` to proper async, expanded to real test domains.
3. **CVE lookup added** — `insert_word` rewritten with `urlparse`/`urlunparse` instead of manual string manipulation, `CVE_Lookup` implemented against the NVD API for the first time.
4. **Facade completed** — every module (`Recon_Spell`, `Vuln_Asses_Spell`, `Exploit_Spell`, `Post_Exploit_Spell`, `Network_Spell`, `OSINT_Spell`) went from an empty stub to a real async orchestrator; a third, socket/thread-based port-scanning implementation was added alongside the asyncio- and nmap-based ones.
5. **Version 7 (v0.8.0)** — the fixes detailed in the table above. The facade class itself was missing from this snapshot, so `TheWizard.md` still described the *previous* facade version.
6. **v0.8.2 (current)** — Postgres persistence, real `Network_tool`/`OSINT_tool`/`Exploitation_tool`, `AI_Suggestions`, and the facade finally received in full — see the top of this file.

---

## Known issues

Resolved as of v0.8.2:
- ✅ `SSL_TSL_CHECKER` was missing `self` → fixed and implemented (Version 7)
- ✅ `CVE_Lookup` opened a new session per call → now reuses the shared session (Version 7)
- ✅ `Nmap_port_scanning` blocked the event loop → offloaded to a thread executor (Version 7)
- ✅ Inconsistent naming `Vulnerability_Assesment_Tool` → renamed, with a compatibility alias (Version 7)
- ✅ Facade class (`wordlist`/`banners`/`security_headers`/`urls`, `Cast_Spell`) missing from the docs' source of truth → received and documented in full (v0.8.2)
- ✅ `wordlist`/`security_headers`/`urls` hardcoded, no history/persistence → Postgres-backed (v0.8.2)
- ✅ `Network_tool`/`OSINT_tool` were thin wrappers with no real logic → real ZAP/ARP and email/metadata tooling (v0.8.2)
- ✅ `Exploitation_tool` was a pure placeholder → builds (non-executing) k6 load-test configs (v0.8.2)
- ✅ Doc/code mismatch on `_port_scanner`'s error output (docs said it printed messages; code silently passes) → doc corrected (v0.8.2)

Still **open**:
- ⏳ NVD API rate limiting in `CVE_Lookup` — still unhandled (unlike the new client-side limiter added for `AI_Suggestions`' Groq calls)
- ⏳ `_port_scanner` timeout: configurable since Version 7, but the default remains 0.1s, aggressive on high-latency networks
- ⏳ `AI_Suggestions.AI_Suggest_Spell` is implemented but not called anywhere in `Cast_Spell` — needs a UI (or an explicit call site) to decide when to trigger it
- ⏳ `Post_Exploitation_tool` is still a pure placeholder
- ⏳ `build_k6_config`'s output is persisted but nothing executes it yet — needs the planned UI layer to actually trigger a k6 run
- ⏳ No automated tests exist for any of the modules above (see [roadmap.md](roadmap.md))

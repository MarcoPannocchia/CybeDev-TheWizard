# Architecture

[← Index](../index.md)

## Pattern

`TheWizard` is a **facade**: a single class inheriting from several specialized modules, each responsible for one phase of a pentest. The user only interacts with `TheWizard`, without needing to know the details of each individual module.

```python
class TheWizard(
    Reconnaissance_Tool,             # recon: ports, subdomains, http
    Vulnerability_Assesment_Tool,    # vuln analysis: headers, CVEs, SSL/TLS (alias of Vulnerability_Assessment_Tool)
    Exploitation_tool,               # k6 load-test config builder (never executes)
    Post_Exploitation_tool,          # post-exploitation (stub)
    Network_tool,                    # OWASP ZAP scanning + ARP/LAN sweep — own file, Network_tool_v082.py
    OSINT_tool,                      # subdomains, email harvesting, document metadata
    AI_Suggestions,                  # Groq-backed triage report (not yet wired into Cast_Spell)
)
```

> **v0.8.2 update**: `AI_Suggestions` is a new mixin, added to the inheritance list. `Network_tool` moved to its own file (`Network_tool_v082.py`) and is imported explicitly in `TheWizard_v082.py` — `from Network_tool_v082 import Network_tool  # supersedes the wildcard-imported stub of the same name` — because `ModulesTheWidzard_v082.py` still defines the *other* five classes via `import *`, and would otherwise shadow the real one.
>
> **Version 7 note (kept for history)**: the vulnerability class was renamed from `Vulnerability_Assesment_Tool` (typo, missing an "s") to `Vulnerability_Assessment_Tool`. A module-level alias `Vulnerability_Assesment_Tool = Vulnerability_Assessment_Tool` keeps old code/docs referencing the old name working — still true in v0.8.2.

Each module exposes a **"spell"**, a method that orchestrates the module's internal functions:

| Module | Spell |
|---|---|
| `Reconnaissance_Tool` | `Recon_Spell(ip)` |
| `Vulnerability_Assessment_Tool` | `Vuln_Asses_Spell(session, url)` |
| `Exploitation_tool` | `Exploit_Spell(target)` *(now takes a `target` argument — see [exploitation doc](../modules/exploitation_and_post_exploitation.md))* |
| `Post_Exploitation_tool` | `Post_Exploit_Spell()` |
| `Network_tool` | `Network_Spell(session, url)` |
| `OSINT_tool` | `OSINT_Spell(session, url)` |
| `AI_Suggestions` | `AI_Suggest_Spell(session, findings, api_key=None)` — not called by `Cast_Spell` |

`TheWizard.Cast_Spell()` is the single entry point: it loads config from Postgres (`_load_lists()`), then iterates over `self.urls` and calls all the spells in sequence for each target, finally releasing the DB pool. See [TheWizard/TheWizard.md](../TheWizard/TheWizard.md) for the full flow.

## Shared state

Class-level attributes defined on `TheWizard`, inherited/used by the modules via `self`:

| Attribute | Type | Used by | Description |
|---|---|---|---|
| `wordlist` | `list[str]` | `Subdomain_Scanner` | words to try as subdomains — **Postgres-backed as of v0.8.2**, starts empty, populated by `_load_lists()` |
| `security_headers` | `list[str]` | `Header_Analyzer` | security headers to check for — Postgres-backed |
| `urls` | `list[str]` | `Cast_Spell` | targets to analyze — Postgres-backed |
| `banners` | `list[str]` | `Port_Scanner` (write), `CVE_Lookup` (read) | banners collected from the last scanned target |
| `db_pool` | `asyncpg.Pool \| None` | every module that persists findings | shared connection pool, set by `_load_lists()` |

**Design note**: `banners` is reset on every call to `Port_Scanner(ip)`, so it's only valid for the current target within the same `Cast_Spell` cycle. Since v0.8.2, other findings (emails, document metadata, ZAP alerts, ARP hosts, k6 configs) *are* persisted across the whole run and across processes — see [database.md](../modules/database.md) — closing the history gap this section used to flag.

## Runtime extension

Three `async classmethod`s allow extending shared state via interactive CLI input, now persisted to Postgres before updating the in-memory list:
- `add_word()` → writes to `wizard_wordlist`, then appends to `wordlist`
- `add_header()` → writes to `wizard_security_headers`, then appends to `security_headers`
- `add_url()` → writes to `wizard_urls`, then appends to `urls`

They are still **not** called automatically by `Cast_Spell`: they must be invoked explicitly (and now `await`ed) before execution, and require `db_pool` to already be initialized.

Two more classmethods/methods manage state beyond the three lists above:
- `clear_findings(target=None)` → empties findings tables (never the three lists above)
- `LAN_Scan(subnet)` → runs an ARP sweep + ZAP scan outside the url-driven loop

## Concurrency: async vs threads vs a real DB driver

The codebase mixes several concurrency models:
- **`asyncio`** for anything that's "native" network I/O (`aiohttp`, `asyncio.open_connection`)
- **`asyncpg`** (new in v0.8.2) for Postgres — also fully async end-to-end (unlike `psycopg2`, it never needs `asyncio.to_thread`)
- **`ThreadPoolExecutor`** for blocking/synchronous code with no direct async counterpart (raw `socket`, the `python-nmap` library)
- **`subprocess`** (via `asyncio.create_subprocess_exec` for `arp-scan`, and a detached `subprocess.Popen` for the long-running ZAP daemon) for external binaries

To avoid blocking the event loop when calling synchronous code from inside an `async def`, the codebase uses `asyncio.to_thread` (for `Socket_Port_Scanner`/`Socket_Banner_Grabber`) and `loop.run_in_executor` (for `nmap.PortScanner.scan`) — see [reconnaissance.md](../modules/reconnaissance.md) and [async.md](async.md).

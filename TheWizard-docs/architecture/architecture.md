# Architecture

[← Index](20_Projects/Test_The-Wizard/index.md)

## Pattern

`TheWidzard` is a **facade**: a single class inheriting from several specialized modules, each responsible for one phase of a pentest. The user only interacts with `TheWidzard`, without needing to know the details of each individual module.

```
TheWidzard(
    Reconnaissance_Tool,            # recon: ports, subdomains, http
    Vulnerability_Assessment_Tool,  # vuln analysis: headers, CVEs, SSL/TLS
    Exploitation_tool,              # exploitation (stub)
    Post_Exploitation_tool,         # post-exploitation (stub)
    Network_tool,                   # network info-gathering wrapper
    OSINT_tool                      # open-source intelligence wrapper
)
```

> **Version 7 note**: the class was renamed from `Vulnerability_Assesment_Tool` (typo, missing an "s") to `Vulnerability_Assessment_Tool`. For backward compatibility a module-level alias is defined: `Vulnerability_Assesment_Tool = Vulnerability_Assessment_Tool` — code/docs still referencing the old name keep working.

Each module exposes a **"spell"**, a method that orchestrates the module's internal functions:

| Module | Spell |
|---|---|
| `Reconnaissance_Tool` | `Recon_Spell(ip)` |
| `Vulnerability_Assessment_Tool` | `Vuln_Asses_Spell(session, url)` |
| `Exploitation_tool` | `Exploit_Spell()` |
| `Post_Exploitation_tool` | `Post_Exploit_Spell()` |
| `Network_tool` | `Network_Spell(session, url)` |
| `OSINT_tool` | `OSINT_Spell(session, url)` |

`TheWidzard.Cast_Spell()` is the single entry point: it iterates over `self.urls` and calls all the spells in sequence for each target. *(The `TheWidzard` class itself wasn't included in the last code exchange — the documentation in `06_thewidzard.md` still reflects the previous version; it needs to be re-checked once the updated facade arrives.)*

## Shared state

Class-level attributes defined on `TheWidzard`, inherited/used by the modules via `self`:

| Attribute | Type | Used by | Description |
|---|---|---|---|
| `wordlist` | `list[str]` | `Subdomain_Scanner` | words to try as subdomains |
| `banners` | `list[str]` | `Port_Scanner` (write), `CVE_Lookup` (read) | banners collected from the last scanned target |
| `security_headers` | `list[str]` | `Header_Analyzer` | security headers to check for |
| `urls` | `list[str]` | `Cast_Spell` | targets to analyze |

**Design note**: `banners` is reset on every call to `Port_Scanner(ip)`, so it's only valid for the current target within the same `Cast_Spell` cycle. If a history is needed in the future, it must be persisted before the next iteration (see `09_roadmap.md`).

## Runtime extension

Three `classmethod`s allow extending shared state via interactive CLI input:
- `add_word()` → appends to `wordlist`
- `add_header()` → appends to `security_headers`
- `add_url()` → appends to `urls`

They are **not** called automatically by `Cast_Spell`: they must be invoked explicitly before execution.

## Concurrency: async vs threads

The codebase mixes two concurrency models:
- **`asyncio`** for anything that's "native" network I/O (`aiohttp`, `asyncio.open_connection`)
- **`ThreadPoolExecutor`** for blocking/synchronous code with no direct async counterpart (raw `socket`, the `python-nmap` library)

To avoid blocking the event loop when calling synchronous code from inside an `async` function, Version 7 introduces `asyncio.to_thread` (for `Socket_Port_Scanner`/`Socket_Banner_Grabber`) and `loop.run_in_executor` (for `nmap.PortScanner.scan`) — see details in `02_reconnaissance_tool.md` and the changelog.

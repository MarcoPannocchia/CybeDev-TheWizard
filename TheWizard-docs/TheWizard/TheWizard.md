# `TheWizard`

[← Index](../index.md)

#verified

> ✅ **Gap closed**: earlier passes (through Version 7 / v0.8.0) only had the modules, not this facade class, so this page described the *previous* version from memory. As of v0.8.2 the full `TheWizard_v082.py` source was received — everything below is verified against it.

Main class (facade). Inherits from all mixins — see [architecture.md](../architecture/architecture.md) — and defines the shared state plus the `Cast_Spell` entry point.

```python
class TheWizard(Reconnaissance_Tool,
                Vulnerability_Assesment_Tool,
                Exploitation_tool, Post_Exploitation_tool,
                Network_tool, OSINT_tool, AI_Suggestions):
```

Note the source spelling: the class is `TheWizard` (not `TheWidzard`) — see the naming note in [facade.md](../architecture/facade.md). `Vulnerability_Assesment_Tool` here is the backward-compatible alias for `Vulnerability_Assessment_Tool` (see [vulnerability.md](../modules/vulnerability.md)); either name works in the inheritance list.

---

## Class attributes

| Attribute | Default | Description |
|---|---|---|
| `wordlist` | `[]` | words for the subdomain scanner — loaded from Postgres by `_load_lists()`, not hardcoded anymore |
| `security_headers` | `[]` | headers checked by the header analyzer — loaded from Postgres |
| `urls` | `[]` | targets to analyze — loaded from Postgres |
| `banners` | `[]` | populated at runtime by `Port_Scanner`, should not be initialized manually |
| `db_pool` | `None` | shared `asyncpg` connection pool; set by `_load_lists()`, stays `None` until then |

> **What changed vs Version 7 / v0.8.0**: `wordlist`, `security_headers`, and `urls` used to be hardcoded literals directly on the class. They now live in Postgres (see [database.md](../modules/database.md)) and are loaded once into these class attributes at the start of `Cast_Spell`. Every *read* during a scan (`Subdomain_Scanner`, `Header_Analyzer`, the url loop, …) hits this in-memory list, not the database — only *writes* (`add_word`/`add_header`/`add_url`) touch Postgres.

---

## `async _load_lists(cls)` *(classmethod, new in v0.8.2)*

**Description:** initializes the shared DB pool (`db.init_pool()`) and loads `wordlist`/`security_headers`/`urls` from Postgres into the class attributes above.

**Fails loudly by design:** if Postgres is unreachable or a required `WIZARD_DB_*` environment variable is missing, `db.init_pool()` raises and the process stops here — it will never silently scan with an empty or stale list. See [database.md](../modules/database.md) and [setup_and_usage.md](../architecture/setup_and_usage.md) for the required environment variables.

**Called by:** `Cast_Spell` (first line) and, lazily, `LAN_Scan` if the pool hasn't been initialized yet.

---

## `async Cast_Spell(self)`

**Description:** main entry point. Loads the config lists from Postgres, then for each url in `self.urls`, runs the full analysis flow using each module's *spell*:

1. `_load_lists()` — populate `wordlist`/`security_headers`/`urls`/`db_pool` from Postgres
2. `Network_Spell(session, url)` — HTTP fetch + ZAP scan (spider → active scan → alerts)
3. `OSINT_Spell(session, url)` — subdomain scan, email harvesting, document metadata extraction
4. DNS resolution → `Recon_Spell(ip)` (orchestrates the 3 port-scan types)
5. `Vuln_Asses_Spell(session, url)` — headers, CVE lookup, SSL/TLS check
6. `Exploit_Spell(url)` — builds (never runs) a k6 load-test config for `url`
7. `Post_Exploit_Spell()`

**DNS error handling:** `socket.gaierror` is caught and logged — if resolution fails, the port scan for that target is skipped (the rest of the flow for that url still runs).

**Resource cleanup (new in v0.8.2):** the whole url loop runs inside `try/finally`, with `await db.close_pool()` in `finally` — the connection pool is released even if a target's scan raises.

**Returns:** `None`

---

## Runtime configuration classmethods

All three now write to Postgres first, then mirror the change into the in-memory list — different from the pre-0.8.2 behavior of appending in-memory only. All three still use blocking CLI `input()` for the new value, and none validate it.

### `async add_word(cls)`
Prompts for a word, calls `db.add_word(cls.db_pool, new_word)`, then appends it to `wordlist`.

### `async add_header(cls)`
Prompts for a header, calls `db.add_security_header(cls.db_pool, new_header)`, then appends it to `security_headers`.

### `async add_url(cls)`
Prompts for a url, calls `db.add_url(cls.db_pool, new_url)`, then appends it to `urls`.

**Guard:** all three print `"[ERROR] Database pool not initialized -- call Cast_Spell (or _load_lists) first"` and return early if `cls.db_pool is None` — i.e. before `Cast_Spell`/`_load_lists` has run at least once.

**Note:** still not called automatically by `Cast_Spell` — must be invoked explicitly, and now must be `await`ed since they're coroutines.

---

## `async clear_findings(cls, target=None)` *(classmethod, new in v0.8.2)*

**Description:** empties the findings tables via `db.clear_findings` — emails, document metadata, k6 configs, ZAP alerts, and (only when `target is None`) ARP hosts, since ARP hosts aren't tied to a single target.

**Parameters:** `target: str | None` — if given, clears only that target's rows; if omitted, clears everything.

**Never touches** the config lists (`wordlist`/`security_headers`/`urls`) — those aren't findings.

**Guard:** same `db_pool is None` early-return pattern as the `add_*` classmethods.

---

## `async LAN_Scan(self, subnet)` *(instance method, new in v0.8.2)*

**Description:** convenience entry point for `Network_tool.LAN_Recon_Spell` (ARP sweep → ZAP on each discovered host) outside the url-driven `Cast_Spell` loop, since a subnet isn't one of `self.urls`.

**Parameters:** `subnet: str` — e.g. `"192.168.1.0/24"`.

**Lifecycle:** lazily calls `_load_lists()` if `self.db_pool is None` (so it works standalone, without `Cast_Spell` having run first), opens its own `aiohttp.ClientSession`, and calls `LAN_Recon_Spell(session, subnet)`. Manages its own session/pool the way `Cast_Spell` does, but does **not** close the pool afterward — it's meant to be callable more than once in the same process.

See [modules/network.md](../modules/network.md) for what `LAN_Recon_Spell`/`ARP_Scanner` actually do.

---

## Running the script

```python
Casper = TheWizard()
asyncio.run(Casper.Cast_Spell())
```

`urls` used to include a placeholder (`https://ejendom.com` in earlier snapshots); as of v0.8.2 it starts empty and is loaded from Postgres, so at least one row must exist in `wizard_urls` before running, or the url loop simply does nothing.

Note: `Casper` is an instance, but all the attributes modified (`wordlist`, `banners`, `db_pool`, etc.) are class attributes — meaning they'd be shared across any additional `TheWizard` instances created within the same process.

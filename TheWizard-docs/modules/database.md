# `DatabaseTheWidzard` (the `db` module)

[← Index](../index.md)

#verified — new in v0.8.2 (`DatabaseTheWidzard_v082.py`)

Not a tool mixin — a plain module imported as `db` by `TheWizard_v082.py`, `ModulesTheWidzard_v082.py`, and `Network_tool_v082.py`. Provides Postgres persistence via `asyncpg`. See [async.md](../architecture/async.md) for why `asyncpg` specifically, and [setup_and_usage.md](../architecture/setup_and_usage.md) for the required environment variables.

---

## Pool management

### `async init_pool()`
Creates (once — idempotent, guarded by a module-level `_pool` global) and returns the shared `asyncpg.Pool`. Reads connection settings from `WIZARD_DB_*` environment variables (`_env()` helper — raises `RuntimeError` if a required one is missing). Registers `_init_connection` as the pool's `init` callback, which sets up `jsonb`/`json` type codecs (`json.dumps`/`json.loads`) — without this, JSONB columns come back as raw strings instead of `dict`/`list`. Calls `_init_schema(pool)` before returning, so the schema always exists after `init_pool()` succeeds.

### `async close_pool()`
Closes and clears the shared pool. Called once, in `TheWizard.Cast_Spell`'s `finally` block.

---

## Schema

Nine tables, created with `CREATE TABLE IF NOT EXISTS` inside a single transaction (`_init_schema`). The `_SCHEMA_STATEMENTS` tuple is **additive by design** — new tables get appended rather than altering existing ones, so old rows and old code paths keep working when a new table is added later.

### Config lists

| Table | Columns | Notes |
|---|---|---|
| `wizard_wordlist` | `id, word (unique)` | backs `TheWizard.wordlist` |
| `wizard_security_headers` | `id, header (unique)` | backs `TheWizard.security_headers` |
| `wizard_urls` | `id, url (unique)` | backs `TheWizard.urls` |

### Findings

| Table | Columns | Notes |
|---|---|---|
| `wizard_emails` | `id, target, email, discovered_at`, unique `(target, email)` | from `Email_Harvester` |
| `wizard_metadata` | `id, target, source_url, file_type, metadata (jsonb), discovered_at`, unique `(target, source_url)` | from `Metadata_Extractor`; upserts on conflict (re-discovering the same doc updates metadata + timestamp) |
| `wizard_k6_configs` | `id, target, config (jsonb), script, created_at` | from `Exploitation_tool.Exploit_Spell` — one row per build, no unique constraint (history is kept) |
| `wizard_zap_alerts` | `id, target, url, risk, alert_name, description, raw (jsonb), discovered_at` | from `Network_tool.ZAP_Scanner` |
| `wizard_arp_hosts` | `id, subnet, ip, mac, vendor, discovered_at`, unique `(subnet, ip, mac)` | from `Network_tool.ARP_Scanner`/`LAN_Recon_Spell` |

---

## Identifier safety

`_LIST_TABLES` (`wordlist`/`security_headers`/`urls` → table+column name) and `_FINDINGS_TABLES` are **hardcoded, fixed whitelists**. Every generic list-access helper (`_get_list`, `_add_to_list`, `_add_many_to_list`, `_remove_from_list`) looks the table/column name up from this dict — never builds it from caller input. This matters because parameterized queries (`$1`, `$2`, …) only protect *values*, not identifiers (table/column names) — there's no equivalent placeholder for those in SQL, so the only safe way to vary an identifier is to select it from a fixed, trusted set rather than interpolate caller-controlled text.

---

## Public API (what the rest of the codebase actually calls)

### Config lists
`get_wordlist` / `add_word` / `add_words_bulk` / `remove_word`, and the equivalent `*_security_header`/`*_url` trio, all thin wrappers over the generic `_get_list`/`_add_to_list`/`_add_many_to_list`/`_remove_from_list` helpers above.

### `async load_config_lists(pool, cooldown=None)`
Fetches `wordlist`/`security_headers`/`urls` in one call — used by `TheWizard._load_lists()` to seed the class attributes at startup. **Rate-limited**: a caller invoking this repeatedly within `cooldown` seconds (default `WIZARD_DB_LOAD_COOLDOWN`, 2s) gets the cached last result instead of hitting Postgres again — guards against, e.g., a retry loop or a future UI re-loading state too aggressively.

### Findings writers/readers
- `save_email` / `save_emails_bulk` / `get_emails`
- `save_metadata` / `get_metadata` (upsert on `(target, source_url)` conflict)
- `save_k6_config` / `get_k6_configs`
- `save_zap_alerts_bulk` (skips a malformed alert dict — missing `risk`/`alert` — per-entry, same guard pattern as `CVE_Lookup`) / `get_zap_alerts`
- `save_arp_hosts_bulk` / `get_arp_hosts`

All the `*_bulk` writers use `executemany()` — one network round-trip instead of one `execute()` per row.

### `async clear_findings(pool, target=None)`
Deletes rows from every table in `_FINDINGS_TABLES`, inside a transaction. With `target=None`, clears everything across all targets **and** `wizard_arp_hosts` (not per-target, so only cleared in the "everything" case). With a `target`, clears only that target's rows in the per-target tables — `wizard_arp_hosts` is left untouched (ARP hosts aren't tied to one target). Config tables (`wordlist`/`security_headers`/`urls`) are never touched here — see [TheWizard/TheWizard.md](../TheWizard/TheWizard.md#async-clear_findingscls-targetnone-classmethod-new-in-v082).

---

## Where each caller reaches the DB

Every module that persists findings uses the same pattern — `db_pool = getattr(self, "db_pool", None)`, then only writes if it's set — so a scan still runs (with findings only printed, not persisted) if `Cast_Spell`/`_load_lists` was somehow skipped. This mirrors the facade's own `add_word`/`add_header`/`add_url`/`clear_findings` guard (`if cls.db_pool is None: print("[ERROR] ...") ; return`).

# Setup and Usage

[← Index](../index.md)

## Requirements

- Python 3.8+ (for the `asyncio` features used)
- `nmap` binary installed at the OS level (required by `python-nmap`)
- A reachable **PostgreSQL** instance (required as of v0.8.2 — `Cast_Spell` fails at startup without one, see [database.md](../modules/database.md))
- **OWASP ZAP** installed, with `zap.sh` on the path configured by `Network_tool.zap_path` (default `/usr/share/zaproxy/zap.sh`) — required for `Network_Spell`'s ZAP scan step
- `arp-scan` binary on `PATH` (or `Network_tool.arp_scan_path` pointed at it) — required for `ARP_Scanner`/`LAN_Scan`, and usually needs root / `CAP_NET_RAW` to send raw ARP frames
- A **Groq** API key (`GROQ_API_KEY`) if you intend to call `AI_Suggest_Spell` — optional, since it isn't wired into `Cast_Spell` yet
- Some features require root/admin privileges (raw sockets, nmap `-sV`, ARP scanning)

## Python dependencies

```bash
pip install aiohttp python-nmap asyncpg pypdf python-docx
```

`socket`, `asyncio`, `ssl`, `subprocess`, `atexit`, `re`, `json`, `time`, `dataclasses`, `collections`, `datetime`, `io`, `urllib.parse`, `concurrent.futures` are all part of the standard library — no installation needed.

## Environment variables (new in v0.8.2)

Read by `DatabaseTheWidzard_v082.py`'s `init_pool()`:

| Variable | Required | Default | Notes |
|---|---|---|---|
| `WIZARD_DB_NAME` | ✅ yes | — | raises if unset |
| `WIZARD_DB_USER` | ✅ yes | — | raises if unset |
| `WIZARD_DB_PASSWORD` | ✅ yes | — | raises if unset |
| `WIZARD_DB_HOST` | no | `localhost` | |
| `WIZARD_DB_PORT` | no | `5432` | |
| `WIZARD_DB_SSL` | no | `require` | set to `disable` to turn off TLS |
| `WIZARD_DB_POOL_MIN` | no | `1` | |
| `WIZARD_DB_POOL_MAX` | no | `10` | size to expected concurrency — see [async.md](async.md) |
| `WIZARD_DB_TIMEOUT` | no | `10` (seconds) | per-command timeout |
| `WIZARD_DB_LOAD_COOLDOWN` | no | `2` (seconds) | cache window for `load_config_lists` |

Read by `AI_Suggestions.AI_Suggest_Spell`:

| Variable | Required | Notes |
|---|---|---|
| `GROQ_API_KEY` | only if `AI_Suggest_Spell` is called without an explicit `api_key` argument | prints `[AI ERROR] No Groq API key found (set GROQ_API_KEY)` and returns `None` if missing |

## Configuring targets

As of v0.8.2, `wordlist`, `security_headers`, and `urls` are **Postgres-backed**, not hardcoded in the source. To change them:

- **at startup**: seed the `wizard_wordlist` / `wizard_security_headers` / `wizard_urls` tables directly (they're created automatically by `_init_schema` on first connect)
- **at runtime**: call `await TheWizard.add_url()` (requires terminal input) — same for `add_word()`/`add_header()`. These persist to Postgres and update the in-memory list.

`Cast_Spell` calls `_load_lists()` first, which will **raise** if Postgres is unreachable or a required `WIZARD_DB_*` variable is missing — there's no fallback to an empty/hardcoded default.

## Running it

```bash
python TheWizard_v082.py
```

Runs `asyncio.run(Casper.Cast_Spell())`, which:
1. loads `wordlist`/`security_headers`/`urls` from Postgres,
2. analyzes every url in `urls` in sequence (recon, vuln assessment, ZAP scan, OSINT, k6 config build, post-exploitation stub),
3. releases the DB connection pool.

For an ARP/LAN sweep outside the url loop:

```python
Casper = TheWizard()
asyncio.run(Casper.LAN_Scan("192.168.1.0/24"))
```

## Output

All output currently goes to stdout via `print()`, with conventional prefixes for visual parsing:

| Prefix | Meaning |
|---|---|
| `[TARGET]` | start of analysis for a new url |
| `[STATUS]` / `[BODY]` | HTTP response |
| `[FOUND]` / `[MISSING]` | header analyzer result / subdomain found |
| `[PORT]` | port scan result |
| `[BANNER]` | captured banner |
| `[RESOLVED]` | successful DNS resolution |
| `[OUTPUT-*]` / `[OUTPUT-SOCKET]` | nmap / socket scanner results |
| `[CVE]` | CVE lookup result |
| `[SSL]` / `[WARNING]` | SSL/TLS check result |
| `[ZAP]` | ZAP daemon/spider/active-scan progress and alerts |
| `[ARP]` / `[LAN]` | ARP sweep results, hosts handed to ZAP |
| `[EMAIL]` | email harvester result |
| `[METADATA]` | document metadata extractor result |
| `[K6]` | k6 load-test config build/persist status |
| `[AI ...]` / `[AI RATE-LIMIT]` | AI_Suggestions status (not yet called during a normal run) |
| `[DB]` | `clear_findings` confirmation |
| `[ERROR]` / `[CVE ERROR]` / `[SSL ERROR]` / `[DEBUG]` / `[CVE PARSE ERROR]` / `[ZAP PARSE ERROR]` / `[METADATA ERROR]` / `[DB ERROR]` / `[DB CONFIG ERROR]` / `[API ERROR]` | handled errors |

As of v0.8.2, scan output is **also** persisted to Postgres (emails, document metadata, k6 configs, ZAP alerts, ARP hosts) — stdout is no longer the only record. See [database.md](../modules/database.md).

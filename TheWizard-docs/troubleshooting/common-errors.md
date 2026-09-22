# Troubleshooting — Common Errors

## UnboundLocalError: idx_insert

**Symptom:**
```
UnboundLocalError: local variable 'idx_insert' referenced before assignment
```

**Cause:**
`insert_word` was called with a URL that does not contain `//` (e.g. `google.com` instead of `https://google.com`).
The loop never finds the condition `i != "/" and prec_i == "/"`, so `idx_insert` is never assigned.

**Fix:**
Always pass full URLs including protocol:
```python
urls = ["https://google.com"]   # ✅
urls = ["google.com"]           # ❌
```

> See also: [[modules/reconnaissance.md]]

---

## TypeError: ClientSession object is not iterable

**Symptom:**
```
TypeError: 'ClientSession' object is not iterable
```

**Cause:**
Parameters `session` and `url` are swapped in a method call.
`insert_word` receives `session` where it expects a string URL and tries to iterate it.

**Fix:**
Check parameter order — all tool methods follow `(self, session, url)`:
```python
await self.Subdomain_Scanner(session, url)   # ✅
await self.Subdomain_Scanner(url, session)   # ❌
```

---

## TypeError: takes N positional arguments but M were given

**Symptom:**
```
TypeError: method() takes 2 positional arguments but 3 were given
```

**Cause:**
`self` is being passed manually in a method call inside the class.

**Fix:**
Never pass `self` explicitly — Python injects it automatically:
```python
await self.fetch_info(session, url)        # ✅
await self.fetch_info(self, session, url)  # ❌
```

---

## RuntimeWarning: coroutine was never awaited

**Symptom:**
```
RuntimeWarning: coroutine 'method' was never awaited
```

**Cause:**
An `async def` function was called without `await`.

**Fix:**
```python
await self.Header_Analyzer(session, url)   # ✅
self.Header_Analyzer(session, url)         # ❌
```

---

## aiohttp import error — ClientTimeout not found

**Symptom:**
```
NameError: name 'ClientTimeout' is not defined
```

**Fix:**
```python
from aiohttp import ClientTimeout   # ✅
```

> See also: [[architecture/async.md]]

---

## RuntimeError: required environment variable WIZARD_DB_* is not set *(new in v0.8.2)*

**Symptom:**
```
[DB CONFIG ERROR] required environment variable WIZARD_DB_NAME is not set
RuntimeError: [DB CONFIG ERROR] required environment variable WIZARD_DB_NAME is not set
```

**Cause:**
`Cast_Spell` calls `_load_lists()` first, which calls `db.init_pool()`. `WIZARD_DB_NAME`, `WIZARD_DB_USER`, and `WIZARD_DB_PASSWORD` have no defaults and are required — this is deliberate (see [modules/database.md](../modules/database.md)): the process is meant to fail loudly here rather than silently scan with an empty/stale config list.

**Fix:**
Set all three before running (see [commands/run.md](../commands/run.md)):
```bash
export WIZARD_DB_NAME=thewizard
export WIZARD_DB_USER=thewizard
export WIZARD_DB_PASSWORD=change-me
```

---

## `[DB ERROR] Could not create connection pool` *(new in v0.8.2)*

**Cause:** Postgres isn't reachable at `WIZARD_DB_HOST:WIZARD_DB_PORT`, or the credentials/SSL mode are wrong (`asyncpg.PostgresError`).

**Fix:** confirm Postgres is running and reachable from the host running `TheWizard_v082.py`; if it's a local dev instance without TLS, set `WIZARD_DB_SSL=disable`.

---

## `add_word`/`add_header`/`add_url`/`clear_findings` print `[ERROR] Database pool not initialized` *(new in v0.8.2)*

**Cause:** one of these classmethods was called before `Cast_Spell` (or `_load_lists()`) has run at least once in the process — `TheWizard.db_pool` is still `None`.

**Fix:**
```python
await TheWizard._load_lists()   # or run Cast_Spell() first
await TheWizard.add_url()       # ✅ now db_pool is set
```

> See also: [modules/database.md](../modules/database.md) | [TheWizard/TheWizard.md](../TheWizard/TheWizard.md)

---

## `[ERROR] ZAP daemon unavailable, skipping scan` / `[ERROR] ZAP executable not found` *(new in v0.8.2)*

**Cause:** `Network_tool.zap_path` doesn't point at a real `zap.sh`, or ZAP isn't installed. `Network_Spell` degrades gracefully — it skips the ZAP step and continues the rest of `Cast_Spell` rather than crashing.

**Fix:** install OWASP ZAP and confirm the path:
```python
class Network_tool():
    zap_path = "/path/to/your/zap.sh"
```

---

## `[ERROR] arp-scan executable not found` / arp-scan exits non-zero mentioning "permitted"/"permission" *(new in v0.8.2)*

**Cause:** `arp-scan` isn't installed, or the process lacks the privileges needed to send raw ARP frames.

**Fix:**
```bash
sudo apt install arp-scan
```
Run with root, or grant the capability instead of running as root:
```bash
sudo setcap cap_net_raw+ep $(which arp-scan)
```

---

## `[AI ERROR] No Groq API key found (set GROQ_API_KEY)` *(new in v0.8.2)*

**Cause:** `AI_Suggest_Spell` was called without an explicit `api_key` argument and `GROQ_API_KEY` isn't set in the environment.

**Fix:**
```bash
export GROQ_API_KEY=gsk_...
```

---

## `[AI ERROR] Groq rate limit hit (429)` *(new in v0.8.2)*

**Cause:** the account-level Groq rate limit was hit despite the client-side `_GroqRateLimiter` — usually means `GroqModelFile.requests_per_minute`/`tokens_per_minute` are set higher than your actual Groq tier allows.

**Fix:** lower `AI_Suggestions.modelfile`'s `requests_per_minute`/`tokens_per_minute` to match your real Groq account limits, or wait `retry-after` seconds (printed in the error message) before retrying.

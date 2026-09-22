# Architecture — Asyncio, aiohttp & asyncpg

#verified

## Overview

TheWizard uses `asyncio` and `aiohttp` for all HTTP operations and network I/O, and, as of v0.8.2, `asyncpg` for Postgres access.

> **Definition:** `asyncio` is an optimization of wait times — it suspends operations waiting for I/O and advances execution of others, all on a single thread.

---

## Why async?

Network operations (HTTP requests, TCP connections) spend most of their time **waiting** for a response.
Without async, each operation blocks the entire program until it completes.

```
# Synchronous — sequential, slow
scan("mail.google.com")   # wait 3s
scan("api.google.com")    # wait 3s
scan("dev.google.com")    # wait 3s
# total: 9s

# Async with gather — concurrent, fast
gather(
    scan("mail.google.com"),   # ─┐
    scan("api.google.com"),    #  ├─ all waiting at the same time
    scan("dev.google.com"),    # ─┘
)
# total: ~3s
```

---

## asyncio.gather

`gather` takes multiple coroutines and runs them concurrently.

```python
await asyncio.gather(*[self._word_scan(session, url, word) for word in self.wordlist])
```

- The list comprehension creates one coroutine per word — none of them execute yet
- `*` unpacks the list into separate arguments
- `gather` launches all of them and waits for all to complete

> See also: [[modules/reconnaissance.md]]

---

## ClientTimeout

`ClientTimeout` sets a maximum wait time for aiohttp requests.

```python
from aiohttp import ClientTimeout

async with session.get(url, timeout=ClientTimeout(total=3)) as r:
    ...
```

| Parameter | Description |
|-----------|-------------|
| `total` | Max time for the entire request (seconds) |
| `connect` | Max time to establish the connection |
| `sock_read` | Max time to read the response |

> Without a timeout, a non-responding host blocks the coroutine indefinitely.

---

## aiohttp.ClientSession

`ClientSession` is the main aiohttp object. It manages connection pooling and should be reused across requests.

```python
async with aiohttp.ClientSession() as session:
    await self.fetch_info(session, url)
    await self.Header_Analyzer(session, url)
    await self.Subdomain_Scanner(session, url)
```

- Created once in `Cast_Spell` (the current entry point — see [[TheWizard]])
- Passed as argument to all tool methods
- Closed automatically at the end of the `async with` block

> [!success] CVE_Lookup session-reuse issue — fixed since Version 7
> `CVE_Lookup` (added v0.5.0, see [[vulnerability.md]]) used to open its own `aiohttp.ClientSession()`
> internally instead of accepting and reusing the shared session. As of Version 7 (v0.8.0) it
> receives `session` as a parameter like every other tool method, and this remains true in v0.8.2.
> Kept here as historical context — see [CHANGELOG.md](../CHANGELOG.md).

---

## asyncpg — a second, separate async driver (new in v0.8.2)

`DatabaseTheWidzard_v082.py` uses `asyncpg` rather than `psycopg2` specifically because it's async end-to-end: socket I/O, wire-protocol parsing, and query execution all yield to the event loop instead of blocking it. `psycopg2` is synchronous and would need `asyncio.to_thread` (the same pattern used for `Socket_Port_Scanner`, see [reconnaissance.md](../modules/reconnaissance.md)) to avoid freezing the loop.

```python
_pool: asyncpg.Pool | None = None

async def init_pool():
    global _pool
    if _pool is not None:
        return _pool
    _pool = await asyncpg.create_pool(host=..., port=..., database=..., user=..., password=...,
                                       min_size=..., max_size=..., command_timeout=..., init=_init_connection)
    await _init_schema(_pool)
    return _pool
```

A connection **pool**, not a single connection, is created once via `TheWizard._load_lists()` at the start of `Cast_Spell` — `pool.acquire()` is used around every individual query (see [database.md](../modules/database.md)). `_init_connection` also registers JSON/JSONB codecs on every new connection, since `asyncpg` doesn't decode `jsonb` columns on its own — without it, every JSONB column (`wizard_metadata.metadata`, `wizard_zap_alerts.raw`, `wizard_k6_configs.config`) would come back as a raw JSON string instead of a `dict`/`list`.

> [!warning] Things that can still slow a scan down even with a fully-async driver — #known-issue
> - **Pool exhaustion**: `pool.acquire()` awaits until a connection is free. If a scan fans out many concurrent DB calls at once, a small pool serializes them — not a blocked event loop, but a self-imposed rate cap. Size `WIZARD_DB_POOL_MAX` to the expected concurrency.
> - **Holding a connection across an unrelated `await`** (e.g. an `aiohttp` call inside the same transaction) locks that connection away from every other concurrent task for the whole duration.
> - **Large result sets**: decoding a big `fetch()` is CPU-bound Python/C work on the loop thread — not a blocking syscall, but it still consumes time other scheduled tasks are waiting on.
> - **Row-by-row writes**: many individual `execute()` calls means many network round-trips; the DB layer uses `executemany()`/bulk helpers instead (`add_words_bulk`, `save_emails_bulk`, `save_zap_alerts_bulk`, `save_arp_hosts_bulk`) — see [database.md](../modules/database.md).

---

## Response object (`r`)

When a GET request succeeds, `r` contains the full HTTP response:

| Attribute | Type | Description |
|-----------|------|-------------|
| `r.status` | int | HTTP status code (200, 404, 500...) |
| `r.headers` | dict | Response headers from the server |
| `await r.text()` | str | Response body as string |

```python
async with session.get(url) as r:
    print(r.status)           # 200
    print(r.headers)          # {"Content-Type": "text/html", ...}
    body = await r.text()     # full HTML
```

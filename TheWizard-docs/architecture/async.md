# Architecture — Asyncio & aiohttp

#verified

## Overview

TheWidzard uses `asyncio` and `aiohttp` for all HTTP operations and network I/O.

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

- Created once in `Cast_Spell` (the current entry point — see [[TheWidzard]])
- Passed as argument to all tool methods
- Closed automatically at the end of the `async with` block

> [!bug] CVE_Lookup breaks this pattern — #known-issue
> `CVE_Lookup` (added v0.5.0, see [[vulnerability.md]]) opens its own `aiohttp.ClientSession()`
> internally instead of accepting and reusing the shared session. Every banner processed spins
> up a brand-new session/connection pool just for that one request — inconsistent with every
> other method in the toolkit, and wasteful if a target has many open ports. Worth refactoring
> to accept `session` as a parameter like the other tool methods do.

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

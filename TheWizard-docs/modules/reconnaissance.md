# `Reconnaissance_Tool`

[← Index](20_Projects/Test_The-Wizard/index.md)

Reconnaissance module: port scanning (three different implementations), banner grabbing, HTTP fetch, and subdomain enumeration.

---

### `async _port_scanner(self, ip, port, timeout=0.1)`
*Private — not called directly by `TheWidzard`.*

**Description:** attempts a raw TCP connection (`asyncio.open_connection`) to `ip:port`. If the port is open, tries to read up to 1024 bytes as a banner and appends it to `self.banners`.

**Parameters:** `ip: str`, `port: int`, `timeout: float = 0.1`

> `timeout` is now a parameter instead of a hardcoded value — allows tuning it per context (LAN vs internet scan) without editing the source.

**Returns:** `None` (side effect: prints to stdout, populates `self.banners`)

**Handled exceptions:**
| Exception | Behavior |
|---|---|
| `asyncio.TimeoutError` | silently ignored (port considered closed/filtered) |
| `ConnectionRefusedError` | prints `"access denied"` |
| `OSError` | prints `"server unreachable"` |

---

### `async Port_Scanner(self, ip, ports=None, timeout=0.1)`

**Description:** public entry point for the async scan. Resets `self.banners`, then runs `_port_scanner` in parallel (`asyncio.gather`) across all requested ports.

**Parameters:**
- `ip: str` — target
- `ports: list[int] | None` — default: 16 common ports (`20, 21, 22, 23, 25, 53, 80, 110, 143, 443, 445, 3306, 3389, 5432, 8080, 8443`)
- `timeout: float = 0.1` — passed through to `_port_scanner`

**Returns:** `None`

---

### `async Nmap_port_scanning(self, ip)`

**Description:** wrapper around [`python-nmap`](https://pypi.org/project/python-nmap/) for version detection.

**Parameters:** `ip: str`

**Returns:** `None` (prints state and service name for each detected TCP port)

**Implementation:**
```python
loop = asyncio.get_running_loop()
await loop.run_in_executor(None, lambda: nm.scan(ip, arguments="-sV"))
```
`nm.scan()` is a **synchronous, blocking** call (it shells out to the `nmap` binary and waits): running it directly inside an `async def` would freeze the entire event loop for the scan's duration. It's offloaded to the default `ThreadPoolExecutor` via `run_in_executor` — the event loop stays free in the meantime.

**Error handling:** `try/except` around `nmap.nmap.PortScannerError` (nmap-specific errors) and a generic `Exception`.

---

### `_socket_banner_grab(self, host, port, timeout=3)`
*Private, synchronous.*

**Description:** banner grabbing via raw `socket` (no `asyncio`). First tries a passive `recv`; if that times out, sends a `HEAD / HTTP/1.0` request and retries the read (useful for services that don't send a banner spontaneously, e.g. HTTP servers).

**Parameters:** `host: str`, `port: int`, `timeout: float = 3`

**Returns:** `bytes | None` — banner cleaned with `.strip()`, or `None` if empty

**Note:** deliberately synchronous/blocking, meant to run inside a `ThreadPoolExecutor`.

---

### `Socket_Banner_Grabber(self, host, port_min=0, port_max=1024, max_threads=100)`

**Description:** runs `_socket_banner_grab` in parallel across a port range using `ThreadPoolExecutor`.

**Parameters:** `host: str`, `port_min: int = 0`, `port_max: int = 1024`, `max_threads: int = 100`

**Returns:** `dict[int, bytes | str | None]` — port → banner map (or an error string if the thread raises an exception)

---

### `_socket_port_scan(self, host, port, timeout=3)`
*Private, synchronous.*

**Description:** checks whether a port is open using `socket.connect_ex` (returns a code instead of raising an exception).

**Parameters:** `host: str`, `port: int`, `timeout: float = 3`

**Returns:** `bool` — `True` if the connection succeeds (`result == 0`)

---

### `Socket_Port_Scanner(self, host, port_start=0, port_end=1024, max_threads=100)`

**Description:** multithreaded alternative to `Port_Scanner`, using raw `socket` instead of `asyncio`.

**Parameters:** `host: str`, `port_start: int = 0`, `port_end: int = 1024`, `max_threads: int = 100`

**Returns:** `list[int]` — open ports, sorted

**Why it exists alongside `asyncio`:** a comparison/fallback implementation — useful for educational purposes, to compare the two concurrency strategies (`asyncio` vs thread pool) applied to the same problem.

---

### `async fetch_info(self, session, url)`

**Description:** generic HTTP GET, used both by recon and by `Network_tool`.

**Parameters:** `session: aiohttp.ClientSession`, `url: str`

**Returns:** `tuple[int | None, str | None]` — `(status, body)`; `(None, None)` on error

**Handled exceptions:** `aiohttp.ClientError`, `asyncio.TimeoutError` (total timeout: 5s)

---

### `insert_word(self, url, word)`

**Description:** synchronous helper to build a subdomain URL: strips `www.` if present, prepends `word.` to the host.

**Parameters:** `url: str`, `word: str`

**Returns:** `str` — new URL, e.g. `insert_word("https://www.example.com", "api")` → `"https://api.example.com"`

**Implementation:** `urlparse` + `urlunparse`.

---

### `async Subdomain_Scanner(self, session, url)`

**Description:** public entry point for subdomain enumeration. Runs `_word_scan` in parallel for every word in `self.wordlist`.

**Parameters:** `session: aiohttp.ClientSession`, `url: str`

**Returns:** `None`

---

### `async _word_scan(self, session, url, word)`
*Private.*

**Description:** builds the subdomain URL via `insert_word` and checks whether it responds via GET (3s timeout).

**Parameters:** `session: aiohttp.ClientSession`, `url: str`, `word: str`

**Returns:** `None` (prints `[FOUND]` if it responds; network/timeout errors are silently ignored, other errors are logged as `[DEBUG]`)

---

### `async Recon_Spell(self, ip)`

**Description:** module orchestrator — runs the three port-scan implementations in sequence and, if the socket-based scan finds open ports, also runs the corresponding banner grabbing.

**Parameters:** `ip: str`

**Flow:**
1. `Port_Scanner(ip)` (asyncio)
2. `Nmap_port_scanning(ip)`
3. `Socket_Port_Scanner(ip, 1, 1024)` — run via `asyncio.to_thread(...)` → if it finds open ports, `Socket_Banner_Grabber` (also via `asyncio.to_thread`) on the found range

**Returns:** `None`

> **Fix — blocked event loop**: `Socket_Port_Scanner`/`Socket_Banner_Grabber` are synchronous and internally build their own `ThreadPoolExecutor`. Calling them directly from inside `Recon_Spell` — as the previous version did — still blocked the event loop for their entire duration: a sync call inside an `async def` doesn't automatically become concurrent with the loop just because it's "inside" an async function. They're now wrapped in `asyncio.to_thread(...)`, which hands them off to a separate thread and awaits the result without blocking the loop in the meantime.

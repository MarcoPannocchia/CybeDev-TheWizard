# `Network_tool`

[← Index](../index.md)

#verified — rewritten from scratch in v0.8.2, now its own file (`Network_tool_v082.py`)

> ⚠️ **Ethical use**: `ZAP_Scanner`'s active scan sends real attack payloads against the target. `ARP_Scanner`/`LAN_Recon_Spell` can discover and then scan hosts on a subnet that were never explicitly listed in `self.urls`. Both require the same explicit-authorization standard as `Exploitation_tool` — see [exploitation doc](exploitation_and_post_exploitation.md).

Previously a thin wrapper around `fetch_info` (see [CHANGELOG.md](../CHANGELOG.md)). As of v0.8.2 it owns real logic: managing an OWASP ZAP daemon, running ZAP's spider and active scan, and sweeping a LAN subnet via ARP.

---

## Class attributes (config, not hardcoded logic)

| Attribute | Default | Description |
|---|---|---|
| `zap_path` | `/usr/share/zaproxy/zap.sh` | ZAP launcher path — adapt to your install |
| `zap_port` | `8080` | local port ZAP's API/proxy runs on |
| `zap_api_key` | `""` | API key configured on ZAP, empty if disabled |
| `arp_scan_path` | `"arp-scan"` | resolved via `PATH`; override to an absolute path if needed |
| `max_lan_hosts_to_scan` | `10` | caps how many ARP-discovered hosts `LAN_Recon_Spell` hands to ZAP |
| `max_spidered_pages_to_scan` | `20` | caps how many ZAP-spidered pages get fed into the OSINT tools |

The two `max_*` bounds exist specifically so LAN discovery / spider results can't silently turn into an unattended mass-scan of everything they find.

---

## ZAP daemon management

### `async _zap_is_up(self, session)`
Probes `GET /JSON/core/view/version/` on the ZAP API (2s timeout). A process existing isn't enough — it has to actually answer the REST API to count as "up".

### `async _start_zap_daemon(self, session)`
If `_zap_is_up` already returns true, reuses the existing daemon (manual or from a previous run) instead of starting a duplicate. Otherwise launches `zap.sh -daemon` via a detached `subprocess.Popen` (never `await`ed — it's a long-running blocking process) and polls readiness every 2s for up to 30 attempts (60s), rather than a fixed sleep. Registers `atexit.register(self._stop_zap_daemon)` so a daemon *this run* started gets cleaned up on exit. Handles `FileNotFoundError` (ZAP not installed at `zap_path`) and generic launch failures.

### `_stop_zap_daemon(self)`
Terminates only the process started by *this run* (`self._zap_process`) — never kills a pre-existing ZAP instance left running for other uses.

---

## ZAP scan

### `async ZAP_Scanner(self, session, url)`
Orchestrates a full ZAP scan against `url`:

1. **Spider** (`/JSON/spider/action/scan/`) — maps the target's URLs so the active scan has more surface than just the entry page. Polls `/JSON/spider/view/status/` until 100%.
2. Reads spidered URLs (`/JSON/spider/view/results/`) and hands them to `_harvest_spidered_pages` (see below).
3. **Active scan** (`/JSON/ascan/action/scan/`) — the step that actually sends attack payloads. Polls `/JSON/ascan/view/status/` until 100%.
4. Reads alerts (`/JSON/core/view/alerts/`) — only reliable once the scan finished, since reading earlier gives a partial/empty list.
5. Prints `[ZAP] <risk> | <name> | <description>` per alert, skipping malformed entries individually (`try/except KeyError`, same per-item guard pattern as `CVE_Lookup`).
6. If `db_pool` is set, persists all alerts via `db.save_zap_alerts_bulk`.

**Exceptions handled:** `aiohttp.ClientError`, `asyncio.TimeoutError`, generic `Exception` as fallback.

### `async _harvest_spidered_pages(self, session, target, page_urls)`
Feeds ZAP-spidered pages into `Email_Harvester`/`Metadata_Extractor` (from `OSINT_tool` — see [osint.md](osint.md)) via `getattr(self, ..., None)` guards, since `Network_tool` alone doesn't have those methods; they're only reachable when mixed into `TheWizard` alongside `OSINT_tool`. Bounded by `max_spidered_pages_to_scan`. Saves emails/metadata found this way to Postgres the same way `OSINT_Spell` does.

---

## ARP / LAN sweep

### `_ARP_LINE_REGEX`
Matches `arp-scan --plain` output lines: `<ip>  <mac>  <vendor>`.

### `async ARP_Scanner(self, subnet)`
Sweeps `subnet` (e.g. `"192.168.1.0/24"`) via the external `arp-scan` binary (`asyncio.create_subprocess_exec`, 60s timeout) — same external-tool pattern as `nmap` in [reconnaissance.md](reconnaissance.md) and the ZAP daemon above, rather than reimplementing raw ARP framing in Python. Requires `arp-scan` installed and usually root/`CAP_NET_RAW`. Parses output into `{"ip", "mac", "vendor"}` dicts, printing `[ARP] <ip> - <mac> - <vendor>` per host. Handles `FileNotFoundError`, timeout, and a non-zero exit code (with a hint if stderr mentions a permission problem).

**Returns:** `list[dict]` — discovered hosts (empty list on any failure).

### `async LAN_Recon_Spell(self, session, subnet)`
1. Runs `ARP_Scanner(subnet)`.
2. Persists discovered hosts (`db.save_arp_hosts_bulk`) if any and if `db_pool` is set.
3. Hands the first `max_lan_hosts_to_scan` hosts to `ZAP_Scanner` as `http://<ip>/` targets.

**Same authorization requirement as `ZAP_Scanner`/`Exploitation_tool` applies to every host reached this way** — an ARP sweep can surface devices nobody explicitly listed as a target.

Called from the facade via `TheWizard.LAN_Scan(subnet)` — see [TheWizard/TheWizard.md](../TheWizard/TheWizard.md).

---

## Orchestration

### `async Network_Spell(self, session, url)`

**Flow:**
1. `fetch_info(session, url)` — prints `[STATUS]`/`[BODY]` if it succeeds (unchanged from the pre-0.8.2 wrapper behavior).
2. `_start_zap_daemon(session)`.
3. If the daemon process was started by this run, or is otherwise already up, runs `ZAP_Scanner(session, url)`. Otherwise prints `[ERROR] ZAP daemon unavailable, skipping scan` and moves on — a missing/broken ZAP install degrades this step rather than crashing the whole `Cast_Spell` run.

**Returns:** `None`

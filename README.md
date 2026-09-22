<div align="center">

<!-- 🖼️ Replace with the generated banner (banner_thewizard.png) -->
<img src="./docs/assets/TheWizard_banner.png" alt="TheWizard banner" width="100%">

# 🧙‍♂️ TheWizard

**Educational async Python security-assessment toolkit — CS50x final project**

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![asyncio](https://img.shields.io/badge/async-aiohttp%20%2F%20asyncio%20%2F%20asyncpg-8A2BE2)]()
[![nmap](https://img.shields.io/badge/scanning-python--nmap%20%2F%20ZAP%20%2F%20arp--scan-orange)]()
[![Status](https://img.shields.io/badge/status-currently%20in%20working-yellow)]()
[![License](https://img.shields.io/badge/license-see%20LICENSE.md-lightgrey)](./LICENSE.md)

</div>

---

## 📖 Table of Contents

- [About TheWizard](#about-thewizard)
- [Architecture](#architecture)
- [What's implemented](#whats-implemented)
- [Output tags](#output-tags)
- [Installation](#installation)
- [Usage](#usage)
- [Known issues](#known-issues)
- [Disclaimer](#disclaimer)
- [Author](#author)

---

## About TheWizard

**TheWizard** (internally `TheWidzard` in some module/file names) is an educational, fully asynchronous Python toolkit for security reconnaissance, vulnerability assessment, network scanning, and OSINT, built as a CS50x final project. It combines `asyncio`/`aiohttp` for network I/O, `python-nmap` and raw sockets for port scanning and service fingerprinting, `asyncpg`/PostgreSQL for persistence, OWASP ZAP for active web-application scanning, and `arp-scan` for local-network discovery.

> ⚠️ Built exclusively for authorized testing in controlled environments (lab environments, permitted bug bounty, or your own assets). The network-scanning and ARP/LAN-sweep features can reach and actively probe hosts beyond a single target URL — use accordingly.

---

## Architecture

TheWizard follows a **Facade pattern**: one orchestrator class inherits from several independent tool classes, each responsible for one phase of a security assessment. The single entry point is `Cast_Spell()`, which first loads its own configuration from PostgreSQL, then loops over every target in `self.urls` and calls each module's own orchestration method (its "**Spell**"):

```python
class TheWizard(Reconnaissance_Tool,
                Vulnerability_Assesment_Tool,
                Exploitation_tool, Post_Exploitation_tool,
                Network_tool, OSINT_tool, AI_Suggestions):
    ...
```

| Module | Spell | Role |
|---|---|---|
| `Reconnaissance_Tool` | `Recon_Spell(ip)` | port scanning (3 implementations), banner grabbing |
| `Vulnerability_Assessment_Tool` | `Vuln_Asses_Spell(session, url)` | header analysis, CVE lookup, SSL/TLS check |
| `Network_tool` | `Network_Spell(session, url)` | HTTP info gathering + OWASP ZAP spider/active scan; `LAN_Scan(subnet)` for ARP sweeps |
| `OSINT_tool` | `OSINT_Spell(session, url)` | subdomain enumeration, email harvesting, document metadata extraction |
| `Exploitation_tool` | `Exploit_Spell(target)` | builds (never executes) a `k6` load-test config/script |
| `Post_Exploitation_tool` | `Post_Exploit_Spell()` | placeholder — reserved for future modules |
| `AI_Suggestions` | `AI_Suggest_Spell(session, findings)` | Groq-backed risk triage report (not yet called by `Cast_Spell`) |

Code is split across four files: `TheWizard_v082.py` (facade), `ModulesTheWidzard_v082.py` (recon, vuln assessment, exploitation, OSINT, AI), `Network_tool_v082.py` (ZAP + ARP, its own file), and `DatabaseTheWidzard_v082.py` (the PostgreSQL/`asyncpg` persistence layer, imported as `db` by the other three).

Shared state (`wordlist`, `banners`, `security_headers`, `urls`) lives on the main class and is used across modules via `self`. `wordlist`, `security_headers`, and `urls` are now **PostgreSQL-backed** — loaded once at the start of `Cast_Spell` and extendable at runtime through `add_word()`, `add_header()`, `add_url()`, which write to the database first. Scan findings (emails, document metadata, ZAP alerts, ARP hosts, k6 configs) are persisted the same way.

Blocking calls (`nmap`, raw `socket`, ZAP's own long-running daemon process, `arp-scan`) are never run directly inside an `async def`: `Nmap_port_scanning` is offloaded via `loop.run_in_executor`, the socket-based scanner/banner grabber via `asyncio.to_thread`, the ZAP daemon via a detached `subprocess.Popen`, and `arp-scan` via `asyncio.create_subprocess_exec` — so the event loop never stalls. `asyncpg` is fully async end-to-end, so the database layer needs none of this offloading.

---

## What's implemented

**`Reconnaissance_Tool`**
- Async TCP port scanner with banner capture (`Port_Scanner` / `_port_scanner`)
- `python-nmap` wrapper with version detection (`Nmap_port_scanning`)
- Socket-based port scanner + banner grabber, `ThreadPoolExecutor`-backed (`Socket_Port_Scanner`, `Socket_Banner_Grabber`)
- Generic HTTP fetch (`fetch_info`)

**`Vulnerability_Assessment_Tool`** *(renamed from `Vulnerability_Assesment_Tool`, alias kept for compatibility)*
- Security header analyzer (`Header_Analyzer`) — checks HSTS, X-Frame-Options, CSP, X-Content-Type-Options by default
- CVE lookup against the NVD API, reusing the shared `aiohttp` session (`CVE_Lookup`)
- SSL/TLS certificate checker — issuer, subject, expiry, warns under 30 days (`SSL_TSL_CHECKER`)

**`Network_tool`**
- OWASP ZAP daemon lifecycle management (starts one if needed, reuses an already-running one, cleans up on exit)
- ZAP spider → active scan → alert collection (`ZAP_Scanner`) — spidered pages are also fed into the OSINT email/metadata tools
- ARP sweeping of a local subnet (`ARP_Scanner`) and a bounded LAN → ZAP pipeline (`LAN_Recon_Spell` / `LAN_Scan`)

**`OSINT_tool`**
- Subdomain scanner driven by `self.wordlist` (`Subdomain_Scanner` / `_word_scan`)
- Passive email harvester over already-fetched page content (`Email_Harvester`)
- Document metadata extractor for linked PDF/DOCX files, size- and count-bounded (`Metadata_Extractor`)

**`Exploitation_tool`**
- Builds a `k6` load-test config and script for a target and persists it — **deliberately never shells out to `k6`**, left for a future UI to review and trigger (`build_k6_config`, `Exploit_Spell`)

**`Post_Exploitation_tool`**
- Still a stub — prints a "ready for deployment" message, reserved for future work

**`AI_Suggestions`**
- Sends aggregated findings to a Groq-hosted LLM and requests a structured JSON triage report (risk-ranked findings, summary, next steps)
- Explicit prompt-injection guard (findings are framed as untrusted data), client-side rate limiting, and per-field truncation before the request is built
- Implemented (`AI_Suggest_Spell`) but not yet called from `Cast_Spell`

**Persistence (`DatabaseTheWidzard`)**
- PostgreSQL via `asyncpg`, fully async, with a small additive schema: config lists (`wizard_wordlist`, `wizard_security_headers`, `wizard_urls`) and findings (`wizard_emails`, `wizard_metadata`, `wizard_k6_configs`, `wizard_zap_alerts`, `wizard_arp_hosts`)
- Table/column names always come from a fixed, hardcoded whitelist — never from caller input

---

## Output tags

All output goes to stdout with consistent prefixes for easy parsing:

`[TARGET]` `[STATUS]` `[BODY]` `[RESOLVED]` `[PORT]` `[BANNER]` `[OUTPUT-{port}]` `[OUTPUT-SOCKET]` `[FOUND]` `[MISSING]` `[CVE]` `[SSL]` `[WARNING]` `[ZAP]` `[ARP]` `[LAN]` `[EMAIL]` `[METADATA]` `[K6]` `[AI ...]` `[DB]` `[ERROR]` `[CVE ERROR]` `[SSL ERROR]` `[ZAP PARSE ERROR]` `[METADATA ERROR]` `[DB ERROR]` `[DB CONFIG ERROR]` `[DEBUG]`

---

## Installation

```bash
git clone https://github.com/MarcoPannocchia/CybeDev-TheWizard.git
cd CybeDev-TheWizard

# system dependencies
sudo apt install nmap arp-scan
# also install OWASP ZAP separately and point Network_tool.zap_path at zap.sh
# if it's not at the default /usr/share/zaproxy/zap.sh

python -m venv venv
source venv/bin/activate   # on Windows: venv\Scripts\activate

pip install aiohttp python-nmap asyncpg pypdf python-docx
```

`socket`, `asyncio`, `ssl`, `subprocess`, `atexit`, `re`, `json`, `datetime`, `urllib.parse`, `concurrent.futures` are part of the standard library — no extra install needed. Some features (nmap `-sV`, ARP scanning) may require root/admin privileges.

### PostgreSQL

A reachable PostgreSQL instance is **required** — `Cast_Spell` fails at startup without one. Set at minimum:

```bash
export WIZARD_DB_NAME=thewizard
export WIZARD_DB_USER=thewizard
export WIZARD_DB_PASSWORD=change-me
# optional: WIZARD_DB_HOST, WIZARD_DB_PORT, WIZARD_DB_SSL, WIZARD_DB_POOL_MIN/MAX, WIZARD_DB_TIMEOUT
```

The schema (config tables + findings tables) is created automatically on first connect.

### Optional: AI triage

```bash
export GROQ_API_KEY=gsk_...
```

---

## Usage

Targets, subdomain wordlist, and headers now live in PostgreSQL rather than the source — seed them via SQL or interactively at runtime (these are coroutines as of the current version):

```python
wizard = TheWizard()
await wizard._load_lists()   # or run Cast_Spell() first — required before add_*/LAN_Scan

await wizard.add_word()      # adds a subdomain word to check (DB + memory)
await wizard.add_header()    # adds a security header to check (DB + memory)
await wizard.add_url()       # adds a target URL (DB + memory)

asyncio.run(wizard.Cast_Spell())
```

```bash
python TheWizard_v082.py
```

This runs the full flow for every URL in `urls`: network info + ZAP scan, OSINT (subdomains/emails/document metadata), DNS resolution, 3-layer port scan, header/CVE/SSL analysis, k6 config build, post-exploitation stub — persisting findings to PostgreSQL along the way.

For a standalone ARP/LAN sweep outside the URL-driven loop:

```python
wizard = TheWizard()
asyncio.run(wizard.LAN_Scan("192.168.1.0/24"))
```

---

## Known issues

- Naming inconsistency across a few module classes (`Exploitation_tool`, `Network_tool`, etc. use a lowercase `t`) — cosmetic, no functional impact
- No rate-limit handling yet for the NVD CVE API — long banner lists can get throttled (unlike the client-side rate limiter already in place for `AI_Suggestions`)
- `Post_Exploitation_tool` is still a placeholder with no real logic
- `AI_Suggest_Spell` is implemented but not yet called anywhere in `Cast_Spell`
- `build_k6_config`'s output is persisted but nothing executes it yet — that's intentional until a UI layer exists to trigger it explicitly
- No automated tests yet for any module

---

## Disclaimer

This tool is developed for educational and cybersecurity research purposes. The author takes no responsibility for improper or unauthorized use. Use it **only** on systems you have explicit authorization to test — this applies with extra force to the OWASP ZAP active scan and the ARP/LAN sweep, both of which can reach hosts beyond a single target URL.

---

## Author

**Marco Pannocchia**

[![GitHub](https://img.shields.io/badge/GitHub-MarcoPannocchia-181717?logo=github&logoColor=white)](https://github.com/MarcoPannocchia)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Marco%20Pannocchia-0A66C2?logo=linkedin&logoColor=white)](https://www.linkedin.com/in/marco-pannocchia-191924433)
[![Instagram](https://img.shields.io/badge/Instagram-marco__pannocchia-E4405F?logo=instagram&logoColor=white)](https://www.instagram.com/marco_pannocchia)

<div align="center">
<sub>Built with 🐍 Python, asyncio and a lot of curiosity for cybersecurity.</sub>
</div>

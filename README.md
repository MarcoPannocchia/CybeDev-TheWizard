<div align="center">

<!-- 🖼️ Replace with the generated banner (banner_thewizard.png) -->
<img src="./docs/assets/TheWizard_banner.png" alt="TheWizard banner" width="100%">

# 🧙‍♂️ TheWizard

**Educational async Python security-assessment toolkit — CS50x final project**

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![asyncio](https://img.shields.io/badge/async-aiohttp%20%2F%20asyncio-8A2BE2)]()
[![nmap](https://img.shields.io/badge/scanning-python--nmap-orange)]()
[![Status](https://img.shields.io/badge/status-v0.7.0%20%E2%80%94%20in%20development-yellow)]()
[![License](https://img.shields.io/badge/license-see%20LICENSE.md-lightgrey)](./LICENSE.md)

</div>

---

## 📖 Table of Contents

- [About TheWizard](#about-thewizard)
- [Architecture](#architecture)
- [What's implemented (v0.7.0)](#whats-implemented-v070)
- [Output tags](#output-tags)
- [Installation](#installation)
- [Usage](#usage)
- [Known issues](#known-issues)
- [Roadmap](#roadmap)
- [Disclaimer](#disclaimer)
- [Author](#author)

---

## About TheWizard

**TheWizard** (internally `TheWidzard`) is an educational, fully asynchronous Python toolkit for security reconnaissance and vulnerability assessment, built as a CS50x final project. It combines `asyncio`/`aiohttp` for network I/O with `python-nmap` and raw sockets for port scanning and service fingerprinting.

> ⚠️ Built exclusively for authorized testing in controlled environments (lab environments, permitted bug bounty, or your own assets).

---

## Architecture

TheWizard follows a **Facade pattern**: one orchestrator class inherits from several independent tool classes, each responsible for one phase of a security assessment. The single entry point is `Cast_Spell()`, which loops over every target in `self.urls` and calls each module's own orchestration method (its "**Spell**"):

```python
class TheWizard(Reconnaissance_Tool,
                Vulnerability_Assessment_Tool,
                Exploitation_tool, Post_Exploitation_tool,
                Network_tool, OSINT_tool):
    ...
```

| Module | Spell | Role |
|---|---|---|
| `Reconnaissance_Tool` | `Recon_Spell(ip)` | port scanning (3 implementations), banner grabbing |
| `Vulnerability_Assessment_Tool` | `Vuln_Asses_Spell(session, url)` | header analysis, CVE lookup, SSL/TLS check |
| `Network_tool` | `Network_Spell(session, url)` | basic HTTP info gathering |
| `OSINT_tool` | `OSINT_Spell(session, url)` | subdomain enumeration |
| `Exploitation_tool` | `Exploit_Spell()` | placeholder — reserved for future modules |
| `Post_Exploitation_tool` | `Post_Exploit_Spell()` | placeholder — reserved for future modules |

Shared state (`wordlist`, `banners`, `security_headers`, `urls`) lives on the main class and is used across modules via `self`. It can be extended at runtime through `add_word()`, `add_header()`, `add_url()`.

Blocking calls (`nmap`, raw `socket`) are never run directly inside an `async def`: `Nmap_port_scanning` is offloaded via `loop.run_in_executor`, and the socket-based scanner/banner grabber via `asyncio.to_thread`, so the event loop never stalls.

---

## What's implemented (v0.7.0)

**`Reconnaissance_Tool`**
- Async TCP port scanner with banner capture (`Port_Scanner` / `_port_scanner`)
- `python-nmap` wrapper with version detection (`Nmap_port_scanning`)
- Socket-based port scanner + banner grabber, `ThreadPoolExecutor`-backed (`Socket_Port_Scanner`, `Socket_Banner_Grabber`)
- Generic HTTP fetch (`fetch_info`)
- Subdomain scanner driven by `self.wordlist` (`Subdomain_Scanner` / `_word_scan`)

**`Vulnerability_Assessment_Tool`** *(renamed from `Vulnerability_Assesment_Tool`, alias kept for compatibility)*
- Security header analyzer (`Header_Analyzer`) — checks HSTS, X-Frame-Options, CSP, X-Content-Type-Options by default
- CVE lookup against the NVD API, reusing the shared `aiohttp` session (`CVE_Lookup`)
- SSL/TLS certificate checker — issuer, subject, expiry, warns under 30 days (`SSL_TSL_CHECKER`)

**`Network_tool` / `OSINT_tool`**
- Thin wrappers that call into `Reconnaissance_Tool` under a clearer pentest-phase naming

**`Exploitation_tool` / `Post_Exploitation_tool`**
- Still stubs — print a "ready for deployment" message, reserved for future work

---

## Output tags

All output goes to stdout with consistent prefixes for easy parsing:

`[TARGET]` `[STATUS]` `[BODY]` `[RESOLVED]` `[PORT]` `[BANNER]` `[OUTPUT-{port}]` `[OUTPUT-SOCKET]` `[FOUND]` `[MISSING]` `[CVE]` `[SSL]` `[WARNING]` `[ERROR]` `[CVE ERROR]` `[SSL ERROR]` `[DEBUG]`

---

## Installation

```bash
git clone https://github.com/MarcoPannocchia/CybeDev-TheWizard.git
cd CybeDev-TheWizard

# system dependency
sudo apt install nmap

python -m venv venv
source venv/bin/activate   # on Windows: venv\Scripts\activate

pip install aiohttp python-nmap
```

`socket`, `asyncio`, `ssl`, `datetime`, `urllib.parse`, `concurrent.futures` are part of the standard library — no extra install needed. Some nmap features may require root/admin privileges.

---

## Usage

Targets, subdomain wordlist and headers are configured as class attributes on the main class (edit the source, or add them interactively at runtime):

```python
wizard = TheWizard()
wizard.add_word()      # adds a subdomain word to check
wizard.add_header()    # adds a security header to check
wizard.add_url()       # adds a target URL

asyncio.run(wizard.Cast_Spell())
```

```bash
python TheWizard_v070.py
```

This runs the full flow — network info, OSINT/subdomain scan, DNS resolution, 3-layer port scan, header/CVE/SSL analysis — for every URL in `urls`.

---

## Known issues

- Naming inconsistency across a few module classes (`Exploitation_tool`, `Network_tool`, etc. use a lowercase `t`) — cosmetic, no functional impact
- No rate-limit handling yet for the NVD CVE API — long banner lists can get throttled
- `Exploitation_tool` / `Post_Exploitation_tool` are placeholders with no real logic

---

## Roadmap

- [ ] Persist results with `sqlite3` (targets, ports, banners, CVEs, headers, subdomains, SSL checks)
- [ ] Minimal UI (TUI or lightweight Flask/FastAPI web app) to launch scans and browse saved results
- [ ] Implement `Exploitation_tool` / `Post_Exploitation_tool`
- [ ] NVD API rate-limit handling

---

## Disclaimer

This tool is developed for educational and cybersecurity research purposes. The author takes no responsibility for improper or unauthorized use. Use it **only** on systems you have explicit authorization to test.

---

## Author

**Marco Pannocchia**

[![GitHub](https://img.shields.io/badge/GitHub-MarcoPannocchia-181717?logo=github&logoColor=white)](https://github.com/MarcoPannocchia)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Marco%20Pannocchia-0A66C2?logo=linkedin&logoColor=white)](https://www.linkedin.com/in/marco-pannocchia-191924433)
[![Instagram](https://img.shields.io/badge/Instagram-marco__pannocchia-E4405F?logo=instagram&logoColor=white)](https://www.instagram.com/marco_pannocchia)

<div align="center">
<sub>Built with 🐍 Python, asyncio and a lot of curiosity for cybersecurity.</sub>
</div>

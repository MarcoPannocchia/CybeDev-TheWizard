# TheWizard — Documentation

> **Status:** Work in progress — active development. Current source: **v0.8.2**.

## Overview

TheWizard is a Python-based cybersecurity toolkit developed under the **CybeDev** brand.
It follows a **Facade architecture** — a central class (`TheWizard`) inherits from multiple specialized tool classes, each covering a specific cybersecurity domain.

Built with `aiohttp`/`asyncio` for asynchronous HTTP and network I/O, and, as of v0.8.2, `asyncpg` for fully-async Postgres persistence.

---

## Architecture (ASCII)

```
TheWizard (Facade)
    |
    |—— Reconnaissance_Tool
    |       |—— fetch_info
    |       |—— Port_Scanner / _port_scanner
    |       |—— Nmap_port_scanning
    |       |—— Socket_Port_Scanner / Socket_Banner_Grabber
    |       |—— Recon_Spell
    |
    |—— Vulnerability_Assessment_Tool
    |       |—— Header_Analyzer
    |       |—— CVE_Lookup (NVD API)
    |       |—— SSL_TSL_CHECKER
    |       |—— Vuln_Asses_Spell
    |
    |—— Exploitation_tool
    |       |—— build_k6_config          (builds, never runs, a k6 load-test)
    |       |—— Exploit_Spell(target)
    |
    |—— Post_Exploitation_tool           [placeholder]
    |
    |—— Network_tool                     (own file: Network_tool_v082.py)
    |       |—— ZAP daemon start/reuse, spider, active scan
    |       |—— ARP_Scanner / LAN_Recon_Spell
    |
    |—— OSINT_tool
    |       |—— Subdomain_Scanner / _word_scan / insert_word
    |       |—— Email_Harvester
    |       |—— Metadata_Extractor (pdf/docx)
    |
    |—— AI_Suggestions                   (not yet wired into Cast_Spell)
            |—— AI_Suggest_Spell (Groq triage report)

DatabaseTheWidzard (db module, not a mixin)
    |—— init_pool / close_pool (asyncpg)
    |—— config lists: wordlist, security_headers, urls (Postgres-backed)
    |—— findings: emails, metadata, k6_configs, zap_alerts, arp_hosts
```

---

## Index

| File | Description |
|------|-------------|
| [architecture/facade.md](architecture/facade.md) | Facade pattern — class hierarchy and design decisions |
| [architecture/architecture.md](architecture/architecture.md) | Shared state, module list, spells |
| [architecture/async.md](architecture/async.md) | Asyncio, aiohttp, asyncpg — concurrency model |
| [architecture/setup_and_usage.md](architecture/setup_and_usage.md) | Requirements, env vars, installation |
| [modules/reconnaissance.md](modules/reconnaissance.md) | `Reconnaissance_Tool` — all recon methods |
| [modules/vulnerability.md](modules/vulnerability.md) | `Vulnerability_Assessment_Tool` — headers, CVE, SSL/TLS |
| [modules/network.md](modules/network.md) | `Network_tool` — ZAP scanning, ARP/LAN sweep |
| [modules/osint.md](modules/osint.md) | `OSINT_tool` — subdomains, emails, document metadata |
| [modules/exploitation_and_post_exploitation.md](modules/exploitation_and_post_exploitation.md) | Exploitation (k6 config builder), Post-Exploitation (stub) |
| [modules/ai_suggestions.md](modules/ai_suggestions.md) | `AI_Suggestions` — Groq-backed triage report |
| [modules/database.md](modules/database.md) | Postgres schema, pool management, config/findings tables |
| [TheWizard/TheWizard.md](TheWizard/TheWizard.md) | `TheWizard` class — lists, classmethods, entry point |
| [commands/run.md](commands/run.md) | How to run TheWizard |
| [troubleshooting/common-errors.md](troubleshooting/common-errors.md) | Common errors and fixes |
| [roadmap.md](roadmap.md) | Upcoming work |
| [CHANGELOG.md](CHANGELOG.md) | Change log |

---

## Tags legend

- `#wip` — work in progress
- `#verified` — tested and working
- `#todo` — planned but not done
- `#open` — unresolved issue

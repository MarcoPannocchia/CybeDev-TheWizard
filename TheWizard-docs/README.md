# TheWizard — Documentation

> **Status:** Work in progress — active development.

## Overview

TheWizard is a Python-based cybersecurity toolkit developed under the **CybeDev** brand.
It follows a **Facade architecture** — a central class (`TheWizard`) inherits from multiple specialized tool classes, each covering a specific cybersecurity domain.

Built with `aiohttp` and `asyncio` for asynchronous HTTP operations.

---

## Architecture (ASCII)

```
TheWizard (Facade)
    |
    |—— Reconnaissance_Tool
    |       |—— fetch_info
    |       |—— Port_Scanner / _port_scanner
    |       |—— Subdomain_Scanner / _word_scan / insert_word
    |       |—— Nmap_port_scanning
    |
    |—— Vulnerability_Assessment_Tool
    |       |—— Header_Analyzer
    |
    |—— Exploitation_Tool           [placeholder]
    |—— Post_Exploitation_Tool      [placeholder]
    |—— Network_Tool                [placeholder]
    |—— OSINT_Tool                  [placeholder]
```

---

## Index

| File | Description |
|------|-------------|
| [architecture/facade.md](architecture/facade.md) | Facade pattern — class hierarchy and design decisions |
| [architecture/async.md](architecture/async.md) | Asyncio and aiohttp — concurrency model |
| [modules/reconnaissance.md](modules/reconnaissance.md) | Reconnaissance_Tool — all recon methods |
| [modules/vulnerability.md](modules/vulnerability.md) | Vulnerability_Assessment_Tool — header analyzer |
| [modules/placeholders.md](modules/placeholders.md) | Exploitation, Post-Exploitation, Network, OSINT |
| [modules/thewizard.md](TheWizard.md) | TheWizard class — lists, classmethods, entry point |
| [commands/run.md](commands/run.md) | How to run TheWizard |
| [troubleshooting/common-errors.md](troubleshooting/common-errors.md) | Common errors and fixes |
| [CHANGELOG.md](CHANGELOG.md) | Change log |

---

## Tags legend

- `#wip` — work in progress
- `#verified` — tested and working
- `#todo` — planned but not done
- `#open` — unresolved issue

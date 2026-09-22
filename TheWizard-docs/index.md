# TheWizard — Documentation

Educational async Python security-assessment toolkit, CS50X final project.
Documentation split by class, meant to be quickly consultable by both a human and an AI.

> ⚠️ **Ethical use**: intended for authorized testing only (lab environments, bug bounty with permission, your own assets). This applies with extra force from v0.8.2 onward: `Network_tool` can now launch a real OWASP ZAP active scan, and `LAN_Scan`/`ARP_Scanner` can sweep and probe hosts on a local subnet that were never explicitly listed as a target.

This documentation describes **v0.8.2**, the current/latest version of the codebase (files suffixed `_v082`). Where relevant, differences from the previous documented snapshot (**Version 7**, aka `_v080`) are called out inline — see [CHANGELOG.md](CHANGELOG.md) for the full history.

## Index

| File | Contents |
| --- | --- |
| [architecture/architecture.md](architecture/architecture.md) | Facade pattern, class hierarchy, shared state |
| [architecture/facade.md](architecture/facade.md) | Facade pattern — design decisions, naming |
| [architecture/async.md](architecture/async.md) | Asyncio / aiohttp / asyncpg — concurrency model |
| [architecture/setup_and_usage.md](architecture/setup_and_usage.md) | Requirements, installation, environment variables, execution |
| [modules/reconnaissance.md](modules/reconnaissance.md) | `Reconnaissance_Tool` — port scanning, subdomain scanning, HTTP fetch |
| [modules/vulnerability.md](modules/vulnerability.md) | `Vulnerability_Assessment_Tool` — header analyzer, CVE lookup, SSL/TLS checker |
| [modules/network.md](modules/network.md) | `Network_tool` — OWASP ZAP daemon/spider/active scan, ARP LAN sweep |
| [modules/osint.md](modules/osint.md) | `OSINT_tool` — subdomain scan, email harvester, document metadata extractor |
| [modules/exploitation_and_post_exploitation.md](modules/exploitation_and_post_exploitation.md) | `Exploitation_tool` (k6 load-test config builder), `Post_Exploitation_tool` (stub) |
| [modules/ai_suggestions.md](modules/ai_suggestions.md) | `AI_Suggestions` — Groq-backed triage report (not yet wired into `Cast_Spell`) |
| [modules/database.md](modules/database.md) | `DatabaseTheWidzard` — Postgres/asyncpg schema, pool, config lists, findings |
| [TheWizard/TheWizard.md](TheWizard/TheWizard.md) | `TheWizard` — main facade class, orchestration, CLI/DB helpers |
| [commands/run.md](commands/run.md) | How to run TheWizard |
| [troubleshooting/common-errors.md](troubleshooting/common-errors.md) | Common errors and fixes |
| [roadmap.md](roadmap.md) | Upcoming work |
| [CHANGELOG.md](CHANGELOG.md) | Version history, function by function |

## A note on the source files

Several snapshots were shared over time, each in its own `TheWizard Versions/Version X.Y.Z/` folder. This documentation reflects **v0.8.2**, the most recent one, and treats everything before it as history — see [CHANGELOG.md](CHANGELOG.md).

As of v0.8.2 the codebase is split across four files instead of one:

- `TheWizard_v082.py` — the facade class (`TheWizard`) and its entry point (`Cast_Spell`)
- `ModulesTheWidzard_v082.py` — `Reconnaissance_Tool`, `Vulnerability_Assessment_Tool`, `Exploitation_tool`, `Post_Exploitation_tool`, `OSINT_tool`, `AI_Suggestions`
- `Network_tool_v082.py` — `Network_tool`, now its own file (ZAP + ARP), imported explicitly to supersede the wildcard-imported stub of the same name
- `DatabaseTheWidzard_v082.py` — the Postgres/asyncpg persistence layer, imported as `db` by the three files above

> **Previous gap now closed**: earlier documentation passes (Version 7 / v0.8.0) repeatedly noted that the facade class itself hadn't been received, only the modules. v0.8.2 includes the full facade, so [TheWizard/TheWizard.md](TheWizard/TheWizard.md) is now verified against real source rather than describing a stale, previous-version guess.

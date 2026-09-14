# TheWizard — Documentation

Educational async Python security-assessment toolkit, CS50X final project.
Documentation split by class, meant to be quickly consultable by both a human and an AI.

> ⚠️ **Ethical use**: intended for authorized testing only (lab environments, bug bounty with permission, your own assets).

This documentation describes **Version 7**, the current/latest version of the codebase. Where relevant, differences from the previous version are called out inline, without assigning version numbers to older snapshots — see [CHANGELOG.md](CHANGELOG.md) for the full history.

## Index

| File                                                                           | Contents                                                                       |
| ------------------------------------------------------------------------------ | ------------------------------------------------------------------------------ |
| [architecture.md](architecture.md)                                             | Facade pattern, class hierarchy, shared state                                  |
| [reconnaissance.md](reconnaissance.md)                                         | `Reconnaissance_Tool` — port scanning, subdomain scanning, HTTP fetch          |
| [vulnerability.md](vulnerability.md)                                           | `Vulnerability_Assessment_Tool` — header analyzer, CVE lookup, SSL/TLS checker |
| [exploitation_and_post_exploitation.md](exploitation_and_post_exploitation.md) | `Exploitation_tool`, `Post_Exploitation_tool`                                  |
| [network_and_osint.md](network_and_osint.md)                                   | `Network_tool`, `OSINT_tool`                                                   |
| [TheWizard.md](TheWizard.md)                                                   | `TheWidzard` — main class, orchestration, CLI helpers                          |
| [changelog.md](changelog.md)                                                   | Version history, function by function                                          |
| [setup_and_usage.md](setup_and_usage.md)                                       | Requirements, installation, execution                                          |
| [roadmap.md](roadmap.md)                                                       | Upcoming work (sqlite3, UI, CS50X demo)                                        |
|                                                                                |                                                                                |

## A note on the source files

All source files shared so far are named `TheWidzard.py` (except one renamed `TheWidzard-v6.py`). Several snapshots were shared over time; this documentation reflects **Version 7**, the most recent one, and treats everything before it simply as "the previous version" for context, without assigning it a specific number.

> **Version 7 also has a gap**: the last code received only includes the modules (`Reconnaissance_Tool`, `Vulnerability_Assessment_Tool`, `Exploitation_tool`, `Post_Exploitation_tool`, `Network_tool`, `OSINT_tool`) — not the `TheWidzard` facade class itself (`wordlist`/`banners`/`security_headers`/`urls`, `Cast_Spell`). `TheWizard.md` still describes the facade as it was in the previous version; it needs a re-check once the updated facade arrives.

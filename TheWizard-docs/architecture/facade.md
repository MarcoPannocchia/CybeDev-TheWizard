# Architecture — Facade Pattern

#verified

## Overview

TheWizard uses a **Facade** design pattern.
Each cybersecurity domain is implemented as an independent class. `TheWizard` inherits from all of them and acts as the single operational interface.

> [!success] Facade naming inconsistency — resolved in v0.8.2
> Earlier passes flagged the facade class itself as misspelled in source (`TheWidzard`, missing a "d" from "Wizard"). The v0.8.2 facade file (`TheWizard_v082.py`) defines `class TheWizard(...)` — the "consistent" name is now what's actually in source. The table below is kept for history/context, with the facade row updated.

| Class (actual, in source) | "Consistent" form | Domain | Status |
|---|---|---|---|
| `Reconnaissance_Tool` | — (already consistent) | Recon — subdomain scan, port scan, fetch info | #verified |
| `Vulnerability_Assessment_Tool` | — (fixed in Version 7; `Vulnerability_Assesment_Tool` kept as a compatibility alias) | Vuln assessment — headers, CVE lookup, SSL/TLS | #verified |
| `Exploitation_tool` | `Exploitation_Tool` (lowercase "t") | k6 load-test config builder (non-executing) | #wip |
| `Post_Exploitation_tool` | `Post_Exploitation_Tool` (lowercase "t") | Post exploitation | #todo |
| `Network_tool` | `Network_Tool` (lowercase "t") | OWASP ZAP scanning, ARP/LAN sweep | #verified |
| `OSINT_tool` | `OSINT_Tool` (lowercase "t") | Subdomains, email harvesting, document metadata | #verified |
| `AI_Suggestions` | — (already consistent) | Groq-backed triage report | #wip — implemented but not wired into `Cast_Spell` |
| `TheWizard` | — **now consistent as of v0.8.2** (was `TheWidzard`) | Facade — inherits all of the above | #verified |

> The lowercase-`t` inconsistency in `Exploitation_tool`/`Post_Exploitation_tool`/`Network_tool`/`OSINT_tool` (vs. capital-`T` `Reconnaissance_Tool`/`Vulnerability_Assessment_Tool`) is still present in v0.8.2 source — only the facade's own name was fixed, not the mixin class-name casing across the hierarchy.

> See also: [[TheWizard]]

---

## Inheritance declaration (v0.8.2)

```python
class TheWizard(Reconnaissance_Tool,
                Vulnerability_Assesment_Tool,
                Exploitation_tool, Post_Exploitation_tool,
                Network_tool, OSINT_tool, AI_Suggestions):
    ...
```

`Network_tool` here is the real implementation imported from `Network_tool_v082.py`, not the wildcard-imported placeholder of the same name that `ModulesTheWidzard_v082.py` also defines — the facade file imports it explicitly *after* the wildcard import specifically to override it:

```python
from ModulesTheWidzard_v082 import *
from Network_tool_v082 import Network_tool  # supersedes the wildcard-imported stub of the same name
```

---

## Design decisions

- **Why multiple inheritance over composition?**
  Each domain class is independent and has no overlapping method names. Multiple inheritance keeps the code compact and avoids unnecessary wrapper methods.

- **Why centralize lists in TheWizard?**
  `wordlist`, `security_headers`, `urls`, and `banners` are shared resources used across multiple tools. Keeping them in the Facade avoids duplication and makes `@classmethod` mutations global. As of v0.8.2 the first three are also the ones persisted to Postgres — see [database.md](../modules/database.md).

- **Private methods prefixed with `_`**
  Methods not meant to be called directly by `TheWizard` are prefixed with `_` (e.g. `_word_scan`, `_port_scanner`, `_load_lists`). This is a Python convention for internal implementation details.

- **Why does `Network_tool` live in its own file now?**
  It grew substantially in v0.8.2 (ZAP daemon lifecycle, spider/active-scan orchestration, ARP sweeping) — splitting it out keeps `ModulesTheWidzard_v082.py` from becoming a single, ever-growing file. The explicit re-import in the facade (see above) is the mechanism used to keep the wildcard-imported placeholder from shadowing it.

- **Why import the DB layer (`db`) into every module file instead of passing a pool explicitly?**
  `Network_tool_v082.py`, `ModulesTheWidzard_v082.py`, and `TheWizard_v082.py` all `import DatabaseTheWidzard_v082 as db` and reach the shared pool via `getattr(self, "db_pool", None)` rather than a constructor argument — consistent with the facade's pattern of centralizing shared state as class attributes rather than passing it through `__init__`.

---

## Planned evolution

- [x] Add SQLite/DB storage for scan results — done in v0.8.2, but with Postgres/asyncpg instead of SQLite (see [database.md](../modules/database.md) and [roadmap.md](../roadmap.md) for why)
- [ ] Add a UI (`Textual`/`Rich` TUI, or a `Flask`/`FastAPI` web app) to drive scans, review k6 configs, and trigger `AI_Suggest_Spell`
- [ ] Wire `AI_Suggest_Spell` into `Cast_Spell` (or into the future UI) so triage reports are actually generated during a run
- [ ] Consider a rename pass to fix the remaining lowercase-`t` casing inconsistencies in the table above
- [ ] Automated tests for the new v0.8.2 modules (`Network_tool`, `OSINT_tool`'s new methods, `Exploitation_tool`, `AI_Suggestions`, the DB layer)

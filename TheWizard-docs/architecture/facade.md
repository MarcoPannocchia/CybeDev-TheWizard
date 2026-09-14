# Architecture — Facade Pattern

#verified

## Overview

TheWidzard uses a **Facade** design pattern.
Each cybersecurity domain is implemented as an independent class. `TheWidzard` inherits from all of them and acts as the single operational interface.

> [!warning] Naming inconsistencies across the hierarchy — #known-issue
> The actual source has inconsistent capitalization/spelling across these classes. Table below
> reflects the real names; "as-if-consistent" is what each *should* probably be if a cleanup
> pass happens.

| Class (actual, in source) | "Consistent" form | Domain | Status |
|---|---|---|---|
| `Reconnaissance_Tool` | — (already consistent) | Recon — subdomain scan, port scan, fetch info | #wip |
| `Vulnerability_Assesment_Tool` | `Vulnerability_Assessment_Tool` (missing an "s") | Vuln assessment — headers, CVE lookup | #wip |
| `Exploitation_tool` | `Exploitation_Tool` (lowercase "t") | Exploitation | #todo |
| `Post_Exploitation_tool` | `Post_Exploitation_Tool` (lowercase "t") | Post exploitation | #todo |
| `Network_tool` | `Network_Tool` (lowercase "t") | Networking | #todo |
| `OSINT_tool` | `OSINT_Tool` (lowercase "t") | OSINT | #todo |
| `TheWidzard` | `TheWizard` (missing a "d") | Facade — inherits all of the above | #wip |

> See also: [[TheWidzard]]

---

## Inheritance declaration

```python
class TheWidzard(Reconnaissance_Tool,
                Vulnerability_Assesment_Tool,
                Exploitation_tool,
                Post_Exploitation_tool,
                Network_tool,
                OSINT_tool):
    ...
```

---

## Design decisions

- **Why multiple inheritance over composition?**
  Each domain class is independent and has no overlapping method names. Multiple inheritance keeps the code compact and avoids unnecessary wrapper methods.

- **Why centralize lists in TheWidzard?**
  `wordlist`, `security_headers`, `urls`, and `banners` are shared resources used across multiple tools. Keeping them in the Facade avoids duplication and makes `@classmethod` mutations global.

- **Private methods prefixed with `_`**
  Methods not meant to be called directly by `TheWidzard` are prefixed with `_` (e.g. `_word_scan`, `_port_scanner`). This is a Python convention for internal implementation details.

---

## Planned evolution

- [ ] Add `main()` and `theWizard()` entry point in `TheWidzard` — `Cast_Spell` currently fills this role, see [[TheWidzard]]
- [ ] Add SQLite storage for scan results — see [[CHANGELOG.md]]
- [ ] Add Tkinter GUI (`TheWidzardGUI`) as separate class
- [ ] Consider a rename pass to fix the casing/spelling inconsistencies in the table above

# Module — Placeholders

#todo

## Overview

This page originally documented four classes that were pure stubs. As of v0.8.2, **three of the four have been implemented** — only `Post_Exploitation_tool` remains a placeholder. Kept as a short pointer page rather than deleted, since "which modules are still stubs" is a question worth answering quickly.

| Class | Status as of v0.8.2 | Docs |
|---|---|---|
| `Exploitation_tool` | ✅ implemented (k6 load-test config builder, never executes) | [exploitation_and_post_exploitation.md](exploitation_and_post_exploitation.md) |
| `Post_Exploitation_tool` | ⏳ **still a stub** | [exploitation_and_post_exploitation.md](exploitation_and_post_exploitation.md) |
| `Network_tool` | ✅ implemented (OWASP ZAP scanning, ARP/LAN sweep) | [network.md](network.md) |
| `OSINT_tool` | ✅ implemented (subdomains, email harvester, document metadata) | [osint.md](osint.md) |

> [!warning] Class name casing — still a `#known-issue` in v0.8.2
> These classes are spelled with a lowercase `t` in "tool" in the actual source
> (`Exploitation_tool`, not `Exploitation_Tool`), unlike `Reconnaissance_Tool` and
> `Vulnerability_Assessment_Tool`, which use a capital `T`. See [[facade.md]] for the full naming inconsistency list — this part of it is unchanged since the facade class's own name (`TheWidzard` → `TheWizard`) was fixed.

---

## `Post_Exploitation_tool` — the one remaining stub

```python
class Post_Exploitation_tool():
    async def Post_Exploit_Spell(self):
        print("\n[*] POST-EXPLOITATION TOOLS")
        print("[INFO] Post-exploitation module ready for deployment")
```

**Planned tools:**
- Password cracker
- Hash analyzer

See [exploitation_and_post_exploitation.md](exploitation_and_post_exploitation.md) for the full picture, including the now-implemented `Exploitation_tool`.

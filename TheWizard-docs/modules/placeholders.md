# Module — Placeholders

#todo

## Overview

The following tool classes are defined in the codebase but not yet implemented.
They inherit into `TheWidzard` and reserve their domain in the architecture.

> [!warning] Class name casing — #known-issue
> These classes are spelled with a lowercase `t` in "tool" in the actual source
> (`Exploitation_tool`, not `Exploitation_Tool`), unlike `Reconnaissance_Tool` and
> `Vulnerability_Assesment_Tool`, which use a capital `T`. Corrected below to match the code.
> See [[facade.md]] for the full naming inconsistency list.

> See also: [[facade.md]]

---

## Exploitation_tool

```python
class Exploitation_tool():
    def Exploit_Spell(self):
        pass
```

**Planned tools:**
- Fuzzer
- Brute forcer
- SQL injection tester

> [!warning] Legal notice
> Exploitation tools must only be used on systems with explicit written authorization.

---

## Post_Exploitation_tool

```python
class Post_Exploitation_tool():
    def Post_Exploit_Spell(self):
        pass
```

**Planned tools:**
- Password cracker
- Hash analyzer

---

## Network_tool

```python
class Network_tool():
    def Network_Spell(self):
        pass
```

**Planned tools:**
- Packet sniffer
- ARP scanner
- Traceroute

---

## OSINT_tool

```python
class OSINT_tool():
    def OSINT_Spell(self):
        pass
```

**Planned tools:**
- Email harvester
- Metadata extractor
- WHOIS lookup

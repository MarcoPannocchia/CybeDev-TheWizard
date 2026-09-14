# `TheWizard`

[← Index](index.md)


> ⚠️ **Note**: the last code received (Version 7) only contains the modules (`Reconnaissance_Tool`, `Vulnerability_Assessment_Tool`, `Exploitation_tool`, `Post_Exploitation_tool`, `Network_tool`, `OSINT_tool`) — not the `TheWizard` facade class with `wordlist`/`banners`/`security_headers`/`urls` and `Cast_Spell`. This page still describes the facade as it was in the previous version. If `Cast_Spell` or the shared attributes have changed since, this page needs updating once the full file arrives.

Main class (facade). Inherits from all modules — see [architecture.md](architecture.md) — and defines the shared state plus the `Cast_Spell` entry point.

```python
class TheWidzard(Reconnaissance_Tool,
                Vulnerability_Assessment_Tool,
                Exploitation_tool, Post_Exploitation_tool,
                Network_tool, OSINT_tool):
```

---

## Class attributes

| Attribute | Default | Description |
|---|---|---|
| `wordlist` | `["mail", "api", "dev", "admin", "test", "staging", "vpn"]` | words for the subdomain scanner |
| `banners` | `[]` | populated at runtime, should not be initialized manually |
| `security_headers` | 4 standard headers (see `03_vulnerability_assessment_tool.md`) | headers checked by the header analyzer |
| `urls` | 1 placeholder url | targets to analyze |

---

## `async Cast_Spell(self)`

**Description:** main entry point. For each url in `self.urls`, runs the full analysis flow using each module's *spell*:

1. `Network_Spell(session, url)`
2. `OSINT_Spell(session, url)`
3. DNS resolution → `Recon_Spell(ip)` (orchestrates the 3 port-scan types)
4. `Vuln_Asses_Spell(session, url)` — includes the SSL/TLS check
5. `Exploit_Spell()`
6. `Post_Exploit_Spell()`

**DNS error handling:** `socket.gaierror` is caught and logged — if resolution fails, the port scan for that target is skipped.

**Returns:** `None`

---

## Runtime configuration classmethods

All three follow the same pattern: blocking CLI `input()` + `.append()` on the corresponding class attribute. No input validation is performed.

### `add_word(cls)`
Appends a word to `wordlist`.

### `add_header(cls)`
Appends a header to `security_headers`.

### `add_url(cls)`
Appends a url to `urls`.

**Note:** not called automatically by `Cast_Spell` — must be invoked explicitly before `asyncio.run(Witch.Cast_Spell())`.

---

## Running the script

```python
Witch = TheWidzard()
asyncio.run(Witch.Cast_Spell())
```

Note: `Witch` is an instance, but all the attributes modified (`wordlist`, `banners`, etc.) are class attributes — meaning they'd be shared across any additional `TheWidzard` instances created within the same process.

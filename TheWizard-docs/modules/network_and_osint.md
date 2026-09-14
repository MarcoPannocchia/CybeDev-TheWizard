# `Network_tool` and `OSINT_tool`

[← Index](20_Projects/Test_The-Wizard/index.md)

Two thin "wrapper" modules: they don't implement new logic, but call functions already defined in `Reconnaissance_Tool`, organizing them under a conceptually distinct pentest phase.

---

## `Network_tool`

### `async Network_Spell(self, session, url)`

**Description:** wraps `fetch_info` (defined in `Reconnaissance_Tool`) for the "basic network info gathering" phase.

**Parameters:** `session: aiohttp.ClientSession`, `url: str`

**Flow:** calls `fetch_info(session, url)` and, if it gets a status, prints the status and the first 100 characters of the body.

**Returns:** `None`

---

## `OSINT_tool`

### `async OSINT_Spell(self, session, url)`

**Description:** wraps `Subdomain_Scanner` (defined in `Reconnaissance_Tool`), categorized as OSINT (open source intelligence) since it relies on public/DNS enumeration rather than direct interaction with the target.

**Parameters:** `session: aiohttp.ClientSession`, `url: str`

**Returns:** `None`

---

## Design note

These two modules illustrate a tradeoff: instead of duplicating logic, `Network_tool` and `OSINT_tool` **reuse** functions already present in `Reconnaissance_Tool` through `TheWidzard`'s multiple inheritance (all modules share the same `self`). This keeps the code DRY, but introduces an implicit coupling: `OSINT_Spell` only works because `TheWidzard` *also* inherits from `Reconnaissance_Tool` — taken on its own, `OSINT_tool` isn't self-sufficient.

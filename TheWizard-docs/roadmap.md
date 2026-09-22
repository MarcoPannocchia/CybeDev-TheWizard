# Roadmap

[← Index](index.md)

## 1. Persistence — ✅ done in v0.8.2 (Postgres/asyncpg, not sqlite3)

The original plan called for `sqlite3`. What actually landed is a full Postgres schema via `asyncpg` — see [modules/database.md](modules/database.md) for the real tables (`wizard_wordlist`, `wizard_security_headers`, `wizard_urls`, `wizard_emails`, `wizard_metadata`, `wizard_k6_configs`, `wizard_zap_alerts`, `wizard_arp_hosts`) and [architecture/async.md](architecture/async.md) for why `asyncpg` over a sync driver.

**Point of attention carried forward**: `self.banners` is still reset on every `Port_Scanner(ip)` call (see [architecture/architecture.md](architecture/architecture.md)) and is **not** currently persisted to its own table — unlike emails, metadata, k6 configs, ZAP alerts, and ARP hosts, which all are. If banner history across targets/runs is needed, a `wizard_banners` table following the same pattern would close this gap.

## 2. UI — still open

Library still to be decided. Options to weigh on a lightness/complexity tradeoff:

| Option | Pros | Cons |
|---|---|---|
| **TUI** (`Textual` or `Rich`) | lightweight, consistent with the already-async approach, no web deployment | less "demo-friendly" for a CS50 presentation |
| **Web app** (`Flask` / `FastAPI` + minimal frontend) | more presentable, browser-accessible; needed to actually review/trigger the k6 configs `Exploitation_tool` now builds, and to drive `AI_Suggest_Spell` | more complexity (routing, templates/API, possibly a separate frontend) |

Given the CS50X delivery goal, a lightweight web app (`Flask` + a few HTML pages) is probably still the more "demo-friendly" tradeoff — and as of v0.8.2 there's more to show it: saved k6 configs to review/trigger, ZAP alerts, ARP-discovered hosts, harvested emails/metadata, and (once wired up) AI triage reports.

## 3. Wire `AI_Suggestions` into a normal run — new, open

`AI_Suggest_Spell` (see [modules/ai_suggestions.md](modules/ai_suggestions.md)) is fully implemented but nothing in `Cast_Spell` calls it. Needs either:
- an explicit call site added to `Cast_Spell` (e.g. after `Vuln_Asses_Spell`, using `_build_findings_payload` with that target's banners/CVE hits/SSL info), or
- a UI action that builds the findings payload on demand.

## 4. Execute the k6 configs `Exploitation_tool` builds — new, open

`build_k6_config`/`Exploit_Spell` deliberately never shell out to the `k6` binary (see [modules/exploitation_and_post_exploitation.md](modules/exploitation_and_post_exploitation.md)) — that's left for the planned UI to do explicitly, as a deliberate safety boundary against an unattended load/DoS run.

## 5. Minimal demo (CS50X submission)

Suggested feature subset for the demo, updated for what's actually available in v0.8.2:
- Port scan (a single implementation, e.g. asyncio — avoid the triple redundancy during the demo)
- Subdomain scan
- Header analyzer
- CVE lookup
- SSL/TLS check (structured, concise output)
- Postgres persistence of results (already the default — no longer a "to-add" item)
- OWASP ZAP scan against a deliberately vulnerable demo target (e.g. OWASP Juice Shop / DVWA) — the most visually compelling new v0.8.2 feature
- Minimal UI to launch a scan on a target and browse the saved findings (emails, metadata, ZAP alerts, k6 configs)

## 6. To complete / revisit

- `Post_Exploitation_tool` — still a pure informational placeholder, to be evaluated whether and how to implement it (with strong emphasis on ethical use, same as `Exploitation_tool`/`Network_tool`'s active-scan step)
- NVD API rate limiting in `CVE_Lookup` — risks throttling on long banner lists; `AI_Suggestions` already has a client-side rate limiter that could serve as a template
- `_port_scanner`'s default timeout (0.1s) — configurable since Version 7, but still aggressive on high-latency networks; worth revisiting the default
- Banner history/persistence (see §1 above)
- Automated tests — none exist yet for any module, including the new v0.8.2 ones
- Naming cleanup: `Exploitation_tool`/`Post_Exploitation_tool`/`Network_tool`/`OSINT_tool` still use a lowercase `t` in "tool", inconsistent with `Reconnaissance_Tool`/`Vulnerability_Assessment_Tool` — see [architecture/facade.md](architecture/facade.md)

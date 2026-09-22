# Commands — Run TheWizard

#wip

## Requirements

```bash
# system dependencies
sudo apt install nmap arp-scan

# OWASP ZAP: install separately (not apt-packaged everywhere), then point
# Network_tool.zap_path at zap.sh if it's not at the default
# /usr/share/zaproxy/zap.sh

# venv setup
cd /home/panno/Desktop/CybeDev/
source venv/bin/activate
pip install aiohttp python-nmap asyncpg pypdf python-docx
```

> [!info] socket / asyncio / ssl / subprocess / json / dataclasses
> All part of Python stdlib — no installation needed.

## PostgreSQL + environment variables (required as of v0.8.2)

```bash
export WIZARD_DB_NAME=thewizard
export WIZARD_DB_USER=thewizard
export WIZARD_DB_PASSWORD=change-me
# optional, defaults shown:
export WIZARD_DB_HOST=localhost
export WIZARD_DB_PORT=5432
export WIZARD_DB_SSL=require   # or "disable" for a local dev DB without TLS
```

`Cast_Spell` will raise at startup if `WIZARD_DB_NAME`/`WIZARD_DB_USER`/`WIZARD_DB_PASSWORD` aren't set, or if Postgres isn't reachable — see [architecture/setup_and_usage.md](../architecture/setup_and_usage.md) for the full variable list and [troubleshooting/common-errors.md](../troubleshooting/common-errors.md).

Optional, only needed for `AI_Suggest_Spell`:

```bash
export GROQ_API_KEY=gsk_...
```

---

## Run

```bash
cd /home/panno/Desktop/CybeDev/
source venv/bin/activate
python3 TheWizard_v082.py
```

This loads `wordlist`/`security_headers`/`urls` from Postgres and scans every url currently in `wizard_urls`. If that table is empty, seed it first via SQL or via `add_url()` (see below).

---

## Add config at runtime

As of v0.8.2 these are coroutines and persist to Postgres before updating the in-memory list — they must be awaited, and `db_pool` must already be initialized (i.e. called after `Cast_Spell`/`_load_lists` has run at least once in the process).

```python
wizard = TheWizard()
await wizard._load_lists()      # or run Cast_Spell() first

await wizard.add_word()         # adds a subdomain word to wordlist (Postgres + memory)
await wizard.add_header()       # adds a header to security_headers (Postgres + memory)
await wizard.add_url()          # adds a target URL to urls (Postgres + memory)
```

## Clear stored findings

```python
await wizard.clear_findings()             # everything, including ARP hosts
await wizard.clear_findings(target=url)   # just one target's emails/metadata/k6 configs/ZAP alerts
```

## Run an ARP/LAN sweep standalone

```python
wizard = TheWizard()
await wizard.LAN_Scan("192.168.1.0/24")
```

---

## Manual tool calls (development)

```python
import asyncio, aiohttp, socket

wizard = TheWizard()

async def test():
    await wizard._load_lists()  # required before anything that touches self.wordlist/security_headers/db_pool

    async with aiohttp.ClientSession() as session:
        # fetch info
        status, body = await wizard.fetch_info(session, "https://example.com")
        if status:
            print(status, body[:100])

        # header analyzer
        await wizard.Header_Analyzer(session, "https://example.com")

        # subdomain scanner
        await wizard.Subdomain_Scanner(session, "https://example.com")

        # email harvester / document metadata extractor (new in v0.8.2)
        await wizard.Email_Harvester(session, "https://example.com")
        await wizard.Metadata_Extractor(session, "https://example.com")

        # port scanner with DNS resolution
        domain = "example.com"
        try:
            ip = socket.gethostbyname(domain)
            await wizard.Port_Scanner(ip)
        except socket.gaierror:
            print(f"[ERROR] Could not resolve {domain}")

        # nmap advanced scan
        await wizard.Nmap_port_scanning(ip)

        # k6 config builder (never executes k6) (new in v0.8.2)
        config, script = wizard.build_k6_config("https://example.com")
        print(config)

    await db.close_pool()  # import DatabaseTheWidzard_v082 as db

asyncio.run(test())
```

> See also: [modules/reconnaissance.md](../modules/reconnaissance.md) | [modules/vulnerability.md](../modules/vulnerability.md) | [modules/network.md](../modules/network.md) | [modules/osint.md](../modules/osint.md)

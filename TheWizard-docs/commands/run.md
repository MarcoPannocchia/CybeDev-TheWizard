# Commands — Run TheWizard

#wip

## Requirements

```bash
# system dependencies
sudo apt install nmap

# venv setup
cd /home/panno/Desktop/CybeDev/
source venv/bin/activate
pip install aiohttp python-nmap
```

> [!info] socket
> `socket` is part of Python stdlib — no installation needed.

---

## Run

```bash
cd /home/panno/Desktop/CybeDev/
source venv/bin/activate
python3 Mega_tool.py
```

---

## Add targets at runtime

```python
wizard = TheWizard()

wizard.add_word()       # adds a subdomain word to wordlist
wizard.add_header()     # adds a header to security_headers
wizard.add_url()        # adds a target URL to urls
```

---

## Manual tool calls (development)

```python
import asyncio, aiohttp, socket

wizard = TheWizard()

async def test():
    async with aiohttp.ClientSession() as session:
        # fetch info
        status, body = await wizard.fetch_info(session, "https://example.com")
        if status:
            print(status, body[:100])

        # header analyzer
        await wizard.Header_Analyzer(session, "https://example.com")

        # subdomain scanner
        await wizard.Subdomain_Scanner(session, "https://example.com")

        # port scanner with DNS resolution
        domain = "example.com"
        try:
            ip = socket.gethostbyname(domain)
            await wizard.Port_Scanner(ip)
        except socket.gaierror:
            print(f"[ERROR] Could not resolve {domain}")

        # nmap advanced scan
        await wizard.Nmap_port_scanning(ip)

asyncio.run(test())
```

> See also: [[modules/reconnaissance.md]] | [[modules/vulnerability.md]]

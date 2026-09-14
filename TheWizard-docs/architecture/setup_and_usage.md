# Setup and Usage

[← Index](20_Projects/Test_The-Wizard/index.md)

## Requirements

- Python 3.8+ (for the `asyncio` features used)
- `nmap` binary installed at the OS level (required by `python-nmap`)
- Some features require root/admin privileges

## Python dependencies

```bash
pip install aiohttp python-nmap
```

`socket`, `asyncio`, `ssl`, `datetime`, `urllib.parse`, `concurrent.futures` are all part of the standard library — no installation needed.

## Configuring targets

Default targets are defined as the `urls` class attribute on `TheWidzard`. To change them:

- **statically**: edit the `urls` list in the source
- **at runtime**: call `TheWidzard.add_url()` before execution (requires terminal input)

Same applies to `wordlist` (`add_word()`) and `security_headers` (`add_header()`).

## Running it

```bash
python TheWidzard.py
```

Runs `asyncio.run(Witch.Cast_Spell())`, which analyzes every url in `urls` in sequence.

## Output

All output currently goes to stdout via `print()`, with conventional prefixes for visual parsing:

| Prefix | Meaning |
|---|---|
| `[TARGET]` | start of analysis for a new url |
| `[STATUS]` / `[BODY]` | HTTP response |
| `[FOUND]` / `[MISSING]` | header analyzer result / subdomain found |
| `[PORT]` | port scan result |
| `[BANNER]` | captured banner |
| `[RESOLVED]` | successful DNS resolution |
| `[OUTPUT-*]` | nmap / socket scanner results |
| `[CVE]` | CVE lookup result |
| `[SSL]` / `[WARNING]` | SSL/TLS check result |
| `[ERROR]` / `[CVE ERROR]` / `[SSL ERROR]` / `[DEBUG]` | handled errors |

No structured output (JSON/DB) yet — see [09_roadmap.md](09_roadmap.md).

from ModulesTheWidzard_v082 import *
from Network_tool_v082 import Network_tool  # supersedes the wildcard-imported stub of the same name
import DatabaseTheWidzard_v082 as db

# ╔════════════════════════════════════════════════════════════════════════════╗
# ║ ████████╗██╗  ██╗███████╗    ██╗    ██╗██╗███████╗ █████╗ ██████╗ ██████╗  ║
# ║    ██╔══╝██║  ██║██╔════╝    ██║    ██║██║╚══███╔╝██╔══██╗██╔══██╗██╔══██╗ ║
# ║    ██║   ███████║█████╗      ██║ █╗ ██║██║  ███╔╝ ███████║██████╔╝██║  ██║ ║
# ║    ██║   ██╔══██║██╔══╝      ██║███╗██║██║ ███╔╝  ██╔══██║██╔══██╗██║  ██║ ║
# ║    ██║   ██║  ██║███████╗    ╚███╔███╔╝██║███████╗██║  ██║██║  ██║██████╔╝ ║
# ║    ╚═╝   ╚═╝  ╚═╝╚══════╝     ╚══╝╚══╝ ╚═╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝  ║
# ╚════════════════════════════════════════════════════════════════════════════╝

class TheWizard(Reconnaissance_Tool,
                Vulnerability_Assesment_Tool,
                Exploitation_tool, Post_Exploitation_tool,
                Network_tool, OSINT_tool, AI_Suggestions):

    # wordlist, security_headers and urls used to be hardcoded here. They now
    # live in Postgres (see DatabaseTheWidzard_v082.py) and are loaded once
    # into these class attributes by _load_lists() at the start of
    # Cast_Spell -- every read during a scan (Subdomain_Scanner,
    # Header_Analyzer, the url loop, ...) hits this in-memory list, not the
    # database, so per-item lookups stay fast even at scale. Only writes
    # (add_word/add_header/add_url) touch Postgres.
    wordlist = []
    security_headers = []
    urls = []

    #List of banners that have been taken: {DO NOT ADD ANY}

    banners = []

    # Shared connection pool, set by _load_lists(). None until then.
    db_pool = None

    @classmethod
    async def _load_lists(cls):
        # Fails loudly by design: if Postgres is unreachable or required
        # WIZARD_DB_* env vars are missing, init_pool() raises and the
        # process stops here rather than silently scanning with an empty
        # or stale wordlist/header/url list.
        cls.db_pool = await db.init_pool()
        lists = await db.load_config_lists(cls.db_pool)
        cls.wordlist = lists["wordlist"]
        cls.security_headers = lists["security_headers"]
        cls.urls = lists["urls"]

    async def Cast_Spell(self): #Test function for the Widzard, it calls all the functions of the inherited classes
        await self._load_lists()
        try:
            async with aiohttp.ClientSession() as session:
                for url in self.urls:
                    print(f"\n{'='*50}")
                    print(f"[TARGET] {url}")
                    print(f"{'='*50}")

                    await self.Network_Spell(session, url)

                    await self.OSINT_Spell(session, url)

                    domain = url.replace("https://", "").replace("http://", "").replace("www.", "")
                    try:
                        ip = socket.gethostbyname(domain)
                        print(f"\n[RESOLVED] {domain} -> {ip}")
                        await self.Recon_Spell(ip)
                    except socket.gaierror:
                        print(f"[ERROR] Could not resolve {domain}")

                    await self.Vuln_Asses_Spell(session, url)

                    await self.Exploit_Spell(url)

                    await self.Post_Exploit_Spell()
        finally:
            await db.close_pool()

    @classmethod
    async def add_word(cls):
        new_word = input(f"ADD A NEW WORD TO CHECK IN THE SUBDOMAIN SCANNER: ")
        if cls.db_pool is None:
            print("[ERROR] Database pool not initialized -- call Cast_Spell (or _load_lists) first")
            return
        await db.add_word(cls.db_pool, new_word)
        cls.wordlist.append(new_word)

    @classmethod
    async def add_header(cls):
        new_header = input(f"ADD A NEW HEADER TO CHECK IN THE HEADER ANALYZER: ")
        if cls.db_pool is None:
            print("[ERROR] Database pool not initialized -- call Cast_Spell (or _load_lists) first")
            return
        await db.add_security_header(cls.db_pool, new_header)
        cls.security_headers.append(new_header)

    @classmethod
    async def add_url(cls):
        new_url = input(f"ADD A NEW URL TO CHECK: ")
        if cls.db_pool is None:
            print("[ERROR] Database pool not initialized -- call Cast_Spell (or _load_lists) first")
            return
        await db.add_url(cls.db_pool, new_url)
        cls.urls.append(new_url)

    @classmethod
    async def clear_findings(cls, target=None):
        # Empties emails/metadata/k6 configs/ZAP alerts -- either
        # everything (no target, which also clears ARP hosts) or just one
        # target's rows. Never touches the config lists
        # (wordlist/security_headers/urls).
        if cls.db_pool is None:
            print("[ERROR] Database pool not initialized -- call Cast_Spell (or _load_lists) first")
            return
        await db.clear_findings(cls.db_pool, target)
        if target is None:
            print("[DB] Cleared all findings (emails, metadata, k6 configs, ZAP alerts, ARP hosts)")
        else:
            print(f"[DB] Cleared findings for target {target}")

    async def LAN_Scan(self, subnet):
        # Convenience entry point for LAN_Recon_Spell (ARP sweep -> ZAP on
        # each discovered host) outside of the url-driven Cast_Spell loop,
        # since a subnet isn't one of self.urls. Manages its own pool/
        # session lifecycle so it can be called on its own.
        if self.db_pool is None:
            await self._load_lists()
        async with aiohttp.ClientSession() as session:
            await self.LAN_Recon_Spell(session, subnet)



Casper = TheWizard()

asyncio.run(Casper.Cast_Spell())

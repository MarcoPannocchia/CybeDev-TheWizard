import subprocess
import atexit
import asyncio
import aiohttp
import re
from aiohttp import ClientTimeout

import DatabaseTheWidzard_v082 as db

class Network_tool():

    # ZAP configuration as class attributes, same pattern as
    # wordlist/security_headers/urls: editable without touching the logic.
    zap_path = "/usr/share/zaproxy/zap.sh"   # ZAP launcher path, adapt to your setup
    zap_port = 8080                           # local port ZAP's API/proxy runs on
    zap_api_key = ""                          # API key configured on ZAP, empty if disabled

    # External binary for ARP sweeping (see ARP_Scanner below). Resolved
    # via PATH; override to an absolute path if it's not on it.
    arp_scan_path = "arp-scan"

    # Bounds so LAN discovery / spider results can't silently turn into an
    # unattended mass-scan of everything they find.
    max_lan_hosts_to_scan = 10
    max_spidered_pages_to_scan = 20

    ######################################
    #ZAP DAEMON MANAGEMENT BLOCK:

    async def _zap_is_up(self, session):
        # Lightweight probe: it's not enough for the process to exist, it
        # has to respond on the REST API -- a process that just started but
        # isn't ready yet would look "up" with a plain process check.
        try:
            params = {"apikey": self.zap_api_key} if self.zap_api_key else {}
            async with session.get(
                f"http://localhost:{self.zap_port}/JSON/core/view/version/",
                params=params, timeout=ClientTimeout(total=2)
            ) as r:
                return r.status == 200
        except (aiohttp.ClientError, asyncio.TimeoutError):
            return False

    async def _start_zap_daemon(self, session):
        # If a daemon is already listening (started manually or by a
        # previous run) reuse it instead of duplicating it.
        if await self._zap_is_up(session):
            print("[ZAP] daemon already running, reusing it")
            return

        print("[ZAP] starting daemon...")
        try:
            # zap.sh is a blocking, long-running process: it must never be
            # awaited, it has to be launched "detached" with Popen, which
            # returns immediately after the fork.
            self._zap_process = subprocess.Popen(
                [self.zap_path, "-daemon", "-port", str(self.zap_port),
                 "-config", f"api.key={self.zap_api_key}",
                 "-config", "api.addrs.addr.name=.*",
                 "-config", "api.addrs.addr.regex=true"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
        except FileNotFoundError:
            print(f"[ERROR] ZAP executable not found at {self.zap_path}")
            self._zap_process = None
            return
        except Exception as e:
            print(f"[ERROR] failed to start ZAP daemon: {e}")
            self._zap_process = None
            return

        # The process just started gets cleaned up on script exit, so we
        # don't leave an orphaned daemon running in the background.
        atexit.register(self._stop_zap_daemon)

        # ZAP takes several seconds to expose its API -- polling is better
        # than a fixed sleep, so slower machines aren't penalized and
        # faster machines don't waste time.
        for attempt in range(30):
            await asyncio.sleep(2)
            if await self._zap_is_up(session):
                print("[ZAP] daemon ready")
                return
        print("[ERROR] ZAP daemon did not become ready in time")

    def _stop_zap_daemon(self):
        # Only terminates the process started by this run -- it must never
        # kill a pre-existing ZAP instance left running for other uses.
        process = getattr(self, "_zap_process", None)
        if process is not None:
            process.terminate()
            print("[ZAP] daemon stopped")

    ######################################
    #ZAP SCAN BLOCK:

    async def _zap_wait_for(self, session, status_endpoint, params, label):
        # Spider and active scan both expose a .../status/ endpoint that
        # rises from 0 to 100 -- same polling logic for both, factored out
        # instead of duplicated.
        while True:
            async with session.get(status_endpoint, params=params, timeout=ClientTimeout(total=5)) as r:
                data = await r.json()
                progress = int(data.get("status", 0))
            print(f"[ZAP] {label} progress: {progress}%")
            if progress >= 100:
                return
            await asyncio.sleep(3)

    async def ZAP_Scanner(self, session, url):
        # WARNING: the active scan sends real attack payloads against the
        # target -- only run this against systems you have explicit
        # authorization for, same principle already stated for
        # Exploitation_tool.
        base = f"http://localhost:{self.zap_port}"
        apikey = self.zap_api_key

        try:
            # Spider first: maps the target's URLs, so the active scan
            # afterwards has more surface to test than just the entry page.
            print(f"\n[ZAP] spidering {url}")
            async with session.get(
                f"{base}/JSON/spider/action/scan/",
                params={"url": url, "apikey": apikey},
                timeout=ClientTimeout(total=10)
            ) as r:
                data = await r.json()
                scan_id = data.get("scan")
            if scan_id is None:
                print(f"[ERROR] ZAP spider did not return a scan id: {data}")
                return
            await self._zap_wait_for(
                session, f"{base}/JSON/spider/view/status/",
                {"scanId": scan_id, "apikey": apikey}, "spider"
            )

            async with session.get(
                f"{base}/JSON/spider/view/results/",
                params={"scanId": scan_id, "apikey": apikey},
                timeout=ClientTimeout(total=10)
            ) as r:
                data = await r.json()
                spidered_urls = data.get("results", [])
            print(f"[ZAP] spider discovered {len(spidered_urls)} URLs")
            await self._harvest_spidered_pages(session, url, spidered_urls)

            print(f"\n[ZAP] active scan on {url}")
            async with session.get(
                f"{base}/JSON/ascan/action/scan/",
                params={"url": url, "apikey": apikey},
                timeout=ClientTimeout(total=10)
            ) as r:
                data = await r.json()
                ascan_id = data.get("scan")
            if ascan_id is None:
                print(f"[ERROR] ZAP active scan did not return a scan id: {data}")
                return
            await self._zap_wait_for(
                session, f"{base}/JSON/ascan/view/status/",
                {"scanId": ascan_id, "apikey": apikey}, "active scan"
            )

            # Alerts are only reliably readable once the scan has finished --
            # reading them earlier would give a partial or empty list.
            async with session.get(
                f"{base}/JSON/core/view/alerts/",
                params={"baseurl": url, "apikey": apikey},
                timeout=ClientTimeout(total=10)
            ) as r:
                data = await r.json()
                alerts = data.get("alerts", [])

            if not alerts:
                print(f"[ZAP] no alerts found for {url}")
                return
            for alert in alerts:
                # A single malformed alert must not interrupt the loop --
                # same pattern already used in CVE_Lookup.
                try:
                    risk = alert["risk"]
                    name = alert["alert"]
                    description = alert.get("description", "")[:150]
                    print(f"[ZAP] {risk} | {name} | {description}")
                except KeyError as e:
                    print(f"[ZAP PARSE ERROR] skipped one malformed alert: {e}")
                    continue

            db_pool = getattr(self, "db_pool", None)
            if db_pool is not None:
                await db.save_zap_alerts_bulk(db_pool, url, alerts)

        except aiohttp.ClientError as e:
            print(f"[ERROR] ZAP API request failed: {e}")
        except asyncio.TimeoutError:
            print(f"[ERROR] Timeout communicating with ZAP for {url}")
        except Exception as e:
            print(f"[ERROR] Unexpected error during ZAP scan: {e}")

    async def _harvest_spidered_pages(self, session, target, page_urls):
        """Feed pages ZAP's spider discovered into the OSINT page-scanning
        tools -- Email_Harvester, Metadata_Extractor, and any future tool
        with the same (session, page_url) -> results shape -- so findings
        aren't limited to the single entry-point URL. Only meaningful when
        Network_tool is mixed into TheWizard alongside OSINT_tool, hence
        the getattr guards; bounded by max_spidered_pages_to_scan so a big
        crawl can't turn into an unattended mass-download.
        """
        db_pool = getattr(self, "db_pool", None)
        email_harvester = getattr(self, "Email_Harvester", None)
        metadata_extractor = getattr(self, "Metadata_Extractor", None)
        if email_harvester is None and metadata_extractor is None:
            return

        for page_url in page_urls[: self.max_spidered_pages_to_scan]:
            if email_harvester is not None:
                emails = await email_harvester(session, page_url)
                if emails and db_pool is not None:
                    await db.save_emails_bulk(db_pool, target, emails)

            if metadata_extractor is not None:
                metadata_results = await metadata_extractor(session, page_url)
                if metadata_results and db_pool is not None:
                    for source_url, file_type, metadata in metadata_results:
                        await db.save_metadata(db_pool, target, source_url, file_type, metadata)

    ######################################
    #ARP SCANNER BLOCK:

    _ARP_LINE_REGEX = re.compile(
        r'^(\d{1,3}(?:\.\d{1,3}){3})\s+([0-9a-fA-F]{2}(?::[0-9a-fA-F]{2}){5})\s*(.*)$'
    )

    async def ARP_Scanner(self, subnet):
        """Sweep `subnet` (e.g. '192.168.1.0/24') for live hosts via ARP.
        Wraps the arp-scan binary via subprocess -- same external-tool
        pattern already used for nmap (Reconnaissance_Tool) and the ZAP
        daemon above, rather than reimplementing raw ARP framing in
        Python. Requires arp-scan installed and (on most systems)
        raw-socket privileges (root / CAP_NET_RAW)."""
        print(f"\n[ARP] scanning {subnet}")
        try:
            proc = await asyncio.create_subprocess_exec(
                self.arp_scan_path, "--quiet", "--plain", subnet,
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=60)
        except FileNotFoundError:
            print(f"[ERROR] arp-scan executable not found (looked for '{self.arp_scan_path}')")
            return []
        except asyncio.TimeoutError:
            print(f"[ERROR] arp-scan timed out on {subnet}")
            return []

        if proc.returncode != 0:
            stderr_text = stderr.decode(errors="ignore")
            print(f"[ERROR] arp-scan exited {proc.returncode}: {stderr_text[:300]}")
            if "permitted" in stderr_text.lower() or "permission" in stderr_text.lower():
                print("[HINT] arp-scan usually needs root / CAP_NET_RAW to send raw ARP frames")
            return []

        hosts = []
        for line in stdout.decode(errors="ignore").splitlines():
            match = self._ARP_LINE_REGEX.match(line.strip())
            if match:
                ip, mac, vendor = match.groups()
                vendor = vendor.strip() or None
                hosts.append({"ip": ip, "mac": mac, "vendor": vendor})
                print(f"[ARP] {ip} - {mac} - {vendor}")

        return hosts

    async def LAN_Recon_Spell(self, session, subnet):
        """Sweep `subnet` via ARP, persist discovered hosts, then hand a
        bounded number of them (max_lan_hosts_to_scan) to ZAP_Scanner as
        http://<ip>/ targets. Same authorization requirement as
        ZAP_Scanner/Exploit_Spell applies to *every* host reached this
        way, not just the ones already in self.urls -- an ARP sweep can
        surface devices nobody explicitly listed as a target."""
        hosts = await self.ARP_Scanner(subnet)

        db_pool = getattr(self, "db_pool", None)
        if hosts and db_pool is not None:
            await db.save_arp_hosts_bulk(db_pool, subnet, hosts)

        for host in hosts[: self.max_lan_hosts_to_scan]:
            target = f"http://{host['ip']}/"
            print(f"\n[LAN] handing {target} to ZAP (discovered via ARP on {subnet})")
            await self.ZAP_Scanner(session, target)

    ######################################
    #ORCHESTRATION:

    async def Network_Spell(self, session, url):
        print("\n[*] NETWORK INFORMATION GATHERING")
        status, body = await self.fetch_info(session, url)
        if status:
            print(f"[STATUS] {status}")
            print(f"[BODY] {body[:100]}")

        print("\n[*] ZAP SCAN")
        await self._start_zap_daemon(session)
        if getattr(self, "_zap_process", None) is not None or await self._zap_is_up(session):
            await self.ZAP_Scanner(session, url)
        else:
            print("[ERROR] ZAP daemon unavailable, skipping scan")
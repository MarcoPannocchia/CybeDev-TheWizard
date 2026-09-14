import nmap, socket, ssl, asyncio, aiohttp
from datetime import datetime, timezone
from aiohttp import ClientTimeout
from urllib.parse import urlparse, urlunparse
from concurrent.futures import ThreadPoolExecutor, as_completed

# Facade strucuture for TheWidzard

class Reconnaissance_Tool():

    ######################################
    #PORT SCANNER BLOCK: (aiohttp and nmap):

    #basic port scanning:
    async def _port_scanner(self, ip, port, timeout=0.1):
        # timeout is now a parameter (was a hardcoded magic number) so callers
        # can tune it per-context (LAN vs internet) instead of editing source.

        try:
            connection_port_scanner = asyncio.open_connection(ip, port) #Attempt of connection to port "port"
            reader, writer = await asyncio.wait_for(connection_port_scanner, timeout=timeout) #Assignment of reader and writer variable (TCP connection channels)

            print(f"[PORT] {port} OPEN") # Successful attempt

            banner = await reader.read(1024) #Reading of the banner, if it's present, with a max size of 1024 bytes
            banner_decoded = banner.decode(errors="ignore") # Decoding of the banner, if it's present, ignoring errors
            if banner_decoded: # If the banner is not empty
                print(f"[BANNER] {port} {banner_decoded.strip()}") # Output of the banner
                self.banners.append(banner_decoded.strip()) # The banner must be added to the banners list
            writer.close() #Closing the writer channel
            await writer.wait_closed() #Wating until complete

        except asyncio.TimeoutError:
            pass  # Port scanning took too long
        except ConnectionRefusedError:
            print(f"[PORT] {port} access denied")  # Port scanning was denied
        except OSError:
            print(f"[PORT] {port} server unreachable")  #  Port scanning is impossible, server unreachable

    async def Port_Scanner(self, ip, ports=None, timeout=0.1): # Callable function
        self.banners = [] # for each ip there are new banners, the old ones must be removed
        if ports is None:
            ports = [20, 21, 22, 23, 25, 53, 80, 110, 143, 443, 445, 3306, 3389, 5432, 8080, 8443]
        await asyncio.gather(*[self._port_scanner(ip, port, timeout) for port in ports]) # Attempting port scanning for each port

    #NMAP port scanning:

    async def Nmap_port_scanning(self, ip): #Advanced nmap tool
        try:
            nm = nmap.PortScanner()     #defining the instance
            loop = asyncio.get_running_loop()
            # nm.scan() is a synchronous, blocking call (it shells out to the
            # nmap binary and waits). Running it directly inside an async def
            # would freeze the whole event loop for the scan's duration, so it
            # is offloaded to the default ThreadPoolExecutor via run_in_executor.
            await loop.run_in_executor(None, lambda: nm.scan(ip, arguments="-sV"))
            for port in nm[ip]["tcp"]:  #scanning the ip with known tcp ports known to nmap
                print(f"[OUTPUT-{port}] {nm[ip]['tcp'][port]['state']} - {nm[ip]['tcp'][port]['name']}") #output of state and name for each port
        except nmap.nmap.PortScannerError as e: #Catching nmap-specific errors
            print(f"[ERROR] Nmap scan failed: {e}") #Informing user of nmap error
        except Exception as e: #Catching any other errors
            print(f"[ERROR] Unexpected error during nmap scanning: {e}") #Informing user of unexpected error

    ######################################
    #HTTP INFO REQUEST BLOCK:

    async def fetch_info(self, session, url):
        try:
            async with session.get(url, timeout=ClientTimeout(total=5)) as r:  # Http general get requests
                return r.status, await r.text()   # Returns status and text
        except aiohttp.ClientError as e:
            print(f"[ERROR] Failed to fetch {url}: {e}")
            return None, None
        except asyncio.TimeoutError:
            print(f"[ERROR] Timeout fetching {url}")
            return None, None


    ######################################
    #SUBDOMAIN SCANNER BLOCK:

    #This function is necessary, it inserts
    #the word into the url to search along all well-known subdomains


    def insert_word(self, url, word):
        parsed = urlparse(url)
        # parsed.netloc = "www.example.com"
        # rimuoviamo "www." se presente
        host = parsed.netloc.replace("www.", "", 1)
        new_netloc = f"{word}.{host}"

        return urlunparse(parsed._replace(netloc=new_netloc))


    async def Subdomain_Scanner(self, session, url):  # This fuction is the one that'll be called by the Widzard
    # Asyncronized function
        # Awaited action that analyzes a list of words for an url
        await asyncio.gather(*[self._word_scan(session, url, word) for word in self.wordlist])

    async def _word_scan(self, session, url, word): # This function is not going to be called by TheWidzard
        # Target is the new url
        target = self.insert_word(url, word)

        # The new url is going to be analyzed by the get command
        try:
            async with session.get(target, timeout=ClientTimeout(total=3)) as r:
                print(f"[FOUND] {target} - status {r.status}")

        except aiohttp.ClientError:
            pass
        except asyncio.TimeoutError:
            pass
        except Exception as e:
            print(f"[DEBUG] Unexpected error scanning {target}: {type(e).__name__}")

    ######################################
    #SOCKET IMPLEMENTATION BLOCK:

    def _socket_banner_grab(self, host, port, timeout=3): #Attempt of connection to port and banner extraction
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #Creating socket
            s.settimeout(timeout) #Setting timeout
            s.connect((host, port)) #Connecting to host:port

            banner = b"" #Banner initialization

            try:
                s.settimeout(1.0) #Timeout for banner reading
                banner = s.recv(1024) #Reading of the banner with a max size of 1024 bytes

            except socket.timeout: #If initial read times out
                try:
                    s.send(b"HEAD / HTTP/1.0\r\nHost: " + host.encode() + b"\r\n\r\n") #HTTP request
                    banner = s.recv(1024) #Reading response
                except Exception:
                    pass #If sending fails, keep banner as empty byte string

            s.close() #Closing socket

        except ConnectionRefusedError:
            print(f"[PORT] {port} access denied") #Port connection was refused
        except Exception as e:
            print(f"[ERROR] error {e}") #Generic error message

        return banner.strip() if banner else None #Return cleaned banner or None

    def Socket_Banner_Grabber(self, host, port_min = 0, port_max = 1024, max_threads = 100): #Callable function for socket banner grabbing
        banners_found = {} #Dictionary for storing results

        with ThreadPoolExecutor(max_workers=max_threads) as executor: #Thread pool creation
            futures = { #Submitting all port tasks
                executor.submit(self._socket_banner_grab, host, p) : p
                                    for p in range(port_min, port_max +1)
            }

            for future in as_completed(futures): #As each task completes
                port_num = futures[future] #Getting the port number
                try:
                    banners_found[port_num] = future.result() #Storing result
                except Exception as e:
                    banners_found[port_num] = f"Error: {str(e)}" #Storing error

        return banners_found #Return all collected banners

    def _socket_port_scan(self, host, port, timeout=3): #Attempt of connection to check if port is open
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #Creating socket
            s.settimeout(timeout) #Setting timeout
            result = s.connect_ex((host, port)) #Attempting connection
            s.close() #Closing socket
            return result == 0 #Return True if connection successful

        except: #If any error occurs
            return False #Port is considered closed

    def Socket_Port_Scanner(self, host, port_start = 0, port_end = 1024, max_threads = 100): #Callable function for socket port scanning
        socket_port_opened = [] #List for storing open ports

        with ThreadPoolExecutor(max_workers=max_threads) as executor: #Thread pool creation
            futures={ #Submitting all port tasks
                executor.submit(self._socket_port_scan, host, p): p
                                    for p in range(port_start, port_end+1)
            }

            for future in as_completed(futures): #As each task completes
                port = futures[future] #Getting the port number
                if future.result(): #If port is open
                    socket_port_opened.append(port) #Adding to open ports list

        return sorted(socket_port_opened) #Return sorted list of open ports

    ######################################

    async def Recon_Spell(self, ip):
        print("\n[*] PORT SCANNER - ASYNCIO IMPLEMENTATION") #Using asyncio-based port scanner
        await self.Port_Scanner(ip)
        print("\n[*] NMAP SCANNING") #Using nmap tool
        await self.Nmap_port_scanning(ip)
        print("\n[*] PORT SCANNER - SOCKET IMPLEMENTATION") #Using socket-based port scanner
        # Socket_Port_Scanner/Socket_Banner_Grabber are synchronous (they build
        # their own ThreadPoolExecutor internally). Calling them directly here
        # would still block the event loop for their entire duration, since a
        # sync call inside an async function is not automatically concurrent
        # with the loop. asyncio.to_thread hands them off to a worker thread
        # and awaits the result, keeping the loop free in the meantime.
        open_ports_socket = await asyncio.to_thread(self.Socket_Port_Scanner, ip, 1, 1024) #Scanning with socket implementation
        if open_ports_socket:
            print(f"[OUTPUT-SOCKET] Open ports found: {open_ports_socket}") #Output of socket scanner results
            print("\n[*] BANNER GRABBING - SOCKET IMPLEMENTATION") #Using socket-based banner grabber
            banners = await asyncio.to_thread(
                self.Socket_Banner_Grabber, ip, min(open_ports_socket), max(open_ports_socket)
            ) #Grabbing banners from open ports
            for port in open_ports_socket:
                if port in banners and banners[port]:
                    print(f"[BANNER] {port} {banners[port]}") #Output of banner for open port
        else:
            print("[OUTPUT-SOCKET] No open ports found with socket implementation") #No open ports message


class Vulnerability_Assessment_Tool():
    # Renamed from "Vulnerability_Assesment_Tool" (missing "s") flagged as a
    # #known-issue in the docs audit. An alias is kept below for backward
    # compatibility, mirroring the same alias pattern already used for
    # renamed files in the Obsidian docs.

    ######################################
    # HEADER ANALYZER BLOCK:

    async def Header_Analyzer(self, session, url):  #callable function for header analyzing
        try:
            async with session.get(url, timeout=ClientTimeout(total=5)) as r: #http get request
                for header in self.security_headers:  #for every header that is in the security_header list
                    if header in r.headers:  #if it's found
                        print(f"[FOUND]: {header}")
                    else: #if it's missing
                        print(f"[MISSING]: {header}")
        except aiohttp.ClientError as e:
            print(f"[ERROR] Failed to analyze headers for {url}: {e}")
        except asyncio.TimeoutError:
            print(f"[ERROR] Timeout analyzing headers for {url}")



    ######################################
    #CVE LOOKUP BLOCK:
    async def CVE_Lookup(self, session, banner):  #Tool that looks upon the documentations
        # Now takes the caller's shared aiohttp session instead of opening a
        # new ClientSession per call. A ClientSession owns a connection pool
        # (TCP connections + DNS cache); recreating it on every lookup throws
        # that pool away each time instead of reusing it across requests.
        url = f"https://services.nvd.nist.gov/rest/json/cves/2.0?keywordSearch={banner}"  #API and automatic search
        try:
            async with session.get(url, timeout=ClientTimeout(total=10)) as r: # get request to the api
                data = await r.json() # Listing all the data in a dictonary
                vulnerabilities = data.get("vulnerabilities", []) # taking only the vulnerabilities
                for v in vulnerabilities: # going along each vulnerability
                    try:
                        cve_id = v["cve"]["id"] # variable takes only cve id information
                        description = v["cve"]["descriptions"][0]["value"] #variable takes only information considered description
                        # A single CVE entry lacking a CVSS v3.1 metric used to
                        # raise a KeyError/IndexError that broke out of the
                        # whole "for v in vulnerabilities" loop, silently
                        # dropping every CVE after the offending one. Each
                        # entry is now parsed in its own try/except so one bad
                        # record just gets skipped, and multiple CVSS metric
                        # versions are tried in order of preference.
                        metrics = v["cve"].get("metrics", {})
                        score = None
                        for metric_key in ("cvssMetricV31", "cvssMetricV30", "cvssMetricV2"):
                            if metric_key in metrics:
                                score = metrics[metric_key][0]["cvssData"]["baseScore"]
                                break
                        score_display = score if score is not None else "N/A"
                        print(f"[CVE] {cve_id} | Score: {score_display} | {description}") # Meaning full output
                    except (KeyError, IndexError) as e:
                        print(f"[CVE PARSE ERROR] skipped one malformed entry: {e}")
                        continue
        except aiohttp.ClientError as e:
            print(f"[CVE ERROR] {e}")
        except asyncio.TimeoutError:
            print(f"[CVE ERROR] Timeout during CVE lookup for banner '{banner}'")
        except Exception as e:
            print(f"[CVE ERROR] {e}")
    ######################################


    ######################################
    #SSL/TLS checker

    async def SSL_TSL_CHECKER(self, host, port=443, timeout=5):
        # "self" was missing entirely in the original stub, meaning this
        # could never actually be called as nm.SSL_TSL_CHECKER() on an
        # instance without a TypeError. Implemented using asyncio's own
        # open_connection with an ssl context (same asyncio-native pattern
        # already used in _port_scanner) so it stays consistent with the
        # rest of the async codebase instead of pulling in a separate sync
        # ssl+socket path.
        context = ssl.create_default_context()
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port, ssl=context, server_hostname=host),
                timeout=timeout
            )
            ssl_object = writer.get_extra_info("ssl_object")
            cert = ssl_object.getpeercert()

            issuer = dict(x[0] for x in cert.get("issuer", []))
            subject = dict(x[0] for x in cert.get("subject", []))
            not_after = cert.get("notAfter")
            expire_date = datetime.strptime(not_after, "%b %d %H:%M:%S %Y %Z").replace(tzinfo=timezone.utc)
            days_left = (expire_date - datetime.now(timezone.utc)).days

            print(f"[SSL] {host}:{port} issuer: {issuer.get('organizationName', 'Unknown')}")
            print(f"[SSL] {host}:{port} subject: {subject.get('commonName', 'Unknown')}")
            print(f"[SSL] {host}:{port} expires: {not_after} ({days_left} days left)")
            if days_left < 30:
                print(f"[WARNING] {host}:{port} certificate expiring soon")

            writer.close()
            await writer.wait_closed()

            return {"issuer": issuer, "subject": subject, "not_after": not_after, "days_left": days_left}

        except ssl.SSLCertVerificationError as e:
            print(f"[SSL ERROR] {host}:{port} certificate verification failed: {e}")
        except asyncio.TimeoutError:
            print(f"[SSL ERROR] {host}:{port} connection timeout")
        except (ConnectionRefusedError, OSError) as e:
            print(f"[SSL ERROR] {host}:{port} connection failed: {e}")
        except Exception as e:
            print(f"[SSL ERROR] {host}:{port} {e}")
        return None

    ######################################

    async def Vuln_Asses_Spell(self, session, url):
        print("\n[*] HEADER ANALYZER")
        await self.Header_Analyzer(session, url)
        print("\n[*] CVE LOOKUP")
        for banner in self.banners:
            await self.CVE_Lookup(session, banner) # now reuses the shared session
        print("\n[*] SSL/TLS CHECK")
        host = urlparse(url).netloc or url
        await self.SSL_TSL_CHECKER(host)


# Backward-compatible alias: any existing code/docs referencing the old
# misspelled class name keeps working after the rename.
Vulnerability_Assesment_Tool = Vulnerability_Assessment_Tool


class Exploitation_tool():

    async def Exploit_Spell(self):
        print("\n[*] EXPLOITATION TOOLS")
        print("[INFO] Exploitation module ready for deployment")

class Post_Exploitation_tool():

    async def Post_Exploit_Spell(self):
        print("\n[*] POST-EXPLOITATION TOOLS")
        print("[INFO] Post-exploitation module ready for deployment")

class Network_tool():

    async def Network_Spell(self, session, url):
        print("\n[*] NETWORK INFORMATION GATHERING")
        status, body = await self.fetch_info(session, url)
        if status:
            print(f"[STATUS] {status}")
            print(f"[BODY] {body[:100]}")


class OSINT_tool():

    async def OSINT_Spell(self, session, url):
        print("\n[*] OPEN SOURCE INTELLIGENCE")
        await self.Subdomain_Scanner(session, url)
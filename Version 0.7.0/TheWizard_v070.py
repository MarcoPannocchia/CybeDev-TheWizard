from ModulesTheWidzard_v070 import *

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
                Network_tool, OSINT_tool):
    
    #List of subdomains to analyze:

    wordlist = ["mail", "api", "dev", "admin", "test", "staging", "vpn"] 

    #List of banners that have been taken: {DO NOT ADD ANY}

    banners = []

    #List of headers to analyze:
    
    security_headers = [
            "Strict-Transport-Security",
            "X-Frame-Options",
            "Content-Security-Policy",
            "X-Content-Type-Options",
    ]

        #List of links to check:
    urls = [
        "https://ejendom.com"
    ]
        
    async def Cast_Spell(self): #Test function for the Widzard, it calls all the functions of the inherited classes
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
                
                await self.Exploit_Spell()
                
                await self.Post_Exploit_Spell()


    @classmethod
    def add_word(cls):
        new_word = input(f"ADD A NEW WORD TO CHECK IN THE SUBDOMAIN SCANNER: ")
        cls.wordlist.append(new_word)

    @classmethod
    def add_header(cls):
        new_header = input(f"ADD A NEW HEADER TO CHECK IN THE HEADER ANALYZER: ")
        cls.security_headers.append(new_header)

    @classmethod

    def add_url(cls):
        new_url = input(f"ADD A NEW URL TO CHECK: ")
        cls.urls.append(new_url)



Casper = TheWizard()

asyncio.run(Casper.Cast_Spell())
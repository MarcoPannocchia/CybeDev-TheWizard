<div align="center">

<!-- 🖼️ Sostituisci questo link con l'immagine generata (banner_thewizard.png) -->
<img src="./docs/assets/banner_thewizard.png" alt="TheWizard banner" width="100%">

# 🧙‍♂️ TheWizard

**Modular Security Framework for Reconnaissance & System Analysis**

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Architecture](https://img.shields.io/badge/architecture-plugin--based-8A2BE2)]()
[![Database](https://img.shields.io/badge/DB-PostgreSQL%20%2F%20asyncpg-336791?logo=postgresql&logoColor=white)]()
[![Status](https://img.shields.io/badge/status-in%20development-yellow)]()
[![License](https://img.shields.io/badge/license-see%20LICENSE.md-lightgrey)](./LICENSE.md)

</div>

---

## 📖 Indice

- [Cos'è TheWizard](#cosè-thewizard)
- [Architettura](#architettura)
- [Moduli](#moduli)
- [Installazione](#installazione)
- [Utilizzo](#utilizzo)
- [Screenshot](#screenshot)
- [Roadmap](#roadmap)
- [Disclaimer](#disclaimer)
- [Autore](#autore)

---

## Cos'è TheWizard

**TheWizard** è un framework modulare per la sicurezza informatica, pensato per attività di **reconnaissance** e **system analysis**. È costruito con un'architettura **plugin-based** che permette di sviluppare tool estendibili e completamente indipendenti tra loro, mantenendo il codice ordinato e facile da estendere nel tempo.

Il progetto nasce come percorso di apprendimento pratico: ogni modulo viene ottimizzato passo dopo passo per consolidare competenze reali di sviluppo e cybersecurity, non solo per "far funzionare" il tool.

> ⚠️ Progettato esclusivamente per attività di ricerca in sicurezza informatica e testing autorizzato in ambienti controllati.

---

## Architettura

- **Pattern Facade** come punto di ingresso unificato verso i vari moduli
- **Architettura a plugin**: ogni tool è indipendente e collegabile senza toccare il core
- **Asincrona** (`asyncio`), con accesso al database gestito tramite `asyncpg`
- Wordlist e dati di supporto gestiti tramite **database PostgreSQL locale**, con l'obiettivo di sincronizzarli in futuro con un'istanza nell'homelab

```
TheWizard/
├── core/                # Facade e orchestrazione dei moduli
├── modules/
│   ├── network_tool/     # Scansione e analisi di rete
│   └── osint_tool/        # Raccolta informazioni OSINT (subdomain scanning, ecc.)
├── db/                   # Schema e accesso PostgreSQL/asyncpg
└── docs/                 # Documentazione e materiale di studio
```

*(struttura indicativa — adattala a quella reale del repo)*

---

## Moduli

### 🌐 Network_tool
Modulo dedicato alla scansione e analisi degli asset di rete.

### 🔍 OSINT_tool
Modulo di raccolta informazioni open-source, tra cui il **Subdomain Scanner**, la cui wordlist viene popolata dinamicamente da database invece che da file statici o valori hardcoded.

---

## Installazione

```bash
git clone https://github.com/MarcoPannocchia/CybeDev-TheWizard.git
cd CybeDev-TheWizard

python -m venv venv
source venv/bin/activate   # su Windows: venv\Scripts\activate

pip install -r requirements.txt
```

Configura la connessione al database PostgreSQL nel file di configurazione prima del primo avvio.

---

## Utilizzo

```bash
python thewizard.py --module network_tool --target <IP/host>
python thewizard.py --module osint_tool --target <dominio>
```

*(sintassi indicativa — aggiorna con i comandi reali una volta stabilizzata la CLI)*

---

## Screenshot

<div align="center">
<img src="./docs/assets/screenshot_cli.png" alt="TheWizard in azione" width="80%">
</div>

---

## Roadmap

- [x] Architettura plugin-based con pattern Facade
- [x] Modulo Network_tool
- [x] Modulo OSINT_tool (subdomain scanner)
- [x] Wordlist gestita via database PostgreSQL
- [ ] Sincronizzazione DB con istanza homelab
- [ ] Nuovi moduli di analisi
- [ ] Documentazione estesa per ogni modulo

---

## Disclaimer

Questo strumento è sviluppato a scopo didattico e di ricerca in ambito cybersecurity. L'autore non si assume responsabilità per usi impropri o non autorizzati. Utilizzare **solo** su sistemi di cui si possiede l'autorizzazione esplicita al testing.

---

## Autore

**Marco Pannocchia**

[![GitHub](https://img.shields.io/badge/GitHub-MarcoPannocchia-181717?logo=github&logoColor=white)](https://github.com/MarcoPannocchia)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Marco%20Pannocchia-0A66C2?logo=linkedin&logoColor=white)](https://www.linkedin.com/in/marco-pannocchia-191924433)
[![Instagram](https://img.shields.io/badge/Instagram-marco__pannocchia-E4405F?logo=instagram&logoColor=white)](https://www.instagram.com/marco_pannocchia)

<div align="center">
<sub>Built with 🐍 Python, PostgreSQL e tanta curiosità per la cybersecurity.</sub>
</div>

<div align="center">

<!-- 🖼️ Replace with the generated banner (banner_thewizard.png) -->
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

## 📖 Table of Contents

- [About TheWizard](#about-thewizard)
- [Architecture](#architecture)
- [Modules](#modules)
- [Installation](#installation)
- [Usage](#usage)
- [Screenshots](#screenshots)
- [Roadmap](#roadmap)
- [Disclaimer](#disclaimer)
- [Author](#author)

---

## About TheWizard

**TheWizard** is a modular security framework built for **reconnaissance** and **system analysis**. It's designed around a **plugin-based architecture** that allows independent, extensible tools to be developed without touching the core, keeping the codebase clean and easy to grow over time.

The project started as a hands-on learning path: every module is optimized step by step to build real development and cybersecurity skills, not just to "make the tool work."

> ⚠️ Built exclusively for cybersecurity research and authorized testing in controlled environments.

---

## Architecture

- **Facade pattern** as a unified entry point to the various modules
- **Plugin-based architecture**: each tool is independent and pluggable without touching the core
- **Asynchronous** (`asyncio`), with database access handled via `asyncpg`
- Wordlists and support data are managed through a **local PostgreSQL database**, with the goal of syncing it with a homelab instance down the line

```
TheWizard/
├── core/                # Facade and module orchestration
├── modules/
│   ├── network_tool/     # Network scanning and analysis
│   └── osint_tool/        # OSINT gathering (subdomain scanning, etc.)
├── db/                   # PostgreSQL/asyncpg schema and access
└── docs/                 # Documentation and study material
```

*(indicative structure — adapt it to match the actual repo layout)*

---

## Modules

### 🌐 Network_tool
Module dedicated to scanning and analyzing network assets.

### 🔍 OSINT_tool
Open-source intelligence gathering module, including the **Subdomain Scanner**, whose wordlist is populated dynamically from a database instead of static files or hardcoded values.

---

## Installation

```bash
git clone https://github.com/MarcoPannocchia/CybeDev-TheWizard.git
cd CybeDev-TheWizard

python -m venv venv
source venv/bin/activate   # on Windows: venv\Scripts\activate

pip install -r requirements.txt
```

Set up your PostgreSQL database connection in the config file before the first run.

---

## Usage

```bash
python thewizard.py --module network_tool --target <IP/host>
python thewizard.py --module osint_tool --target <domain>
```

*(indicative syntax — update with the real commands once the CLI is stable)*

---

## Screenshots

<div align="center">
<img src="./docs/assets/screenshot_cli.png" alt="TheWizard in action" width="80%">
</div>

---

## Roadmap

- [x] Plugin-based architecture with Facade pattern
- [x] Network_tool module
- [x] OSINT_tool module (subdomain scanner)
- [x] Wordlist managed via PostgreSQL database
- [ ] Sync DB with homelab instance
- [ ] New analysis modules
- [ ] Extended documentation for each module

---

## Disclaimer

This tool is developed for educational and cybersecurity research purposes. The author takes no responsibility for improper or unauthorized use. Use it **only** on systems you have explicit authorization to test.

---

## Author

**Marco Pannocchia**

[![GitHub](https://img.shields.io/badge/GitHub-MarcoPannocchia-181717?logo=github&logoColor=white)](https://github.com/MarcoPannocchia)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Marco%20Pannocchia-0A66C2?logo=linkedin&logoColor=white)](https://www.linkedin.com/in/marco-pannocchia-191924433)
[![Instagram](https://img.shields.io/badge/Instagram-marco__pannocchia-E4405F?logo=instagram&logoColor=white)](https://www.instagram.com/marco_pannocchia)

<div align="center">
<sub>Built with 🐍 Python, PostgreSQL and a lot of curiosity for cybersecurity.</sub>
</div>

# HOUND v2.0 | Autonomous OSINT Platform

> **Cognitive Weapon System** — An advanced, locally-executed Open Source Intelligence framework featuring autonomous AI analysis, concurrent multi-platform reconnaissance, and persistent evidence correlation.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![AI](https://img.shields.io/badge/AI-Ollama%20Llama3-purple.svg)](https://ollama.com)

---

## Executive Summary

HOUND v2.0 is not just a scraper; it is a modular intelligence engine designed for security researchers and engineers. It moves beyond simple API calls by implementing a **Correlation Engine** that fuses data from DNS, Social Media, Infrastructure, and Mobile networks into a unified SQLite graph. The system is powered by a local LLM (Ollama) that provides real-time, evidence-based intelligence briefs without external data dependency.

## What Makes HOUND Legendary?

*   **Zero-Dependency AI:** Unlike cloud-based tools, HOUND’s AI analyst runs entirely offline via Ollama. This ensures that sensitive intelligence briefs never leave the local machine.
*   **Aggressive Enumeration:** The DNS module doesn't just resolve records; it actively brute-forces 80+ subdomains and attempts Zone Transfers (AXFR) to uncover hidden infrastructure.
*   **Concurrent Social Hunting:** Utilizing Python’s `ThreadPoolExecutor`, HOUND scans 83 social platforms simultaneously, providing results in seconds rather than minutes.
*   **Persistent Memory:** Every piece of evidence is stored in a local SQLite database. If you investigate a phone number today and an email tomorrow, HOUND will automatically link them if they share common attributes.
*   **Professional Aesthetics:** From the glitching terminal UI to the sophisticated reporting, every interaction is designed to feel like a high-end cognitive weapon.

## Core Capabilities

| Module | Technical Implementation |
| :--- | :--- |
| **DNS Recon** | A/AAAA/MX/NS/TXT/CNAME/SOA records, zone transfers, subdomain brute-force (80+ prefixes), CNAME hijack detection. |
| **Social Hunt** | 83 platforms concurrently, GitHub deep metadata extraction, category-based classification (Dev, Social, Gaming). |
| **Mobile Intel** | E.164 parsing, carrier detection, VoIP identification, HLR status validation (Numverify), cell tower geolocation (OpenCelliD). |
| **Infrastructure** | Shodan API integration for port mapping, CVE identification, and organizational footprinting. |
| **AI Analyst** | Self-starting Ollama server, one-time model warmup, evidence-based intelligence briefs with confidence scoring. |
| **Correlation** | Cross-module entity linking (e.g., Phone-to-Email-to-Username) stored in a persistent SQLite state manager. |

## System Architecture

The framework follows a modular "Collector-Processor-Analyst" pipeline:

1.  **Collectors (`modules/`):** Independent modules responsible for raw data acquisition. They handle their own error states and return standardized dictionaries.
2.  **Correlation Engine (`engine/correlation_engine.py`):** The brain of the operation. It ingests raw data, normalizes it into `Evidence` objects, and identifies relationships between entities.
3.  **State Manager (`engine/state_manager.py`):** Uses SQLite to persist investigations, allowing for long-term tracking of target evolution.
4.  **AI Agent (`engine/ai_agent.py`):** Interacts with the local Ollama instance to synthesize findings into human-readable reports.

```text
Hound-osint/
├── main.py                    # CLI Entry Point & Controller
├── modules/                   # Data Collectors
│   ├── dns.py                 # DNS & Subdomain Enumeration
│   ├── social.py              # 83-Platform Concurrent Hunter
│   ├── phone.py               # Mobile Intelligence & HLR
│   ├── shodan.py              # Infrastructure Mapping
│   └── web.py                 # WHOIS, SSL, & Tech Detection
├── engine/                    # Core Logic
│   ├── ai_agent.py            # Local LLM Integration
│   ├── correlation_engine.py  # Evidence Fusion & Graph Linking
│   └── state_manager.py       # SQLite Persistence Layer
├── models/                    # Data Schemas
│   └── evidence.py            # Evidence & Relationship Classes
└── config/                    # Configuration
    └── api_keys.template.json # Safe API Key Template﻿

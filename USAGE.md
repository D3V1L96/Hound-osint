# HOUND v2.0 | Usage Manual

This document provides a detailed guide on how to operate the HOUND v2.0 Cognitive Weapon System. All commands are executed via the main CLI entry point (`main.py`).

## 1. Global Flags

| Flag | Short | Description |
| :--- | :--- | :--- |
| `--help` | `-h` | Display the help message and exit. |
| `--full` | `-f` | Activate "Deep Scan" mode. Performs additional checks like WHOIS, SSL certificate analysis, and technology detection. |

---

## 2. Module-Specific Commands

### A. Domain Reconnaissance
Performs DNS resolution, subdomain enumeration, and infrastructure mapping.

**Basic Scan:**
```bash
python main.py --domain target.com

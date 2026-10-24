#!/usr/bin/env python3
"""
HOUND v2.0 - Autonomous OSINT Platform with Self-Starting AI
Author: Tilak Kumar (D3V1L96)
"""
import argparse
import sys
import time
import os
import subprocess
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from modules.dns import DNSRecon
from modules.web import WebRecon
from modules.email import EmailRecon
from modules.social import SocialMediaRecon
from modules.shodan import ShodanRecon
from modules.phone import PhoneRecon
from utils.report import ReportGenerator
from engine.ai_agent import AIAgent
from engine.state_manager import StateManager
from engine.correlation_engine import CorrelationEngine

class VisualEngine:
    WOLF_LOGO = r'''
          /\
         /  \__
        (  @   \___
       /         O
      /   (_____/
     /_____/   U
    '''

    def __init__(self):
        self.typing_speed = 0.02
        self.color_primary = "\033[38;2;0;102;255m"
        self.color_accent = "\033[38;2;139;92;246m"
        self.color_success = "\033[38;2;16;185;129m"
        self.color_error = "\033[38;2;239;68;68m"
        self.color_warning = "\033[38;2;245;158;11m"
        self.color_reset = "\033[0m"
        self.color_bold = "\033[1m"

    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def type_text(self, text, color=None, speed=None, end='\n'):
        if color is None: color = self.color_primary
        if speed is None: speed = self.typing_speed
        sys.stdout.write(color)
        for char in text:
            sys.stdout.write(char)
            sys.stdout.flush()
            time.sleep(speed)
        sys.stdout.write(self.color_reset + end)

    def print_logo(self):
        self.clear_screen()
        print(f"{self.color_bold}{self.color_accent}")
        print("╔══════════════════════════════════════════╗")
        print("║         HOUND OSINT FRAMEWORK v2.0      ")
        print("║      Cognitive Weapon System            ║")
        print("╚══════════════════════════════════════════╝")
        print(f"{self.color_reset}\n")
        lines = self.WOLF_LOGO.strip().split('\n')
        for line in lines:
            print(f"{' '*18}{self.color_primary}{line}{self.color_reset}")
        print("\n")

    def print_header(self, title):
        print(f"\n{self.color_bold}{self.color_primary}{'─'*60}{self.color_reset}")
        self.type_text(f"  {title}", color=self.color_bold, speed=0.01)
        print(f"{self.color_bold}{self.color_primary}{'─'*60}{self.color_reset}\n")

    def print_status(self, status, message):
        icons = {'info': '•', 'success': '✓', 'error': '✗', 'warning': ''}
        colors = {
            'info': self.color_primary, 'success': self.color_success,
            'error': self.color_error, 'warning': self.color_warning
        }
        icon = icons.get(status, '•')
        color = colors.get(status, self.color_primary)
        sys.stdout.write(f"{color}[{icon}] {message}{self.color_reset}\n")
        sys.stdout.flush()

    def print_error(self, message): self.print_status('error', message)
    def print_warning(self, message): self.print_status('warning', message)
    def print_success(self, message): self.print_status('success', message)
    def print_info(self, message): self.print_status('info', message)


class HOUNDController:
    def __init__(self):
        self.visual = VisualEngine()
        self.dns_mod = DNSRecon(self.visual)
        self.web_mod = WebRecon(self.visual)
        self.email_mod = EmailRecon(self.visual)
        self.social_mod = SocialMediaRecon(self.visual)
        self.shodan_mod = ShodanRecon(self.visual)
        self.phone_mod = PhoneRecon(self.visual) 
        self.reports = ReportGenerator(self.visual)
        self.ai = AIAgent(model="llama3.2")
        self.state_mgr = StateManager()
        self.correlator = CorrelationEngine(self.state_mgr)
        self._ai_warmed = False 

    def launch_ollama_if_needed(self):
        if self.ai.is_available(): return True
        self.visual.print_warning("Ollama service not detected...")
        self.visual.print_status('info', 'Autonomously launching local AI server...')
        try:
            subprocess.Popen(['ollama', 'serve'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
            for i in range(30):
                time.sleep(1)
                if self.ai.is_available():
                    self.visual.print_success(f"Ollama server initialized after {i+1}s")
                    return True
            self.visual.print_error("Ollama failed to start within 30s timeout")
            return False
        except FileNotFoundError:
            self.visual.print_error("Ollama executable not found. Install from ollama.com")
            return False
        except Exception as e:
            self.visual.print_error(f"Failed to launch Ollama: {e}")
            return False

    def warmup_ai_agent_once(self):
        if self._ai_warmed: return True
        self.visual.print_status('info', 'Initializing AI Neural Core...')
        if not self.ai.is_available(): return False
        try:
            import requests
            start = time.time()
            response = requests.post(f"{self.ai.base_url}/api/chat", json={"model": self.ai.model, "messages": [{"role": "user", "content": "ack"}], "stream": False, "options": {"num_ctx": 512}}, timeout=60)
            if response.status_code == 404:
                response = requests.post(f"{self.ai.base_url}/api/generate", json={"model": self.ai.model, "prompt": "ack", "stream": False, "options": {"num_ctx": 512}}, timeout=60)
            elapsed = time.time() - start
            if response.status_code == 200:
                self.visual.print_success(f"AI Agent warmed up in {elapsed:.1f}s [READY]")
                self._ai_warmed = True
                return True
            else:
                self.visual.print_error(f"AI warmup failed: HTTP {response.status_code}")
                return False
        except Exception as e:
            self.visual.print_error(f"AI warmup error: {e}")
            return False

    def run_ai_analysis(self, target: str, results: dict, recon_type: str):
        if not self.ai.is_available(): return
        self.visual.print_status('info', 'AI Analyst processing evidence...')
        summary = self.ai.analyze_evidence(target, results)
        self.visual.print_header(f"AI INTELLIGENCE BRIEF [{recon_type.upper()}]")
        for line in summary.split('\n'):
            print(f"{self.visual.color_accent}{line}{self.visual.color_reset}")
            sys.stdout.flush()
        print("\n")

    def run_domain_recon(self, domain, full=False):
        inv_id = str(uuid.uuid4())
        self.state_mgr.create_investigation(inv_id, domain)
        self.visual.print_header(f"TARGET DOMAIN: {domain}")
        results = {"target_domain": domain}
        self.visual.print_status('info', 'Initiating DNS Resolution...')
        dns_results = self.dns_mod.resolve_domain(domain)
        results['dns'] = dns_results.get('dns', [])
        results['vulnerabilities'] = dns_results.get('vulnerabilities', [])
        self.correlator.ingest_collector_output(inv_id, "dns_mod", results)
        if full:
            self.visual.print_status('info', 'Deep Scan Mode Activated...')
            results['whois'] = self.web_mod.get_whois(domain)
            results['ssl'] = self.web_mod.check_ssl(domain)
            results['headers'] = self.web_mod.http_headers(domain)
            results['tech'] = self.web_mod.technology_detection(domain)
            self.correlator.ingest_collector_output(inv_id, "web_mod", results)
        self.reports.save_report(domain, results, report_type='domain')
        self.visual.print_status('success', 'Domain Reconnaissance Complete.')
        self.run_ai_analysis(domain, results, 'domain')

    def run_ip_recon(self, ip):
        inv_id = str(uuid.uuid4())
        self.state_mgr.create_investigation(inv_id, ip)
        self.visual.print_header(f"TARGET IP: {ip}")
        results = {}
        self.visual.print_status('info', 'Performing Reverse DNS Lookup...')
        results['reverse_dns'] = self.dns_mod.reverse_dns(ip)
        self.visual.print_status('info', 'Querying Shodan Intelligence...')
        shodan_results = self.shodan_mod.search_ip(ip)
        results['shodan'] = shodan_results
        self.correlator.ingest_collector_output(inv_id, "shodan_mod", results)
        self.reports.save_report(ip, results, report_type='ip')
        self.visual.print_status('success', 'IP Reconnaissance Complete.')
        self.run_ai_analysis(ip, results, 'ip')

    def run_email_recon(self, email):
        inv_id = str(uuid.uuid4())
        self.state_mgr.create_investigation(inv_id, email)
        self.visual.print_header(f"TARGET EMAIL: {email}")
        results = {}
        self.visual.print_status('info', 'Validating Email Structure...')
        valid = self.email_mod.verify_email(email)
        results['valid'] = valid
        if valid:
            self.visual.print_status('info', 'Analyzing Domain Security...')
            try: results['security'] = self.email_mod.analyze_email_security(email)
            except AttributeError: self.visual.print_warning("Advanced security analysis unavailable.")
        self.correlator.ingest_collector_output(inv_id, "email_mod", results)
        self.reports.save_report(email, results, report_type='email')
        self.visual.print_status('success', 'Email Reconnaissance Complete.')
        self.run_ai_analysis(email, results, 'email')

    def run_username_recon(self, username):
        inv_id = str(uuid.uuid4())
        self.state_mgr.create_investigation(inv_id, username)
        self.visual.print_header(f"TARGET USERNAME: {username}")
        results = {}
        self.visual.print_status('info', 'Launching Cross-Platform Identity Hunt...')
        social_results = self.social_mod.check_profiles(username)
        results['social'] = social_results
        self.visual.print_status('info', 'Extracting GitHub Intelligence...')
        try: results['github'] = self.social_mod.github_recon(username)
        except AttributeError: self.visual.print_warning("GitHub deep dive unavailable.")
        self.correlator.ingest_collector_output(inv_id, "social_mod", results)
        self.reports.save_report(username, results, report_type='username')
        self.visual.print_status('success', 'Username Reconnaissance Complete.')
        self.run_ai_analysis(username, results, 'username')

    def run_phone_recon(self, phone_number):
        inv_id = str(uuid.uuid4())
        self.state_mgr.create_investigation(inv_id, phone_number)
        self.visual.print_header(f"TARGET PHONE: {phone_number}")
        results = {}
        self.visual.print_status('info', 'Initiating Mobile Intelligence Extraction...')
        phone_data = self.phone_mod.analyze_number(phone_number)
        results['phone'] = phone_data
        self.correlator.ingest_collector_output(inv_id, "phone_mod", results)
        self.reports.save_report(phone_number, results, report_type='phone')
        self.visual.print_status('success', 'Phone Reconnaissance Complete.')
        self.run_ai_analysis(phone_number, results, 'phone')


def main():
    parser = argparse.ArgumentParser(description='HOUND v2.0 - Advanced OSINT Platform')
    parser.add_argument('--domain', '-d', help='Target domain')
    parser.add_argument('--ip', '-i', help='Target IP address')
    parser.add_argument('--email', '-e', help='Target email address')
    parser.add_argument('--username', '-u', help='Target username')
    parser.add_argument('--phone', '-p', help='Target phone number')
    parser.add_argument('--full', '-f', action='store_true', help='Full deep scan')
    args = parser.parse_args()

    hound = HOUNDController()
    hound.visual.print_logo()
    server_ready = hound.launch_ollama_if_needed()
    ai_ready = hound.warmup_ai_agent_once() if server_ready else False
    if ai_ready: hound.visual.type_text(">> NEURAL CORE ONLINE...", color=hound.visual.color_success)
    hound.visual.type_text(">> HOUND READY FOR HOWLING...", color=hound.visual.color_accent)
    print("\n")

    if not any([args.domain, args.ip, args.email, args.username, args.phone]):
        hound.visual.type_text("ERROR: No target specified. Use --help", color=hound.visual.color_error)
        sys.exit(1)

    try:
        if args.domain: hound.run_domain_recon(args.domain, full=args.full)
        if args.ip: hound.run_ip_recon(args.ip)
        if args.email: hound.run_email_recon(args.email)
        if args.username: hound.run_username_recon(args.username)
        if args.phone: hound.run_phone_recon(args.phone)
    except KeyboardInterrupt:
        print("\n")
        hound.visual.type_text(">> OPERATION ABORTED", color=hound.visual.color_error)
    except Exception as e:
        hound.visual.print_error(f"Critical Error: {e}")

    print("\n")
    hound.visual.type_text(">> HOUND STANDING BY...", color=hound.visual.color_accent)


if __name__ == '__main__':
    main()




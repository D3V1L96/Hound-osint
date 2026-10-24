import requests, ssl, socket
class WebRecon:
    def __init__(self, display):
        self.display = display
    def get_whois(self, domain):
        try:
            import whois
            w = whois.whois(domain)
            self.display.print_success("WHOIS retrieved")
            return {'domain': w.domain_name, 'registrar': w.registrar}
        except Exception as e:
            self.display.print_error(f"WHOIS failed: {e}")
            return None
    def check_ssl(self, domain):
        try:
            context = ssl.create_default_context()
            conn = context.wrap_socket(socket.socket(), server_hostname=domain)
            conn.settimeout(5)
            conn.connect((domain, 443))
            cert = conn.getpeercert()
            conn.close()
            self.display.print_success("SSL retrieved")
            return cert
        except Exception as e:
            self.display.print_error(f"SSL failed: {e}")
            return None
    def http_headers(self, url):
        try:
            if not url.startswith('http'): url = f"https://{url}"
            response = requests.head(url, timeout=10, allow_redirects=True)
            self.display.print_success(f"Headers retrieved from {url}")
            return dict(response.headers)
        except Exception as e:
            self.display.print_error(f"HTTP failed: {e}")
            return None
    def technology_detection(self, url):
        return []

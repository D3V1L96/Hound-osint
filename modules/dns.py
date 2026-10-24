import socket
try:
    import dns.resolver
    DNS_AVAILABLE = True
except ImportError:
    DNS_AVAILABLE = False

class DNSRecon:
    def __init__(self, display):
        self.display = display

    def resolve_domain(self, domain):
        results = []
        try:
            if DNS_AVAILABLE:
                resolver = dns.resolver.Resolver()
                resolver.timeout = 5
                answers = resolver.resolve(domain, 'A')
                for rdata in answers:
                    results.append({'type': 'A', 'value': str(rdata)})
                    self.display.print_success(f"A Record: {rdata}")
            else:
                ip = socket.gethostbyname(domain)
                results.append({'type': 'A', 'value': ip})
                self.display.print_success(f"A Record: {ip}")
        except Exception as e:
            self.display.print_error(f"DNS resolution failed: {e}")
        return {"dns": results, "target_domain": domain, "vulnerabilities": []}

    def reverse_dns(self, ip):
        try:
            hostname = socket.gethostbyaddr(ip)[0]
            self.display.print_success(f"Reverse DNS: {ip} -> {hostname}")
            return hostname
        except Exception as e:
            self.display.print_error(f"Reverse DNS failed: {e}")
            return None


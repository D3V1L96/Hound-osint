"""Shodan API Integration Module"""
import os

class ShodanRecon:
    """Shodan reconnaissance operations"""
    
    def __init__(self, display, api_key=None):
        self.display = display
        # Using the key provided in your snippet
        self.api_key = api_key or os.getenv('SHODAN_API_KEY') or '18XmwBLqCoulMtwydJO7YJK6L7jZ4cyp'
        self.shodan_api = None
        
        if self.api_key:
            try:
                from shodan import Shodan
                self.shodan_api = Shodan(self.api_key)
            except ImportError:
                self.display.print_warning(
                    "Shodan library not installed. Install with: pip install shodan"
                )
    
    def search_ip(self, ip):
        """Search IP on Shodan"""
        if not self.shodan_api:
            if not self.api_key:
                self.display.print_warning(
                    "Shodan API key not configured."
                )
            return None
        
        try:
            host = self.shodan_api.host(ip)
            
            info = {
                'ip': host.get('ip_str'),
                'ports': host.get('ports', []),
                'os': host.get('os', 'Unknown'),
                'country': host.get('country_name', 'Unknown'),
                'city': host.get('city', 'Unknown'),
                'org': host.get('org', 'Unknown'),
                'isp': host.get('isp', 'Unknown'),
                'hostnames': host.get('hostnames', []),
                'vulns': host.get('vulns', [])
            }
            
            self.display.print_success(f"Shodan data retrieved for {ip}")
            self.display.print_info(f"Open ports: {', '.join(map(str, info['ports']))}")
            
            if info['vulns']:
                self.display.print_warning(f"Vulnerabilities found: {', '.join(info['vulns'])}")
            
            return info
        except Exception as e:
            self.display.print_error(f"Shodan search failed: {e}")
            return None
    
    def search_domain(self, domain):
        """Search domain on Shodan"""
        if not self.shodan_api:
            return None
        
        try:
            results = self.shodan_api.search(f'hostname:{domain}')
            matches = []
            for match in results.get('matches', [])[:10]:
                match_info = {
                    'ip': match.get('ip_str'),
                    'port': match.get('port'),
                    'product': match.get('product'),
                    'version': match.get('version'),
                    'country': match.get('location', {}).get('country_name', 'Unknown')
                }
                matches.append(match_info)
            
            self.display.print_success(f"Found {len(matches)} Shodan results for {domain}")
            return matches
        except Exception as e:
            self.display.print_error(f"Shodan domain search failed: {e}")
            return None
    
    def search_query(self, query):
        """Custom Shodan search query"""
        if not self.shodan_api:
            return None
        
        try:
            results = self.shodan_api.search(query)
            summary = {'total': results.get('total', 0), 'matches': []}
            
            for match in results.get('matches', [])[:5]:
                match_info = {
                    'ip': match.get('ip_str'),
                    'port': match.get('port'),
                    'product': match.get('product'),
                    'version': match.get('version')
                }
                summary['matches'].append(match_info)
            
            self.display.print_success(f"Query returned {summary['total']} results")
            return summary
        except Exception as e:
            self.display.print_error(f"Shodan query failed: {e}")
            return None

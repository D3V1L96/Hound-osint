import re, json, time
from typing import Dict, Any, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


class SocialMediaRecon:
    DEFAULT_PLATFORMS = {
        'github': {'url': 'https://github.com/{}', 'check': 'status_200', 'category': 'dev'},
        'gitlab': {'url': 'https://gitlab.com/{}', 'check': 'status_200', 'category': 'dev'},
        'bitbucket': {'url': 'https://bitbucket.org/{}/', 'check': 'status_200', 'category': 'dev'},
        'codepen': {'url': 'https://codepen.io/{}', 'check': 'status_200', 'category': 'dev'},
        'replit': {'url': 'https://replit.com/@{}', 'check': 'status_200', 'category': 'dev'},
        'kaggle': {'url': 'https://www.kaggle.com/{}', 'check': 'status_200', 'category': 'dev'},
        'npm': {'url': 'https://www.npmjs.com/~{}', 'check': 'status_200', 'category': 'dev'},
        'dockerhub': {'url': 'https://hub.docker.com/u/{}', 'check': 'status_200', 'category': 'dev'},
        'twitter': {'url': 'https://twitter.com/{}', 'check': 'status_200', 'category': 'social'},
        'instagram': {'url': 'https://www.instagram.com/{}/', 'check': 'status_200', 'category': 'social'},
        'facebook': {'url': 'https://www.facebook.com/{}', 'check': 'status_200', 'category': 'social'},
        'tiktok': {'url': 'https://www.tiktok.com/@{}', 'check': 'status_200', 'category': 'social'},
        'snapchat': {'url': 'https://www.snapchat.com/add/{}', 'check': 'status_200', 'category': 'social'},
        'threads': {'url': 'https://www.threads.net/@{}', 'check': 'status_200', 'category': 'social'},
        'mastodon': {'url': 'https://mastodon.social/@{}', 'check': 'status_200', 'category': 'social'},
        'bluesky': {'url': 'https://bsky.app/profile/{}.bsky.social', 'check': 'status_200', 'category': 'social'},
        'tumblr': {'url': 'https://{}.tumblr.com/', 'check': 'status_200', 'category': 'social'},
        'reddit': {'url': 'https://www.reddit.com/user/{}', 'check': 'custom_reddit', 'category': 'forum'},
        'stackoverflow': {'url': 'https://stackoverflow.com/users/{}', 'check': 'custom_so', 'category': 'forum'},
        'hackernews': {'url': 'https://news.ycombinator.com/user?id={}', 'check': 'custom_hn', 'category': 'forum'},
        'telegram': {'url': 'https://t.me/{}', 'check': 'status_200', 'category': 'forum'},
        '9gag': {'url': 'https://9gag.com/u/{}', 'check': 'status_200', 'category': 'forum'},
        'imgur': {'url': 'https://imgur.com/user/{}', 'check': 'status_200', 'category': 'forum'},
        'youtube': {'url': 'https://www.youtube.com/@{}', 'check': 'status_200', 'category': 'creative'},
        'vimeo': {'url': 'https://vimeo.com/{}', 'check': 'status_200', 'category': 'creative'},
        'twitch': {'url': 'https://www.twitch.tv/{}', 'check': 'status_200', 'category': 'creative'},
        'soundcloud': {'url': 'https://soundcloud.com/{}', 'check': 'status_200', 'category': 'creative'},
        'spotify': {'url': 'https://open.spotify.com/user/{}', 'check': 'status_200', 'category': 'creative'},
        'bandcamp': {'url': 'https://{}.bandcamp.com/', 'check': 'status_200', 'category': 'creative'},
        'deviantart': {'url': 'https://www.deviantart.com/{}', 'check': 'status_200', 'category': 'creative'},
        'artstation': {'url': 'https://www.artstation.com/{}', 'check': 'status_200', 'category': 'creative'},
        'behance': {'url': 'https://www.behance.net/{}', 'check': 'status_200', 'category': 'creative'},
        'dribbble': {'url': 'https://dribbble.com/{}', 'check': 'status_200', 'category': 'creative'},
        'flickr': {'url': 'https://www.flickr.com/photos/{}', 'check': 'status_200', 'category': 'creative'},
        'unsplash': {'url': 'https://unsplash.com/@{}', 'check': 'status_200', 'category': 'creative'},
        'pinterest': {'url': 'https://www.pinterest.com/{}/', 'check': 'status_200', 'category': 'creative'},
        'medium': {'url': 'https://medium.com/@{}', 'check': 'status_200', 'category': 'creative'},
        'substack': {'url': 'https://{}.substack.com/', 'check': 'status_200', 'category': 'creative'},
        'wordpress': {'url': 'https://{}.wordpress.com/', 'check': 'status_200', 'category': 'creative'},
        'linkedin': {'url': 'https://www.linkedin.com/in/{}', 'check': 'status_200', 'category': 'professional'},
        'xing': {'url': 'https://www.xing.com/profile/{}', 'check': 'status_200', 'category': 'professional'},
        'aboutme': {'url': 'https://about.me/{}', 'check': 'status_200', 'category': 'professional'},
        'crunchbase': {'url': 'https://www.crunchbase.com/person/{}', 'check': 'status_200', 'category': 'professional'},
        'angellist': {'url': 'https://angel.co/u/{}', 'check': 'status_200', 'category': 'professional'},
        'producthunt': {'url': 'https://www.producthunt.com/@{}', 'check': 'status_200', 'category': 'professional'},
        'indiehackers': {'url': 'https://www.indiehackers.com/@{}', 'check': 'status_200', 'category': 'professional'},
        'steam': {'url': 'https://steamcommunity.com/id/{}', 'check': 'status_200', 'category': 'gaming'},
        'epicgames': {'url': 'https://www.epicgames.com/id/api/redirect?displayName={}', 'check': 'status_200', 'category': 'gaming'},
        'xbox': {'url': 'https://account.xbox.com/en-us/profile?gamertag={}', 'check': 'status_200', 'category': 'gaming'},
        'roblox': {'url': 'https://www.roblox.com/user.aspx?username={}', 'check': 'status_200', 'category': 'gaming'},
        'chess': {'url': 'https://www.chess.com/member/{}', 'check': 'status_200', 'category': 'gaming'},
        'wikipedia': {'url': 'https://en.wikipedia.org/wiki/User:{}', 'check': 'status_200', 'category': 'writing'},
        'goodreads': {'url': 'https://www.goodreads.com/user/show/{}', 'check': 'status_200', 'category': 'writing'},
        'letterboxd': {'url': 'https://letterboxd.com/{}/', 'check': 'status_200', 'category': 'writing'},
        'quora': {'url': 'https://www.quora.com/profile/{}', 'check': 'status_200', 'category': 'writing'},
        'patreon': {'url': 'https://www.patreon.com/{}', 'check': 'status_200', 'category': 'writing'},
        'ko-fi': {'url': 'https://ko-fi.com/{}', 'check': 'status_200', 'category': 'writing'},
        'buymeacoffee': {'url': 'https://www.buymeacoffee.com/{}', 'check': 'status_200', 'category': 'writing'},
        'keybase': {'url': 'https://keybase.io/{}', 'check': 'status_200', 'category': 'tech'},
        'hackthebox': {'url': 'https://app.hackthebox.com/profile/{}', 'check': 'status_200', 'category': 'tech'},
        'tryhackme': {'url': 'https://tryhackme.com/p/{}', 'check': 'status_200', 'category': 'tech'},
        'bugcrowd': {'url': 'https://bugcrowd.com/{}', 'check': 'status_200', 'category': 'tech'},
        'hackerone': {'url': 'https://hackerone.com/{}', 'check': 'status_200', 'category': 'tech'},
        'ctftime': {'url': 'https://ctftime.org/user/{}', 'check': 'status_200', 'category': 'tech'},
        'ebay': {'url': 'https://www.ebay.com/usr/{}', 'check': 'status_200', 'category': 'marketplace'},
        'etsy': {'url': 'https://www.etsy.com/shop/{}', 'check': 'status_200', 'category': 'marketplace'},
        'gravatar': {'url': 'https://en.gravatar.com/{}', 'check': 'status_200', 'category': 'misc'},
        'disqus': {'url': 'https://disqus.com/by/{}/', 'check': 'status_200', 'category': 'misc'},
        'lastfm': {'url': 'https://www.last.fm/user/{}', 'check': 'status_200', 'category': 'misc'},
        'slideshare': {'url': 'https://www.slideshare.net/{}', 'check': 'status_200', 'category': 'misc'},
        'academia': {'url': 'https://independent.academia.edu/{}', 'check': 'status_200', 'category': 'misc'},
        'researchgate': {'url': 'https://www.researchgate.net/profile/{}', 'check': 'status_200', 'category': 'misc'},
        'strava': {'url': 'https://www.strava.com/athletes/{}', 'check': 'status_200', 'category': 'misc'},
        'tripadvisor': {'url': 'https://www.tripadvisor.com/members/{}', 'check': 'status_200', 'category': 'misc'},
        'meetup': {'url': 'https://www.meetup.com/members/{}', 'check': 'status_200', 'category': 'misc'},
        'instructables': {'url': 'https://www.instructables.com/member/{}/', 'check': 'status_200', 'category': 'misc'},
        'thingiverse': {'url': 'https://www.thingiverse.com/{}', 'check': 'status_200', 'category': 'misc'},
        'freelancer': {'url': 'https://www.freelancer.com/u/{}', 'check': 'status_200', 'category': 'misc'},
        'upwork': {'url': 'https://www.upwork.com/freelancers/~{}', 'check': 'status_200', 'category': 'misc'},
        'fiverr': {'url': 'https://www.fiverr.com/{}', 'check': 'status_200', 'category': 'misc'},
        'codementor': {'url': 'https://www.codementor.io/@{}', 'check': 'status_200', 'category': 'misc'},
        'adplist': {'url': 'https://adplist.org/mentors/{}', 'check': 'status_200', 'category': 'misc'},
        'calendly': {'url': 'https://calendly.com/{}', 'check': 'status_200', 'category': 'misc'},
    }

    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
    }

    def __init__(self, display, config_path=None):
        self.display = display
        if not REQUESTS_AVAILABLE:
            self.display.print_error("Requests library missing. Install: pip install requests")
            return
        if config_path and Path(config_path).exists():
            with open(config_path, 'r') as f:
                self.platforms = json.load(f)
            self.display.print_success(f"Loaded {len(self.platforms)} platforms from {config_path}")
        else:
            self.platforms = self.DEFAULT_PLATFORMS
            self.display.print_info(f"Using default {len(self.platforms)} platform configuration")

    def check_profiles(self, username, max_workers=15):
        if not REQUESTS_AVAILABLE:
            return {"error": "Requests unavailable"}
        results = {}
        found_platforms = []
        categories = {}
        self.display.print_info(f"HUNTING '{username}' ACROSS {len(self.platforms)} PLATFORMS...")
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self._check_single_platform, platform, config, username): platform
                for platform, config in self.platforms.items()
                if config.get('check') != 'unsupported'
            }
            completed = 0
            total = len(futures)
            for future in as_completed(futures):
                platform = futures[future]
                completed += 1
                try:
                    result = future.result(timeout=20)
                    results[platform] = result
                    if result.get('exists'):
                        found_platforms.append(platform)
                        cat = self.platforms[platform].get('category', 'unknown')
                        categories.setdefault(cat, []).append(platform)
                        self.display.print_success(f"[{completed}/{total}] FOUND: {platform.upper()} ({cat})")
                    elif result.get('error'):
                        self.display.print_warning(f"[{completed}/{total}] WARN: {platform.upper()}: {result['error']}")
                except Exception as e:
                    results[platform] = {'exists': False, 'error': str(e)}
        self.display.print_header(f"SOCIAL INTELLIGENCE SUMMARY: {username}")
        self.display.print_info(f"Platforms Checked: {total}")
        self.display.print_success(f"Profiles Found: {len(found_platforms)}")
        for cat, sites in sorted(categories.items()):
            self.display.print_info(f"  [{cat.upper()}] {', '.join(sites)}")
        return {
            'username': username,
            'total_checked': total,
            'profiles_found': len(found_platforms),
            'active_platforms': found_platforms,
            'categories': categories,
            'details': results
        }

    def github_recon(self, username):
        if not REQUESTS_AVAILABLE:
            return {"error": "Requests unavailable"}
        try:
            url = f"https://api.github.com/users/{username}"
            response = requests.get(url, headers=self.HEADERS, timeout=10)
            if response.status_code == 200:
                data = response.json()
                info = {
                    'login': data.get('login'), 'name': data.get('name', 'N/A'),
                    'bio': data.get('bio', 'N/A'), 'location': data.get('location', 'N/A'),
                    'company': data.get('company', 'N/A'), 'blog': data.get('blog', 'N/A'),
                    'email': data.get('email', 'N/A'), 'public_repos': data.get('public_repos', 0),
                    'followers': data.get('followers', 0), 'following': data.get('following', 0),
                    'created_at': data.get('created_at', 'N/A'), 'updated_at': data.get('updated_at', 'N/A'),
                    'profile_url': data.get('html_url')
                }
                self.display.print_success(f"GitHub profile extracted: {info['login']}")
                self.display.print_info(f"Repos: {info['public_repos']} | Followers: {info['followers']}")
                if info['location'] != 'N/A':
                    self.display.print_info(f"Location: {info['location']}")
                if info['email'] and info['email'] != 'N/A':
                    self.display.print_warning(f"Public email found: {info['email']}")
                return info
            elif response.status_code == 404:
                return {"exists": False}
            elif response.status_code == 403:
                self.display.print_warning("GitHub API rate limited.")
                return {"error": "Rate limited"}
            else:
                return {"error": f"HTTP {response.status_code}"}
        except Exception as e:
            self.display.print_error(f"GitHub recon failed: {e}")
            return {"error": str(e)}

    def _check_single_platform(self, platform, config, username):
        check_type = config.get('check', 'status_200')
        if check_type == 'unsupported':
            return {'exists': False, 'error': 'Not supported'}
        url_template = config.get('url')
        if not url_template:
            return {'exists': False, 'error': 'No URL pattern'}
        url = url_template.format(username)
        try:
            if check_type == 'custom_reddit':
                resp = requests.get(url, headers=self.HEADERS, timeout=10)
                exists = resp.status_code == 200 and 'u/' + username.lower() in resp.text.lower()
            elif check_type == 'custom_so':
                resp = requests.get(url, headers=self.HEADERS, timeout=10)
                exists = resp.status_code == 200 and ('user-profile' in resp.text.lower() or username.lower() in resp.text.lower())
            elif check_type == 'custom_hn':
                resp = requests.get(url, headers=self.HEADERS, timeout=10)
                exists = resp.status_code == 200 and 'no such user' not in resp.text.lower()
            else:
                resp = requests.head(url, headers=self.HEADERS, timeout=8, allow_redirects=True)
                exists = resp.status_code == 200
            return {
                'exists': exists, 'url': url,
                'status_code': resp.status_code if 'resp' in locals() else None,
                'category': config.get('category', 'unknown')
            }
        except requests.exceptions.Timeout:
            return {'exists': False, 'error': 'Timeout'}
        except requests.exceptions.ConnectionError:
            return {'exists': False, 'error': 'Connection failed'}
        except Exception as e:
            return {'exists': False, 'error': str(e)}

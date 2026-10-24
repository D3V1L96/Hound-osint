import re, json, time, base64
from typing import Dict, Any, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    import phonenumbers
    from phonenumbers import carrier, geocoder, timezone, number_type, PhoneNumberType
    PHONENUMBERS_AVAILABLE = True
except ImportError:
    PHONENUMBERS_AVAILABLE = False

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


class PhoneRecon:
    VOIP_PROVIDERS = {'google voice', 'textnow', 'burner', 'hushed', 'sideline', 'grasshopper', 'openphone'}

    def __init__(self, display, api_keys: Optional[Dict[str, str]] = None):
        self.display = display
        self.api_keys = api_keys or {}
        if not PHONENUMBERS_AVAILABLE:
            self.display.print_error("phonenumbers missing: pip install phonenumbers")
        if not REQUESTS_AVAILABLE:
            self.display.print_error("requests missing: pip install requests")

    def analyze_number(self, phone_str: str) -> Dict[str, Any]:
        results = {"raw_input": phone_str, "valid": False, "formatted": "", "country": "", "region": "",
                   "carrier": "", "line_type": "", "is_voip": False, "timezones": [],
                   "owner_name": None, "registered_email": None, "hlr_status": {},
                   "breach_exposure": [], "social_identities": [], "reputation": {}}
        if not PHONENUMBERS_AVAILABLE or not REQUESTS_AVAILABLE:
            return {"error": "Libraries unavailable"}
        try:
            parsed = phonenumbers.parse(phone_str, None)
            if not phonenumbers.is_valid_number(parsed):
                self.display.print_error(f"Invalid: {phone_str}"); return results
            results["valid"] = True
            results["formatted"] = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
            results["country"] = phonenumbers.region_code_for_number(parsed)
            results["region"] = geocoder.description_for_number(parsed, "en")
        except Exception as e:
            self.display.print_error(f"Parse error: {e}"); return results

        cname = carrier.name_for_number(parsed, "en") or "Unknown"
        ntype = number_type(parsed)
        tmap = {PhoneNumberType.MOBILE:"Mobile", PhoneNumberType.FIXED_LINE:"Landline",
                PhoneNumberType.VOIP:"VoIP", PhoneNumberType.UNKNOWN:"Unknown"}
        results["carrier"], results["line_type"] = cname, tmap.get(ntype, "Unknown")
        results["is_voip"] = (ntype == PhoneNumberType.VOIP or any(v in cname.lower() for v in self.VOIP_PROVIDERS))
        results["timezones"] = list(timezone.time_zones_for_number(parsed) or [])

        self.display.print_info(f"Active recon on {results['formatted']}...")
        with ThreadPoolExecutor(max_workers=5) as ex:
            futs = {ex.submit(self._resolve_owner, results["formatted"], results["country"]): "Owner",
                    ex.submit(self._find_email, results["formatted"]): "Email",
                    ex.submit(self._hlr, parsed): "HLR",
                    ex.submit(self._breaches, results["formatted"]): "Breaches",
                    ex.submit(self._social, results["formatted"], results["country"]): "Social"}
            for fut in as_completed(futs):
                lbl = futs[fut]
                try:
                    d = fut.result(timeout=15); k = lbl.lower()
                    results[k] = d
                    if lbl=="Owner" and d: self.display.print_success(f"OWNER: {d}")
                    elif lbl=="Email" and d: self.display.print_warning(f"EMAIL: {d}")
                    elif lbl=="HLR" and d.get("status")=="active": self.display.print_success("HLR: ACTIVE")
                    elif lbl=="Breaches" and d: self.display.print_warning(f"{len(d)} breach(es)")
                except Exception as e:
                    self.display.print_warning(f"{lbl} failed: {e}"); results[k] = None if k in ["owner","email"] else []

        sc = self._risk(results); results["reputation"] = {"spam_score": sc}
        if sc>70: self.display.print_warning(f"HIGH RISK: {sc}/100")
        elif sc>40: self.display.print_warning(f"MODERATE RISK: {sc}/100")
        else: self.display.print_success(f"LOW RISK: {sc}/100")

        self.display.print_header(f"MOBILE INTEL: {results['formatted']}")
        self.display.print_info(f"{results['country']} | {results['region']} | {results['carrier']} | {results['line_type']}")
        if results.get("owner"): self.display.print_success(f"Owner: {results['owner']}")
        if results.get("email"): self.display.print_warning(f"Email: {results['email']}")
        if results["is_voip"]: self.display.print_warning("VOIP DETECTED")
        return results

    def _resolve_owner(self, num, cc):
        if "truecaller" in self.api_keys:
            try:
                r = requests.get(f"https://api.truecaller.com/v1/search?phone={num}&countryCode={cc}",
                                 headers={"Authorization":f"Bearer {self.api_keys['truecaller']}"}, timeout=10)
                if r.status_code==200 and r.json().get("data"): return r.json()["data"][0].get("name")
            except: pass
        s = self._social(num, cc)
        return s[0]["name"] if s and s[0].get("name") else None

    def _find_email(self, num):
        emails = []
        for b in self._breaches(num):
            emails.extend(b.get("associated_emails", []))
        return emails[0] if emails else None

    def _hlr(self, p):
        res = {"status":"unknown","ported":False,"roaming":False}
        if "numverify" in self.api_keys:
            try:
                r = requests.get(f"https://api.numverify.com/v1/validate/{phonenumbers.format_number(p, phonenumbers.PhoneNumberFormat.E164)}",
                                 params={"access_key":self.api_keys["numverify"]}, timeout=10)
                if r.status_code==200:
                    d=r.json(); res["status"]="active" if d.get("valid") else "inactive"
                    res["ported"]=d.get("carrier","")!=carrier.name_for_number(p,"en")
            except: pass
        return res

    def _breaches(self, num):
        bs=[]
        try:
            r=requests.get(f"https://api.github.com/search/code?q={num}",headers={"Accept":"application/vnd.github.v3+json"},timeout=8)
            if r.status_code==200:
                cnt=r.json().get("total_count",0); emls=[]
                if cnt>0:
                    for it in r.json().get("items",[])[:5]:
                        cr=requests.get(it["git_url"],timeout=5)
                        if cr.status_code==200:
                            c=base64.b64decode(cr.json()["content"]).decode()
                            emls.extend(re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',c))
                if cnt>0: bs.append({"source":"GitHub","exposures":cnt,"risk":"HIGH" if cnt>5 else "MEDIUM","associated_emails":list(set(emls))[:3]})
        except: pass
        return bs

    def _social(self, num, cc):
        ids=[]
        if "truecaller" in self.api_keys:
            try:
                r=requests.get(f"https://api.truecaller.com/v1/search?phone={num}&countryCode={cc}",
                               headers={"Authorization":f"Bearer {self.api_keys['truecaller']}"},timeout=10)
                if r.status_code==200 and r.json().get("data"):
                    for e in r.json()["data"]: ids.append({"platform":"Truecaller","name":e.get("name",""),"score":e.get("score",0)})
            except: pass
        return ids

    def _risk(self, r):
        sc=0
        if r["is_voip"]: sc+=30
        sc+=min(len(r.get("breaches",[]))*15,40)
        h=r.get("hlr",{})
        if h.get("ported"): sc+=10
        if r.get("owner") and r.get("email"): sc-=20
        if not r.get("social") and r["line_type"]=="Mobile": sc+=10
        return max(0,min(sc,100))

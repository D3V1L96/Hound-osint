# engine/correlation_engine.py
"""Advanced Evidence Correlation & Intelligence Fusion Engine"""
import hashlib
import json
from typing import Dict, Any, List, Tuple
from models.evidence import Evidence, Relationship, EntityType, ConfidenceLevel
from engine.state_manager import StateManager


class CorrelationEngine:
    """Fuses raw collector output into actionable intelligence graph"""

    def __init__(self, state_mgr: StateManager):
        self.state_mgr = state_mgr

    def ingest_collector_output(self, investigation_id: str, source: str, raw_data: Dict[str, Any]) -> Tuple[List[Evidence], List[Relationship]]:
        evidences: List[Evidence] = []
        relationships: List[Relationship] = []

        try:
            if source == "dns_mod":
                evidences, relationships = self._process_dns(investigation_id, raw_data)
            elif source == "shodan_mod":
                evidences, relationships = self._process_shodan(investigation_id, raw_data)
            elif source == "social_mod":
                evidences, relationships = self._process_social(investigation_id, raw_data)
            elif source == "email_mod":
                evidences, relationships = self._process_email(investigation_id, raw_data)
            elif source == "web_mod":
                evidences, relationships = self._process_web(investigation_id, raw_data)
            elif source == "phone_mod":
                evidences, relationships = self._process_phone(investigation_id, raw_data)

            # Persist atomically
            for ev in evidences:
                self.state_mgr.save_evidence(ev)
            for rel in relationships:
                self.state_mgr.save_relationship(rel)

            return evidences, relationships

        except Exception as e:
            print(f"[CORRELATION ERROR] Failed to ingest {source}: {e}")
            import traceback
            traceback.print_exc()
            return [], []

    def _process_dns(self, inv_id: str, data: Any) -> Tuple[List[Evidence], List[Relationship]]:
        evidences, relationships = [], []
        
        # ROBUST DATA EXTRACTION
        dns_records = []
        domain_val = ""
        
        if isinstance(data, dict):
            dns_records = data.get("dns", [])
            domain_val = data.get("target_domain", "")
        elif isinstance(data, list):
            # Fallback if main.py passed a raw list
            dns_records = data
        
        for record in dns_records:
            # CRITICAL FIX: Ensure record is a dict before calling .get()
            if not isinstance(record, dict):
                continue
                
            rtype = record.get("type", "")
            value = record.get("value", "")
            
            if not rtype or not value:
                continue

            etype = EntityType.IP_ADDRESS if rtype == "A" else EntityType.DOMAIN
            conf = ConfidenceLevel.VERIFIED if rtype == "A" else ConfidenceLevel.HIGH

            ev = Evidence(
                investigation_id=inv_id, source="dns_mod",
                entity_type=etype, value=value,
                metadata={"record_type": rtype},
                confidence=conf, raw_data_hash=self._hash(record)
            )
            evidences.append(ev)

            if rtype == "A" and domain_val:
                domain_ev = Evidence(
                    investigation_id=inv_id, source="dns_mod",
                    entity_type=EntityType.DOMAIN, value=domain_val,
                    confidence=ConfidenceLevel.VERIFIED
                )
                evidences.append(domain_ev)
                relationships.append(Relationship(
                    source_entity_id=domain_ev.id, target_entity_id=ev.id,
                    relationship_type="resolves_to",
                    evidence_ids=[domain_ev.id, ev.id],
                    confidence=ConfidenceLevel.VERIFIED
                ))
        return evidences, relationships

    def _process_shodan(self, inv_id: str, data: dict) -> Tuple[List[Evidence], List[Relationship]]:
        evidences, relationships = [], []
        shodan = data.get("shodan", {})
        if not shodan or not shodan.get("ip"):
            return evidences, relationships

        ip_ev = Evidence(
            investigation_id=inv_id, source="shodan_mod",
            entity_type=EntityType.IP_ADDRESS, value=shodan["ip"],
            metadata={"ports": shodan.get("ports", []), "org": shodan.get("org", "")},
            confidence=ConfidenceLevel.HIGH, raw_data_hash=self._hash(shodan)
        )
        evidences.append(ip_ev)

        org_val = shodan.get("org")
        if org_val and org_val != "Unknown":
            org_ev = Evidence(
                investigation_id=inv_id, source="shodan_mod",
                entity_type=EntityType.ORGANIZATION, value=org_val,
                confidence=ConfidenceLevel.MEDIUM
            )
            evidences.append(org_ev)
            relationships.append(Relationship(
                source_entity_id=ip_ev.id, target_entity_id=org_ev.id,
                relationship_type="hosted_by",
                evidence_ids=[ip_ev.id, org_ev.id],
                confidence=ConfidenceLevel.MEDIUM
            ))
        return evidences, relationships

    def _process_social(self, inv_id: str, data: dict) -> Tuple[List[Evidence], List[Relationship]]:
        evidences, relationships = [], []
        social_data = data.get("social", {})
        github_data = data.get("github", {})
        username = social_data.get("username", "")

        details = social_data.get("details", {})
        for platform in social_data.get("active_platforms", []):
            plat_info = details.get(platform, {})
            ev = Evidence(
                investigation_id=inv_id, source="social_mod",
                entity_type=EntityType.USERNAME, value=username,
                metadata={"platform": platform, "url": plat_info.get("url"),
                          "category": plat_info.get("category", "unknown")},
                confidence=ConfidenceLevel.VERIFIED, raw_data_hash=self._hash(platform)
            )
            evidences.append(ev)

        if github_data and github_data.get("login"):
            gh_ev = Evidence(
                investigation_id=inv_id, source="social_mod",
                entity_type=EntityType.USERNAME, value=github_data["login"],
                metadata={"platform": "github", "bio": github_data.get("bio", "")},
                confidence=ConfidenceLevel.VERIFIED
            )
            evidences.append(gh_ev)

            email_val = github_data.get("email")
            if email_val and email_val != "N/A":
                em_ev = Evidence(
                    investigation_id=inv_id, source="social_mod",
                    entity_type=EntityType.EMAIL, value=email_val,
                    metadata={"source_platform": "github"},
                    confidence=ConfidenceLevel.HIGH
                )
                evidences.append(em_ev)
                relationships.append(Relationship(
                    source_entity_id=gh_ev.id, target_entity_id=em_ev.id,
                    relationship_type="owns",
                    evidence_ids=[gh_ev.id, em_ev.id],
                    confidence=ConfidenceLevel.HIGH
                ))

            loc_val = github_data.get("location")
            if loc_val and loc_val != "N/A":
                loc_ev = Evidence(
                    investigation_id=inv_id, source="social_mod",
                    entity_type=EntityType.ORGANIZATION, value=loc_val,
                    metadata={"source_platform": "github", "type": "location"},
                    confidence=ConfidenceLevel.MEDIUM
                )
                evidences.append(loc_ev)
                relationships.append(Relationship(
                    source_entity_id=gh_ev.id, target_entity_id=loc_ev.id,
                    relationship_type="located_in",
                    evidence_ids=[gh_ev.id, loc_ev.id],
                    confidence=ConfidenceLevel.MEDIUM
                ))
        return evidences, relationships

    def _process_email(self, inv_id: str, data: dict) -> Tuple[List[Evidence], List[Relationship]]:
        evidences, relationships = [], []
        email_val = ""
        if data.get("valid"):
            for key, val in data.items():
                if isinstance(val, str) and "@" in val:
                    email_val = val; break
        if email_val:
            local, domain = email_val.rsplit("@", 1)
            em_ev = Evidence(
                investigation_id=inv_id, source="email_mod",
                entity_type=EntityType.EMAIL, value=email_val,
                metadata=data.get("security", {}),
                confidence=ConfidenceLevel.HIGH
            )
            evidences.append(em_ev)
            dom_ev = Evidence(
                investigation_id=inv_id, source="email_mod",
                entity_type=EntityType.DOMAIN, value=domain,
                confidence=ConfidenceLevel.VERIFIED
            )
            evidences.append(dom_ev)
            relationships.append(Relationship(
                source_entity_id=em_ev.id, target_entity_id=dom_ev.id,
                relationship_type="registered_at",
                evidence_ids=[em_ev.id, dom_ev.id],
                confidence=ConfidenceLevel.VERIFIED
            ))
        return evidences, relationships

    def _process_web(self, inv_id: str, data: dict) -> Tuple[List[Evidence], List[Relationship]]:
        evidences, relationships = [], []
        ssl = data.get("ssl", {})
        if ssl and ssl.get("issuer"):
            issuer = ssl["issuer"].get("O", ssl["issuer"].get("CN", ""))
            if issuer and issuer != "Unknown":
                org_ev = Evidence(
                    investigation_id=inv_id, source="web_mod",
                    entity_type=EntityType.ORGANIZATION, value=issuer,
                    metadata={"cert_issuer": True},
                    confidence=ConfidenceLevel.HIGH
                )
                evidences.append(org_ev)
        return evidences, relationships

    def _process_phone(self, inv_id: str, data: dict) -> Tuple[List[Evidence], List[Relationship]]:
        evidences, relationships = [], []
        pd = data.get("phone", {})
        if not pd.get("valid"):
            return evidences, relationships

        phone_ev = Evidence(
            investigation_id=inv_id, source="phone_mod",
            entity_type=EntityType.PHONE_NUMBER, value=pd["formatted"],
            metadata={
                "carrier": pd.get("carrier"), "line_type": pd.get("line_type"),
                "is_voip": pd.get("is_voip"), "hlr_status": pd.get("hlr_status"),
                "spam_score": pd.get("reputation", {}).get("spam_score"),
                "owner_name": pd.get("owner_name"),
                "registered_email": pd.get("registered_email")
            },
            confidence=ConfidenceLevel.HIGH if not pd.get("is_voip") else ConfidenceLevel.MEDIUM,
            raw_data_hash=self._hash(pd)
        )
        evidences.append(phone_ev)

        if pd.get("owner_name"):
            person_ev = Evidence(
                investigation_id=inv_id, source="phone_mod",
                entity_type=EntityType.USERNAME, value=pd["owner_name"],
                metadata={"source": "phone_reverse_lookup", "type": "person"},
                confidence=ConfidenceLevel.HIGH
            )
            evidences.append(person_ev)
            relationships.append(Relationship(
                source_entity_id=phone_ev.id, target_entity_id=person_ev.id,
                relationship_type="owned_by",
                evidence_ids=[phone_ev.id, person_ev.id],
                confidence=ConfidenceLevel.HIGH
            ))

        if pd.get("registered_email"):
            email_ev = Evidence(
                investigation_id=inv_id, source="phone_mod",
                entity_type=EntityType.EMAIL, value=pd["registered_email"],
                metadata={"source": "phone_registration", "verified": True},
                confidence=ConfidenceLevel.HIGH
            )
            evidences.append(email_ev)
            relationships.append(Relationship(
                source_entity_id=phone_ev.id, target_entity_id=email_ev.id,
                relationship_type="registered_with",
                evidence_ids=[phone_ev.id, email_ev.id],
                confidence=ConfidenceLevel.HIGH
            ))

        if pd.get("carrier") and pd["carrier"] != "Unknown":
            carrier_ev = Evidence(
                investigation_id=inv_id, source="phone_mod",
                entity_type=EntityType.ORGANIZATION, value=pd["carrier"],
                metadata={"type": "telecom_carrier"},
                confidence=ConfidenceLevel.MEDIUM
            )
            evidences.append(carrier_ev)
            relationships.append(Relationship(
                source_entity_id=phone_ev.id, target_entity_id=carrier_ev.id,
                relationship_type="served_by",
                evidence_ids=[phone_ev.id, carrier_ev.id],
                confidence=ConfidenceLevel.MEDIUM
            ))
        return evidences, relationships

    @staticmethod
    def _hash(data: Any) -> str:
        return hashlib.sha256(json.dumps(data, sort_keys=True, default=str).encode()).hexdigest()[:16]
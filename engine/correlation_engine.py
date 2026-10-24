import hashlib
import json
from typing import Dict, Any, List, Tuple
from models.evidence import Evidence, Relationship, EntityType, ConfidenceLevel
from engine.state_manager import StateManager

class CorrelationEngine:
    def __init__(self, state_mgr: StateManager):
        self.state_mgr = state_mgr

    def ingest_collector_output(self, investigation_id: str, source: str, raw_data: Dict[str, Any]) -> Tuple[List[Evidence], List[Relationship]]:
        evidences, relationships = [], []
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

            for ev in evidences:
                self.state_mgr.save_evidence(ev)
            for rel in relationships:
                self.state_mgr.save_relationship(rel)
            return evidences, relationships
        except Exception as e:
            print(f"[CORRELATION ERROR] {source}: {e}")
            import traceback; traceback.print_exc()
            return [], []

    def _process_dns(self, inv_id: str, data: Any) -> Tuple[List[Evidence], List[Relationship]]:
        evidences, relationships = [], []
        dns_records = []
        domain_val = ""

        # BULLETPROOF TYPE CHECKING
        if isinstance(data, dict):
            dns_records = data.get("dns", [])
            domain_val = data.get("target_domain", "")
        elif isinstance(data, list):
            dns_records = data

        for record in dns_records:
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

    def _process_shodan(self, inv_id, data): return [], []
    def _process_social(self, inv_id, data): return [], []
    def _process_email(self, inv_id, data): return [], []
    def _process_web(self, inv_id, data): return [], []
    def _process_phone(self, inv_id, data): return [], []

    @staticmethod
    def _hash(data):
        return hashlib.sha256(json.dumps(data, sort_keys=True, default=str).encode()).hexdigest()[:16]

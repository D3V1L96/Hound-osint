from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum

class ConfidenceLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERIFIED = "verified"

class EntityType(str, Enum):
    DOMAIN = "domain"
    IP_ADDRESS = "ip_address"
    EMAIL = "email"
    USERNAME = "username"
    ORGANIZATION = "organization"
    
    PHONE_NUMBER = "phone_number"

class Evidence(BaseModel):
    id: str = Field(default_factory=lambda: f"ev_{datetime.now().timestamp()}")
    investigation_id: str
    source: str
    entity_type: EntityType
    value: str
    metadata: Dict[str, Any] = {}
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    timestamp: datetime = Field(default_factory=datetime.now)
    raw_data_hash: Optional[str] = None

class Relationship(BaseModel):
    source_entity_id: str
    target_entity_id: str
    relationship_type: str
    evidence_ids: List[str] = []
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM


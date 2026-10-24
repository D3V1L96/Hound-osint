# engine/state_manager.py
import sqlite3
import json
from datetime import datetime
from typing import List, Optional
from models.evidence import Evidence, Relationship

class StateManager:
    def __init__(self, db_path: str = "hound_state.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''CREATE TABLE IF NOT EXISTS investigations (
            id TEXT PRIMARY KEY,
            target TEXT,
            status TEXT,
            created_at TIMESTAMP,
            completed_at TIMESTAMP
        )''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS evidence (
            id TEXT PRIMARY KEY,
            investigation_id TEXT,
            source TEXT,
            entity_type TEXT,
            value TEXT,
            metadata TEXT,
            confidence TEXT,
            timestamp TIMESTAMP,
            raw_data_hash TEXT,
            FOREIGN KEY(investigation_id) REFERENCES investigations(id)
        )''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS relationships (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_entity_id TEXT,
            target_entity_id TEXT,
            relationship_type TEXT,
            evidence_ids TEXT,
            confidence TEXT,
            UNIQUE(source_entity_id, target_entity_id, relationship_type)
        )''')
        
        # Indexes for fast correlation queries
        c.execute('CREATE INDEX IF NOT EXISTS idx_evidence_value ON evidence(value)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_evidence_investigation ON evidence(investigation_id)')
        
        conn.commit()
        conn.close()

    def save_evidence(self, evidence: Evidence):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""INSERT OR REPLACE INTO evidence VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                  (evidence.id, evidence.investigation_id, evidence.source, 
                   evidence.entity_type.value, evidence.value, json.dumps(evidence.metadata),
                   evidence.confidence.value, evidence.timestamp.isoformat(), 
                   evidence.raw_data_hash))
        conn.commit()
        conn.close()

    def save_relationship(self, rel: Relationship):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""INSERT OR IGNORE INTO relationships 
                     (source_entity_id, target_entity_id, relationship_type, evidence_ids, confidence)
                     VALUES (?, ?, ?, ?, ?)""",
                  (rel.source_entity_id, rel.target_entity_id, rel.relationship_type,
                   json.dumps(rel.evidence_ids), rel.confidence.value))
        conn.commit()
        conn.close()

    def get_related_entities(self, entity_value: str) -> List[dict]:
        """Find all entities connected to a given value"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""
            SELECT r.relationship_type, e2.value, e2.entity_type, r.confidence
            FROM relationships r
            JOIN evidence e1 ON r.source_entity_id = e1.id
            JOIN evidence e2 ON r.target_entity_id = e2.id
            WHERE e1.value = ? OR e2.value = ?
        """, (entity_value, entity_value))
        results = [dict(zip(['relationship', 'value', 'type', 'confidence'], row)) for row in c.fetchall()]
        conn.close()
        return results
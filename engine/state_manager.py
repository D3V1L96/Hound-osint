import sqlite3
import json
from datetime import datetime

class StateManager:
    def __init__(self, db_path: str = "hound_state.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS investigations (
            id TEXT PRIMARY KEY, target TEXT, status TEXT,
            created_at TIMESTAMP, completed_at TIMESTAMP)''')
        c.execute('''CREATE TABLE IF NOT EXISTS evidence (
            id TEXT PRIMARY KEY, investigation_id TEXT, source TEXT,
            entity_type TEXT, value TEXT, metadata TEXT, confidence TEXT,
            timestamp TIMESTAMP, raw_data_hash TEXT,
            FOREIGN KEY(investigation_id) REFERENCES investigations(id))''')
        c.execute('''CREATE TABLE IF NOT EXISTS relationships (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_entity_id TEXT, target_entity_id TEXT,
            relationship_type TEXT, evidence_ids TEXT, confidence TEXT,
            UNIQUE(source_entity_id, target_entity_id, relationship_type))''')
        c.execute('CREATE INDEX IF NOT EXISTS idx_evidence_value ON evidence(value)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_evidence_inv ON evidence(investigation_id)')
        conn.commit()
        conn.close()

    def create_investigation(self, inv_id: str, target: str):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO investigations VALUES (?, ?, ?, ?, ?)",
                  (inv_id, target, 'active', datetime.now(), None))
        conn.commit()
        conn.close()

    def save_evidence(self, evidence):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""INSERT OR REPLACE INTO evidence VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                  (evidence.id, evidence.investigation_id, evidence.source,
                   evidence.entity_type.value, evidence.value, json.dumps(evidence.metadata),
                   evidence.confidence.value, evidence.timestamp.isoformat(),
                   evidence.raw_data_hash))
        conn.commit()
        conn.close()

    def save_relationship(self, rel):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""INSERT OR IGNORE INTO relationships
                     (source_entity_id, target_entity_id, relationship_type, evidence_ids, confidence)
                     VALUES (?, ?, ?, ?, ?)""",
                  (rel.source_entity_id, rel.target_entity_id, rel.relationship_type,
                   json.dumps(rel.evidence_ids), rel.confidence.value))
        conn.commit()
        conn.close()

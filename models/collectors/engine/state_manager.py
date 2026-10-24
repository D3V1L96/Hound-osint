# engine/state_manager.py
import sqlite3
import json
from datetime import datetime
from typing import List, Optional
from models.evidence import Evidence

class StateManager:
    def __init__(self, db_path: str = "hound_state.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Investigations Table
        c.execute('''CREATE TABLE IF NOT EXISTS investigations (
            id TEXT PRIMARY KEY,
            target TEXT,
            status TEXT,
            created_at TIMESTAMP,
            completed_at TIMESTAMP
        )''')
        
        # Evidence Table
        c.execute('''CREATE TABLE IF NOT EXISTS evidence (
            id TEXT PRIMARY KEY,
            investigation_id TEXT,
            source TEXT,
            type TEXT,
            value TEXT,
            metadata TEXT,
            confidence TEXT,
            timestamp TIMESTAMP,
            raw_data TEXT,
            FOREIGN KEY(investigation_id) REFERENCES investigations(id)
        )''')
        
        conn.commit()
        conn.close()

    def create_investigation(self, inv_id: str, target: str):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("INSERT INTO investigations VALUES (?, ?, ?, ?, ?)",
                  (inv_id, target, 'active', datetime.now(), None))
        conn.commit()
        conn.close()

    def save_evidence(self, evidence: Evidence):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""INSERT INTO evidence VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                  (evidence.id, evidence.investigation_id, evidence.source, 
                   evidence.type.value, evidence.value, json.dumps(evidence.metadata),
                   evidence.confidence.value, evidence.timestamp, 
                   json.dumps(evidence.raw_data) if evidence.raw_data else None))
        conn.commit()
        conn.close()

    def get_investigation_evidence(self, inv_id: str) -> List[Evidence]:
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT * FROM evidence WHERE investigation_id=?", (inv_id,))
        rows = c.fetchall()
        conn.close()
        
        evidences = []
        for row in rows:
            # Reconstruct Evidence object from DB row
            ev = Evidence(
                id=row[0], investigation_id=row[1], source=row[2],
                type=row[3], value=row[4], metadata=json.loads(row[5]),
                confidence=row[6], timestamp=row[7],
                raw_data=json.loads(row[8]) if row[8] else None
            )
            evidences.append(ev)
        return evidences
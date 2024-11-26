"""Contact database management for email marketing."""
import sqlite3
from typing import Dict, List, Optional
from datetime import datetime
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class ContactDatabase:
    """Manages contact information and tracking."""
    
    def __init__(self, db_path: str = "contacts.db"):
        """Initialize the contact database."""
        self.db_path = db_path
        self.setup_logging()
        self.initialize_database()
    
    def setup_logging(self):
        """Set up logging configuration."""
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
    
    def initialize_database(self):
        """Create database tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Contacts table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS contacts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE NOT NULL,
                    name TEXT,
                    company TEXT,
                    phone TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'active',
                    custom_data TEXT
                )
            """)
            
            # Email interactions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS email_interactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    contact_id INTEGER,
                    email_id TEXT,
                    interaction_type TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT,
                    FOREIGN KEY (contact_id) REFERENCES contacts (id)
                )
            """)
            
            # Sequence tracking table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sequence_tracking (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    contact_id INTEGER,
                    sequence_id TEXT,
                    current_step INTEGER,
                    status TEXT,
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_email_date TIMESTAMP,
                    next_email_date TIMESTAMP,
                    FOREIGN KEY (contact_id) REFERENCES contacts (id)
                )
            """)
            
            # A/B test results table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ab_test_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    contact_id INTEGER,
                    test_id TEXT,
                    variant TEXT,
                    result TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (contact_id) REFERENCES contacts (id)
                )
            """)
            
            conn.commit()
    
    def add_contact(self, contact_data: Dict) -> int:
        """Add a new contact to the database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            try:
                custom_data = contact_data.get('custom_data', {})
                cursor.execute("""
                    INSERT INTO contacts (
                        email, name, company, phone, custom_data
                    ) VALUES (?, ?, ?, ?, ?)
                """, (
                    contact_data['email'],
                    contact_data.get('name'),
                    contact_data.get('company'),
                    contact_data.get('phone'),
                    json.dumps(custom_data)
                ))
                
                contact_id = cursor.lastrowid
                logger.info(f"Added new contact: {contact_data['email']}")
                return contact_id
                
            except sqlite3.IntegrityError:
                logger.warning(f"Contact already exists: {contact_data['email']}")
                cursor.execute(
                    "SELECT id FROM contacts WHERE email = ?",
                    (contact_data['email'],)
                )
                return cursor.fetchone()[0]
    
    def get_contact(self, contact_id: int) -> Optional[Dict]:
        """Get contact information by ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM contacts WHERE id = ?",
                (contact_id,)
            )
            row = cursor.fetchone()
            
            if row:
                columns = [desc[0] for desc in cursor.description]
                contact = dict(zip(columns, row))
                contact['custom_data'] = json.loads(contact['custom_data'])
                return contact
            return None
    
    def update_contact(self, contact_id: int, updates: Dict) -> bool:
        """Update contact information."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            set_clause = []
            values = []
            
            for key, value in updates.items():
                if key in ['email', 'name', 'company', 'phone', 'status']:
                    set_clause.append(f"{key} = ?")
                    values.append(value)
                elif key == 'custom_data':
                    set_clause.append("custom_data = ?")
                    values.append(json.dumps(value))
            
            if not set_clause:
                return False
            
            set_clause.append("updated_at = CURRENT_TIMESTAMP")
            query = f"""
                UPDATE contacts 
                SET {', '.join(set_clause)}
                WHERE id = ?
            """
            values.append(contact_id)
            
            cursor.execute(query, values)
            return cursor.rowcount > 0
    
    def record_interaction(
        self,
        contact_id: int,
        email_id: str,
        interaction_type: str,
        metadata: Dict = None
    ):
        """Record an email interaction."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO email_interactions (
                    contact_id, email_id, interaction_type, metadata
                ) VALUES (?, ?, ?, ?)
            """, (
                contact_id,
                email_id,
                interaction_type,
                json.dumps(metadata or {})
            ))
    
    def update_sequence_status(
        self,
        contact_id: int,
        sequence_id: str,
        current_step: int,
        status: str,
        next_email_date: datetime
    ):
        """Update sequence tracking status."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO sequence_tracking (
                    contact_id, sequence_id, current_step,
                    status, last_email_date, next_email_date
                ) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, ?)
            """, (
                contact_id,
                sequence_id,
                current_step,
                status,
                next_email_date.isoformat()
            ))
    
    def record_ab_test_result(
        self,
        contact_id: int,
        test_id: str,
        variant: str,
        result: str
    ):
        """Record A/B test result."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO ab_test_results (
                    contact_id, test_id, variant, result
                ) VALUES (?, ?, ?, ?)
            """, (contact_id, test_id, variant, result))
    
    def get_pending_emails(self) -> List[Dict]:
        """Get contacts due for next email in their sequences."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    c.id as contact_id,
                    c.email,
                    c.name,
                    c.custom_data,
                    st.sequence_id,
                    st.current_step
                FROM contacts c
                JOIN sequence_tracking st ON c.id = st.contact_id
                WHERE st.status = 'active'
                AND st.next_email_date <= CURRENT_TIMESTAMP
            """)
            
            results = []
            for row in cursor.fetchall():
                contact = {
                    'contact_id': row[0],
                    'email': row[1],
                    'name': row[2],
                    'custom_data': json.loads(row[3]),
                    'sequence_id': row[4],
                    'current_step': row[5]
                }
                results.append(contact)
            
            return results
    
    def get_ab_test_stats(self, test_id: str) -> Dict:
        """Get A/B test statistics."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    variant,
                    result,
                    COUNT(*) as count
                FROM ab_test_results
                WHERE test_id = ?
                GROUP BY variant, result
            """, (test_id,))
            
            stats = {}
            for row in cursor.fetchall():
                variant = row[0]
                result = row[1]
                count = row[2]
                
                if variant not in stats:
                    stats[variant] = {}
                stats[variant][result] = count
            
            return stats

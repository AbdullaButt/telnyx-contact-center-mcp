"""
Analytics database helpers for Telnyx Contact Center
Provides functions to log call events, IVR interactions, and transfers to SQLite
"""
import sqlite3
import os
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
DEFAULT_DB_PATH = "./analytics.sqlite"
DB_PATH = os.environ.get("ANALYTICS_DB", DEFAULT_DB_PATH)

def get_db_connection():
    """Get database connection with Row factory for dict-like access"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database with schema from db/schema.sql"""
    try:
        # Read schema file
        schema_path = os.path.join(os.path.dirname(__file__), "db", "schema.sql")
        with open(schema_path, 'r') as f:
            schema_sql = f.read()
        
        # Execute schema
        conn = get_db_connection()
        conn.executescript(schema_sql)
        conn.commit()
        conn.close()
        
        logger.info(f"Database initialized at {DB_PATH}")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

def ensure_db():
    """Ensure database exists and is initialized"""
    if not os.path.exists(DB_PATH):
        init_db()

def save_call_if_new(call_control_id: str, from_number: str, to_number: str):
    """Save call information if not already exists"""
    ensure_db()
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if call already exists
        cursor.execute("SELECT 1 FROM calls WHERE call_control_id = ?", (call_control_id,))
        if cursor.fetchone():
            conn.close()
            return
        
        # Insert new call
        now = datetime.utcnow().isoformat() + "Z"
        cursor.execute("""
            INSERT INTO calls (call_control_id, from_number, to_number, created_at)
            VALUES (?, ?, ?, ?)
        """, (call_control_id, from_number, to_number, now))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Saved new call: {call_control_id}")
    except Exception as e:
        logger.error(f"Failed to save call {call_control_id}: {e}")

def log_event(call_control_id: str, event_type: str, payload_dict: Dict[str, Any]):
    """Log call event with timestamp"""
    ensure_db()
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        now = datetime.utcnow().isoformat() + "Z"
        payload_json = json.dumps(payload_dict) if payload_dict else None
        
        cursor.execute("""
            INSERT INTO call_events (call_control_id, event_type, ts, payload_json)
            VALUES (?, ?, ?, ?)
        """, (call_control_id, event_type, now, payload_json))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Logged event {event_type} for call {call_control_id}")
    except Exception as e:
        logger.error(f"Failed to log event {event_type} for {call_control_id}: {e}")

def log_ivr_selection(call_control_id: str, digit: str, department: str):
    """Log IVR digit selection and department routing"""
    ensure_db()
    
    # Validate department
    valid_departments = {"sales", "support", "porting"}
    if department not in valid_departments:
        logger.warning(f"Invalid department '{department}' for call {call_control_id}")
        return
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        now = datetime.utcnow().isoformat() + "Z"
        
        cursor.execute("""
            INSERT INTO ivr_interactions (call_control_id, digit, department, ts)
            VALUES (?, ?, ?, ?)
        """, (call_control_id, digit, department, now))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Logged IVR selection: {digit} -> {department} for call {call_control_id}")
    except Exception as e:
        logger.error(f"Failed to log IVR selection for {call_control_id}: {e}")

def log_transfer(call_control_id: str, to_sip_uri: str, status: str):
    """Log transfer attempt with success/error status"""
    ensure_db()
    
    # Validate status
    if status not in {"success", "error"}:
        logger.warning(f"Invalid transfer status '{status}' for call {call_control_id}")
        return
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        now = datetime.utcnow().isoformat() + "Z"
        
        cursor.execute("""
            INSERT INTO transfers (call_control_id, to_sip_uri, status, ts)
            VALUES (?, ?, ?, ?)
        """, (call_control_id, to_sip_uri, status, now))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Logged transfer {status} to {to_sip_uri} for call {call_control_id}")
    except Exception as e:
        logger.error(f"Failed to log transfer for {call_control_id}: {e}")

def kpis_24h(department: Optional[str] = None) -> Dict[str, Any]:
    """Get 24-hour KPIs: inbound volume, selection rate, transfer success"""
    ensure_db()
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Calculate 24h window
        cutoff = (datetime.utcnow() - timedelta(hours=24)).isoformat() + "Z"
        
        # Base query conditions
        dept_filter = ""
        params = [cutoff]
        if department:
            dept_filter = " AND ivr.department = ?"
            params.append(department)
        
        # Inbound volume (calls in last 24h)
        cursor.execute(f"""
            SELECT COUNT(DISTINCT c.call_control_id) as volume
            FROM calls c
            LEFT JOIN ivr_interactions ivr ON c.call_control_id = ivr.call_control_id
            WHERE c.created_at >= ?{dept_filter}
        """, params)
        inbound_volume = cursor.fetchone()["volume"]
        
        # Selection rate (calls with IVR interactions / total calls)
        if department:
            cursor.execute("""
                SELECT 
                    COUNT(DISTINCT ivr.call_control_id) as with_selection,
                    (SELECT COUNT(DISTINCT c2.call_control_id) 
                     FROM calls c2 
                     LEFT JOIN ivr_interactions ivr2 ON c2.call_control_id = ivr2.call_control_id
                     WHERE c2.created_at >= ? AND ivr2.department = ?) as total_calls
                FROM ivr_interactions ivr
                JOIN calls c ON ivr.call_control_id = c.call_control_id
                WHERE c.created_at >= ? AND ivr.department = ?
            """, (cutoff, department, cutoff, department))
        else:
            cursor.execute("""
                SELECT 
                    COUNT(DISTINCT ivr.call_control_id) as with_selection,
                    COUNT(DISTINCT c.call_control_id) as total_calls
                FROM calls c
                LEFT JOIN ivr_interactions ivr ON c.call_control_id = ivr.call_control_id
                WHERE c.created_at >= ?
            """, (cutoff,))
        
        selection_data = cursor.fetchone()
        selection_rate = (selection_data["with_selection"] / selection_data["total_calls"] 
                         if selection_data["total_calls"] > 0 else 0.0)
        
        # Transfer success rate
        if department:
            cursor.execute("""
                SELECT 
                    COUNT(CASE WHEN t.status = 'success' THEN 1 END) as successful,
                    COUNT(*) as total_transfers
                FROM transfers t
                JOIN calls c ON t.call_control_id = c.call_control_id
                JOIN ivr_interactions ivr ON c.call_control_id = ivr.call_control_id
                WHERE c.created_at >= ? AND ivr.department = ?
            """, (cutoff, department))
        else:
            cursor.execute("""
                SELECT 
                    COUNT(CASE WHEN status = 'success' THEN 1 END) as successful,
                    COUNT(*) as total_transfers
                FROM transfers t
                JOIN calls c ON t.call_control_id = c.call_control_id
                WHERE c.created_at >= ?
            """, (cutoff,))
        
        transfer_data = cursor.fetchone()
        transfer_success = (transfer_data["successful"] / transfer_data["total_transfers"] 
                           if transfer_data["total_transfers"] > 0 else 0.0)
        
        conn.close()
        
        return {
            "window": "24h",
            "department": department or "all",
            "inbound_volume": inbound_volume,
            "selection_rate": round(selection_rate, 3),
            "transfer_success": round(transfer_success, 3)
        }
        
    except Exception as e:
        logger.error(f"Failed to get 24h KPIs: {e}")
        return {
            "window": "24h",
            "department": department or "all",
            "inbound_volume": 0,
            "selection_rate": 0.0,
            "transfer_success": 0.0
        }

def volume_trend_days(days: int = 7, department: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get daily call volume trend for specified days"""
    ensure_db()
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Calculate date range
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat() + "Z"
        
        if department:
            cursor.execute("""
                SELECT 
                    DATE(c.created_at) as day,
                    COUNT(DISTINCT c.call_control_id) as calls
                FROM calls c
                LEFT JOIN ivr_interactions ivr ON c.call_control_id = ivr.call_control_id
                WHERE c.created_at >= ? AND (ivr.department = ? OR ivr.department IS NULL)
                GROUP BY DATE(c.created_at)
                ORDER BY day DESC
            """, (cutoff, department))
        else:
            cursor.execute("""
                SELECT 
                    DATE(created_at) as day,
                    COUNT(*) as calls
                FROM calls
                WHERE created_at >= ?
                GROUP BY DATE(created_at)
                ORDER BY day DESC
            """, (cutoff,))
        
        results = [{"day": row["day"], "calls": row["calls"]} for row in cursor.fetchall()]
        conn.close()
        
        return results
        
    except Exception as e:
        logger.error(f"Failed to get volume trend: {e}")
        return []

def recent_calls(limit: int = 20, department: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get recent calls with IVR selections and department info"""
    ensure_db()
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if department:
            cursor.execute("""
                SELECT 
                    c.call_control_id,
                    ivr.department,
                    ivr.digit,
                    c.created_at as ts
                FROM calls c
                LEFT JOIN ivr_interactions ivr ON c.call_control_id = ivr.call_control_id
                WHERE ivr.department = ?
                ORDER BY c.created_at DESC
                LIMIT ?
            """, (department, limit))
        else:
            cursor.execute("""
                SELECT 
                    c.call_control_id,
                    ivr.department,
                    ivr.digit,
                    c.created_at as ts
                FROM calls c
                LEFT JOIN ivr_interactions ivr ON c.call_control_id = ivr.call_control_id
                ORDER BY c.created_at DESC
                LIMIT ?
            """, (limit,))
        
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return results
        
    except Exception as e:
        logger.error(f"Failed to get recent calls: {e}")
        return []
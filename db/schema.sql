-- Analytics SQLite Schema for Telnyx Contact Center
-- Stores call events, IVR selections, and transfers for KPI analysis

-- Core call information
CREATE TABLE IF NOT EXISTS calls (
    call_control_id TEXT PRIMARY KEY,
    from_number TEXT NOT NULL,
    to_number TEXT NOT NULL,
    created_at TEXT NOT NULL  -- ISO8601 UTC string
);

-- All call events (initiated, gather started/ended, hangup, etc.)
CREATE TABLE IF NOT EXISTS call_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    call_control_id TEXT NOT NULL,
    event_type TEXT NOT NULL,  -- 'call.initiated', 'call.gather.started', etc.
    ts TEXT NOT NULL,  -- ISO8601 UTC string
    payload_json TEXT,  -- JSON string of event data
    FOREIGN KEY (call_control_id) REFERENCES calls(call_control_id)
);

-- IVR interactions and department routing
CREATE TABLE IF NOT EXISTS ivr_interactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    call_control_id TEXT NOT NULL,
    digit TEXT NOT NULL,  -- DTMF digit pressed
    department TEXT NOT NULL,  -- 'sales', 'support', 'porting'
    ts TEXT NOT NULL,  -- ISO8601 UTC string
    FOREIGN KEY (call_control_id) REFERENCES calls(call_control_id)
);

-- Transfer attempts and outcomes
CREATE TABLE IF NOT EXISTS transfers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    call_control_id TEXT NOT NULL,
    to_sip_uri TEXT NOT NULL,
    status TEXT NOT NULL,  -- 'success' or 'error'
    ts TEXT NOT NULL,  -- ISO8601 UTC string
    FOREIGN KEY (call_control_id) REFERENCES calls(call_control_id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_calls_created_at ON calls(created_at);
CREATE INDEX IF NOT EXISTS idx_call_events_call_id ON call_events(call_control_id);
CREATE INDEX IF NOT EXISTS idx_call_events_ts ON call_events(ts);
CREATE INDEX IF NOT EXISTS idx_ivr_call_id ON ivr_interactions(call_control_id);
CREATE INDEX IF NOT EXISTS idx_ivr_ts ON ivr_interactions(ts);
CREATE INDEX IF NOT EXISTS idx_ivr_department ON ivr_interactions(department);
CREATE INDEX IF NOT EXISTS idx_transfers_call_id ON transfers(call_control_id);
CREATE INDEX IF NOT EXISTS idx_transfers_ts ON transfers(ts);
CREATE INDEX IF NOT EXISTS idx_transfers_status ON transfers(status);
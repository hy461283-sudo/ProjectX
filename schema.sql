CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    type TEXT NOT NULL,
    severity TEXT NOT NULL,
    description TEXT NOT NULL,
    metric_value REAL,
    threshold REAL
);

CREATE TABLE IF NOT EXISTS actions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER,
    timestamp TEXT NOT NULL,
    type TEXT NOT NULL,
    status TEXT NOT NULL,
    output TEXT,
    duration_ms INTEGER,
    target_process TEXT,
    target_service TEXT,
    files_deleted TEXT,
    FOREIGN KEY(event_id) REFERENCES events(id)
);

CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    action_id INTEGER,
    affected_resources TEXT,
    status TEXT,
    FOREIGN KEY(action_id) REFERENCES actions(id)
);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS recommendations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    event_id INTEGER,
    category TEXT NOT NULL,
    recommendation_text TEXT NOT NULL,
    action_type TEXT,
    priority TEXT DEFAULT 'medium',
    status TEXT DEFAULT 'pending',
    applied_at TEXT,
    FOREIGN KEY (event_id) REFERENCES events(id)
);

-- Default Settings
INSERT OR IGNORE INTO settings (key, value) VALUES ('cpu_threshold', '80.0');
INSERT OR IGNORE INTO settings (key, value) VALUES ('memory_threshold', '85.0');
INSERT OR IGNORE INTO settings (key, value) VALUES ('disk_threshold', '90.0');
INSERT OR IGNORE INTO settings (key, value) VALUES ('auto_remediate', 'false');
INSERT OR IGNORE INTO settings (key, value) VALUES ('updates_pending_threshold', '5');

import sqlite3
from config import DB_PATH

def init_db():
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS tests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    download REAL, upload REAL, jitter REAL, ping REAL,
                    packet_loss REAL, country TEXT, isp TEXT,
                    ip_address TEXT, dns REAL, dns_server TEXT
                )
            ''')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON tests(timestamp)')
        print("[DB] Database initialized successfully.")
    except Exception as e:
        print(f"[DB] Error initializing database: {e}")

def save_test_result(results: dict):
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute('''
                INSERT INTO tests (
                    timestamp, download, upload, jitter, ping,
                    packet_loss, country, isp, ip_address, dns, dns_server
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                results['timestamp'],
                round(results.get('download', 0), 3),
                round(results.get('upload', 0), 3),
                round(results.get('jitter', 0), 3),
                round(results.get('ping', 0), 3),
                round(results.get('packet_loss', 0), 3),
                results.get('country', 'Unknown'),
                results.get('isp', 'Unknown'),
                results.get('ip_address', 'Unknown'),
                round(results.get('dns', 0), 3) if results.get('dns', 0) > 0 else None,
                results.get('dns_server', 'Unknown')
            ))
    except Exception as e:
        print(f"[DB SAVE ERROR] {e}")
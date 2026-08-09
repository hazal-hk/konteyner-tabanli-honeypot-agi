import json
import time
import os
import sqlite3

LOG_FILE = "/logs/cowrie.json"   # Docker içindeki yol
DB_FILE = "/data/attacks.db"

# Veritabanını hazırla
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    src_ip TEXT,
                    event_type TEXT,
                    details TEXT
                )''')
    conn.commit()
    conn.close()

def insert_event(event):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO events (timestamp, src_ip, event_type, details) VALUES (?, ?, ?, ?)",
              (event['timestamp'], event['src_ip'], event['event_type'], event['details']))
    conn.commit()
    conn.close()

def follow(file_path):
    """Dosyayı sürekli oku (tail -f mantığı)"""
    with open(file_path, 'r') as f:
        f.seek(0, os.SEEK_END)  # Dosyanın sonuna git
        while True:
            line = f.readline()
            if line:
                yield line.strip()
            else:
                time.sleep(0.1)

def parse_line(line):
    try:
        data = json.loads(line)
        event_type = data.get('eventid', '')
        src_ip = data.get('src_ip', '')
        timestamp = data.get('timestamp', '')

        # Önemli olayları filtrele ve detaylandır
        if event_type == 'cowrie.login.success':
            details = f"Login success: {data.get('username','')}/{data.get('password','')}"
        elif event_type == 'cowrie.login.failed':
            details = f"Login failed: {data.get('username','')}/{data.get('password','')}"
        elif event_type == 'cowrie.command.input':
            details = f"Command: {data.get('input','')}"
        elif event_type == 'cowrie.session.file_download':
            details = f"File download: {data.get('url','')}"
        else:
            return None  # ilgilenmediğimiz olay

        return {
            'timestamp': timestamp,
            'src_ip': src_ip,
            'event_type': event_type,
            'details': details
        }
    except json.JSONDecodeError:
        return None

if __name__ == "__main__":
    print("Log işleyici başlatılıyor...")
    init_db()
    # Cowrie log dosyası henüz oluşmamışsa bekle
    while not os.path.exists(LOG_FILE):
        print("Log dosyası bekleniyor...")
        time.sleep(2)
    print(f"{LOG_FILE} bulundu. İzleme başladı.")
    for line in follow(LOG_FILE):
        event = parse_line(line)
        if event:
            insert_event(event)
            print(f"Yeni olay: {event['event_type']} - {event['details']}")
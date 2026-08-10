import json
import time
import os
import sqlite3
import requests
from datetime import datetime, timezone, timedelta

LOG_FILE = "/logs/cowrie.json"
DB_FILE = "/data/attacks.db"

# Telegram ayarları
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

# IP Geolocation API (ücretsiz, hız limitli: dakikada 45 istek)
GEO_API = "http://ip-api.com/json/{}"

# ---------- Veritabanı ----------
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Ana olay tablosu
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
    
    # IP önbellek tablosu
    c.execute('''CREATE TABLE IF NOT EXISTS ip_cache (
                    ip TEXT PRIMARY KEY,
                    country TEXT,
                    city TEXT,
                    country_code TEXT,
                    lat REAL,
                    lon REAL,
                    last_updated TEXT
                )''')
    
    # Eksik sütunları ekle (eğer tablo zaten varsa)
    try:
        c.execute("ALTER TABLE events ADD COLUMN country TEXT DEFAULT ''")
    except sqlite3.OperationalError:
        pass
    try:
        c.execute("ALTER TABLE events ADD COLUMN city TEXT DEFAULT ''")
    except sqlite3.OperationalError:
        pass
    try:
        c.execute("ALTER TABLE events ADD COLUMN country_code TEXT DEFAULT ''")
    except:
        pass
    try:
        c.execute("ALTER TABLE events ADD COLUMN lat REAL DEFAULT 0")
    except:
        pass
    try:
        c.execute("ALTER TABLE events ADD COLUMN lon REAL DEFAULT 0")
    except:
        pass
    
    conn.commit()
    conn.close()

# ----------Zaman damgası formatlama ----------
def format_local_time(utc_timestamp_str):
    # Cowrie timestamp örneği: "2026-08-10T12:34:56.123456Z"
    dt = datetime.fromisoformat(utc_timestamp_str.replace('Z', '+00:00'))
    local_dt = dt.astimezone(timezone(timedelta(hours=3)))  # Türkiye saati (UTC+3)
    return local_dt.strftime('%d.%m.%Y %H:%M:%S')

# ---------- Coğrafi Konum ----------
def get_geolocation(ip):
    """IP adresi için ülke, şehir, koordinat bilgisini döndür."""
    # Yerel IP'ler için boş dön
    if ip.startswith("127.") or ip.startswith("192.168.") or ip.startswith("10.") or ip.startswith("172."):
        return "", "", "", 0, 0
    
    # Önbelleğe bak
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT country, city, country_code, lat, lon FROM ip_cache WHERE ip = ?", (ip,))
    row = c.fetchone()
    if row:
        conn.close()
        return row
    
    # API'den çek
    try:
        resp = requests.get(GEO_API.format(ip), timeout=3)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("status") == "success":
                country = data.get("country", "")
                city = data.get("city", "")
                country_code = data.get("countryCode", "")
                lat = data.get("lat", 0)
                lon = data.get("lon", 0)
                # Önbelleğe yaz
                c.execute("INSERT OR REPLACE INTO ip_cache (ip, country, city, country_code, lat, lon, last_updated) VALUES (?,?,?,?,?,?,?)",
                          (ip, country, city, country_code, lat, lon, datetime.now().isoformat()))
                conn.commit()
                conn.close()
                return country, city, country_code, lat, lon
    except Exception as e:
        print(f"Geolocation hatası: {e}")
    conn.close()
    return "", "", "", 0, 0

# ---------- Telegram Bildirimi ----------
def send_telegram(event):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        return
    
    # Olay tipine göre emoji ve mesaj
    emoji_map = {
        "cowrie.login.failed": "❌",
        "cowrie.login.success": "✅",
        "cowrie.command.input": "💻",
        "cowrie.session.file_download": "📥"
    }
    emoji = emoji_map.get(event["event_type"], "⚠️")
    #zaman dilimini ayarlama
    local_time = format_local_time(event['timestamp'])

    msg = f"{emoji} **Honeypot Uyarısı**\n"
    msg += f"📅 Zaman: {local_time}\n"
    msg += f"🌍 IP: {event['src_ip']}"
    if event.get("country"):
        msg += f" ({event['country']}, {event['city']})"
    msg += f"\n🔍 Olay: {event['event_type']}\n"
    msg += f"📝 Detay: {event['details']}"
    
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": msg,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print(f"Telegram gönderilemedi: {e}")

# ---------- Olay İşleme ----------
def insert_event(event):
    # Coğrafi bilgiyi ekle
    country, city, country_code, lat, lon = get_geolocation(event['src_ip'])
    event['country'] = country
    event['city'] = city
    event['country_code'] = country_code
    event['lat'] = lat
    event['lon'] = lon
    
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""INSERT INTO events 
                 (timestamp, src_ip, event_type, details, country, city, country_code, lat, lon)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
              (event['timestamp'], event['src_ip'], event['event_type'],
               event['details'], event['country'], event['city'],
               event['country_code'], event['lat'], event['lon']))
    conn.commit()
    conn.close()
    
    # Telegram'a gönder (tüm olaylar değil, önemli olanlar)
    if event['event_type'] in ["cowrie.login.failed", "cowrie.login.success",
                               "cowrie.command.input", "cowrie.session.file_download"]:
        send_telegram(event)
    
    if event['event_type'] in ["cowrie.login.success", "cowrie.session.file_download"]:
        block_ip(event['src_ip'])

# ---------- Dosya İzleme (önceki ile aynı) ----------
def follow(file_path):
    with open(file_path, 'r') as f:
        f.seek(0, os.SEEK_END)
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

        if event_type == 'cowrie.login.success':
            details = f"Login success: {data.get('username','')}/{data.get('password','')}"
        elif event_type == 'cowrie.login.failed':
            details = f"Login failed: {data.get('username','')}/{data.get('password','')}"
        elif event_type == 'cowrie.command.input':
            details = f"Command: {data.get('input','')}"
        elif event_type == 'cowrie.session.file_download':
            details = f"File download: {data.get('url','')}"
        else:
            return None

        return {
            'timestamp': timestamp,
            'src_ip': src_ip,
            'event_type': event_type,
            'details': details
        }
    except json.JSONDecodeError:
        return 
def block_ip(ip):
    """IP'yi blocklist dosyasına ekle (yerel IP'leri atla)."""
    if ip.startswith("127."):     # Sadece gerçek loopback'i engelleme, demo için özel IP'lere izin ver
        return
    blockfile = "/data/blocklist.txt"
    try:
        # Daha önce eklenmiş mi kontrol et
        with open(blockfile, "a+") as f:
            f.seek(0)
            blocked = [line.strip() for line in f.readlines()]
            if ip not in blocked:
                f.write(ip + "\n")
                print(f"[BLOCK] IP blocklist'e eklendi: {ip}")
    except Exception as e:
        print(f"[BLOCK] Dosya yazma hatası: {e}")

if __name__ == "__main__":
    print("Log işleyici başlatılıyor...")
    init_db()
    while not os.path.exists(LOG_FILE):
        print("Log dosyası bekleniyor...")
        time.sleep(2)
    print(f"{LOG_FILE} bulundu. İzleme başladı.")
    for line in follow(LOG_FILE):
        event = parse_line(line)
        if event:
            insert_event(event)
            print(f"Yeni olay: {event['event_type']} - {event['details']}")
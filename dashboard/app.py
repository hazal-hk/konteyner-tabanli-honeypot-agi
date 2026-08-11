from flask import Flask, render_template, jsonify
import sqlite3
import os

DASHBOARD_USER = os.environ.get("DASHBOARD_USER", "admin")
DASHBOARD_PASS = os.environ.get("DASHBOARD_PASS", "password")

def check_auth(username, password):
    return username == DASHBOARD_USER and password == DASHBOARD_PASS

app = Flask(__name__)
DB_FILE = "/data/attacks.db"

# ---------- Bayrak Emoji Filtresi ----------
def flag_emoji(country_code):
    if not country_code:
        return ''
    return ''.join(chr(ord(c) + 127397) for c in country_code.upper())

app.jinja_env.filters['flag_emoji'] = flag_emoji

# ---------- Veritabanı Şemasını Garantile ----------
def ensure_schema():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    src_ip TEXT,
                    event_type TEXT,
                    details TEXT
                )''')
    for col, col_type in [('country', 'TEXT DEFAULT ""'),
                          ('city', 'TEXT DEFAULT ""'),
                          ('country_code', 'TEXT DEFAULT ""'),
                          ('lat', 'REAL DEFAULT 0'),
                          ('lon', 'REAL DEFAULT 0')]:
        try:
            c.execute(f"ALTER TABLE events ADD COLUMN {col} {col_type}")
        except sqlite3.OperationalError:
            pass
    conn.commit()
    conn.close()

ensure_schema()  # uygulama başlar başlamaz çağır

# ---------- Veritabanı Fonksiyonları ----------
def get_recent_events(limit=50):
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM events ORDER BY id DESC LIMIT ?", (limit,))
    rows = c.fetchall()
    conn.close()
    return rows

def get_stats():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM events")
    total = c.fetchone()[0]
    c.execute("SELECT details, COUNT(*) as cnt FROM events WHERE event_type='cowrie.login.failed' GROUP BY details ORDER BY cnt DESC LIMIT 5")
    top_failures = c.fetchall()
    conn.close()
    return total, top_failures

def get_top_countries(limit=5):
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("""SELECT country, country_code, COUNT(*) as cnt
                 FROM events WHERE country != ''
                 GROUP BY country_code
                 ORDER BY cnt DESC LIMIT ?""", (limit,))
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

# ---------- Rotalar ----------
@app.route('/')
def index():
    total, top_failures = get_stats()
    top_countries = get_top_countries()
    return render_template('index.html', total=total, top_failures=top_failures, top_countries=top_countries)

@app.route('/api/events')
def api_events():
    events = get_recent_events(30)
    data = []
    for e in events:
        data.append({
            'id': e['id'],
            'timestamp': e['timestamp'],
            'src_ip': e['src_ip'],
            'event_type': e['event_type'],
            'details': e['details'],
            'country': e['country'],
            'city': e['city'],
            'country_code': e['country_code'],
            'lat': e['lat'],
            'lon': e['lon']
        })
    return jsonify(data)

@app.route('/api/countries')
def api_countries():
    return jsonify(get_top_countries(10))

@app.route('/api/stats')
def api_stats():
    total, top_failures = get_stats()
    top_countries = get_top_countries(5)
    return jsonify({
        'total': total,
        'top_failures': [{'details': r[0], 'count': r[1]} for r in top_failures],
        'top_countries': [{'country': c['country'], 'country_code': c['country_code'], 'cnt': c['cnt']} for c in top_countries]
    })

BLOCKLIST_FILE = "/data/blocklist.txt"

@app.route('/api/blocked')
def api_blocked():
    blocked_ips = []
    try:
        with open(BLOCKLIST_FILE, "r") as f:
            blocked_ips = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        pass
    return jsonify(blocked_ips)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
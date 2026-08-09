from flask import Flask, render_template
import sqlite3

app = Flask(__name__)
DB_FILE = "/data/attacks.db"

def get_recent_events(limit=50):
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row  # sözlük gibi erişim için
    c = conn.cursor()
    c.execute("SELECT * FROM events ORDER BY id DESC LIMIT ?", (limit,))
    rows = c.fetchall()
    conn.close()
    return rows

def get_stats():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # Toplam olay sayısı
    c.execute("SELECT COUNT(*) FROM events")
    total = c.fetchone()[0]
    # En çok denenen kullanıcı adları
    c.execute("SELECT details, COUNT(*) as cnt FROM events WHERE event_type='cowrie.login.failed' GROUP BY details ORDER BY cnt DESC LIMIT 5")
    top_failures = c.fetchall()
    conn.close()
    return total, top_failures

@app.route('/')
def index():
    events = get_recent_events()
    total, top_failures = get_stats()
    return render_template('index.html', events=events, total=total, top_failures=top_failures)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
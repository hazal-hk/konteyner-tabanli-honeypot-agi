from flask import Flask, render_template, jsonify
import sqlite3

app = Flask(__name__)
DB_FILE = "/data/attacks.db"

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

@app.route('/')
def index():
    total, top_failures = get_stats()
    return render_template('index.html', total=total, top_failures=top_failures)

@app.route('/api/events')
def api_events():
    events = get_recent_events(30)  # son 30 olay
    data = []
    for e in events:
        data.append({
            'id': e['id'],
            'timestamp': e['timestamp'],
            'src_ip': e['src_ip'],
            'event_type': e['event_type'],
            'details': e['details']
        })
    return jsonify(data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
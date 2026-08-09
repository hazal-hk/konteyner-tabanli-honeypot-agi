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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
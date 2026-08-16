import requests
import json
import os
import time
from datetime import datetime, timezone, timedelta
from html import escape

BOT_TOKEN = os.environ.get('BOT_TOKEN', '')
CHAT_ID = os.environ.get('CHAT_ID', '')
API_KEY = os.environ.get('FOOTBALL_API_KEY', '')

EAT = timezone(timedelta(hours=3))
headers = {'X-Auth-Token': API_KEY}

today = datetime.now(EAT).date()
yesterday = today - timedelta(days=1)
plus5 = today + timedelta(days=5)

# 1. FETCH ALL MATCHES (yesterday -> next 5 days)
url = f"https://api.football-data.org/v4/matches?dateFrom={yesterday}&dateTo={plus5}"
r = requests.get(url, headers=headers, timeout=30)
print("Matches API status:", r.status_code)
matches = r.json().get('matches', []) if r.status_code == 200 else []

# 2. FETCH REAL LEAGUE TABLES (so the bot can compare team strength)
standings = {}
codes = sorted({m['competition']['code'] for m in matches})[:6]
for code in codes:
    time.sleep(1)
    sr = requests.get(f"https://api.football-data.org/v4/competitions/{code}/standings", headers=headers, timeout=30)
    print(f"Standings {code}:", sr.status_code)
    if sr.status_code == 200:
        try:
            for row in sr.json()['standings'][0]['table']:
                standings[row['team']['id']] = {"position": row['position'], "points": row['points']}
        except Exception as e:
            print("Standings parse error:", e)

# 3. SMART PREDICTION LOGIC
def predict(h, a):
    if not h or not a:
        return "Over 1.5 Goals"
    hp, ap = h['position'], a['position']
    hpts, apts = h['points'], a['points']
    if hp <= 4 and ap <= 4:
        return "Over 2.5 Goals"
    if (ap - hp) >= 4:
        return "Home Win (1)"
    if (hp - ap) >= 4:
        return "Away Win (2)"
    if abs(hp - ap) <= 1 and abs(hpts - apts) <= 3:
        return "Draw (X)"
    return "Home Win (1)" if hp < ap else "Away Win (2)"

data_out = {"yesterday": [], "today": [], "upcoming": []}

for m in matches:
    home = escape(m.get('homeTeam', {}).get('name', 'TBD'))
    away = escape(m.get('awayTeam', {}).get('name', 'TBD'))
    league = escape(m.get('competition', {}).get('name', ''))
    utc = datetime.strptime(m['utcDate'], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    ke = utc.astimezone(EAT)
    status = m.get('status', '')

    prediction = predict(standings.get(m['homeTeam']['id']), standings.get(m['awayTeam']['id']))

    entry = {
        "home": home, "away": away, "league": league,
        "prediction": prediction,
        "kickoff": m['utcDate'],
        "time_eat": ke.strftime('%H:%M'),
        "date_eat": ke.strftime('%a %d %b'),
    }

    if status == 'FINISHED':
        ft = m.get('score', {}).get('fullTime') or {}
        entry['result'] = f"{ft.get('home')}-{ft.get('away')}"
        if ke.date() == yesterday:
            data_out['yesterday'].append(entry)
    elif ke.date() == today:
        data_out['today'].append(entry)
    elif ke.date() > today:
        data_out['upcoming'].append(entry)

with open('predictions.json', 'w') as f:
    json.dump(data_out, f, indent=2)
print("Saved:", len(data_out['today']), "today /", len(data_out['upcoming']), "upcoming /", len(data_out['yesterday']), "finished")

# 4. SEND TO TELEGRAM
lines = ["⚽ <b>WORLD BEST SPORTS PREDICTIONS</b> ⚽", f"📅 {today.strftime('%A %d %B %Y')}", ""]
for e in data_out['today'][:8]:
    lines.append(f"🕒 {e['time_eat']} EAT | {e['league']}")
    lines.append(f"<b>{e['home']} vs {e['away']}</b>")
    lines.append(f"✅ Pick: {e['prediction']}")
    lines.append("━━━━━━━━━━━━")
lines.append("👑 Full 5-day board + Jackpot VIP:")
lines.append("🔗 buymeacoffee.com/thesportspredictions")

resp = requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={
    "chat_id": CHAT_ID, "text": "\n".join(lines), "parse_mode": "HTML"
})
print("Telegram:", resp.status_code)

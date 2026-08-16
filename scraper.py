import requests
import json
import os
from datetime import datetime, timezone, timedelta
from html import escape

BOT_TOKEN = os.environ.get('BOT_TOKEN', '')
CHAT_ID = os.environ.get('CHAT_ID', '')
API_KEY = os.environ.get('FOOTBALL_API_KEY', '')

EAT = timezone(timedelta(hours=3))  # Kenya time

today = datetime.now(EAT).date()
yesterday = today - timedelta(days=1)
plus5 = today + timedelta(days=5)

data_out = {"yesterday": [], "today": [], "upcoming": []}

url = f"https://api.football-data.org/v4/matches?dateFrom={yesterday}&dateTo={plus5}"
headers = {'X-Auth-Token': API_KEY}

try:
    r = requests.get(url, headers=headers, timeout=30)
    print("Football API status:", r.status_code)
    matches = r.json().get('matches', []) if r.status_code == 200 else []
except Exception as e:
    print("API request failed:", e)
    matches = []

for m in matches:
    home = escape(m.get('homeTeam', {}).get('name', 'TBD'))
    away = escape(m.get('awayTeam', {}).get('name', 'TBD'))
    league = escape(m.get('competition', {}).get('name', ''))
    utc = datetime.strptime(m['utcDate'], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    ke = utc.astimezone(EAT)
    status = m.get('status', '')

    # Starter prediction logic (we'll upgrade this with real stats later)
    prediction = 'Over 2.5 Goals' if league in ('German Bundesliga', 'English Premier League') else 'Home Win (1)'

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

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
past15 = today - timedelta(days=15)

def get(url, retries=1):
    for attempt in range(retries + 1):
        r = requests.get(url, headers=headers, timeout=30)
        print("GET", r.status_code, url)
        if r.status_code == 200:
            return r.json()
        if r.status_code == 429 and attempt < retries:
            print("Rate limited. Waiting 65 seconds...")
            time.sleep(65)
    return {}

# 1. MAIN MATCHES (yesterday -> next 5 days)
all_matches = get(f"https://api.football-data.org/v4/matches?dateFrom={yesterday}&dateTo={plus5}", retries=1).get('matches', [])

# 2. BONUS: last 15 days results for "previous games" lists (optional)
time.sleep(2)
past_matches = get(f"https://api.football-data.org/v4/matches?dateFrom={past15}&dateTo={yesterday}").get('matches', [])

form_games = {}
for m in past_matches:
    if m.get('status') != 'FINISHED':
        continue
    ft = m.get('score', {}).get('fullTime') or {}
    if ft.get('home') is None or ft.get('away') is None:
        continue
    hid, aid = m['homeTeam']['id'], m['awayTeam']['id']
    hn, an = m['homeTeam']['name'], m['awayTeam']['name']
    hs, aws = ft['home'], ft['away']
    form_games.setdefault(hid, []).append({"date": m['utcDate'], "opp": an, "score": f"{hs}-{aws}", "res": 'W' if hs > aws else ('D' if hs == aws else 'L')})
    form_games.setdefault(aid, []).append({"date": m['utcDate'], "opp": hn, "score": f"{aws}-{hs}", "res": 'W' if aws > hs else ('D' if aws == hs else 'L')})

for tid in form_games:
    form_games[tid].sort(key=lambda x: x['date'], reverse=True)
    form_games[tid] = form_games[tid][:5]

# 3. LEAGUE TABLES (prediction brain + form backup)
standings = {}
codes = sorted({m['competition']['code'] for m in all_matches})[:6]
for code in codes:
    time.sleep(2)
    sd = get(f"https://api.football-data.org/v4/competitions/{code}/standings")
    try:
        for row in sd['standings'][0]['table']:
            standings[row['team']['id']] = {
                "position": row['position'],
                "points": row['points'],
                "form": row.get('form', '').replace(',', '')
            }
    except Exception:
        pass

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

# Wait a full minute so we never break the 10-requests-per-minute rule
time.sleep(61)

data_out = {"yesterday": [], "today": [], "upcoming": []}
h2h_quota = 5

for m in all_matches:
    home = escape(m.get('homeTeam', {}).get('name', 'TBD'))
    away = escape(m.get('awayTeam', {}).get('name', 'TBD'))
    league = escape(m.get('competition', {}).get('name', ''))
    utc = datetime.strptime(m['utcDate'], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    ke = utc.astimezone(EAT)
    status = m.get('status', '')
    hid, aid = m['homeTeam']['id'], m['awayTeam']['id']

    home_form = "".join(g['res'] for g in form_games.get(hid, [])) or standings.get(hid, {}).get('form', '') or 'N/A'
    away_form = "".join(g['res'] for g in form_games.get(aid, [])) or standings.get(aid, {}).get('form', '') or 'N/A'

    entry = {
        "home": home, "away": away, "league": league,
        "prediction": predict(standings.get(hid), standings.get(aid)),
        "kickoff": m['utcDate'],
        "time_eat": ke.strftime('%H:%M'),
        "date_eat": ke.strftime('%a %d %b'),
        "home_form": home_form, "away_form": away_form,
        "home_last": form_games.get(hid, []),
        "away_last": form_games.get(aid, []),
        "h2h": [],
    }

    if h2h_quota > 0 and ke.date() == today and status != 'FINISHED':
        time.sleep(8)
        hd = get(f"https://api.football-data.org/v4/matches/{m['id']}/head2head?limit=5")
        for hm in hd.get('matches', []):
            ft = hm.get('score', {}).get('fullTime') or {}
            entry["h2h"].append({
                "date": hm['utcDate'][:10],
                "home": escape(hm['homeTeam']['name']),
                "away": escape(hm['awayTeam']['name']),
                "score": f"{ft.get('home')}-{ft.get('away')}"
            })
        h2h_quota -= 1

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
if data_out['today']:
    for e in data_out['today'][:8]:
        lines.append(f"🕒 {e['time_eat']} EAT | {e['league']}")
        lines.append(f"<b>{e['home']} vs {e['away']}</b>")
        lines.append(f"✅ Pick: {e['prediction']}")
        lines.append("━━━━━━━━━━━━")
else:
    lines.append("No major matches today. Check the 5-day board on the website!")
lines.append("👑 Full 5-day board + Jackpot VIP:")
lines.append("🔗 buymeacoffee.com/thesportspredictions")

resp = requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={
    "chat_id": CHAT_ID, "text": "\n".join(lines), "parse_mode": "HTML"
})
print("Telegram:", resp.status_code)

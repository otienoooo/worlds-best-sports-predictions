import requests
import json
import os

BOT_TOKEN = os.environ.get('BOT_TOKEN', '')
CHAT_ID = os.environ.get('CHAT_ID', '')

predictions_data = {
    "yesterday": [{"home": "Arsenal", "away": "Chelsea", "prediction": "Home Win", "result": "2-1"}],
    "today": [{"home": "Man City", "away": "Liverpool", "prediction": "Home Win"}],
    "upcoming": [{"home": "Real Madrid", "away": "Barcelona", "prediction": "Over 2.5 Goals"}]
}

telegram_message = "⚽ *WORLD BEST SPORTS VIP* ⚽\n\n🔥 *TODAY'S TOP PICK:*\n👉 Man City vs Liverpool\n✅ Pick: Home Win\n\n🔗 VIP: buymeacoffee.com/thesportspredictions"

with open('predictions.json', 'w') as f:
    json.dump(predictions_data, f, indent=4)

telegram_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
payload = {"chat_id": CHAT_ID, "text": telegram_message, "parse_mode": "Markdown"}
response = requests.post(telegram_url, json=payload)

if response.status_code == 200:
    print("SUCCESS! Check your Telegram!")
else:
    print("Error:", response.text)

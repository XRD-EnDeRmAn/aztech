import os
from dotenv import load_dotenv
load_dotenv()
import requests

token = os.getenv("TELEGRAM_BOT_TOKEN")
r = requests.get(f"https://api.telegram.org/bot{token}/getUpdates", timeout=10)
data = r.json()

if data.get("result"):
    for update in data["result"]:
        msg = update.get("message", {})
        chat = msg.get("chat", {})
        user = msg.get("from", {})
        if chat:
            print(f"Chat ID : {chat.get('id')}")
            print(f"Ad      : {chat.get('first_name')} {chat.get('last_name','')}")
            print(f"Username: @{chat.get('username','')}")
            print(f"Tip     : {chat.get('type')}")
            print("---")
else:
    print("Heç bir mesaj tapilmadi. Bota /start yaz!")
    print(data)

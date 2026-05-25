# Bot Templates

Three minimal, copy-pasteable bots to bootstrap your first projects. Save each in its own file and run with `python3 file.py`.

## 1. Daily Summary Bot (Telegram)

```python
import os, requests
from telegram.ext import Application, CommandHandler

BOT = os.environ["TELEGRAM_BOT_TOKEN"]

async def hn(update, context):
    r = requests.get("https://hacker-news.firebaseio.com/v0/topstories.json").json()[:10]
    out = []
    for sid in r:
        s = requests.get(f"https://hacker-news.firebaseio.com/v0/item/{sid}.json").json()
        out.append(f"• {s['title']} — {s.get('url','(comments)')}")
    await update.message.reply_text("\n".join(out))

app = Application.builder().token(BOT).build()
app.add_handler(CommandHandler("hn", hn))
app.run_polling()
```

## 2. Price Alert Bot (BTC)

```python
import time, os, requests

BOT = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT = os.environ["TELEGRAM_CHAT_ID"]
last = None

def send(msg):
    requests.post(f"https://api.telegram.org/bot{BOT}/sendMessage",
                  json={"chat_id": CHAT, "text": msg})

while True:
    p = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd").json()["bitcoin"]["usd"]
    if last and abs(p - last) / last > 0.03:
        send(f"BTC moved >3%: ${last:,.0f} → ${p:,.0f}")
    last = p
    time.sleep(300)
```

## 3. Simple FastAPI Webhook

```python
from fastapi import FastAPI, Request
app = FastAPI()

@app.post("/webhook")
async def hook(req: Request):
    data = await req.json()
    print("got:", data)
    return {"ok": True}

# Run: uvicorn file:app --host 0.0.0.0 --port 8000
```

---

Adapt these to your own use case — they're starting points, not finished products.

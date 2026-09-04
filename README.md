# 🦞 ClawBot — Premium OpenClaw Setup Assistant

A $49 Telegram bot that guides users through setting up OpenClaw on a cloud server in ~30 minutes. Stripe-gated, refundable, deployable to Fly.io (Railway retired — too expensive).

## Layout

```
clawbot-setup/
├─ bot.py               # Telegram bot (long-polling)
├─ webhook.py           # Flask webhook for Stripe + success/cancel pages
├─ flow.py              # Setup-flow stages (prompts + keywords)
├─ db.py                # SQLite persistence
├─ payments.py          # Stripe Checkout helpers
├─ bonuses/             # Files sent via /bonuses after payment
├─ Dockerfile           # Container that runs bot + webhook together
├─ railway.json         # Railway deploy config
├─ requirements.txt
└─ .env.example
```

## Local run (test mode)

1. `cp .env.example .env` and fill it in — see Stripe Setup below.
2. `pip3 install -r requirements.txt`
3. Two terminals:
   - `python3 webhook.py` (port 8000)
   - `python3 bot.py`
4. Expose the webhook publicly so Stripe can hit it:
   - `ngrok http 8000` → put `https://xxxx.ngrok.io` in `.env` as `PUBLIC_URL`.
5. In Stripe Dashboard → Developers → Webhooks → add endpoint `https://xxxx.ngrok.io/stripe/webhook` for event `checkout.session.completed` and `charge.refunded`. Copy the signing secret into `.env`.

## Stripe Setup

1. Create a *Product* called "ClawBot Premium Setup" at $49 USD one-time.
2. Copy the *Price ID* (`price_xxx`) into `.env` as `STRIPE_PRICE_ID`.
3. Copy your *Secret Key* (`sk_test_...` to start) as `STRIPE_SECRET_KEY`.
4. Add the webhook endpoint above, then copy *Signing Secret* (`whsec_...`) as `STRIPE_WEBHOOK_SECRET`.

## Telegram Setup

1. Talk to `@BotFather` on Telegram → `/newbot` → grab token → put in `.env` as `TELEGRAM_BOT_TOKEN`.
2. `/setcommands` and paste:
   ```
   start - Pitch + setup menu
   buy - Get a secure $49 checkout link
   paid - Resume your setup after paying
   status - Show your progress
   bonuses - Download guide + templates
   support - Contact a human
   refund - Request a refund (within 7 days)
   help - Show all commands
   ```


## Deploy to Fly.io

1. Install flyctl and `fly auth login`.
2. From this folder: `fly launch --copy-config --yes` (or create app `clawbot-pro` manually).
3. Create a persistent volume for SQLite:
   `fly volumes create clawbot_data --region iad --size 1`
4. Set secrets (never commit these):
   ```
   fly secrets set \
     TELEGRAM_BOT_TOKEN=... \
     STRIPE_SECRET_KEY=... \
     STRIPE_WEBHOOK_SECRET=... \
     STRIPE_PRICE_ID=... \
     PUBLIC_URL=https://clawbot-pro.fly.dev \
     DB_PATH=/data/clawbot.db
   ```
5. `fly deploy`
6. Stripe Dashboard → Webhooks → endpoint `https://clawbot-pro.fly.dev/stripe/webhook` for `checkout.session.completed` and `charge.refunded`.
7. Bot uses long-polling (`bot.py`) — no Telegram webhook required. Keep `PUBLIC_URL` for Stripe redirects.

`railway.json` is legacy and unused on Fly.

## Deploy to Railway (legacy)

1. `railway init` → connect GitHub repo for this folder.
2. Add the `.env` values as Railway variables.
3. Railway auto-builds the Dockerfile. The container runs *both* the bot (polling) and the webhook (gunicorn) in one process group.
4. Update Stripe webhook endpoint to Railway's public URL.
5. Update `PUBLIC_URL` in Railway to the same URL and redeploy.

## Commands

| Command   | Audience        | Notes                                            |
|-----------|-----------------|--------------------------------------------------|
| /start    | everyone        | Pitch + inline buttons                           |
| /buy      | unpaid          | Generates a fresh Stripe Checkout link           |
| /paid     | paid            | Kicks off the setup flow (gated by DB)           |
| /status   | everyone        | Shows paid + current stage                       |
| /bonuses  | paid            | Sends every file in `bonuses/`                   |
| /support  | everyone        | Surfaces the human support handle                |
| /refund   | paid            | Logs a refund request                            |
| /admin    | ADMIN_USER_IDS  | Stats: users, paid, refunded, revenue            |

## State machine

User goes through these stages in `flow.py`:

`start → confirm_ready → aws_account → server_launch → termius_install → ssh_connect → openclaw_install → api_key → first_project → complete`

Advancement requires a paid status + a keyword match in the user's reply. Non-text messages no longer crash the handler.

## TODO / future

- [ ] Inline-photo screenshots for each step (host on a CDN)
- [ ] Drip-feed support messages over 7 days
- [ ] Webhook idempotency hardening for partial refunds
- [ ] i18n for non-English users

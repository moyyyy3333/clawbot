#!/usr/bin/env python3
"""
ClawBot — Premium Hermes / OpenClaw Setup Assistant
$49 guided setup in ~30 minutes.
"""

import os
import logging
from dotenv import load_dotenv

load_dotenv()

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, constants
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)

import db
import payments
import flow
import faq as faq_module

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO,
)
log = logging.getLogger("clawbot")

SUPPORT_HANDLE = os.getenv("SUPPORT_HANDLE", "@ElCapitanNeo")
ADMIN_USER_IDS = {
    int(x.strip())
    for x in os.getenv("ADMIN_USER_IDS", "").split(",")
    if x.strip().isdigit()
}
USDC_WALLET = os.getenv("USDC_WALLET", "")
MD = constants.ParseMode.MARKDOWN


def _is_admin(user_id: int) -> bool:
    return user_id in ADMIN_USER_IDS


async def _ensure_user(update: Update):
    u = update.effective_user
    db.upsert_user(u.id, u.username or "")


# ---------- Commands ----------

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _ensure_user(update)
    keyboard = [
        [
            InlineKeyboardButton("🦾 Hermes", callback_data="stack_hermes"),
            InlineKeyboardButton("🦞 OpenClaw", callback_data="stack_openclaw"),
        ],
        [InlineKeyboardButton("💳 /buy — Unlock $49", callback_data="buy")],
        [InlineKeyboardButton("📹 What You'll Build", callback_data="demo")],
        [InlineKeyboardButton("💬 How It Works", callback_data="how")],
    ]
    await update.message.reply_text(
        flow.START_PITCH,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=MD,
    )


async def cmd_buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _ensure_user(update)
    user = update.effective_user
    user_row = db.get_user(user.id)

    if user_row and user_row.get("paid") and not user_row.get("refunded"):
        await update.message.reply_text(
            "✅ You've already paid. Use /paid to resume your setup."
        )
        return

    try:
        url, session_id = payments.create_checkout_session(
            user.id, user.username or ""
        )
        db.set_stripe_session(user.id, session_id)
        db.log_event(user.id, "checkout_created", {"session_id": session_id})
    except Exception as e:
        log.exception("checkout create failed")
        msg = (
            "⚠️ Stripe isn't fully configured yet.\n\n"
            f"_Detail:_ `{e}`\n\n"
        )
        if USDC_WALLET:
            msg += (
                "\n*Crypto fallback (USDC):*\n"
                f"`{USDC_WALLET}`\n\n"
                "After sending, message your TX hash to "
                f"{SUPPORT_HANDLE}."
            )
        await update.message.reply_text(msg, parse_mode=MD)
        return

    keyboard = [[InlineKeyboardButton("💳 Pay $49 via Stripe", url=url)]]
    body = (
        "💳 *Secure checkout*\n\n"
        "Click below to pay $49 via Stripe. Cards, Apple Pay, Google Pay accepted.\n\n"
        "After payment you'll be redirected back, and I'll automatically unlock "
        "your setup here in this chat."
    )
    if USDC_WALLET:
        body += (
            f"\n\n*Prefer crypto?* Send $49 USDC to:\n`{USDC_WALLET}`\n"
            f"Then message the TX hash to {SUPPORT_HANDLE}."
        )
    await update.message.reply_text(
        body,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=MD,
    )


async def cmd_paid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User says they paid. We only proceed if Stripe webhook has confirmed it."""
    await _ensure_user(update)
    user_row = db.get_user(update.effective_user.id)

    if not user_row or not user_row.get("paid"):
        await update.message.reply_text(
            "🔒 I can't see a confirmed payment for your account yet.\n\n"
            "If you just paid via Stripe, give it ~30 seconds and try again.\n"
            "Haven't paid? Tap /buy.\n"
            f"Stuck? Message {SUPPORT_HANDLE}.",
        )
        return

    if user_row.get("refunded"):
        await update.message.reply_text(
            "⚠️ Your payment was refunded. Tap /buy to start a new order."
        )
        return

    await update.message.reply_text(
        "✅ *Payment confirmed — welcome to ClawBot Premium* 🦞\n\n"
        "Your setup starts now. Takes 30–40 minutes.",
        parse_mode=MD,
    )
    stack = (user_row.get("metadata") or {}).get("stack")
    stage = user_row.get("stage") or "start"
    # Resume mid-setup if already past stack choice; otherwise pick stack then shared flow.
    if stage in flow.STAGES and stage not in ("choose_stack", "start"):
        await _advance_to(update, context, stage)
    elif stack in ("hermes", "openclaw"):
        await _advance_to(update, context, "confirm_ready")
    else:
        await _advance_to_choose_stack(update, context)


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "*ClawBot commands:*\n\n"
        "/start — Pitch + setup menu\n"
        "/buy — Get a secure checkout link ($49)\n"
        "/paid — Resume your setup after paying\n"
        "/status — Where you are in the setup\n"
        "/bonuses — Download guide + templates (after setup)\n"
        "/support — Get help from a human\n"
        "/refund — Request a refund (within 7 days)\n"
        "/help — This message",
        parse_mode=MD,
    )


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _ensure_user(update)
    user_row = db.get_user(update.effective_user.id)
    stage = user_row.get("stage", "start") if user_row else "start"
    paid = bool(user_row and user_row.get("paid"))
    refunded = bool(user_row and user_row.get("refunded"))
    stack = ((user_row or {}).get("metadata") or {}).get("stack") or "not chosen"
    await update.message.reply_text(
        f"*Your status*\n\n"
        f"• Paid: {'✅' if paid and not refunded else ('↩️ refunded' if refunded else '❌')}\n"
        f"• Stack: `{stack}`\n"
        f"• Stage: `{stage}`\n\n"
        f"Use /paid to continue if your setup is paused.",
        parse_mode=MD,
    )


async def cmd_support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"💬 *Support*\n\n"
        f"Message a human: {SUPPORT_HANDLE}\n\n"
        f"Include /status output if you're stuck mid-setup — it helps a lot.",
        parse_mode=MD,
    )


async def cmd_refund(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _ensure_user(update)
    user_row = db.get_user(update.effective_user.id)
    if not user_row or not user_row.get("paid"):
        await update.message.reply_text("No paid order found on your account.")
        return
    if user_row.get("refunded"):
        await update.message.reply_text("You've already been refunded ↩️")
        return

    db.log_event(update.effective_user.id, "refund_requested", {})
    await update.message.reply_text(
        "↩️ *Refund requested.*\n\n"
        f"{SUPPORT_HANDLE} will process it within 24 hours. "
        "You'll get a Stripe email confirmation.",
        parse_mode=MD,
    )


async def cmd_bonuses(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _ensure_user(update)
    user_row = db.get_user(update.effective_user.id)
    if not user_row or not user_row.get("paid") or user_row.get("refunded"):
        await update.message.reply_text("🔒 Bonuses unlock after payment. Use /buy.")
        return

    bonuses_dir = os.path.join(os.path.dirname(__file__), "bonuses")
    files = []
    if os.path.isdir(bonuses_dir):
        files = sorted(
            f for f in os.listdir(bonuses_dir) if not f.startswith(".")
        )

    if not files:
        await update.message.reply_text(
            "🎁 Bonuses are being finalized. "
            f"Ping {SUPPORT_HANDLE} and we'll send them over directly."
        )
        return

    await update.message.reply_text("🎁 *Your bonuses:*", parse_mode=MD)
    for fname in files:
        path = os.path.join(bonuses_dir, fname)
        try:
            with open(path, "rb") as f:
                await update.message.reply_document(document=f, filename=fname)
        except Exception as e:
            log.exception("send bonus %s failed", fname)
            await update.message.reply_text(f"⚠️ Couldn't send {fname}: {e}")


# ---------- FAQ ----------

async def cmd_faq(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _ensure_user(update)
    keyboard = faq_module.get_categories_keyboard()
    await update.message.reply_text(
        "📖 *ClawBot FAQ*\n\n"
        "Select a topic below to see common issues and fixes:",
        parse_mode=MD,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# ---------- Admin ----------

async def cmd_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _is_admin(update.effective_user.id):
        return
    s = db.stats()
    await update.message.reply_text(
        f"*ClawBot admin stats*\n\n"
        f"• Users: `{s['total_users']}`\n"
        f"• Paid: `{s['paid']}`\n"
        f"• Refunded: `{s['refunded']}`\n"
        f"• Completed: `{s['completed_setup']}`\n"
        f"• Net revenue: `${s['net_revenue_usd']}`",
        parse_mode=MD,
    )


# ---------- Flow ----------

def _stack_keyboard():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🦾 Hermes", callback_data="stack_hermes"),
                InlineKeyboardButton("🦞 OpenClaw", callback_data="stack_openclaw"),
            ]
        ]
    )


async def _advance_to(update: Update, context: ContextTypes.DEFAULT_TYPE, stage: str):
    user_id = update.effective_user.id
    db.set_stage(user_id, stage)
    stage_data = flow.get_stage(stage)
    if not stage_data:
        return
    target = update.message or update.callback_query.message
    kwargs = {"parse_mode": MD}
    if stage == "choose_stack":
        kwargs["reply_markup"] = _stack_keyboard()
    await target.reply_text(stage_data["prompt"], **kwargs)


async def _advance_to_choose_stack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _advance_to(update, context, "choose_stack")


async def _set_stack_and_continue(update: Update, context: ContextTypes.DEFAULT_TYPE, stack: str):
    """Persist chosen stack and continue into shared setup (or buy CTA if unpaid)."""
    user_id = update.effective_user.id
    db.set_metadata(user_id, "stack", stack)
    db.log_event(user_id, "stack_chosen", {"stack": stack})
    user_row = db.get_user(user_id) or {}
    label = "Hermes" if stack == "hermes" else "OpenClaw"
    target = update.message or update.callback_query.message

    if not user_row.get("paid") or user_row.get("refunded"):
        await target.reply_text(
            f"Got it — *{label}* saved.\n\n"
            "Unlock setup with /buy, then /paid to start.",
            parse_mode=MD,
        )
        return

    # Paid: if still choosing stack (or restarting), enter shared flow.
    stage = user_row.get("stage") or "start"
    if stage in ("start", "choose_stack", "complete") or stage not in flow.STAGES:
        await target.reply_text(f"✅ Stack set to *{label}*.", parse_mode=MD)
        await _advance_to(update, context, "confirm_ready")
    else:
        await target.reply_text(
            f"✅ Stack set to *{label}*. Continue with /status — "
            f"you're on `{stage}`.",
            parse_mode=MD,
        )


async def on_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await _ensure_user(update)

    if query.data in ("stack_hermes", "stack_openclaw"):
        stack = "hermes" if query.data == "stack_hermes" else "openclaw"
        await _set_stack_and_continue(update, context, stack)

    elif query.data == "demo":
        await query.message.reply_text(
            "📹 *What you'll build:*\n\n"
            "*Week 1:* cloud server + Hermes or OpenClaw + first website live.\n"
            "*Week 3:* trading bot monitoring Kalshi/Polymarket 24/7.\n"
            "*Month 2:* iOS app shipped to App Store — no Mac needed.\n"
            "*Month 3:* freelance clients @ $500–1200/site.\n\n"
            "Real results. Real timeline.\n\n"
            "Ready? Pick Hermes or OpenClaw on /start, then /buy.",
            parse_mode=MD,
        )

    elif query.data == "how":
        await query.message.reply_text(
            "💬 *How ClawBot works*\n\n"
            "1️⃣ Pick Hermes or OpenClaw\n"
            "2️⃣ Pay $49 via Stripe (or USDC)\n"
            "3️⃣ I guide you step-by-step in this chat\n"
            "4️⃣ ~30 minutes later: your agent is running on your server\n"
            "5️⃣ First website is LIVE\n"
            "6️⃣ 7 days of support included\n\n"
            "*If anything doesn't work → refund window. No questions.*\n\n"
            "Compare:\n"
            "❌ DIY guide: 3–6 hours, 40% give up\n"
            "❌ Fiverr: $100–200, hit or miss\n"
            "✅ ClawBot: ~30 min, guided\n\n"
            "Ready? /buy",
            parse_mode=MD,
        )

    elif query.data == "buy":
        # Reuse /buy logic via a synthetic message reply.
        fake_update = Update(update.update_id, message=query.message)
        # Need to preserve effective_user; trick: call cmd_buy with the real update,
        # but reply will go to the message owner (the bot). Use message.chat to reply manually.
        try:
            url, session_id = payments.create_checkout_session(
                update.effective_user.id, update.effective_user.username or ""
            )
            db.set_stripe_session(update.effective_user.id, session_id)
            db.log_event(update.effective_user.id, "checkout_created", {"session_id": session_id})
            keyboard = [[InlineKeyboardButton("💳 Pay $49 via Stripe", url=url)]]
            await query.message.reply_text(
                "💳 *Secure checkout*\n\nClick to pay $49 via Stripe. "
                "You'll be auto-unlocked here after payment.",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=MD,
            )
        except Exception as e:
            await query.message.reply_text(
                f"⚠️ Stripe isn't configured: `{e}`. Use /buy to retry or "
                f"contact {SUPPORT_HANDLE}.",
                parse_mode=MD,
            )

    elif query.data.startswith("faq_"):
        category = query.data[4:]
        if category == "all":
            faq_text = faq_module.format_faq()
            keyboard = [[InlineKeyboardButton("🔙 Back to Topics", callback_data="back")]]
        else:
            faq_text = faq_module.format_faq(category)
            keyboard = faq_module.get_categories_keyboard()
        await query.message.reply_text(
            faq_text, parse_mode=MD, reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif query.data == "back":
        await cmd_faq(update, context)


async def on_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return  # ignore non-text without crashing

    await _ensure_user(update)
    user_id = update.effective_user.id
    user_row = db.get_user(user_id) or {}
    text = update.message.text.lower().strip()
    stage = user_row.get("stage", "start")

    # Gate the flow on payment except for early stages.
    if not user_row.get("paid") or user_row.get("refunded"):
        # Allow pre-pay stack pick via text (Hermes / OpenClaw).
        picked = flow.normalize_stack(text)
        if picked:
            await _set_stack_and_continue(update, context, picked)
            return
        await update.message.reply_text(
            "👀 To start the setup I'll need your $49 payment first.\n"
            "Tap /buy to get a secure Stripe link."
        )
        return

    stage_data = flow.get_stage(stage)
    if not stage_data:
        await update.message.reply_text(
            "Hmm, I'm not sure where you are. Try /status or /paid."
        )
        return

    # choose_stack: reply Hermes or OpenClaw (buttons also work).
    if stage == "choose_stack":
        picked = flow.normalize_stack(text)
        if picked:
            await _set_stack_and_continue(update, context, picked)
            return
        await update.message.reply_text(
            flow.CHOOSE_STACK_PROMPT,
            reply_markup=_stack_keyboard(),
            parse_mode=MD,
        )
        return

    keywords = stage_data.get("keywords") or []
    project_stages = ("first_project", "hermes_first_project")
    matched = (
        any(kw in text for kw in keywords) if keywords else False
    ) or (stage in project_stages and ("http" in text))

    if matched:
        if stage in project_stages and (
            "http" in text or "vercel.app" in text or "://" in text
        ):
            db.set_metadata(user_id, "deployed_url", update.message.text.strip())
        next_stage = stage_data.get("next_stage")
        if stage == "ssh_connect":
            stack = (user_row.get("metadata") or {}).get("stack")
            next_stage = flow.next_after_ssh(stack)
        if next_stage:
            await _advance_to(update, context, next_stage)
        else:
            await update.message.reply_text(
                "✨ You're done with the guided flow. Use /bonuses or just ask me anything."
            )
        return

    # Generic nudge.
    await update.message.reply_text(
        f"I'm waiting for one of these to confirm this step: "
        f"{', '.join(f'`{k}`' for k in keywords) or '(send me what you see)'}.\n\n"
        f"Stuck? Send a screenshot or message {SUPPORT_HANDLE}.",
        parse_mode=MD,
    )


# ---------- Main ----------

def main():
    db.init_db()
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print("❌ TELEGRAM_BOT_TOKEN not set. See .env.example.")
        return

    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("buy", cmd_buy))
    app.add_handler(CommandHandler("paid", cmd_paid))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("support", cmd_support))
    app.add_handler(CommandHandler("refund", cmd_refund))
    app.add_handler(CommandHandler("bonuses", cmd_bonuses))
    app.add_handler(CommandHandler("faq", cmd_faq))
    app.add_handler(CommandHandler("admin", cmd_admin))
    app.add_handler(CallbackQueryHandler(on_button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_message))

    log.info("🦞 ClawBot starting...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()

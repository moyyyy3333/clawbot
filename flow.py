"""Setup-flow content. Each stage has prompt text + acceptance keywords + next stage."""

# Stage machine. Each stage matches user input via `keywords` (lowercased substrings).
# `next_stage` is what to set after a match. `prompt` is what we send when entering this stage.
STAGES = {
    "confirm_ready": {
        "prompt": (
            "🚀 *Let's go!*\n\n"
            "Before we start — quick check. Do you have:\n"
            "✅ 40 minutes uninterrupted?\n"
            "✅ A credit card (for AWS verification — not charged)?\n"
            "✅ Email access?\n\n"
            "Reply *yes* when you're ready."
        ),
        "keywords": ["yes", "ready", "y", "yep"],
        "next_stage": "aws_account",
    },
    "aws_account": {
        "prompt": (
            "📱 *Step 1 of 5 — AWS Account*\n\n"
            "We need a cloud server that runs 24/7.\n"
            "AWS gives you *12 months FREE*.\n\n"
            "Open this on your phone:\n"
            "👉 https://aws.amazon.com/free\n\n"
            "Tap *Create a Free Account*. They'll ask for a credit card to verify you're real — "
            "they won't charge unless you use more than 750 hrs/month (you'll use ~50).\n\n"
            "Reply *created* when your account is ready.\n"
            "Stuck? Send me a screenshot."
        ),
        "keywords": ["created", "done", "ready"],
        "next_stage": "server_launch",
    },
    "server_launch": {
        "prompt": (
            "✅ *AWS account ready!*\n\n"
            "🚀 *Step 2 of 5 — Launch Server*\n\n"
            "In AWS Console, search for *EC2*. Then:\n\n"
            "1. Click orange *Launch Instance*\n"
            "2. Name: `openclaw-server`\n"
            "3. OS: *Ubuntu 22.04 LTS* (free tier)\n"
            "4. Instance type: *t2.micro* (free tier)\n"
            "5. Create new key pair:\n"
            "   • Name: `my-phone-key`\n"
            "   • Type: RSA\n"
            "   • Download the `.pem` file\n"
            "6. Click *Launch Instance*\n\n"
            "Takes ~2 minutes. Reply *launched* when you see it running."
        ),
        "keywords": ["launched", "running", "started"],
        "next_stage": "termius_install",
    },
    "termius_install": {
        "prompt": (
            "🎉 *Server running!*\n\n"
            "📱 *Step 3 of 5 — Connect From Phone*\n\n"
            "Download *Termius* (SSH app):\n"
            "• iPhone: https://apps.apple.com/app/termius/id549039908\n"
            "• Android: https://play.google.com/store/apps/details?id=com.server.auditor\n\n"
            "Install it, then reply *installed*."
        ),
        "keywords": ["installed", "got it", "done"],
        "next_stage": "ssh_connect",
    },
    "ssh_connect": {
        "prompt": (
            "🔐 *Connect to your server*\n\n"
            "In Termius:\n"
            "1. Tap *Keychain* → *+* → Import from file\n"
            "2. Select the `.pem` file you downloaded\n"
            "3. Name it: `my-phone-key`\n\n"
            "Then:\n"
            "4. Tap *Hosts* → *+*\n"
            "5. Alias: `OpenClaw Server`\n"
            "6. Hostname: [Your server IP from AWS]\n"
            "7. Username: `ubuntu`\n"
            "8. Key: `my-phone-key`\n"
            "9. Save & Connect\n\n"
            "You should see: `ubuntu@ip-xxx:~$`\n\n"
            "Reply *connected* when you're in."
        ),
        "keywords": ["connected", "in", "logged in"],
        "next_stage": "openclaw_install",
    },
    "openclaw_install": {
        "prompt": (
            "🦞 *Step 4 of 5 — Install OpenClaw*\n\n"
            "Copy this *exactly* into Termius:\n\n"
            "`curl -fsSL https://openclaw.ai/install.sh | bash`\n\n"
            "Takes 2–3 minutes.\n\n"
            "When it asks *\"Choose LLM provider\"*, reply *choose* here."
        ),
        "keywords": ["choose", "provider", "llm"],
        "next_stage": "api_key",
    },
    "api_key": {
        "prompt": (
            "🔑 *Get your Claude API key*\n\n"
            "In the terminal prompt, type: `anthropic`\n\n"
            "Then to get a key:\n"
            "1. Open https://console.anthropic.com\n"
            "2. Sign up (free)\n"
            "3. Go to *API Keys* → *Create Key*\n"
            "4. Copy it\n"
            "5. Paste in your terminal\n\n"
            "⚠️ *Don't send me the key.* Paste it in your terminal only.\n\n"
            "Reply *added* when done."
        ),
        "keywords": ["added", "pasted", "done"],
        "next_stage": "first_project",
    },
    "first_project": {
        "prompt": (
            "🎉 *OpenClaw is RUNNING!*\n\n"
            "🚀 *Step 5 of 5 — Build Something*\n\n"
            "In your terminal, type:\n\n"
            "`openclaw chat`\n\n"
            "Then send this prompt:\n\n"
            "_Create a simple personal website with my name, a short bio, and contact "
            "info. Deploy it to Vercel when done._\n\n"
            "Watch the magic happen ✨\n\n"
            "Reply with your live website URL when it's deployed."
        ),
        "keywords": ["http", "vercel.app", "://"],
        "next_stage": "complete",
    },
    "complete": {
        "prompt": (
            "🎊 *CONGRATS!*\n\n"
            "You just:\n"
            "✅ Set up a cloud server\n"
            "✅ Installed OpenClaw\n"
            "✅ Built and deployed a website\n\n"
            "*FROM YOUR PHONE.*\n\n"
            "🎁 *Your bonuses:*\n"
            "Use /bonuses to grab the guide, 50 prompts, and templates.\n\n"
            "💬 *7-day support active:*\n"
            "Ask me anything about OpenClaw — I'm here.\n\n"
            "What do you want to build next?"
        ),
        "keywords": [],
        "next_stage": None,
    },
}


def get_stage(stage: str) -> dict:
    return STAGES.get(stage, {})

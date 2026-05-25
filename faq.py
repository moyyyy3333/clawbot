"""
ClawBot FAQ — Common issues and solutions for each setup step
"""

FAQ = {
    "general": {
        "title": "❓ General",
        "items": [
            {
                "q": "How long does this actually take?",
                "a": "30-40 minutes if you follow the steps. AWS account creation takes ~5 min, EC2 launch ~2 min, OpenClaw install ~3 min. Slowest part is reading and following each step."
            },
            {
                "q": "Do I need a laptop?",
                "a": "No. Everything is done from your phone. The only requirement is internet access."
            },
            {
                "q": "Will AWS charge me?",
                "a": "AWS Free Tier gives you 750 hours/month of t2.micro for 12 months. You'll use ~50 hours/month. As long as you don't upgrade the server, you pay $0."
            },
            {
                "q": "What if I get stuck and can't continue?",
                "a": "Reply to the bot with what's wrong — I'll help you through it. If you're really stuck, send a screenshot and your setup admin will unblock you."
            },
            {
                "q": "What if it takes longer than 30 minutes?",
                "a": "That's normal for your first time. The 30-minute estimate is for someone who reads fast and follows along. Take your time."
            },
            {
                "q": "Can I pause and come back later?",
                "a": "Yes. The bot remembers your stage in the setup. Just type /start again when you're ready to continue."
            },
            {
                "q": "What happens after I complete the setup?",
                "a": "You get access to /bonuses (prompts, templates, guide) and 7-day premium support. Reply anytime with questions."
            },
        ]
    },
    "payment": {
        "title": "💳 Payment Issues",
        "items": [
            {
                "q": "My card was declined",
                "a": "Make sure:\n• Your card has international payments enabled\n• You have sufficient funds ($49+)\n• You're not using a prepaid card (most don't work)\n\nTry a different card or contact your bank."
            },
            {
                "q": "I paid but the bot didn't unlock",
                "a": "Sometimes Stripe takes a few seconds. Wait 30 seconds and type /start again. If it still doesn't work, forward your payment receipt to admin."
            },
            {
                "q": "Do you accept crypto?",
                "a": "USDC is available. Contact @ElCapitanNeo directly to arrange."
            },
            {
                "q": "Can I get a refund?",
                "a": "Yes — money-back guarantee if the setup doesn't work. Just message admin and they'll process it."
            },
        ]
    },
    "aws": {
        "title": "☁️ Step 1 — AWS Account",
        "items": [
            {
                "q": "AWS asks for a credit card — is this safe?",
                "a": "Yes. AWS requires a card for identity verification. They will NOT charge you as long as you stay within Free Tier limits (t2.micro, 750 hrs/month). Thousands of developers do this."
            },
            {
                "q": "My card was declined by AWS",
                "a": "AWS is strict about cards. Try:\n• A different card (Visa works best)\n• Check your billing address matches exactly\n• Some international cards get blocked — contact your bank\n\nIf nothing works, use a Revolut/Wise virtual card."
            },
            {
                "q": "Which AWS region should I pick?",
                "a": "Pick the one closest to you:\n• US East (N. Virginia) — best for most people\n• EU (Frankfurt) — if you're in Europe\n• Asia Pacific (Singapore/Tokyo) — if you're in Asia\n\nAll regions have Free Tier."
            },
            {
                "q": "AWS says 'phone verification required'",
                "a": "This is normal. Enter your phone number, they'll call or text a code. If SMS doesn't arrive, try 'Call me' instead of text."
            },
            {
                "q": "I already have an AWS account",
                "a": "Perfect — skip ahead to Step 2. Reply 'launched' after you've started an EC2 instance."
            },
        ]
    },
    "ec2": {
        "title": "🚀 Step 2 — Launch EC2 Server",
        "items": [
            {
                "q": "I can't find EC2 in the AWS Console",
                "a": "Type 'EC2' in the search bar at the top of the AWS Console. Click the first result that says 'EC2 — Virtual Servers in the Cloud'."
            },
            {
                "q": "I don't see 't2.micro' as an option",
                "a": "Make sure you're on the Free Tier tab when choosing instance type. Also check your region has t2.micro available (most do). If not, t3.micro also qualifies for Free Tier."
            },
            {
                "q": "I lost my key pair (.pem file)",
                "a": "⚠️ You can't recover it. Terminate the EC2 instance and launch a new one. This time:\n• Download the .pem file\n• Save it to your phone's Files app immediately\n• Don't lose it"
            },
            {
                "q": "My instance status is 'pending' for a long time",
                "a": "Wait up to 2 minutes. If it stays 'pending' longer, refresh the page. Sometimes AWS is slow."
            },
            {
                "q": "What is a key pair and why do I need it?",
                "a": "It's like a password file that lets you connect to your server securely. Without it, you can't SSH in. Download the .pem file and save it somewhere you can find."
            },
            {
                "q": "How do I find my server's IP address?",
                "a": "In EC2 Console → Instances → click your instance. Look for 'Public IPv4 address' — that's the IP you'll use in Termius. It looks like: 54.123.45.67"
            },
        ]
    },
    "termius": {
        "title": "📱 Step 3 — Termius (SSH App)",
        "items": [
            {
                "q": "Termius won't install",
                "a": "Make sure you have enough storage space (~200 MB free). If still stuck, try:\n• iPhone: App Store → search 'Termius' → tap Get\n• Android: Play Store → search 'Termius' → Install"
            },
            {
                "q": "I can't import the .pem file into Termius",
                "a": "1. Save the .pem file to your phone first (Files app on iPhone, Downloads on Android)\n2. In Termius, go to Keychain → + → Import Key\n3. Navigate to where you saved the file\n4. Select it\n\nIf 'Import Key' isn't visible, make sure you're in Keychain view (bottom tab)."
            },
            {
                "q": "Termius shows 'No key found' or 'Invalid key format'",
                "a": "The .pem file must start with '-----BEGIN RSA PRIVATE KEY-----'. If it doesn't, you downloaded the wrong format. Re-launch the EC2 instance and choose 'RSA' as the key pair type."
            },
        ]
    },
    "ssh": {
        "title": "🔐 Step 3.5 — SSH Connection",
        "items": [
            {
                "q": "Connection timeout in Termius",
                "a": "Most common issue. Fix:\n1. Make sure you're using the server's Public IPv4 address (not the Private IP)\n2. Username must be 'ubuntu' (not 'ec2-user' or 'admin')\n3. Wait 2-3 minutes after launching — the server takes time to start accepting connections"
            },
            {
                "q": "Permission denied (publickey)",
                "a": "This means you're using the wrong key or wrong username. Double check:\n• Username: 'ubuntu' (all lowercase)\n• Key: the exact .pem file you downloaded\n• If you generated a new key pair, use that one"
            },
            {
                "q": "Host key verification failed",
                "a": "If you've connected before and see this, it means the server changed. In Termius, delete the host entry and create a new one with the same IP."
            },
            {
                "q": "It says 'Connection refused'",
                "a": "The SSH service isn't ready yet. Wait 2-3 minutes after launching the EC2 instance, then try again. If it persists, reboot the instance from AWS Console."
            },
            {
                "q": "Where do I find the username and IP?",
                "a": "IP: AWS Console → EC2 → Instances → click yours → copy 'Public IPv4 address'\nUsername: always 'ubuntu' for Ubuntu servers\nPort: 22 (default, don't change)"
            },
        ]
    },
    "openclaw": {
        "title": "🦞 Step 4 — OpenClaw Install",
        "items": [
            {
                "q": "The curl command does nothing / returns nothing",
                "a": "In Termius, type or paste exactly:\n`curl -fsSL https://openclaw.ai/install.sh | bash`\n\nIf it hangs for >30 seconds, press Ctrl+C and try again. Sometimes the network needs a retry."
            },
            {
                "q": "Permission denied when running install",
                "a": "Make sure you're logged in as 'ubuntu' (not 'root'). If it says 'Permission denied', try:\n`sudo curl -fsSL https://openclaw.ai/install.sh | bash`\n\n(Adding 'sudo' runs it with admin privileges.)"
            },
            {
                "q": "OpenClaw install asks about LLM provider — what do I choose?",
                "a": "Type 'anthropic' (or 'claude') when asked. The bot will guide you through getting an API key."
            },
            {
                "q": "Where do I get an Anthropic/Claude API key?",
                "a": "1. Open https://console.anthropic.com on your phone\n2. Sign up (free, email + phone)\n3. Go to API Keys → + Create Key\n4. Copy the key (starts with 'sk-ant-')\n5. Paste it in your Termius terminal when prompted\n\n⚠️ Never share your API key with anyone."
            },
            {
                "q": "The install script is taking too long",
                "a": "The install downloads ~500 MB of dependencies. On a good connection it takes 2-3 minutes. If it's been >5 minutes, press Ctrl+C and run the command again."
            },
            {
                "q": "OpenClaw is installed — now what?",
                "a": "Type 'openclaw chat' in Termius. Then send a prompt like:\n'Create a simple personal website with my name, a short bio, and contact info. Deploy it to Vercel.'\n\nWatch it build and deploy automatically."
            },
        ]
    },
    "server": {
        "title": "🖥️ After Setup — Using Your Server",
        "items": [
            {
                "q": "My server turned off / I disconnected Termius",
                "a": "Open Termius → tap your host → Connect. You'll be back at the command line. Type 'openclaw chat' to resume."
            },
            {
                "q": "How do I keep OpenClaw running 24/7?",
                "a": "It already runs 24/7 on AWS. Even if you close Termius, OpenClaw keeps running. Reconnect anytime via Termius."
            },
            {
                "q": "Can I access my website from my phone?",
                "a": "If you deployed with OpenClaw and it gave you a URL (usually *.vercel.app or similar), yes — open that URL in any browser."
            },
            {
                "q": "The free tier expires after 12 months — what then?",
                "a": "You'll have plenty of warning. Options:\n• t2.micro costs ~$9/month after free tier\n• Move to a cheaper provider (Hetzner ~$4/month)\n• Upgrade to a bigger server if you need more power"
            },
        ]
    },
}


def format_faq(category=None):
    """Format FAQ as a markdown string."""
    lines = []
    lines.append("📖 *ClawBot FAQ — Quick Help*\n")

    if category and category in FAQ:
        categories = {category: FAQ[category]}
    else:
        categories = FAQ

    for key, cat in categories.items():
        lines.append(f"─── {cat['title']} ───\n")
        for item in cat["items"]:
            lines.append(f"*Q: {item['q']}*")
            lines.append(f"{item['a']}\n")
        lines.append("")

    return "\n".join(lines)


def get_categories_keyboard():
    """Return inline keyboard for FAQ categories."""
    buttons = []
    row = []
    for i, (key, cat) in enumerate(FAQ.items()):
        row.append(InlineKeyboardButton(cat["title"], callback_data=f"faq_{key}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton("📖 All FAQs", callback_data="faq_all")])
    buttons.append([InlineKeyboardButton("🔙 Back", callback_data="back")])
    return buttons

# 🦞 OpenClaw Setup Guide

The complete reference for everything you just did with ClawBot — keep this for next time.

## Table of Contents

1. AWS EC2 from your phone
2. SSH with Termius
3. Installing OpenClaw
4. Picking an LLM provider
5. Your first project
6. Keeping OpenClaw running 24/7
7. Common issues + fixes
8. Going further

---

## 1. AWS EC2 from your phone

- Sign up at https://aws.amazon.com/free (12 months free tier).
- Region: pick the one closest to you. `us-east-1` is the cheapest by default.
- Launch instance: **Ubuntu 22.04 LTS, t2.micro** (free tier).
- Key pair: RSA, download the `.pem`. Without this you cannot SSH in.
- Security group inbound:
  - SSH (22) from your IP only — *never* `0.0.0.0/0`.
  - HTTP (80) + HTTPS (443) if you'll host websites from this server.

## 2. SSH with Termius

- Import the `.pem` into Keychain. Don't share it.
- New Host: paste the public IPv4 from AWS. Username: `ubuntu`.
- First connect: accept the host fingerprint.
- Snapshot tip: enable Termius cloud sync so you can reconnect from any device.

## 3. Installing OpenClaw

```bash
curl -fsSL https://openclaw.ai/install.sh | bash
```

This installs the OpenClaw CLI and gateway. After install:

```bash
openclaw --version
openclaw status
```

## 4. Picking an LLM provider

Recommended first picks:
- **Anthropic (Claude)** — strongest at reasoning + tool use. Best default.
- **OpenAI** — broadest model lineup.
- **Groq / Cerebras** — extremely fast, cheaper for high-volume work.
- **Ollama** — local-only, free, but slower and needs RAM.

Get your key from the provider's console and paste it when the installer asks.

## 5. Your first project

```bash
openclaw chat
```

Try prompts like:
- *"Build me a simple personal site and deploy to Vercel."*
- *"Make me a Telegram bot that posts a daily news summary."*
- *"Write a Polymarket price tracker that DM's me when a market moves >5%."*

## 6. Keeping OpenClaw running 24/7

The installer wires up a systemd service. Useful commands:

```bash
sudo systemctl status openclaw
sudo systemctl restart openclaw
journalctl -u openclaw -f
```

Tip: keep a small swap file on t2.micro to avoid OOM:

```bash
sudo fallocate -l 2G /swapfile && sudo chmod 600 /swapfile
sudo mkswap /swapfile && sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

## 7. Common issues + fixes

- **`Permission denied (publickey)`** — your `.pem` permissions are too open. `chmod 400 my-phone-key.pem`.
- **OpenClaw won't start** — check `journalctl -u openclaw -f`. Usually an invalid API key.
- **Out of memory** — add the swap file above, or upgrade to t3.small.
- **Vercel deploy fails** — link the project first: `npx vercel link`.

## 8. Going further

- Pair your phone as an OpenClaw node so you can run commands directly from Telegram.
- Hook up a custom domain via Cloudflare → your server's IP.
- Add a second provider as a fallback so you don't get rate-limited.
- Use OpenClaw skills to capture repeatable workflows.

---

Built with ClawBot. Questions → message me in Telegram.

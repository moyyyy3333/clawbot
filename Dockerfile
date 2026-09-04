FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1
ENV PORT=8080
ENV DB_PATH=/data/clawbot.db
EXPOSE 8080

# Ensure volume mount point exists (Fly mounts over /data at runtime)
RUN mkdir -p /data

# Two processes: Stripe/Flask webhook (gunicorn) + Telegram bot (long-polling)
CMD ["bash", "-c", "gunicorn -w 2 -b 0.0.0.0:${PORT} webhook:app & python3 bot.py"]

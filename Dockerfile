FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1
ENV PORT=8000
EXPOSE 8000

# Two processes: webhook (Flask via gunicorn) + bot (polling). Use a tiny launcher.
CMD ["bash", "-c", "gunicorn -w 2 -b 0.0.0.0:${PORT} webhook:app & python3 bot.py"]

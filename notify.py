"""
notify.py — optional Discord notifications ("the agent tells you what it did").

Posts a short message to a Discord webhook. No-op (safe) if DISCORD_WEBHOOK_URL is
unset, so nothing breaks when it's not configured. Stdlib only — no new dependency.

Set it locally in .env and as a GitHub repo secret:
    DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/....
"""
from __future__ import annotations
import os, json, urllib.request

WEBHOOK = os.getenv('DISCORD_WEBHOOK_URL', '')


def send(text: str) -> bool:
    """Send a plain message to Discord. Returns True if sent, False if unconfigured/failed."""
    if not WEBHOOK:
        return False
    try:
        data = json.dumps({'content': text[:1900]}).encode()   # Discord 2000-char limit
        req = urllib.request.Request(
            WEBHOOK, data=data, headers={'Content-Type': 'application/json'})
        urllib.request.urlopen(req, timeout=10)
        return True
    except Exception:
        return False

"""
assistant.py — optional in-dashboard explainer ("explain my numbers").

Calls Claude (Haiku) to EXPLAIN the dashboard's numbers in plain language. It is an
*explainer, never an advisor*: it lays out facts and trade-offs and hands decisions back
to the user — it never says whether an action is "safe"/"unsafe" or gives buy/sell advice.

Safe by default: returns a friendly notice (never raises) if ANTHROPIC_API_KEY is unset
or the `anthropic` package isn't installed, so the dashboard works exactly as before when
it isn't configured. Nothing here touches the trading agent or the cloud workflows —
read-only, explanation-only, and only reached from the dashboard's /api/ask route.

Enable locally:  pip install -r requirements-assistant.txt  +  ANTHROPIC_API_KEY=... in .env
"""
from __future__ import annotations
import os

MODEL = 'claude-haiku-5-5'          # cheapest current Haiku (~$0.10/$0.50 per 1M tokens)
MAX_ANSWER_TOKENS = 1200
MAX_QUESTION_CHARS = 1000

CHARTER = """You are the explainer assistant inside "Risk Gate", a PAPER-money trading
dashboard (no real money). You help a user who is new to trading and finance understand
their own numbers.

HARD RULES — follow these exactly:
- You EXPLAIN and CALCULATE only. You are NOT a financial advisor.
- NEVER say whether an action is "safe" or "not safe", and NEVER give buy / sell / hold or
  investment advice. Lay out the facts and the trade-offs, then hand the decision back:
  the decision is always the user's.
- For withdrawal / real-money / "should I..." questions: explain the mechanics — realized
  vs unrealized profit, cash vs money locked in open positions, that open positions still
  carry risk, and that realizing gains triggers tax on REAL money — then say plainly that
  the judgment call is theirs, and for real money a licensed human advisor's, not an AI's.
- Use ONLY the data provided in the DATA section. If something isn't there, say you don't
  know rather than guessing or inventing any number.
- Keep it short, concrete, and plain-language for a beginner. Quote the actual numbers.
- Honest context: this strategy has no proven edge; a good stretch can be luck."""


def available() -> bool:
    """True only if a key is set AND the anthropic package is importable."""
    if not os.getenv('ANTHROPIC_API_KEY'):
        return False
    try:
        import anthropic  # noqa: F401
        return True
    except Exception:
        return False


def _fmt_acct(label: str, a: dict, positions: list) -> str:
    if not a:
        return f"{label}: (no data)"
    lines = [f"{label}: equity ${a.get('equity', 0):,.0f}, cash ${a.get('cash', 0):,.0f}, "
             f"P&L vs $100k ${a.get('pl', 0):,.0f} ({a.get('pl_pct', 0):+.2f}%)"]
    for p in positions or []:
        lines.append(f"   - {p.get('symbol')}: value ${p.get('value', 0):,.0f}, "
                     f"unrealized ${p.get('pl', 0):,.0f} ({p.get('plpc', 0):+.0f}%)")
    return "\n".join(lines)


def _format_context(ctx: dict) -> str:
    """Compact, plain-text snapshot — NO account IDs or keys, only figures."""
    parts = [f"Mode: {ctx.get('mode', '?')} (paper money) | Market: {ctx.get('market', '?')}"]
    parts.append(_fmt_acct("Account A (options only)", ctx.get('account'), ctx.get('positions')))
    parts.append(_fmt_acct("Account B (options + crypto)", ctx.get('accountB'), ctx.get('positionsB')))
    log = ctx.get('log') or []
    if log:
        parts.append("Recent agent decisions (newest first):")
        for e in log[:8]:
            parts.append(f"   - {e.get('ts', '')} [{e.get('acct', '')}] {e.get('summary', '')}")
    return "\n".join(parts)


def answer(question: str, ctx: dict) -> dict:
    """Return {'ok': bool, 'text': str}. Never raises — always a friendly message."""
    if not os.getenv('ANTHROPIC_API_KEY'):
        return {'ok': False, 'text': "Assistant isn't set up yet — add ANTHROPIC_API_KEY "
                                     "to your .env to enable it."}
    try:
        import anthropic
    except Exception:
        return {'ok': False, 'text': "Assistant needs the anthropic package: "
                                     "pip install -r requirements-assistant.txt"}
    q = (question or '').strip()
    if not q:
        return {'ok': False, 'text': "Ask me something about your numbers."}
    try:
        client = anthropic.Anthropic(timeout=30.0)
        msg = client.messages.create(
            model=MODEL,
            max_tokens=MAX_ANSWER_TOKENS,
            output_config={'effort': 'low'},     # a simple explain task — keep it cheap/fast
            system=CHARTER,
            messages=[{'role': 'user',
                       'content': f"DATA:\n{_format_context(ctx)}\n\nQUESTION: {q[:MAX_QUESTION_CHARS]}"}],
        )
        text = "".join(b.text for b in msg.content if b.type == 'text').strip()
        return {'ok': True, 'text': text or "(no answer)"}
    except Exception as e:
        return {'ok': False, 'text': f"Assistant error: {str(e)[:160]}"}

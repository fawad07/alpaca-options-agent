# Deploy the dashboard (public demo URL) — Render

This gets you a clickable **demo URL** for the submission. It hosts the live status
dashboard, which reads your paper account through the Alpaca MCP server.

## Steps
1. Code is already on GitHub with a `render.yaml`, so:
   - Go to **render.com** → **New → Blueprint**.
   - Pick the repo **`fawad07/alpaca-options-agent`** → Render reads `render.yaml`.
   *(Or: New → Web Service → same repo → it uses the build/start commands.)*
2. When prompted, set the **environment variables** (these are NOT in the repo):
   - `ALPACA_API_KEY` = your paper key
   - `ALPACA_SECRET_KEY` = your paper secret
   - `DASH_TOKEN` = *(optional)* a secret word — then the URL is `…/?token=WORD`
3. Click **Deploy**. First build takes a few minutes.
4. Render gives you a URL like `https://risk-gate-dashboard.onrender.com` → that's your
   **demo URL** for lablab.ai.

## Good to know
- **Free tier sleeps** after ~15 min idle; the first hit then takes ~50s to wake. For a
  live demo/recording, open it a minute early so it's warm.
- The page is **read-only** and the account is **paper** — but it does show your account
  status publicly. If you'd rather keep it private, set `DASH_TOKEN` and share the URL
  with `?token=…` only in your submission.
- The dashboard launches the Alpaca MCP server inside the web service, so it needs the
  keys above and Python 3.11 (both handled by `render.yaml`).
- If the free instance is tight on memory, you can instead just **demo the dashboard
  locally** (`.venv/bin/python dashboard.py`) in your video and submit the repo as the URL.

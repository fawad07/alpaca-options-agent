# 🩺 Daily Monitoring — the "no surprises" routine

Do this on each trading day: **Tue Sep 1, Wed Sep 2, Thu Sep 3.**
Best time: mid-morning and mid-afternoon **during US market hours**
(9:30 AM–4:00 PM ET  =  8:30 AM–3:00 PM CDT your time).

Everything is one command. From the project folder:
```bash
cd ~/Desktop/alpaca-options-agent
./check.sh
```

`check.sh` shows you three things. Here's exactly what to look for in each.

---

## ① LAST 8 CLOUD RUNS — is it running & healthy?
Each line is one run. The 2nd word is what matters:

- **`success`** ✅ — the run worked. Good.
- **`failure`** ❌ — something broke. Open the log:
  `gh run view <the-run-id> --log-failed` — or just tell me and I'll fix it.
- **`schedule`** = GitHub fired it automatically. **`workflow_dispatch`** = you (or I) fired it manually.

**Healthy day:** you should see several `success` runs with `schedule`, spaced ~15 min
apart, through the day. A stray old `failure` from before today is fine — ignore it.

**🚩 Red flag:** no new runs in the last ~30 min during market hours →
GitHub skipped them. Fix in 10 seconds: **`./trade-now.sh`** (forces a run).

---

## ② DECISION JOURNAL — what did it actually decide?
The table shows the newest runs at the bottom. Read the **"What happened"** column:

- **`BOUGHT 3x AAPL call; ...`** → a real trade was placed. 🎉
- **`no signal — all 7 symbols neutral/low-confidence`** → it ran fine, but nothing
  met the entry rule. **This is normal and OK** — not every run trades.
- **`N signal(s) fired but none opened (risk gate / ...)`** → a signal appeared but a
  **risk gate blocked it** on purpose. Also good — that's the whole point of Risk Gate.
- **`closed 1 position(s)`** → it hit a take-profit or stop and exited. Good.
- **`market closed — no action`** → ran outside trading hours. Ignore.
- **`ERROR: ...`** 🚩 → something failed mid-run. Tell me the message.

**Key mindset:** an empty dashboard is NOT a problem if the journal says
"no signal." The journal is the truth. Silence never means "broken" anymore —
it means the journal will *tell you* it was a quiet day.

---

## ③ LIVE ACCOUNT P&L — the numbers
Your account's real state, straight from Alpaca. This is what goes on the slide
later. During the week it's just for your awareness; you'll capture the FINAL
version Thursday after close (see `SUBMISSION_CHECKLIST.md`).

---

## The only two commands you need

| I want to… | Command |
|---|---|
| **Check status** (runs + journal + P&L) | `./check.sh` |
| **Force a trade pass now** (guarantee a run) | `./trade-now.sh` |

You can also force a run with no terminal at all:
**GitHub → your repo → Actions → risk-gate-agent → "Run workflow".**

---

## 30-second daily plan (that's it)
1. **Late morning:** `./check.sh`. See `success` runs + journal rows appearing? Done.
2. If there's a **gap** (no runs in 30 min): `./trade-now.sh`. Done.
3. **Mid-afternoon:** `./check.sh` once more.
4. See a **`failure`** or **`ERROR`**? Copy it here and I'll fix it.

Do that Tue/Wed/Thu and you're guaranteed trades on the board — with a full,
honest record of every decision for your presentation.

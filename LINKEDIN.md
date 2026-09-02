# LinkedIn posts — ready to paste (submit the post links, up to 5)

**How to tag:** type `@` then start typing the company name and pick it from the
dropdown — **Alpaca** and **lablab.ai** (picking from the dropdown is what makes it
a real tag/notification). Attach the suggested image to each post before posting.
Copy the submitted post's URL (··· menu → "Copy link to post") for the submission form.

You can post just #1, or #1 + #3, or all three — each is a valid submittable link.

---

## Post 1 — Launch (post today or Wednesday) · attach `cover.png`

I built an AI trading agent for the Alpaca × lablab.ai AI Trading Agents Hackathon — and it does something most trading bots won't: it's honest about not having a magic edge. 🛡️

Meet Risk Gate.

Most "AI trading bots" promise easy money. The catch: a backtest that dazzles you has usually just memorized the past. So I built the opposite of a hype bot.

Risk Gate is an autonomous options-trading agent that runs on an Alpaca paper account, entirely through Alpaca's official MCP server — the "AI drives the broker" pattern. Its real edge isn't a secret signal. It's:

🔹 Discipline — hard risk gates on every trade: ≤2% risked per trade, ≤5 open positions, a 5% daily-loss halt, defined-risk long options only.
🔹 Transparency — every trade is a simple, explainable rule, and every decision (traded, no-signal, or risk-blocked) is written to a public journal.
🔹 Honesty — I out-of-sample tested the signal. It beat buy-and-hold on 0 of 7 stocks. Instead of hiding that, I put it on a slide.

It trades itself in the cloud, applies the gates, and manages its own exits — fully autonomous. Paper money only. Every trade explainable, every risk capped.

Code (MIT, open source): github.com/fawad07/alpaca-options-agent

@Alpaca @lablab.ai
#AITrading #MCP #buildinpublic #Alpaca #quant #optionstrading

---

## Post 2 — Risk gate in action (Wednesday/Thursday) · attach a screenshot of `ACTIVITY.md`

Day 2 of building Risk Gate for the Alpaca × lablab.ai hackathon — and today the agent did exactly what it's designed to do: it refused to trade. 🛑

Once it filled to its 5-position cap, more buy signals fired — and the risk gate blocked every one. No over-leveraging, no chasing. Protect the account first, chase profit second.

And every one of those decisions is logged, timestamped, in the agent's public decision journal — so there's an honest record of what it did and didn't do, even on the quiet passes.

That's the whole philosophy: the edge is risk control, not a magic signal. Built entirely on Alpaca's MCP server. Paper account only.

github.com/fawad07/alpaca-options-agent

@Alpaca @lablab.ai
#riskmanagement #AITrading #buildinpublic #MCP

---

## Post 3 — Results (Thursday after close) · attach final P&L + equity-curve screenshot

Wrapping up Risk Gate for the Alpaca × lablab.ai AI Trading Agents Hackathon. 🛡️

One week of autonomous options trading on a paper account — every order placed through Alpaca's MCP server, every trade filtered through hard risk gates, every decision logged.

Final paper P&L: [FILL IN]
Trades placed: [FILL IN] · Risk-gate blocks: [FILL IN]

The honest takeaway: one week of options P&L is mostly luck. What I set out to prove is that an AI agent can be transparent, disciplined, and safe — every trade explainable, every risk capped, and the signal's real (limited) edge measured instead of oversold.

That's the version of "AI trading" I think is worth building.

Code (MIT): github.com/fawad07/alpaca-options-agent

@Alpaca @lablab.ai
#AITrading #Alpaca #buildinpublic #quant

---

**Note:** the numbers in Post 3 come straight from `./check.sh` / `results.py` and the
Alpaca equity-curve screenshot — the same ones you'll drop into slide 9 and WRITEUP.md.

// build_deck.js — generates presentation.pptx for Risk Gate (Honest Options AI)
const pptxgen = require("pptxgenjs");
const p = new pptxgen();
p.layout = "LAYOUT_WIDE";                 // 13.3 x 7.5

const BG="0B1018", CARD="141C28", CARD2="1B2533", LINE="2A3646",
      TEXT="E8EEF6", MUTED="8FA0B5", BLUE="5FA8FF", GREEN="3FB950",
      RED="F85149", AMBER="E0A13A", GREENBG="12251A", AMBERBG="271F12";
const SANS="Calibri", MONO="Courier New";

function bg(s){ s.background = { color: BG }; }
function foot(s, n){
  s.addText("Risk Gate · Honest Options AI", {x:0.5,y:7.05,w:6,h:0.3,
    fontFace:MONO,fontSize:9,color:MUTED,align:"left",isTextBox:true,margin:0});
  s.addText(String(n), {x:12.5,y:7.05,w:0.4,h:0.3,fontFace:MONO,fontSize:9,
    color:MUTED,align:"right",isTextBox:true,margin:0});
}
function card(s,x,y,w,h,fill,line){
  s.addShape(p.ShapeType.roundRect,{x,y,w,h,rectRadius:0.1,
    fill:{color:fill||CARD},line:{color:line||LINE,width:1}});
}

// ── Slide 1 — Title ───────────────────────────────────────────
let s = p.addSlide(); bg(s);
s.addText("🛡", {x:0.9,y:1.0,w:2,h:1.6,fontSize:110,align:"left",isTextBox:true,margin:0});
s.addText("ALPACA × LABLAB.AI  ·  AI TRADING AGENTS HACKATHON 2026",
  {x:0.95,y:2.75,w:11,h:0.4,fontFace:MONO,fontSize:13,color:BLUE,charSpacing:2,isTextBox:true,margin:0});
s.addText("Risk Gate", {x:0.9,y:3.1,w:11,h:1.5,fontFace:SANS,fontSize:76,bold:true,color:TEXT,isTextBox:true,margin:0});
s.addText("Honest Options AI", {x:0.95,y:4.55,w:11,h:0.7,fontFace:SANS,fontSize:30,bold:true,color:GREEN,isTextBox:true,margin:0});
s.addText("An autonomous options agent that trades through Alpaca's MCP server — its edge is discipline and risk gates, not hype.",
  {x:0.95,y:5.35,w:10.5,h:0.8,fontFace:SANS,fontSize:16,color:MUTED,isTextBox:true,margin:0});
s.addText("github.com/fawad07/alpaca-options-agent   ·   paper account only",
  {x:0.95,y:6.5,w:11,h:0.4,fontFace:MONO,fontSize:12,color:MUTED,isTextBox:true,margin:0});

// ── Slide 2 — The problem ─────────────────────────────────────
s = p.addSlide(); bg(s);
s.addText("The problem", {x:0.9,y:0.6,w:11,h:0.8,fontFace:SANS,fontSize:40,bold:true,color:TEXT,isTextBox:true,margin:0});
s.addText("Every “AI trading bot” promises easy money.", {x:0.9,y:1.9,w:11.5,h:0.7,fontFace:SANS,fontSize:26,color:TEXT,isTextBox:true,margin:0});
s.addText("Almost all of them lose —", {x:0.9,y:2.7,w:11.5,h:0.7,fontFace:SANS,fontSize:26,color:TEXT,isTextBox:true,margin:0});
s.addText("because a backtest that dazzles you has usually just memorized the past.",
  {x:0.9,y:3.4,w:11.5,h:0.9,fontFace:SANS,fontSize:26,bold:true,color:AMBER,isTextBox:true,margin:0});
card(s,0.9,4.9,11.5,1.4,CARD);
s.addText("So we built the opposite of a hype bot — one whose edge is risk control and honesty, not a secret signal.",
  {x:1.2,y:5.1,w:10.9,h:1.0,fontFace:SANS,fontSize:18,color:MUTED,valign:"middle",isTextBox:true,margin:0});
foot(s,2);

// ── Slide 3 — Thesis (3 pillars) ──────────────────────────────
s = p.addSlide(); bg(s);
s.addText("Our thesis", {x:0.9,y:0.6,w:11,h:0.8,fontFace:SANS,fontSize:40,bold:true,color:TEXT,isTextBox:true,margin:0});
s.addText("The edge isn't a magic prediction. It's discipline.", {x:0.9,y:1.5,w:11.5,h:0.6,fontFace:SANS,fontSize:20,color:MUTED,isTextBox:true,margin:0});
const pill=[["Transparent","Every trade is a simple, explainable rule — no black box."],
            ["Risk-gated","Hard caps on size, exposure, and losses protect the account first."],
            ["Honest","We validate out-of-sample and report what's real — no cherry-picking."]];
pill.forEach((c,i)=>{ const x=0.9+i*4.05; card(s,x,2.5,3.75,3.4,CARD);
  s.addShape(p.ShapeType.ellipse,{x:x+0.35,y:2.9,w:0.7,h:0.7,fill:{color:CARD2},line:{color:BLUE,width:1.5}});
  s.addText(String(i+1),{x:x+0.35,y:2.9,w:0.7,h:0.7,fontFace:MONO,fontSize:22,bold:true,color:BLUE,align:"center",valign:"middle",isTextBox:true,margin:0});
  s.addText(c[0],{x:x+0.3,y:3.85,w:3.2,h:0.6,fontFace:SANS,fontSize:22,bold:true,color:TEXT,isTextBox:true,margin:0});
  s.addText(c[1],{x:x+0.3,y:4.5,w:3.2,h:1.3,fontFace:SANS,fontSize:14,color:MUTED,isTextBox:true,margin:0}); });
foot(s,3);

// ── Slide 4 — Architecture flow ───────────────────────────────
s = p.addSlide(); bg(s);
s.addText("How it works", {x:0.9,y:0.6,w:11,h:0.8,fontFace:SANS,fontSize:40,bold:true,color:TEXT,isTextBox:true,margin:0});
const steps=[["Price data","daily bars"],["Signal","EMA · RSI"],["Risk gates","size / block"],["Alpaca MCP","place order"],["Paper account","$100k"]];
const bw=2.25, gap=0.35, x0=0.55, y=3.1, bh=1.7;
steps.forEach((st,i)=>{ const x=x0+i*(bw+gap); const mcp=(i===3);
  card(s,x,y,bw,bh,mcp?AMBERBG:CARD,mcp?AMBER:LINE);
  s.addText(st[0],{x:x+0.1,y:y+0.35,w:bw-0.2,h:0.6,fontFace:SANS,fontSize:17,bold:true,color:mcp?AMBER:TEXT,align:"center",isTextBox:true,margin:0});
  s.addText(st[1],{x:x+0.1,y:y+0.95,w:bw-0.2,h:0.5,fontFace:MONO,fontSize:12,color:MUTED,align:"center",isTextBox:true,margin:0});
  if(i<4) s.addText("▸",{x:x+bw-0.02,y:y+0.55,w:0.4,h:0.5,fontSize:22,color:BLUE,align:"center",isTextBox:true,margin:0}); });
s.addText("The signal decides direction; the risk gates decide if — and how big. Orders execute through Alpaca's MCP — autonomously each market-hours cycle, with every decision logged to a journal.",
  {x:0.9,y:5.3,w:11.5,h:0.9,fontFace:SANS,fontSize:16,color:MUTED,isTextBox:true,margin:0});
foot(s,4);

// ── Slide 5 — AI logic ────────────────────────────────────────
s = p.addSlide(); bg(s);
s.addText("The AI logic (transparent on purpose)", {x:0.9,y:0.6,w:11.5,h:0.8,fontFace:SANS,fontSize:36,bold:true,color:TEXT,isTextBox:true,margin:0});
card(s,0.9,1.9,5.6,4.2,CARD);
s.addText("Signal",{x:1.2,y:2.1,w:5,h:0.5,fontFace:SANS,fontSize:20,bold:true,color:BLUE,isTextBox:true,margin:0});
s.addText([
  {text:"Trend:  20-day EMA vs 50-day EMA",options:{bullet:true,breakLine:true}},
  {text:"Filter:  14-day RSI (skip overbought/oversold)",options:{bullet:true,breakLine:true}},
  {text:"Confidence scales with trend strength",options:{bullet:true,breakLine:true}},
  {text:"Weak setups → no trade",options:{bullet:true}}],
  {x:1.2,y:2.7,w:5.1,h:3.2,fontFace:SANS,fontSize:16,color:TEXT,paraSpaceAfter:14,isTextBox:true});
card(s,6.9,1.9,5.5,4.2,CARD);
s.addText("Action",{x:7.2,y:2.1,w:5,h:0.5,fontFace:SANS,fontSize:20,bold:true,color:BLUE,isTextBox:true,margin:0});
s.addText("Uptrend  →  BUY a CALL",{x:7.2,y:2.8,w:5,h:0.6,fontFace:SANS,fontSize:20,bold:true,color:GREEN,isTextBox:true,margin:0});
s.addText("Downtrend  →  BUY a PUT",{x:7.2,y:3.6,w:5,h:0.6,fontFace:SANS,fontSize:20,bold:true,color:RED,isTextBox:true,margin:0});
s.addText("Otherwise  →  no trade",{x:7.2,y:4.4,w:5,h:0.6,fontFace:SANS,fontSize:20,bold:true,color:MUTED,isTextBox:true,margin:0});
s.addText("Always defined-risk: a bought call or put, ~30 days out, near the money.",
  {x:7.2,y:5.2,w:5,h:0.8,fontFace:SANS,fontSize:13,color:MUTED,isTextBox:true,margin:0});
foot(s,5);

// ── Slide 6 — Risk gates grid ─────────────────────────────────
s = p.addSlide(); bg(s);
s.addText("Risk gates (the heart of it)", {x:0.9,y:0.6,w:11.5,h:0.8,fontFace:SANS,fontSize:40,bold:true,color:TEXT,isTextBox:true,margin:0});
const gates=[["≤ 2%","risked per trade"],["≤ 5","open positions"],["5%","daily-loss halt"],
             ["Long-only","never sells naked"],["14–60d","expiry window"],["+50 / −50%","take-profit / stop"]];
gates.forEach((g,i)=>{ const col=i%3, row=Math.floor(i/3);
  const x=0.9+col*4.05, yy=1.9+row*2.05; card(s,x,yy,3.75,1.8,CARD);
  s.addText(g[0],{x:x+0.3,y:yy+0.3,w:3.2,h:0.8,fontFace:SANS,fontSize:30,bold:true,color:AMBER,isTextBox:true,margin:0});
  s.addText(g[1],{x:x+0.3,y:yy+1.15,w:3.2,h:0.5,fontFace:SANS,fontSize:15,color:MUTED,isTextBox:true,margin:0}); });
s.addText("Real evidence: at the 5-position cap the agent REFUSED further signals — and every block is logged in the decision journal.",
  {x:0.9,y:6.15,w:11.5,h:0.5,fontFace:SANS,fontSize:14,color:MUTED,italic:true,isTextBox:true,margin:0});
foot(s,6);

// ── Slide 7 — MCP ─────────────────────────────────────────────
s = p.addSlide(); bg(s);
s.addText("Built on MCP", {x:0.9,y:0.6,w:11,h:0.8,fontFace:SANS,fontSize:40,bold:true,color:TEXT,isTextBox:true,margin:0});
s.addText("The hackathon's core theme — the agent trades THROUGH Alpaca's official MCP server.",
  {x:0.9,y:1.5,w:11.5,h:0.6,fontFace:SANS,fontSize:18,color:MUTED,isTextBox:true,margin:0});
s.addText("72", {x:0.9,y:2.5,w:2.6,h:1.6,fontFace:SANS,fontSize:90,bold:true,color:BLUE,align:"center",isTextBox:true,margin:0});
s.addText("MCP tools\navailable", {x:0.9,y:4.1,w:2.6,h:0.9,fontFace:SANS,fontSize:15,color:MUTED,align:"center",isTextBox:true,margin:0});
card(s,3.9,2.5,8.5,3.1,CARD);
s.addText("Tools the agent calls",{x:4.2,y:2.7,w:8,h:0.5,fontFace:SANS,fontSize:16,bold:true,color:TEXT,isTextBox:true,margin:0});
const tools=["get_account_info","get_option_contracts","get_option_snapshot","place_option_order","get_all_positions","close_position"];
tools.forEach((t,i)=>{ const col=i%2,row=Math.floor(i/2);
  s.addText("•  "+t,{x:4.3+col*4.0,y:3.35+row*0.62,w:3.9,h:0.5,fontFace:MONO,fontSize:15,color:GREEN,isTextBox:true,margin:0}); });
foot(s,7);

// ── Slide 8 — Honesty check ───────────────────────────────────
s = p.addSlide(); bg(s);
s.addText("The honesty check", {x:0.9,y:0.6,w:11,h:0.8,fontFace:SANS,fontSize:40,bold:true,color:TEXT,isTextBox:true,margin:0});
s.addText("0 of 7", {x:0.9,y:2.0,w:11.5,h:1.7,fontFace:SANS,fontSize:120,bold:true,color:AMBER,align:"center",isTextBox:true,margin:0});
s.addText("Out-of-sample, the signal beat buy-and-hold on ZERO of 7 stocks.",
  {x:0.9,y:3.9,w:11.5,h:0.6,fontFace:SANS,fontSize:22,color:TEXT,align:"center",isTextBox:true,margin:0});
card(s,2.4,4.9,8.5,1.4,CARD);
s.addText("So we don't claim a magic edge. We compete on discipline, safety & transparency. Most teams hide this — we put it on a slide.",
  {x:2.7,y:5.05,w:7.9,h:1.1,fontFace:SANS,fontSize:16,color:MUTED,align:"center",valign:"middle",isTextBox:true,margin:0});
foot(s,8);

// ── Slide 9 — Results (placeholders) ──────────────────────────
s = p.addSlide(); bg(s);
s.addText("Results", {x:0.9,y:0.6,w:11,h:0.8,fontFace:SANS,fontSize:40,bold:true,color:TEXT,isTextBox:true,margin:0});
s.addText("Aug 28 – Sep 4, 2026 · paper account PA327FXF8G6D", {x:0.9,y:1.5,w:11.5,h:0.5,fontFace:MONO,fontSize:13,color:MUTED,isTextBox:true,margin:0});
const stats=[["Final P&L","+1.82%"],["Trades","9"],["TP / Stops","2 / 0"],["Risk-gate blocks","87"]];
stats.forEach((st,i)=>{ const x=0.9+i*3.0; card(s,x,2.3,2.75,2.0,CARD);
  s.addText(st[1],{x:x+0.1,y:2.6,w:2.55,h:0.9,fontFace:SANS,fontSize:28,bold:true,color:GREEN,align:"center",isTextBox:true,margin:0});
  s.addText(st[0],{x:x+0.1,y:3.5,w:2.55,h:0.6,fontFace:SANS,fontSize:14,color:MUTED,align:"center",isTextBox:true,margin:0}); });
card(s,0.9,4.6,11.5,1.7,CARD2);
s.addText("Final equity $101,823  ·  +1.82% on the week  ·  2 take-profits captured (+54%, +74%)  ·  0 stop-losses\n[ add screenshot: Alpaca equity curve + P&L ]",
  {x:1.1,y:4.6,w:11.1,h:1.7,fontFace:SANS,fontSize:16,color:MUTED,italic:true,align:"center",valign:"middle",isTextBox:true,margin:0});
foot(s,9);

// ── Slide 10 — Close ──────────────────────────────────────────
s = p.addSlide(); bg(s);
s.addText("🛡", {x:0.9,y:0.9,w:2,h:1.4,fontSize:90,isTextBox:true,margin:0});
s.addText("Honest. Disciplined. Safe.", {x:0.9,y:2.5,w:11.5,h:1.1,fontFace:SANS,fontSize:52,bold:true,color:TEXT,isTextBox:true,margin:0});
s.addText("An autonomous options agent that's honest about risk. Every trade explainable, every risk capped.",
  {x:0.95,y:3.8,w:11,h:0.8,fontFace:SANS,fontSize:18,color:MUTED,isTextBox:true,margin:0});
s.addText([
  {text:"github.com/fawad07/alpaca-options-agent   ·   MIT",options:{breakLine:true}},
  {text:"Account: PA327FXF8G6D   ·   @lablabai  @AlpacaHQ",options:{}}],
  {x:0.95,y:5.2,w:11.5,h:1.0,fontFace:MONO,fontSize:14,color:BLUE,paraSpaceAfter:8,isTextBox:true,margin:0});

p.writeFile({ fileName: "submission/presentation.pptx" }).then(f=>console.log("wrote", f));

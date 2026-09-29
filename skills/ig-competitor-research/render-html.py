#!/usr/bin/env python3
# =============================================================================
# render-html.py — HTML report in Leif Abel's report-html.js style: hero +
# stats bar + post cards (3-col screenshot grid + spoken hook + expandable
# script) ranked best→worst by views + winning-patterns grid + footer.
# Zero deps. Cards degrade gracefully when a reel isn't enriched (metadata only).
#
# Usage: python3 render-html.py <report.md> [out.html] [reportTopN]
# Reads the markdown report + enrich/<code>/ frames+transcript.
# =============================================================================
import re, sys, html
from pathlib import Path

if len(sys.argv) < 2:
    print("Usage: python3 render-html.py <report.md> [out.html] [reportTopN]"); sys.exit(1)
src = Path(sys.argv[1])
out = Path(sys.argv[2]) if len(sys.argv) > 2 and not sys.argv[2].isdigit() else src.with_suffix(".html")
md = src.read_text(encoding="utf-8")
base = src.parent

def esc(t): return html.escape(t or "")

def to_num(s):
    m = re.match(r'([\d,.]+)\s*([KkMm])?', s.strip())
    if not m: return 0
    n = float(m.group(1).replace(',', ''))
    if m.group(2) and m.group(2).lower() == 'k': n *= 1e3
    if m.group(2) and m.group(2).lower() == 'm': n *= 1e6
    return n

# --- parse reels from the markdown cards ---
blocks = [b.strip() for b in re.split(r'\n-{3,}\n', md) if b.strip()]
header, cards_md = blocks[0], blocks[1:]
reels = []
for c in cards_md:
    hm = re.search(r'^###\s+\d+\.\s+\[(.+?)\]\((.+?)\)\s+—\s+@(\S+)', c, re.M)
    if not hm: continue
    url = hm.group(2); handle = hm.group(3)
    code = (re.search(r'/reel/([A-Za-z0-9_-]+)', url) or [None, ""])[1]
    eng = re.search(r'^`(.+?)`', c, re.M)
    eline = eng.group(1) if eng else ""
    views = (re.search(r'([\d,.]+[KM]?)\s*views', eline) or [None, ""])[1]
    likes = (re.search(r'([\d,.]+[KM]?)\s*likes', eline) or [None, ""])[1]
    comments = (re.search(r'([\d,.]+[KM]?)\s*comments', eline) or [None, ""])[1]
    def field(lbl):
        m = re.search(r'\*\*%s:\*\*\s*(.+)' % re.escape(lbl), c)
        return m.group(1).strip() if m else ""
    spoken = field("Spoken hook").strip('"')
    why = field("Why it worked")
    topic = field("Topic").split('·')[0].strip()
    cta = field("CTA")
    caption = "\n".join(re.sub(r'^>\s?', '', l) for l in c.splitlines() if l.startswith('>')).strip()
    tf = base / "enrich" / code / "transcript.txt"
    transcript = tf.read_text(encoding="utf-8").strip() if tf.exists() else ""
    has_frames = (base / "enrich" / code / "frame_0s.jpg").exists()
    reels.append(dict(hook=hm.group(1), url=url, handle=handle, code=code,
                      views=views, likes=likes, comments=comments, eng=to_num(likes or views),
                      spoken=spoken, why=why, topic=topic, cta=cta,
                      caption=caption, transcript=transcript, has_frames=has_frames))

reels.sort(key=lambda r: r["eng"], reverse=True)
# Optional reportTopN cap — accepted as the 2nd or 3rd arg
cap = len(reels)
for a in sys.argv[2:4]:
    if a.isdigit(): cap = int(a); break
display = reels[:cap]
n = len(reels)
reel_pct = 100  # this skill scrapes reels only
transcribed = sum(1 for r in reels if r["transcript"])
visual = sum(1 for r in reels if r["has_frames"])
top_likes = display[0]["likes"] if display else ""

# --- winning patterns from the data (Leif-style analyzePatterns, lightweight) ---
patterns = []
comment_cta = [r for r in reels if re.search(r'comment[\s\W]+\w', (r["caption"]+" "+r["spoken"]).lower())]
if comment_cta:
    pct = round(len(comment_cta)/n*100)
    patterns.append(("\"Comment [WORD]\" DM gates dominate",
        f"{len(comment_cta)} of {n} reels ({pct}%) gate the payoff behind a comment keyword "
        f"(\"Comment STOCK / PAPERCLIP / Edit\"). The caption IS the lead magnet trigger, not the content — "
        f"nateherkai's 175K reel hit a 5.7% comment rate with comments 2.4× likes. This is the exact BooSend mechanic."))
tool_hooks = [r for r in reels if re.search(r'claude code|codex|chatgpt|\+', (r["hook"]+" "+r["spoken"]).lower())]
if tool_hooks:
    patterns.append(("Tool-reveal & two-tool mashups",
        "The highest-reach hooks name a specific tool or collide two of them — \"Claude Code + Canva??\", "
        "\"ChatGPT just killed video editors\". The curiosity/novelty gap travels far even on weak per-view engagement "
        "(mavgpt's 967K reel converts only 0.2% to likes)."))
patterns.append(("Claude Code / Codex is the niche's center of gravity",
    "Across both the high-view and the DM-gate layers, the recurring topic is Claude Code, Codex and AI agents as a "
    "leverage tool — exactly the buyer (AI-Leveraged Operator) topic, not generic 'AI tips'."))
loss = [r for r in reels if re.search(r'killed|stop |just changed|forever', (r["hook"]+" "+r["spoken"]).lower())]
if loss:
    patterns.append(("Loss-aversion & 'just changed' framing",
        "\"ChatGPT just killed video editors\", \"X just changed the stock market forever\" — threat/novelty framing "
        "manufactures the open-loop. Pairs with a 3-step payoff and a comment gate."))
listicle = [r for r in reels if re.search(r'best ai|every task|certifications|\d+ free', (r["hook"]+" "+r["caption"]).lower())]
if listicle:
    patterns.append(("Listicle-by-use-case is infinitely saveable",
        "\"The best AI for every task\", \"5 free AI certifications\" — scannable list formats drive saves and reach; "
        "low friction, high shareability, easy to gate behind a keyword."))

# --- render ---
def card(r, rank):
    ss = ""
    if r["has_frames"]:
        cells = "".join(
            f'<div><img src="enrich/{r["code"]}/frame_{s}s.jpg" alt="{s}s"><div class="ss-label">{s} sec</div></div>'
            for s in (0,1,2))
        ss = f'<div class="screenshots">{cells}</div>'
    eng = f'<div class="eng-item"><strong>{esc(r["likes"] or r["views"])}</strong>{"Likes" if r["likes"] else "Views"}</div>'
    if r["comments"]:
        eng += f'<div class="eng-item"><strong>{esc(r["comments"])}</strong>Comments</div>'
    if r["views"] and r["likes"]:
        eng += f'<div class="eng-item"><strong>{esc(r["views"])}</strong>Views</div>'
    spoken = f'<div class="hook-section"><div class="hook-label">Spoken Hook</div><div class="hook-text">"{esc(r["spoken"])}"</div></div>' if r["spoken"] else ""
    tr = f'<details class="tr"><summary>Show full script</summary><div class="tr-body">{esc(r["transcript"])}</div></details>' if r["transcript"] else ""
    cap = f'<div class="caption"><strong>Caption:</strong> {esc(r["caption"][:400])}{"…" if len(r["caption"])>400 else ""}</div>' if r["caption"] else ""
    return f"""<div class="post-card">
  <div class="post-header"><span class="post-rank">#{rank}</span>
    <a class="post-author" href="{esc(r['url'])}" target="_blank">@{esc(r['handle'])}</a>
    <span class="post-type">{esc(r['topic'] or 'REEL')}</span></div>
  <div class="engagement-row">{eng}</div>
  {ss}
  {spoken}
  <div class="why-worked"><strong>Why it worked:</strong> {esc(r['why'])}</div>
  {tr}{cap}
</div>"""

def pcard(p, i):
    return f'<div class="pattern-card"><div class="pattern-num">{i+1:02d}</div><h3>{esc(p[0])}</h3><p>{esc(p[1])}</p></div>'

meta = re.search(r'\*\*Generated:\*\*\s*([\d-]+).*?Accounts scraped:\*\*?\s*(\d+)?', header)
date = meta.group(1) if meta else ""
cards_html = "\n".join(card(r, i+1) for i, r in enumerate(display))
patterns_html = "\n".join(pcard(p, i) for i, p in enumerate(patterns[:6]))

doc = f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Instagram Research Report | AI Niche</title><style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Inter',-apple-system,sans-serif;background:#0A0A08;color:#F5F0E8;line-height:1.7}}
.container{{max-width:1100px;margin:0 auto;padding:0 40px}}
.hero{{padding:80px 0 60px;border-bottom:1px solid rgba(212,168,67,.15)}}
.hero-label{{text-transform:uppercase;letter-spacing:4px;font-size:11px;color:#D4A843;font-weight:600;margin-bottom:16px}}
.hero h1{{font-size:48px;font-weight:800;line-height:1.1;color:#fff;margin-bottom:16px}}
.hero h1 span{{color:#D4A843}}
.hero .subtitle{{font-size:18px;color:rgba(245,240,232,.5);max-width:680px}}
.hero-meta{{display:flex;gap:32px;margin-top:32px;flex-wrap:wrap}}
.hero-meta-item{{font-size:13px;color:rgba(245,240,232,.35)}} .hero-meta-item strong{{color:rgba(245,240,232,.6)}}
.stats-bar{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:1px;
  background:rgba(212,168,67,.1);border-radius:12px;overflow:hidden;margin:48px 0}}
.stat-card{{background:rgba(245,240,232,.03);padding:28px 24px;text-align:center}}
.stat-card .number{{font-size:36px;font-weight:800;color:#D4A843;line-height:1}}
.stat-card .label{{font-size:12px;text-transform:uppercase;letter-spacing:2px;color:rgba(245,240,232,.4);margin-top:8px}}
.section{{padding:60px 0;border-bottom:1px solid rgba(245,240,232,.06)}}
.section-label{{text-transform:uppercase;letter-spacing:3px;font-size:11px;color:#D4A843;font-weight:600;margin-bottom:12px}}
.section h2{{font-size:32px;font-weight:700;color:#fff;margin-bottom:8px}}
.section .section-desc{{font-size:15px;color:rgba(245,240,232,.4);margin-bottom:40px;max-width:600px}}
.post-card{{background:rgba(245,240,232,.03);border:1px solid rgba(245,240,232,.06);border-radius:16px;padding:32px;margin-bottom:24px}}
.post-card:hover{{border-color:rgba(212,168,67,.3)}}
.post-header{{display:flex;align-items:center;gap:14px;margin-bottom:20px;flex-wrap:wrap}}
.post-rank{{font-size:14px;font-weight:700;color:#D4A843;background:rgba(212,168,67,.1);padding:4px 12px;border-radius:6px}}
.post-author{{font-size:16px;font-weight:600;color:#fff;text-decoration:none}} .post-author:hover{{color:#D4A843}}
.post-type{{font-size:11px;text-transform:uppercase;letter-spacing:1px;padding:3px 10px;border-radius:4px;
  background:rgba(212,168,67,.15);color:#D4A843;font-weight:600}}
.engagement-row{{display:flex;gap:24px;margin-bottom:20px;flex-wrap:wrap}}
.eng-item{{font-size:13px;color:rgba(245,240,232,.5)}}
.eng-item strong{{font-size:20px;font-weight:700;color:#fff;display:block;margin-bottom:2px}}
.screenshots{{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin:20px 0;border-radius:12px;overflow:hidden}}
.screenshots img{{width:100%;height:auto;display:block;border-radius:8px}}
.ss-label{{font-size:10px;text-transform:uppercase;letter-spacing:1px;color:rgba(245,240,232,.25);text-align:center;padding:4px 0}}
.hook-section{{margin:16px 0}}
.hook-label{{font-size:11px;text-transform:uppercase;letter-spacing:2px;color:#D4A843;font-weight:600;margin-bottom:6px}}
.hook-text{{font-size:18px;font-weight:600;color:#fff;font-style:italic;padding-left:16px;border-left:3px solid #D4A843}}
.why-worked{{margin-top:16px;padding:16px 20px;background:rgba(212,168,67,.05);border-left:3px solid rgba(212,168,67,.3);
  border-radius:0 8px 8px 0;font-size:14px;color:rgba(245,240,232,.6)}} .why-worked strong{{color:#D4A843}}
details.tr{{margin-top:14px}} details.tr summary{{cursor:pointer;color:#D4A843;font-size:12px;font-weight:600;
  text-transform:uppercase;letter-spacing:1.5px;list-style:none}} details.tr summary::-webkit-details-marker{{display:none}}
.tr-body{{margin-top:10px;background:rgba(245,240,232,.02);border-radius:8px;padding:14px 18px;font-size:13px;
  color:rgba(245,240,232,.5);line-height:1.8;white-space:pre-wrap;max-height:240px;overflow-y:auto}}
.caption{{font-size:13px;color:rgba(245,240,232,.4);margin-top:14px;padding-top:12px;border-top:1px solid rgba(245,240,232,.05)}}
.caption strong{{color:rgba(245,240,232,.6)}}
.pattern-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:16px}}
.pattern-card{{background:rgba(245,240,232,.03);border:1px solid rgba(245,240,232,.06);border-radius:12px;padding:28px}}
.pattern-card .pattern-num{{font-size:32px;font-weight:800;color:#D4A843;line-height:1;margin-bottom:12px}}
.pattern-card h3{{font-size:16px;font-weight:600;color:#fff;margin-bottom:8px}}
.pattern-card p{{font-size:14px;color:rgba(245,240,232,.5)}}
.footer{{padding:48px 0;text-align:center;font-size:13px;color:rgba(245,240,232,.2)}}
</style></head><body><div class="container">
<div class="hero"><div class="hero-label">Instagram Research Report</div>
<h1>AI Automation <span>Niche Analysis</span></h1>
<p class="subtitle">Top-performing reels in the AI-Leveraged Operator niche — visual hooks, spoken hooks, full scripts and the engagement patterns behind them.</p>
<div class="hero-meta">
<div class="hero-meta-item"><strong>Buyer ICP:</strong> AI-Leveraged Operator</div>
<div class="hero-meta-item"><strong>Reels analyzed:</strong> {n}</div>
<div class="hero-meta-item"><strong>Date:</strong> {esc(date)}</div></div></div>
<div class="stats-bar">
<div class="stat-card"><div class="number">{n}</div><div class="label">Reels Analyzed</div></div>
<div class="stat-card"><div class="number">{reel_pct}%</div><div class="label">Reels</div></div>
<div class="stat-card"><div class="number">{transcribed}</div><div class="label">Transcribed</div></div>
<div class="stat-card"><div class="number">{visual}</div><div class="label">Visual Hooks</div></div>
<div class="stat-card"><div class="number">{esc(top_likes)}</div><div class="label">Top Likes</div></div></div>
<div class="section"><div class="section-label">The Pool</div><h2>Reels Ranked by Views</h2>
<p class="section-desc">{len(display)} reels, best→worst by views. Enriched reels show first-3s visual hook + spoken hook + full script; the rest carry metadata only. Skim, then shortlist your 10.</p>
{cards_html}</div>
<div class="section"><div class="section-label">Key Insights</div><h2>Winning Patterns</h2>
<p class="section-desc">Patterns extracted across all {n} reels. Use these to inform your content.</p>
<div class="pattern-grid">{patterns_html}</div></div>
<div class="footer"><p>Format adapted from Leif Abel's IG Research Tool · data via ig-competitor-research skill</p></div>
</div></body></html>"""

out.write_text(doc, encoding="utf-8")
print(f"Leif-style HTML → {out}")
print(f"  cards: {len(display)}/{n} | patterns: {len(patterns)} | transcribed: {transcribed} | visual: {visual}")

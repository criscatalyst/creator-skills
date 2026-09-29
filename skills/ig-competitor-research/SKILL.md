---
name: ig-competitor-research
description: "Weekly Instagram competitor research via Chrome: scrapes the reels grids of the accounts in competitor-list.md (plus optional hashtag discovery for new creators), ranks reels by views, enriches the top ones with first-3s frames and a Whisper transcript of the spoken hook, and renders a ranked HTML report to shortlist ~10 reels to model. Use when the user wants to research Instagram competitors or their niche, see what's trending on IG, research a hashtag, find outliers on specific IG @handles, or pull competitors' reel hooks. YouTube outlier detection is the separate outliers skill."
---

# IG Competitor Research — Top 3 by Views Per Handle

A two-stage, disk-persisted weekly pipeline. **Stage 1** runs in phases against one Chrome tab, each phase WRITING its output to `research/` (never to a return message — a single agent can't hold the whole run and dies mid-way): **1A** a Sonnet URL agent scrolls every reels grid + runs Hashtag Discovery → `_pool_urls.json`; **1B** sequential metadata agents (one per ~45-reel chunk) visit each reel for views/likes/comments/caption → `_meta_<n>.json`, which the orchestrator merges through a JSON-repair parser. **Stage 2:** the orchestrator sorts by views, enriches the top `enrichTopN` via `enrich-reel.sh` (yt-dlp + ffmpeg frames + Whisper transcript) with a verify+retry tail, then writes the markdown and renders a Leif-style HTML report ranked best→worst. The user skims it and shortlists ~10 reels to publish.

## How to Trigger
- "research competitors" / "run content research"
- "what's trending in my niche"
- "find outliers on @handle, @handle, @handle"

## Prerequisites

- **Claude in Chrome extension** installed and connected (https://claude.ai/chrome). The skill drives a real Chrome window via the `mcp__claude-in-chrome__*` tools.
- **A `competitor-list.md` file** in the project root listing IG handles to scrape (any format that lists `@handle` or `instagram.com/handle/`). The orchestrator just needs to extract handles from it. If the file is missing, the user must name handles inline.
- **macOS launch command**: the skill uses `open -a "Google Chrome"` to launch Chrome if the extension isn't connected. On Linux/Windows, swap that for the OS-appropriate launcher.
- **A `research/` directory** at the project root. The skill creates it if missing.

## Inputs

### `competitor-list.md` — accounts + hashtags + settings
Read `competitor-list.md` from the project root. It has three parts (format in the README):
- **Accounts** — `@handle` per line. Scrape every one.
- **Hashtags** — `#tag` per line. Run Hashtag Discovery on each (in addition to the accounts).
- **Workflow settings** — `key: value` lines that tune the run. Honor them:
  - `reelsPerAccount` (default 4) — top-N reels by views per account.
  - `scroll` (default true) — scroll the grid to reach beyond the initial ~9 thumbnails (catches non-recent outliers, not just the latest posts).
  - `scrollRounds` (default 3) — number of scroll passes per grid. 3 ≈ 30-40 reels/account; 6 ≈ 60; 10 ≈ 100 (slower, deeper history). Ignored if `scroll` is false.
  - `enrichTopN` (default 40) — enrich only the N highest-view reels of the whole pool.
  - `reportTopN` (default 40) — how many ranked reels the HTML shows.
  - `whisperModel` (default base) — passed to `enrich-reel.sh`.

Override: the user can name handles/hashtags inline ("research @x @y", "research #aiagency") — those take precedence over the file for that run.

### Default mode = the weekly pipeline
This skill's normal run is the **two-stage weekly research** (see Main Skill Flow): scrape a wide metadata pool from all accounts+hashtags → enrich only the top `enrichTopN` by views → render the HTML report ranked best→worst. The goal is a pool the user skims to shortlist ~10 reels to publish. Enrichment (frames + transcript) is ON by default in this mode. A quick "just check @handle" ad-hoc run can skip enrichment.

---

## Architecture

```
Orchestrator (opens tab, assigns ID)
  → Stage 1A: URL agent — scrolled grids + hashtags → WRITES research/_pool_urls.json (returns summary only)
  → Stage 1B: metadata agents (chunked, SEQUENTIAL) → each WRITES research/_meta_<n>.json
  → Orchestrator merges _meta_*.json (with JSON repair), sorts by views, picks top enrichTopN
  → Stage 2: enrich-reel.sh on top enrichTopN (frames + transcript) → VERIFY + retry missing
  → Orchestrator writes markdown → render-html.py → Competitor-Research_YYYY-MM-DD.html
```

**Why this design:**
- **Persist to disk, never to a return message.** A full run (~34 grids + ~130 reel visits) is long enough that a single agent can hit its turn or token ceiling mid-run, and whatever lived only in its context is lost with it. So each phase WRITES its output to a file under `research/` and returns only a short summary line. If a phase dies, its predecessor's file is intact and you re-run only the failed phase. Nothing volatile.
- **Chunk the metadata pass.** ~130 reel visits × ~5s = the part that blows the turn budget. Split the deduped profile pool into ~45-reel chunks (sorted by views desc, so the highest-value reels are captured first) and run ONE sequential metadata agent per chunk, each writing `_meta_<n>.json`. 3 chunks ≈ 3 agents, each ~4-7 min — comfortably within a turn.
- **JSON-safety: agents hand-format JSON badly.** Captions contain `"` and newlines; an agent emitting JSON text by hand produces invalid JSON (unescaped quotes/newlines → `json.loads` fails on every file). Two defenses, use both: (1) tell agents to write via `JSON.stringify` (browser-produced, correctly escaped) as NDJSON; (2) the orchestrator ALWAYS merges through the tolerant repair parser below — it recovered 100% of records when files were corrupt. Never trust a metadata file to be valid JSON; repair on read.
- **Orchestrator owns tab creation; the LAST metadata agent owns teardown.** Splitting lifecycle keeps the orchestrator's view of Chrome state authoritative. All Stage-1 agents share the one tab the orchestrator opened; only the final chunk agent closes it.
- **One tab, serial.** Avoids Chrome's background-tab throttling and IG's anti-bot quirks (intersection observers don't fire on hidden tabs, IG soft-blocks parallel sessions). Phases run one after another against the same tab.
- **Two stages, cheap then expensive.** Stage 1 collects metadata for the whole pool (no downloads — can be 100+ reels fast). Stage 2 only downloads/transcribes the top `enrichTopN` by views. You never pay enrichment cost on reels nobody will shortlist.
- **Enrichment: verify, then retry the tail.** Running `enrich-reel.sh` 4-parallel rate-limits IG at the tail — the last few reels lose their download (no frames) or Whisper output (no transcript). After the parallel pass, VERIFY every top-N code has `frame_0s.jpg` + `transcript.txt`, then retry the missing ones SEQUENTIALLY (single-stream dodges the rate-limit). Today this recovered 7/7.
- **Scroll the grid.** 3 scroll rounds widen the window past the initial ~9 thumbnails, so high-view OLDER reels surface — not just the latest posts. Cost is a few seconds per account; the payoff is a representative pool, not a recency snapshot.
- **Top N by views, not recency.** View-sort within each account's scrolled window surfaces its strongest reels; the global pool sort then ranks everything best→worst for the report.

---

## Hashtag Discovery (optional pre-step — surfaces new creators)

Use when the user gives hashtags instead of / alongside handles. The orchestrator (or scraper) navigates the SAME tab to each hashtag's explore grid and pulls the top reels by views — these are reel URLs from accounts you may not know. They feed straight into the scraper's metadata pass (the existing per-reel `navigate → extract` in STEP 2), and into Enrichment if enabled.

Why DOM, not yt-dlp: yt-dlp's Instagram profile/hashtag listing extractors are broken (IG changes them constantly — verified failing). The logged-in Chrome grid is the only reliable discovery source. (yt-dlp is still used, reliably, for the single-reel *download* in Enrichment.)

Per hashtag, ONE `browser_batch`: navigate → wait 8s → extract. Extraction JS:

```js
(() => {
  const parseViews = s => {
    const m = s.match(/(\d+(?:\.\d+)?)([KMB])/i);
    return m ? parseFloat(m[1]) * ({K:1e3,M:1e6,B:1e9}[m[2].toUpperCase()]) : (parseInt(s.replace(/,/g,''),10) || null);
  };
  const seen = new Set(), out = [];
  for (const a of document.querySelectorAll('a[href*="/reel/"]')) {
    if (seen.has(a.href)) continue; seen.add(a.href);
    out.push({ url: a.href, views: parseViews(a.innerText.trim()) });
  }
  return out.sort((x,y) => (y.views||0)-(x.views||0)).slice(0, 12);
})()
```

Navigate to `https://www.instagram.com/explore/tags/<TAG_WITHOUT_HASH>/`. Pool the top reels across all hashtags, keep the top ~10-15 by views, dedupe against any profile reels, then run STEP 2 metadata extraction on them.

### When the tag grid returns 0 reels — fallback chain (IG gates `/explore/tags/`)

A 0-reel result is NOT always a hidden tab. In 2026 IG increasingly **gates `/explore/tags/` and redirects it into keyword search** (the page shows a search box / account results instead of a reel grid). Walk this chain in order, stop at the first that yields reels:

1. **Re-hydrate once.** Wait another 5s and re-run the extractor — slow loads look like gating. (If the tab is genuinely hidden/backgrounded, ALL navigation returns empty, including profiles → that's the hidden-tab case: stop and ask the user to make the tab visible.)
2. **Keyword-search fallback.** Navigate to `https://www.instagram.com/explore/search/keyword/?q=%23<TAG>` and extract from the results with the SAME JS (it still matches `a[href*="/reel/"]`). This is the surface IG now routes tags into.
3. **Top-results page.** Try `https://www.instagram.com/explore/tags/<TAG>/?__a=1` is dead; instead open the tag via the search UI result (click the top `#tag` row) and read the grid that loads.
4. **Seed-account expansion (always works).** If 1-3 all return 0, switch discovery model: take the handles you DID find (from profile inputs or any reels already surfaced), open each profile's `/reels/` grid, and ALSO scrape the "Suggested for you" / related-accounts strip (`header a[href^="/"][role="link"]`) to surface adjacent creators. This sidesteps hashtag gating entirely.

Always `log()` which tier produced the reels (e.g. "hashtag grid gated → used keyword search" / "→ fell back to seed-account expansion"), and say so in the report's Pattern line — never present a degraded run as full hashtag discovery. If every tier returns 0, report that hashtag discovery is unavailable this session and proceed with whatever profile reels exist.

### ⚠️ Hashtag finds carry NO view counts (2026 reality) — they are unranked

As of this run, the keyword-search surface IG routes tags into renders **`/p/` shortcode links with no view count in the DOM** (and the `/explore/tags/` grid is gated). So hashtag finds come back with `views: null`. The report body is strictly **view-ranked**, so unranked hashtag finds CANNOT slot into it. Treat hashtag discovery as a **creator-discovery signal only**: collect the URLs (and the handles behind them — new accounts to add to `competitor-list.md`), but do NOT mix them into the view-sorted top-N body or the enrichment set. Note the limitation explicitly in the Pattern line (e.g. "hashtag discovery was metadata-only this run — IG no longer exposes tag view counts, so N hashtag finds are unranked and excluded from the body"). If a future IG change restores view counts on the tag/keyword grid, hashtag finds rejoin the ranked pool automatically.

---

## Stage 1A — URL Agent Brief (grids + hashtags → disk)

⚠️ **Do NOT use a single agent for grids AND metadata.** That monolith dies mid-run and loses everything (see Architecture). Stage 1A collects only URLs (grid-light), writes them to disk, and returns a summary.

Spawn with `subagent_type: general-purpose`, `model: sonnet`. Substitute the placeholders below — `{RESEARCH_DIR}` is the ABSOLUTE path to this run's research directory (e.g. `$HOME/research`, resolved by the orchestrator so the subagent's cwd doesn't matter), plus `{HANDLES_JSON}`, `{HASHTAGS_JSON}`, `{TAB_ID}`, `{REELS_PER_ACCOUNT}`, `{SCROLL_ROUNDS}`:

```
You are collecting Instagram reel URLs for content research. A Chrome tab already exists (TAB_ID {TAB_ID}), logged into Instagram. Use ONLY that tab. Do NOT create a new tab. Do NOT close the tab (a later agent closes it). Do NOT force-focus Chrome (no osascript activate / wmctrl).

HANDLES: {HANDLES_JSON}
HASHTAGS: {HASHTAGS_JSON}
REELS_PER_ACCOUNT: {REELS_PER_ACCOUNT}
SCROLL_ROUNDS: {SCROLL_ROUNDS}

STEP 0 — Load tools: ToolSearch "select:mcp__claude-in-chrome__navigate,mcp__claude-in-chrome__javascript_tool,mcp__claude-in-chrome__browser_batch"

STEP 1 — Per handle, ONE browser_batch:
  1. navigate → https://www.instagram.com/{HANDLE}/reels/
  2. javascript_tool → `new Promise(r => setTimeout(() => r('w'), 7000))`
  3. javascript_tool → `await (async()=>{for(let i=0;i<{SCROLL_ROUNDS};i++){window.scrollBy(0,2000);await new Promise(r=>setTimeout(r,1500));}return 'scrolled';})()`
  4. javascript_tool → extract:
    (() => {
      const parseViews = s => { const m = s.match(/(\d+(?:\.\d+)?)([KMB])/i); return m ? parseFloat(m[1]) * ({K:1e3,M:1e6,B:1e9}[m[2].toUpperCase()]) : (parseInt(s.replace(/,/g,''),10)||null); };
      const all = [...document.querySelectorAll('a[href*="/reel/"]')];
      const isPinned = a => !!a.querySelector('svg[aria-label="Pinned post icon"]');
      const nonPinned = all.filter(a => !isPinned(a)).map(a => ({ url: a.href, views: parseViews(a.innerText.trim()) }));
      const topN = [...nonPinned].sort((a,b)=>(b.views||0)-(a.views||0)).slice(0,{REELS_PER_ACCOUNT});
      return { nonPinnedCount: nonPinned.length, topN };
    })()

If nonPinnedCount < 3 on the FIRST handle → the MCP tab is hidden/backgrounded. STOP, return {"error":"hydration_failed"}. (A LATER handle returning 0 = private/empty: record views null, continue. Only the FIRST handle failing signals a hidden tab.)

CRITICAL: pinned detection is `svg[aria-label="Pinned post icon"]` — never an innerText `/Nx/` regex (unreliable, only shows on hover).

STEP 2 — Hashtags. Per hashtag, ONE browser_batch: navigate → https://www.instagram.com/explore/tags/{TAG}/ → wait 7s → extract (same parseViews + dedupe, slice 12). If a tag returns 0: wait 5s + retry once; still 0 → keyword fallback https://www.instagram.com/explore/search/keyword/?q=%23{TAG} (same JS); still 0 → skip and note it. NOTE: the keyword surface returns /p/ links with NO view counts (views null) — that's expected, collect them anyway as discovery signal.

STEP 3 — Write the pool to {RESEARCH_DIR}/_pool_urls.json using the **Write tool** with this exact shape:
{ "handles": { "<handle>": [{"url":"...","views":123000}, ...], ... },
  "hashtags": { "<tag>": [{"url":"...","views":null}, ...], ... },
  "hashtag_notes": "which tags gated/skipped/fallback used" }

STEP 4 — Return ONE short line only: handles scraped, total reel URLs, total hashtag URLs, any errors. Do NOT paste the JSON (it's on disk). Do NOT close the tab.
```

After Stage 1A returns, the ORCHESTRATOR (you, in Bash/python) reads `_pool_urls.json`, dedupes by URL (strip `?` query), keeps only `source:'profile'` reels for the ranked body, sorts by views desc, and splits into chunk files `_chunk_1.json … _chunk_k.json` of ~45 reels each (`ceil(n/3)` is a good chunk size).

## Stage 1B — Metadata-Chunk Agent Brief (one per chunk, SEQUENTIAL)

Spawn ONE agent per chunk, **sequentially** (never parallel — one tab, IG soft-blocks parallel sessions). Each reads its chunk file, visits every reel, writes `_meta_<n>.json`. The agent for the **last** chunk also closes the tab.

Substitute `{N}` (chunk number), `{RESEARCH_DIR}` (absolute research dir path), `{TAB_ID}`, and `{IS_LAST}` (true/false):

```
You are extracting Instagram reel metadata. A Chrome tab exists (TAB_ID {TAB_ID}), logged into Instagram. Use ONLY that tab. Do NOT create or (unless told) close any tab. Do NOT force-focus Chrome.

STEP 0 — Load tools: ToolSearch "select:mcp__claude-in-chrome__navigate,mcp__claude-in-chrome__javascript_tool,mcp__claude-in-chrome__browser_batch"

STEP 1 — Read {RESEARCH_DIR}/_chunk_{N}.json (Read tool). Array of {url, views, handle, source}.

STEP 2 — For EACH reel, batch 6 per browser_batch. Per reel chain:
  1. navigate → reel url
  2. javascript_tool → `new Promise(r => setTimeout(() => r('w'), 2500))`
  3. javascript_tool → extract (NOTE: returns a JSON STRING via JSON.stringify — this guarantees valid escaping of quotes/newlines in captions):
    (() => {
      const t = document.querySelector('meta[property="og:title"]')?.content || '';
      const d = document.querySelector('meta[property="og:description"]')?.content || '';
      const c = t.match(/: "([\s\S]*)"$/);
      return JSON.stringify({ caption: c ? c[1] : t,
        likes: d.match(/([\d.,]+[KMB]?)\s+likes?/i)?.[1] || null,
        comments: d.match(/([\d.,]+[KMB]?)\s+comments?/i)?.[1] || null,
        date: d.match(/on\s+([A-Z][a-z]+\s+\d{1,2},\s+\d{4})/)?.[1] || null });
    })()
If a reel errors/redirects, record caption null and move on — retry at most once.

STEP 3 — Merge each input reel (url, views, handle) with its extracted fields + hook = first line of caption trimmed to 120 chars. Write to {RESEARCH_DIR}/_meta_{N}.json as a JSON array, using the **Write tool**. ⚠️ Write the caption/hook strings EXACTLY as the browser returned them (already escaped) — do NOT re-pretty-print or hand-edit quotes/newlines. (The orchestrator also runs a repair parser on read, so minor breakage is tolerated, but clean output is preferred.)

STEP 4 — {IS_LAST ? "This is the LAST chunk: after writing, load mcp__claude-in-chrome__tabs_close_mcp via ToolSearch and call it on tabId {TAB_ID}." : "Do NOT close the tab — more chunks follow."}

STEP 5 — Return ONE line only: N reels processed, M with captions, errors. Do NOT paste the JSON.
```

## JSON repair parser (orchestrator ALWAYS runs this on merge)

Metadata files may be invalid JSON (agents hand-format captions with raw `"`/newlines). Never `json.load` a `_meta_*.json` directly — always merge through this tolerant parser, which anchors on the known key order and re-emits clean JSON. It recovered 100% of records when files were corrupt:

```python
import re, json, os
R = os.path.expanduser('~/research')   # this run's research dir (adjust if you run from elsewhere)
def repair(path):
    txt = open(path).read()
    recs = []
    for b in re.split(r'\n  \},?\n', txt):     # object blocks
        if '"url"' not in b: continue
        url = re.search(r'"url":\s*"([^"]+)"', b).group(1)
        vm = re.search(r'"views":\s*(null|[\d.]+)', b); views = None if vm.group(1)=='null' else float(vm.group(1))
        hm = re.search(r'"handle":\s*(null|"[^"]*")', b).group(1).strip('"'); handle = None if hm=='null' else hm
        cap_m = re.search(r'"caption":\s*"(.*?)",\s*\n\s*"likes"', b, re.DOTALL)   # anchor on next key
        cap = cap_m.group(1) if cap_m else None
        lk = re.search(r'"likes":\s*(null|"[^"]*")', b); likes = lk.group(1).strip('"') if lk and lk.group(1)!='null' else None
        cm = re.search(r'"comments":\s*(null|"[^"]*")', b); comments = cm.group(1).strip('"') if cm and cm.group(1)!='null' else None
        hk_m = re.search(r'"hook":\s*"(.*?)"\s*$', b, re.DOTALL); hook = hk_m.group(1) if hk_m else None
        recs.append({'url':url,'views':views,'handle':handle,'source':'profile','caption':cap,'likes':likes,'comments':comments,'date':None,'hook':hook})
    return recs
allr = []
for i in (1,2,3): allr += repair(f'{R}/_meta_{i}.json')
allr.sort(key=lambda r: -(r.get('views') or 0))
json.dump(allr, open(f'{R}/_meta_all.json','w'), indent=1, ensure_ascii=False)
```

---

## Enrichment — Visual + Spoken Hook

After the scraper returns the pooled reels (metadata only), sort the whole pool by views and enrich the **top `enrichTopN`** (default 40). Enriching the entire pool is wasteful — the user only shortlists from the top. For each of those reels, call the helper (run them in parallel, ~4 at a time, each a separate Bash call):

```bash
bash "${CLAUDE_SKILL_DIR}/enrich-reel.sh" "<reel-url>" "<project_root>/enrich" base
```

It downloads the reel via yt-dlp using the logged-in **Chrome cookies** (`--cookies-from-browser chrome` — works even when Chrome isn't running, as long as it's logged into IG), then:
- **Visual hook** → `enrich/<code>/frame_0s.jpg` `frame_1s.jpg` `frame_2s.jpg` (ffmpeg, first 3 seconds).
- **Spoken hook** → `enrich/<code>/hook.txt` (first spoken line) + `transcript.txt` (full).
- Prints one JSON line: `{"code","dir","frames":true/false,"transcript":true/false}` (or `{"error":"download_failed"}` for private/removed reels — skip those, don't retry).

The video is deleted after extraction (only frames + transcript are kept; ~200KB/reel). Whisper model from `whisperModel` (default `base` — `tiny` mangles jargon: ChatGPT→"Chat TV", Claude Code→"cloud code"; `base` is much cleaner). `<code>` is the reel shortcode, matching the URL so you map results back.

**⚠️ Verify + retry the tail (REQUIRED, not optional).** Running 4-parallel rate-limits IG on the last few reels — they come back with no frames (`download_failed`) or no transcript (Whisper got no audio / was killed). After the parallel pass, check every top-N code for BOTH `frame_0s.jpg` and `transcript.txt`; collect the misses; re-run `enrich-reel.sh` on them **sequentially** (single-stream sidesteps the rate-limit). Today this recovered 7/7. Don't write the report until this passes.

```python
import json, os
R = os.path.expanduser('~/research')
codes = [u.rstrip('/').split('/')[-1] for u in json.load(open(f'{R}/_enrich_urls.json'))]
missing = [c for c in codes if not (os.path.exists(f'{R}/enrich/{c}/frame_0s.jpg')
                                     and os.path.exists(f'{R}/enrich/{c}/transcript.txt'))]
# → re-run enrich-reel.sh on the URLs for `missing`, one at a time, then re-check.
```

**Grammar pass (run AFTER verify+retry, on all top-N).** Even `base` mis-hears AI brand names. Normalize across every `enrich/<code>/transcript.txt` + `hook.txt` before writing the report — case-insensitive find-replace: ChatGPT (←"Chat TV"/"Chat GPT"), Claude / Claude Code (←"Clod"/"Clawd"/"cloud code"), Codex (←"codecs"), Ollama (←"Olama"), n8n (←"N8N"/"nAton"), Midjourney, Cursor, Perplexity, Remotion. Idempotent — safe to re-run after retries.

Verified end-to-end on real IG reels: cookie auth (works headless), yt-dlp download, ffmpeg frames, Whisper, JSON — all functioning. Needs Chrome logged into IG.

---

## Report Format (you, the orchestrator, write this directly)

Take the scraper's combined JSON, sort the whole pool by views high-to-low, and write the top `reportTopN` (default 40) into the markdown — the body is strictly view-ranked, no editorial reordering. (The pool can be larger than `reportTopN`; the overflow stays unlisted — that's intentional, the user only shortlists from the top.)

For each reel, add:
  - **Topic tag** — Education / Journey / Hot take / Lifestyle / Behind-the-scenes / Build-in-public / Story / Tutorial
  - **CTA type** — Comment-bait / Follow-bait / Save-bait / DM / None
  - **Why it worked** — one line on hook archetype, format mechanic, topic angle, or engagement trigger

Add a **Pattern paragraph** at the top — 2-3 sentences on what repeats across the pool: dominant themes, hook archetypes, format mechanics, comment-keyword games, etc. If a handle had a scrape error, omit it from the body but call it out in the Pattern line.

Write to: `<project_root>/Competitor-Research_<DATE>.md` (computed in step 2)

Format EXACTLY:

```
# Competitor Research — Top Reels

**Generated:** YYYY-MM-DD | **Accounts scraped:** N | **Reels in report:** M (top reportTopN by views, from a pool of P)

> **Pattern:** <2-3 sentences on what's repeating across the pool — dominant themes, hook archetypes, format mechanics, comment-keyword games. Be specific.>

---

### 1. [<HOOK — first line of caption>](<URL>) — @handle

`<views> views · <likes> likes · <comments> comments` · <like%> like rate · <comment%> comment rate · posted <date>

**Topic:** <tag> · **CTA:** <type>

**Why it worked:** <one line>

[IF ENRICHED, add these two lines — omit if enrichment was off or failed for this reel:]
**Spoken hook:** "<contents of hook.txt>"
**Visual hook:** ![0s](research/enrich/<code>/frame_0s.jpg) ![1s](research/enrich/<code>/frame_1s.jpg) ![2s](research/enrich/<code>/frame_2s.jpg)

> <full caption, blockquoted. Preserve line breaks. Don't truncate.>

---

### 2. [<HOOK>](<URL>) — @handle

[same structure, repeat for every reel in the pool, ordered by views high-to-low]
```

RULES:
- Format view counts human-readable (1.1M, 296K, 47.3K). Likes/comments same.
- Engagement rates: likes ÷ views × 100, rounded to 1 decimal (e.g. "1.8%"). Comments same.
- HOOK is the first line of the caption. Trim emojis only if they break the markdown link.
- Strict view-sort across the whole pool — no editorial reordering.
- No closing wrap-up. The list IS the report.

---

## Main Skill Flow (what YOU do, the orchestrator)

1. **Resolve sources + settings.** Read `competitor-list.md` from the project root → accounts, hashtags, and workflow settings (`reelsPerAccount`, `scroll`, `enrichTopN`, `reportTopN`, `whisperModel`). Inline handles/hashtags from the user override the file. If no handles AND no hashtags anywhere, ask.
2. **Compute the output path.** Today's date `YYYY-MM-DD` → `<project_root>/Competitor-Research_<DATE>.md`. `rm` any existing file at that path for a clean Write.
3. **Open the Chrome tab.** Load Chrome tab tools via `ToolSearch` (`select:mcp__claude-in-chrome__tabs_context_mcp,mcp__claude-in-chrome__tabs_create_mcp`). Then:
   - Call `tabs_context_mcp`. If "No MCP tab groups found" AND Chrome isn't running (`pgrep -x "Google Chrome"`), launch Chrome (`open -a "Google Chrome"`), wait ~2s, then `tabs_context_mcp` with `createIfEmpty: true`. If Chrome is running but the group is empty, `createIfEmpty: true`. If the group exists, `tabs_create_mcp` for a fresh tab.
   - Capture the new tab's ID → `{TAB_ID}`.
   - If "Browser extension is not connected", STOP and ask the user to connect the Claude in Chrome extension (https://claude.ai/chrome) and make the MCP tab visible (IG won't hydrate behind another window). Wait for confirmation. Don't force-focus Chrome.
4. **Stage 1A — collect URLs to disk.** Spawn the URL agent (brief above) with `{HANDLES_JSON}`, `{HASHTAGS_JSON}`, `{TAB_ID}`, `{REELS_PER_ACCOUNT}`, `{SCROLL_ROUNDS}`. It scrolls every grid + runs hashtag discovery, writes `_pool_urls.json`, returns a summary, leaves the tab open. If it returns `hydration_failed`, stop and ask the user to make the MCP tab visible, then retry.
5. **Dedupe + chunk (orchestrator, Bash/python).** Read `_pool_urls.json`, dedupe by URL, keep `source:'profile'` reels for the ranked body (hashtag finds are unranked — see Hashtag section), sort by views desc, split into `_chunk_1..k.json` (~45 reels/chunk).
6. **Stage 1B — metadata pass, chunked + SEQUENTIAL.** Spawn ONE metadata-chunk agent per chunk, one after another (NOT parallel). Each writes `_meta_<n>.json`; the last one closes the tab. Then merge all `_meta_*.json` through the **JSON repair parser** → `_meta_all.json` (sorted by views). Never `json.load` the chunk files directly.
7. **Stage 2 — enrich the top `enrichTopN`.** Take the top `enrichTopN` (default 40) URLs from `_meta_all.json` → write `_enrich_urls.json`. Run `enrich-reel.sh` on each, ~4 in parallel (`xargs -P4`). Then **verify + sequential retry** of any code missing frames/transcript (REQUIRED — see Enrichment). Then the grammar normalization pass. Long runs auto-background — that's fine, you're notified on completion; data is on disk so nothing is lost.
8. **Write the markdown report.** Generate the Report Format for the top `reportTopN` reels — best done with a python script reading `_meta_all.json` + the `enrich/<code>/` files (computes view formatting + like/comment rates, detects CTA/topic from the caption, pulls spoken hook from `hook.txt`, wires frame paths). Body strictly view-ranked. One Write.
9. **Render the HTML (this is the deliverable).** `python3 "${CLAUDE_SKILL_DIR}/render-html.py" <report.md> <reportTopN>` → Leif-style `Competitor-Research_<DATE>.html`. `open` it.
10. **Clean up temp files** (`_pool_urls.json`, `_chunk_*`, `_meta_1..k`, `_enrich_urls.json`, etc.) — keep `_meta_all.json` + the `.md`/`.html` + the `enrich/` dir.
11. Report both paths; tell the user to skim the HTML and shortlist ~10 reels to publish.

---

## Rules of Thumb
- **Persist every phase to disk; agents return summaries, not data.** A single agent running ~34 grids + ~130 metadata visits can die mid-run and take its in-context data with it. Phase it: URL agent → disk, chunked metadata agents → disk, merge from disk. If a phase fails, re-run only that phase.
- **Never `json.load` a `_meta_*.json` directly — always run the repair parser.** Agents hand-format captions with unescaped quotes/newlines → invalid JSON. The repair parser recovered 100%.
- **Enrichment: verify + sequential retry the tail.** 4-parallel rate-limits IG on the last reels (missing frames/transcript). Always verify all top-N codes have both, retry misses one-at-a-time, THEN write the report.
- **Single tab, serial phases — no parallel agents.** One Chrome tab; IG soft-blocks parallel sessions. Metadata chunks run sequentially.
- **Hashtag finds are unranked (no view counts in 2026).** IG routes tags into keyword search → `/p/` links with `views:null`. Use them as creator-discovery only; exclude from the view-ranked body; note it in the Pattern line.
- **Don't force-focus Chrome.** No `osascript activate` / `wmctrl -a`. Only launch Chrome when it's not already running (`pgrep -x "Google Chrome"`); after launch use `tabs_context_mcp` with `createIfEmpty:true`.
- Hydration failure on the FIRST handle (<3 non-pinned reels even after scroll) means the MCP tab is hidden/backgrounded → stop, ask the user to make the tab visible, retry. A later handle returning 0 is just a private/empty account — record and continue.
- Scroll `scrollRounds`× per grid (default 3). NO window resize.
- Pinned detection is `svg[aria-label="Pinned post icon"]` — never the innerText regex.
- Lifecycle ownership: orchestrator opens the tab + assigns the ID; Stage-1A and all-but-last Stage-1B agents leave it open; the LAST metadata-chunk agent closes it.
- Two-stage: collect a wide metadata pool first, enrich only the top `enrichTopN`. Never enrich the whole pool.
- HTML (render-html.py, Leif-style) is the deliverable; markdown is the source of truth. Report shows the top `reportTopN`, strictly view-ranked.

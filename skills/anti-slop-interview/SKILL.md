---
name: anti-slop-interview
description: Guided 30-minute interview that builds a complete creator persona file (~/CLAUDE.md) so Claude writes content that sounds like the user — not generic AI. Trigger when the user asks to "set up my voice", "build my persona", "teach Claude to be me", "anti-slop interview", or runs the skill explicitly. Outputs four sections (About me, Voice rules, Anti-slop rules, Offer & goals) plus a voice-samples reference file.
---

# Anti-Slop Interview

Run a single end-to-end interview that loads the user's identity, voice, anti-AI-detection rules, and offer into `~/CLAUDE.md`. The result: every script, email, and DM the user later asks Claude to write starts with this context already loaded.

## Outcome

After this skill runs, the user has:

- `~/CLAUDE.md` with four sections: **About me**, **Voice rules**, **Anti-slop rules**, **Offer & goals**
- `~/memory/voice-samples.md` containing the 5 raw writing samples
- A verification test (one generated script) that proves the persona is loaded

## Operating principles

1. **One session, one shot.** All five steps happen in the current Claude Code session. Do NOT advise the user to restart or open a new session mid-interview — the working memory of the conversation is what makes the final save coherent.
2. **One question at a time.** Never dump a list of questions. Ask one, wait, follow up if vague, move on.
3. **The user does NOT touch files.** You write everything. The user only talks. If they ask "where do I save this?" the answer is always "you don't — I'll handle it at the end."
4. **Don't save partial files between steps.** Hold everything in conversation context. Save once at Step 5.
5. **If `~/CLAUDE.md` already exists** with real content, ask once: "I see an existing CLAUDE.md. Replace it, merge new sections in, or back it up first?" Default to backup-then-replace if they're unsure (`cp ~/CLAUDE.md ~/CLAUDE.md.bak.$(date +%Y%m%d)`).

## The five steps

### Step 1 — Persona Interview (10–15 min)

Tell the user: *"I'm going to interview you one question at a time. Answer in your own words — don't try to write polished copy, talk like you'd talk to a friend. The whole point is for me to learn your voice."*

Then ask, ONE AT A TIME, with follow-ups when answers are vague:

1. Brand name and the human behind it
2. Niche (be specific — "fitness" is too broad; "strength training for desk workers in their 30s" is the level)
3. Unique angle in that niche — what they do differently
4. Target audience: demographics, where they hang out online, what they already follow
5. Their audience's #1 pain point (in the audience's own words, not marketing-speak)
6. What they currently sell or plan to sell (price, format, who it's for)
7. 60-day goal (revenue, audience size, launch — something measurable)
8. Distribution channels (which platforms they post on, frequency)

End with: *"Do I have what I need to write your About me section? Anything else you want me to know about you?"* — then move on. Don't write the section yet.

### Step 2 — Voice Analysis (10 min)

Tell the user: *"Now paste 5 of your best content pieces — tweets, scripts, captions, anywhere they live. Performance doesn't matter. Pick the 5 most 'you' pieces. One at a time. I'll confirm each before you paste the next."*

After each sample, just confirm receipt ("Got sample 1, ready for the next") — don't analyze yet.

After sample 5, analyze for: typical sentence length, opener style, transition style, words frequently used, words avoided, level of formality, level of specificity, emotional register, use of contractions, pacing rhythm, paragraph structure.

Hold the analysis in your head — don't show the rules yet. They'll be written in Step 5.

### Step 3 — Anti-Slop Rules (3 min, automatic)

No new user input needed. Based on what you've seen in their samples, build a **Don't list** of AI tells they should never produce, each rule tied to what the samples show ("no em dashes: none of your 5 samples uses one"), and open the section with one line describing the rhythm and register they DO use. A future model follows a reasoned rule better than a bare ban. Cover:

- **Words/phrases**: em dashes, "let's dive in", "in conclusion", "unlock", "powerful", "leverage", "harness", "robust", "it's worth noting", "embark on a journey", "delve into", "navigate", "elevate", "seamless", "game-changer", plus any specific terms YOU spotted in their samples that they avoided
- **Sentence patterns**: AABBC rhythm, perfect parallelism, predictable three-item lists, transition phrases ("Furthermore", "Moreover", "Additionally")
- **Punctuation**: em dashes (always), Oxford-comma uniformity, smiley emojis, exclamation marks at sentence end (unless their samples used them)
- **Structure**: opening with a rhetorical question, closing with a CTA question, every paragraph starting with the same word

Tailor specifically to what their samples revealed. If they write short sentences, the rule is "max 18 words avg, mix short bursts with longer reflective lines." If they avoid contractions, lock that in. Be concrete with examples, not abstract.

### Step 4 — Offer & Goals (3 min)

Pull from the persona interview answers. Organize into:
- **Offer one-liner**: who they help, what outcome, with what mechanism
- **Price point and format**
- **ICP one-liner**: their audience in one specific sentence
- **60-day goal** (measurable)
- **Distribution channels** (with cadence if known)

If anything is missing or contradictory from earlier answers, ask one targeted clarifying question before writing.

### Step 5 — Save Everything (2 min)

Now write to disk in this exact order:

1. **Backup** any existing `~/CLAUDE.md`: `cp ~/CLAUDE.md ~/CLAUDE.md.bak.$(date +%Y%m%d-%H%M%S) 2>/dev/null || true`
2. **Write `~/CLAUDE.md`** with these four sections in this order:
   ```
   # About me
   ...
   # Voice rules
   ...
   # Anti-slop rules
   ...
   # Offer & goals
   ...
   ```
3. **Create `~/memory/`** if missing: `mkdir -p ~/memory`
4. **Write `~/memory/voice-samples.md`** with the 5 raw samples (verbatim, exactly as pasted, including any typos — do NOT clean them up).
5. **Add a footer line to `~/CLAUDE.md`**:
   ```
   ---
   When generating content in my voice, read ~/memory/voice-samples.md for raw reference samples.
   ```
6. **Confirm**: list every file written and its absolute path.

### Step 6 — Verification

Tell the user: *"Last step. I'll write a 30-second script in your niche right now using everything we just built. Read it out loud — if it sounds like you wrote it, we're done. If not, tell me what's off and I'll fix the rules."*

Generate the test script. Wait for feedback. If they flag something:
- "Output sounds generic" → voice rules too abstract; add concrete examples
- "Used a word I hate" → add to anti-slop word list with explicit example
- "Wrong offer mentioned" → fix Offer & goals section
- "Sounds great" → done.

## Anti-patterns (avoid these)

- ❌ Asking all 8 persona questions in one message
- ❌ Showing voice rules before Step 5 (they should land all at once with the file write)
- ❌ Letting the user write or paste sections of CLAUDE.md themselves — you do all writing
- ❌ Generic anti-slop list copy-pasted from this skill — it must be tailored to what their samples actually revealed
- ❌ Skipping the verification script — it's how the user catches a bad persona before they trust it for production

## Time budget

~30 minutes guided (vs 60–90 min manual). The shorter time is the value: fewer drop-offs, same quality output.

## Notes

- This skill is the foundation of every other content skill. If a future content skill produces generic output, the fix is usually here, not in the content skill — go back and tighten anti-slop rules and voice rules.
- Iterate over time: as the user spots Claude making mistakes in later sessions, they should tell Claude to add the rule to `~/CLAUDE.md`. The persona file is a living document.

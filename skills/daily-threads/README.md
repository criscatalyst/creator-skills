# daily-threads

> Part of [**creator-skills**](../../README.md). Install as a plugin: `/plugin install daily-threads@creator-skills` (manual install below).

A [Claude Code](https://claude.com/claude-code) skill that turns a **conversational brain-dump into a full day of ready-to-post text posts** for Threads and Twitter/X.

You talk. The skill listens, agrees on a goal with you, mines your dump for raw material, maps it onto proven post templates, and hands you finished copy-paste-ready posts — each one explained so you learn the reasoning and can repeat it yourself.

No more staring at an empty composer. You ramble for two minutes, you get a posting day back.

---

## Why this exists

Most people don't struggle to *have* ideas. They struggle to turn the messy stuff in their head into posts that are actually structured to perform. This skill is the bridge: it does the part you hate (structuring, hooks, formatting, anti-AI-detection) and leaves you the part only you can do (the real experience and the taste to pick).

Everything in here is built on **proven posting learnings**, not theory: the templates and the engagement logic come from formats that have repeatedly worked on Threads and Twitter, distilled into reusable structures.

---

## How it works

The whole thing is a conversation. You start it, then you just talk.

```
You:    "plan my posts for today"
Skill:  "Talk to me. What happened this week, what are you proud of,
         what's annoying you, or what do you want people to know?"
You:    [dump everything — messy is fine]
Skill:  "Got it. What's the goal for today — sell something, grow, or
         start conversations with potential buyers?"
You:    "grow, but I'd take some DMs"
Skill:  → mines your dump → builds the day → writes every post →
         delivers them copy-paste ready, each with the reasoning
```

### The 6 steps under the hood

1. **Dump.** You ramble your thoughts, wins, opinions, frustrations, or whatever you want to post about. No structure required.
2. **Goal.** The skill locks **one** primary goal with you — this changes which templates and CTAs it uses:
   - **Sell a product** → optimizes for demand for a specific offer
   - **Grow on social** → optimizes for reach, follows, saves, replies
   - **Create sales opportunities** → optimizes for DMs, replies, and warm leads
3. **Mine.** It pulls the raw material out of what you said and sorts it: stories, numbers, workflows, hot takes, pains, lessons, mission.
4. **Build the day.** It assembles a slot plan (5 posts by default, or a lighter 3) with a varied format mix so the day never feels monotone.
5. **Write.** Each post is drafted in your voice, mapped to a template, given a deliberate hook, and run through an anti-AI-detection filter.
6. **Deliver.** You get every post **copy-paste ready**, plus a short *"why this works"* so you understand the move and can repeat it.

### What a delivered post looks like

```
─────────────────────────────────────
SLOT 1 · 09:00 · 6-Part Thread · Goal: grow
─────────────────────────────────────

1/6 I edited a full video in 8 minutes.
Not in Premiere.
Not with an editor.
Here's the exact workflow 🧵

2/6 ...

WHY THIS WORKS:
• Hook archetype: Achievement + Contrarian — a concrete result plus
  "not the obvious tool" stops the scroll
• Template: 6-Part Step-by-Step Thread
• Pure value + a flex = saves and follows, no selling needed
```

You read it, you copy it, you post it. Then you reply to your audience (the growth comes from there too).

---

## The post templates

The skill carries **11 proven structures** and picks the right one for your material and goal:

| # | Template | Best for |
|---|---|---|
| 0 | **6-Part Step-by-Step Thread** ⭐ | Showing a workflow or a build (the default workhorse) |
| 1 | Listicle Timeframe | Practical expertise built over time |
| 2 | Stop / Start One-liner | A direct, scroll-stopping challenge |
| 3 | You Don't X, You Y | A two-line mindset reframe |
| 4 | Long-Form Viral Thread | 8-12 dense lessons, big reach |
| 5 | Age + If-You-Feel Listicle | Speaking to a segment with empathy |
| 6 | 1-3-1-3-1 Me-At-Age | A credible before/after transformation |
| 7 | Don't X, Verb Y | A mic-drop reframe against a vanity metric |
| 8 | Raise Your Hand | Identity rally / community filter |
| 9 | Truth-Bomb Mic-Drop | A shareable truth in two lines |
| 10 | I Don't Want To Be Rich For | An emotional mission statement |

Plus a **10-archetype hook bank** (HookForge) and a 100-verb power bank, so every post opens with a hook chosen on purpose instead of guessed.

---

## The writing rules (anti-AI-detection)

Every post is run through a filter before you see it. It **cleans** the post (removes the AI tells) without rewriting your voice:

- **No em dashes.** Ever. The single biggest AI tell.
- **Every thread part ≤ 280 characters** so the same text works on both Twitter (280) and Threads (500).
- One idea per line, ≤ 25 words per sentence, 5th-grade reading level.
- A banned-vocabulary list (delve, leverage-as-filler, unlock, supercharge, game-changer…).
- Contractions enforced, all-caps phrases killed, ≤ 3 emoji per thread, never 🚀 or 🔥.
- **Never fabricate** numbers, wins, or stories — verifiable first-person only.
- Honest tool attribution and human+AI framing (you provide the input/taste, AI helps structure and scale).

---

## Personalization

If you have a `~/CLAUDE.md` with your own **voice rules** and **anti-slop rules**, the skill reads them and the posts sound like *you* instead of generic AI. The fastest way to build that file is the [`anti-slop-interview`](https://github.com/anthropics/claude-code) style persona skill. Without a `~/CLAUDE.md`, the skill works neutral and infers your voice from how you talk during the dump.

---

## Installation

Clone into your Claude Code skills directory:

```bash
git clone https://github.com/criscatalyst/creator-skills.git ~/creator-skills
ln -s ~/creator-skills/skills/daily-threads ~/.claude/skills/daily-threads
```

That's it. Claude Code auto-discovers skills in `~/.claude/skills/`. `git -C ~/creator-skills pull` updates every skill at once.

### Skill structure

```
daily-threads/
├── SKILL.md                      # the conversational workflow
├── README.md
└── references/
    ├── templates.md              # the 11 post structures
    ├── hook-bank.md              # 10 hook archetypes + verb bank
    ├── writing-rules.md          # anti-AI-detection filter + quality gate
    └── daily-plan.md             # goal→format mapping, slot plan, CTA rules
```

---

## Usage

In Claude Code, just say one of:

- *"plan my posts for today"*
- *"daily threads"*
- *"turn this into posts"*
- *"what should I post today"*

…then start talking. The skill takes it from there.

### Iterating

After delivery, push back freely — edits are surgical, not full rewrites:

- *"more aggressive hook on #3"* → re-pulls from the hook bank, rewrites that post only
- *"I don't like the selling one"* → swaps the template or softens the CTA
- *"make it sound more like me"* → re-reads your voice rules
- *"give me 3 more standalone ones"* → same goal, fresh templates

---

## License

MIT. Use it, fork it, adapt it to your own voice and niche.

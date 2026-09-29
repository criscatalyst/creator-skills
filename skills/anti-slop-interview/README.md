# Anti-Slop Interview — Claude Code skill

> Part of [**creator-skills**](../../README.md). Install as a plugin: `/plugin install anti-slop-interview@creator-skills` (manual install below).

A 30-minute guided interview that loads YOUR identity into Claude's memory — so every script, email, and DM you ask Claude to write later sounds like you wrote it, not like generic AI.

This is the highest-leverage hour you spend setting Claude up. Without it, your content sounds like every other creator using Claude badly. With it, your content sounds like you.

## What it produces

After the interview, you have:

- **`~/CLAUDE.md`** — your personal context file with four sections:
  - `About me` — brand, niche, audience, unique angle
  - `Voice rules` — how you write (sentence length, openers, words you use, words you avoid)
  - `Anti-slop rules` — the AI tells Claude must never produce in your name
  - `Offer & goals` — what you sell, your ICP, your 60-day goal
- **`~/memory/voice-samples.md`** — your 5 raw writing samples (reference for Claude when it generates content in your voice)
- A test script generated at the end so you can verify it sounds like you before you trust it for real work

## How it works

1. You run the skill in Claude Code.
2. Claude interviews you — one question at a time — about who you are, who you serve, what you sell.
3. You paste 5 of your best content pieces (tweets, scripts, captions — wherever).
4. Claude analyzes your voice, builds anti-AI-detection rules, organizes your offer.
5. Claude writes everything to `~/CLAUDE.md` and `~/memory/voice-samples.md`.
6. Claude generates a test script in your voice. You read it. If it sounds like you, you're done.

You never touch a file. You only talk.

## Install

```bash
mkdir -p ~/.claude/skills
git clone https://github.com/criscatalyst/creator-skills.git ~/creator-skills
ln -s ~/creator-skills/skills/anti-slop-interview ~/.claude/skills/anti-slop-interview
```

That's it. No dependencies, no API keys, no scripts to make executable. The skill is pure instructions for Claude.

## Usage

In a new Claude Code session, just say:

> Run the anti-slop interview.

Or:

> Set up my voice / build my persona / teach Claude to be me.

Claude picks up the `anti-slop-interview` skill and starts the interview.

## Before you run it

Have ready:

- 5 of your best content pieces — tweets, scripts, captions, anywhere they live. Not the ones with the most views, the ones that sound the most like *you*. The ones a friend would say "yeah, that's how you sound."
- 30 minutes of focus. Don't do this between meetings. Don't do it on your phone. Sit with it.
- A clear-ish answer to: "what do you sell or plan to sell, and to whom?"

You don't need polished answers. Talk how you talk. Claude is taking notes on your voice, not grading your responses.

## After you run it

Iterate over the next week. Every time Claude writes something for you that doesn't quite sound right, tell it to update the rule in `~/CLAUDE.md`:

> Never use the word "unlock". Add that to my anti-slop rules.

> My average sentence is too long. Cap it at 18 words. Add to voice rules.

The persona file is a living document. The more you correct it, the sharper Claude gets.

## Existing CLAUDE.md?

If you already have `~/CLAUDE.md`, the skill will ask whether to replace it, merge into it, or back it up first. Default is back-up-then-replace, so nothing is ever lost.

— Cris

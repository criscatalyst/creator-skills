# Hemingway — Claude Code skill

> Part of [**creator-skills**](../../README.md). Install as a plugin: `/plugin install hemingway@creator-skills` (manual install below).

Sentence-by-sentence readability filter for anything you write — scripts, emails, sales pages, captions, tweets. Catches the weak sentences before you publish.

The check is **personal**, not generic. It reads your own Voice rules and Anti-slop rules from `~/CLAUDE.md` and grades against your standards — not a one-size list of AI tells.

## What it does

You paste a draft. The skill grades every sentence:

- `OK` — clear and direct
- `~` — a bit long or weak, suggest a tighter version
- `X` — needs to be rewritten (too long, AI tell, broken)

Then it gives you a score, the fixes for the weak sentences, and asks if you want the clean version ready to paste back into your post.

## Example

```
READABILITY CHECK
=================

  "Most creators using AI ship their first draft."                    OK
  "And the first draft, as we all know by now, tends to be where..."  ~  FIX BELOW
  "AI tells live in there."                                           OK
  "This skill helps you unlock the power of human writing."           X  FIX BELOW

SCORE: 2 OK | 1 ~ | 1 X
-----

FIX:
  ~ "And the first draft, as we all know by now, tends to be where..."
    -> "The first draft is where AI tells live."

  X "This skill helps you unlock the power of human writing."
    -> "This skill catches the AI tells. You ship the human version."
```

## Install

```bash
mkdir -p ~/.claude/skills
git clone https://github.com/criscatalyst/creator-skills.git ~/creator-skills
ln -s ~/creator-skills/skills/hemingway ~/.claude/skills/hemingway
```

No dependencies. Pure Claude skill — just markdown instructions.

## Usage

In Claude Code, paste your draft and say one of:

> hemingway

> readability check on this

> is this clear?

> tighten this up

Claude grades it and gives you the fixes. If you say yes when asked, you also get the cleaned version ready to copy.

## How the personalization works

If you've already run [`anti-slop-interview`](../anti-slop-interview/) (the persona setup), your `~/CLAUDE.md` has a Voice rules section and an Anti-slop rules section tailored to **your** writing. Hemingway reads those and grades against them. Your specific "never use the word `unlock`" rule, your specific "max 18 words per sentence" rule — all enforced.

If you haven't, no problem. The skill falls back to sensible defaults (no em dashes, no AI clichés, no 30-word monsters) and reminds you once that running `anti-slop-interview` will calibrate it to your voice.

## When to use it

Run hemingway as the **last step** before posting. Order:

1. Generate the draft (with Claude or by hand)
2. Run hemingway
3. Apply the fixes
4. Post

It's not meant to run on every Claude output automatically. It's a manual filter you invoke when the draft matters.

## Spoken vs written

Hemingway detects whether the text is meant to be spoken (reel script, video, podcast) or read (email, caption, sales page). It doesn't penalize natural connectors (`and`, `but`, `so`) on spoken scripts — that's where they belong.

## Pairs well with

- [`anti-slop-interview`](../anti-slop-interview/) — builds your personal voice + anti-slop rules into `~/CLAUDE.md`. Hemingway then enforces them.
- [`script-writer`](../script-writer/) — generates scripts using Hook → Build-Up → Value → Payoff → CTA. Run hemingway on the output to tighten.

— Cris

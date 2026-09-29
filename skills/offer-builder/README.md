# Offer Builder — Claude Code skill

> Part of [**creator-skills**](../../README.md). Install as a plugin: `/plugin install offer-builder@creator-skills` (manual install below).

A 60-minute guided interview that takes you from "I don't know what to sell" to a written, pinned, defensible offer.

The hardest decision in creator monetization, made conversational.

## What it does

Claude interviews you on five dimensions:

1. Your **unfair advantage**
2. **Time** you can dedicate per week to delivery
3. **Technical comfort** with Claude Code
4. **Audience size**
5. Your **appetite** for high-touch vs hands-off delivery

Then it recommends one of four offer types — **course, digital product, code/tool, or service** — with full reasoning. Generates 3 specific, shippable offer ideas tailored to your niche from `~/CLAUDE.md`. Lets you push back. Locks in one. Writes the final one-liner to disk.

## Output

A single sentence in this format:

> *"I help [ICP] [outcome] with [delivery type]."*

Saved to `~/CLAUDE.md` under "Offer & goals". Optionally pushed to Mission Control.

That sentence does three jobs:
- Names the buyer
- Names the outcome they get
- Names the delivery format

Every other monetization step (lead magnet, sales page, email flow, funnel) compounds off this single sentence. Wrong sentence here = wasted work everywhere downstream.

## The four offer types you'll choose between

| Type | Price | Best for |
|---|---|---|
| **Course** | $97–997 | Strong teachers with a proven framework |
| **Digital product** | $27–97 | Anyone with a finished asset (template, swipe, pack) |
| **Code / tool** | $47–297 | Creators good with Claude Code who solve a repeatable workflow |
| **Service** | $1k+ | High-touch operators (high-ticket later) |

The skill stays neutral. The right answer depends on YOUR profile — your unfair advantage, time, skill, audience, preferences. Not on what's hot in 2026.

## Install

```bash
mkdir -p ~/.claude/skills
git clone https://github.com/criscatalyst/creator-skills.git ~/creator-skills
ln -s ~/creator-skills/skills/offer-builder ~/.claude/skills/offer-builder
```

No dependencies. Pure markdown skill.

## Usage

In a Claude Code session, say:

> build my offer

> what should I sell?

> offer builder

> I don't know what to sell

Claude picks up the `offer-builder` skill and starts the interview.

## Before you run it

Ideally, run [`anti-slop-interview`](../anti-slop-interview/) first. It builds your `~/CLAUDE.md` with niche, ICP, and voice — which makes the 3 offer ideas way sharper. The offer builder will read that context and propose ideas that actually fit you.

If you skip that step, the skill will warn you and propose ideas based only on the conversation. Still works, just less calibrated.

Have ready:
- Honest answers about your unfair advantage (not "I work hard" — actually unfair)
- A real number for hours per week you can deliver
- A real number for your audience size

The skill works because you're honest. Inflated answers = inflated recommendation = wrong offer.

## Pushback round

After the recommendation, you'll get prompted to push back. Use it.

> "What if I want to ship in a week?"

> "What if I'm not as technical as I said?"

> "What if my audience is smaller than I said?"

> "I don't actually want to teach."

The skill recalculates and tells you what changed. Don't accept the first answer if it doesn't feel right.

## Pairs well with

- [`anti-slop-interview`](../anti-slop-interview/) — run first to load your persona
- [`script-writer`](../script-writer/) — once you have an offer, write content that subtly points to it
- [`hemingway`](../hemingway/) — readability check on the final one-liner and any positioning copy

— Cris

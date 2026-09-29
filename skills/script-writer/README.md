# Script Writer — Claude Code skill

> Part of [**creator-skills**](../../README.md). Install as a plugin: `/plugin install script-writer@creator-skills` (manual install below).

Turn any rough video idea into a full retention-optimized short-form script (Reel / TikTok / Short) using a proven viral structure: **Hook → Build-Up → Value → Payoff → CTA**.

Comes with a library of 100+ real viral hooks (with view counts) and a psychology tricks toolkit so every line in your script earns its place.

## What it does

You hand Claude a rambled idea, a topic, or even just a vibe. It:

1. Distills the concept into a clear core message.
2. Picks a hook format from the library (or proposes 2-3 options).
3. Drafts the full script in a clean annotated template — every line tagged with the psychology trick it's pulling.
4. Writes a ready-to-paste caption with hashtags.

You iterate from there: swap the hook, change the duration, adjust the tone, rework the CTA.

## Install (1 minute)

```bash
mkdir -p ~/.claude/skills
git clone https://github.com/criscatalyst/creator-skills.git ~/creator-skills
ln -s ~/creator-skills/skills/script-writer ~/.claude/skills/script-writer
```

That's it. No dependencies, no API key.

## Try it

Open a new Claude Code session and paste something like:

> write me a reel script about why most beginner creators stall at 1k followers

or

> turn this idea into a 60s reel: I want to show how I edit my videos in CapCut in under 5 minutes

Claude will pick up the `script-writer` skill, ask one or two quick questions if needed (audience, goal), and deliver the full script.

## What's inside

- `SKILL.md` — the skill instructions Claude follows
- `references/scripting-methodology.md` — the full framework (5-part structure, 6 principles of persuasion, psychology tricks)
- `references/script-template.md` — the output format + duration guidelines (15s / 30s / 60s / 90s)
- `references/viral-hooks.md` — 100+ proven hooks with view counts, sorted by virality

You can read those files directly if you just want to learn the framework without using the skill.

## Tips

- **Be honest about the goal.** "Views" and "conversions" need different hooks. Tell Claude up front.
- **Give it real specifics.** The script is only as good as the value you put into it. If your "value" section is vague, the script will be vague.
- **Iterate on the hook first.** The hook is 80% of the video. If the hook is weak, ask Claude for 3 alternatives before writing the rest.

— Cris

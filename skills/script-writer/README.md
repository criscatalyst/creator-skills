# Script Writer — Claude Code skill

> Part of [**creator-skills**](../../README.md). Install as a plugin: `/plugin install script-writer@creator-skills` (manual install below).

Turn a rough idea or a competitor reel into a short-form script (Reel / TikTok / Short) you'd post with confidence: hooks that stop the scroll, a reason to stay every few seconds, and value the viewer can see on screen.

Written in your voice, from your freshest niche hooks, with a beat map of what's on screen for every line.

## What it does

You hand Claude a rambled idea, a topic, or a competitor reel to adapt. It:

1. Reads your voice, audience and script rules from `~/CLAUDE.md`, plus your freshest niche hooks if you keep them (hook bank, outlier research).
2. Writes 10 hooks across different mechanics (callout, paid vs free, proof first, stakes, counted list, experiment...), each with spoken line, on-screen text and first frame. Scores them and keeps the best 3.
3. Builds a beat map for the format (tool drop, list, test, contrarian, demo, story): one open loop closed at the end, a re-hook every 6-8 seconds, a pattern interrupt, proof on screen.
4. Runs a quality gate (attention, value, voice, ending) and rewrites anything that fails before you see it.
5. Delivers the clean script, the beat map with what's on screen for each line, a caption, and a list of what to prepare before filming.

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

Claude will pick up the `script-writer` skill, ask for the one real specific it needs (your tool, number or result), and deliver hooks, script and beat map.

## What's inside

- `SKILL.md`: the workflow Claude follows
- `references/hook-engine.md`: hook anatomy, 12 mechanics with measured 2026 examples, power words, scoring, dead openers
- `references/formats.md`: the attention rules and a beat map per format
- `references/quality-gate.md`: the checklist every script passes before delivery

You can read those files directly if you just want to learn the method.

## Tips

- **Be honest about the goal.** "Views" and "conversions" need different hooks. Tell Claude up front.
- **Give it real specifics.** The script is only as good as the value you put into it. If your "value" section is vague, the script will be vague.
- **Iterate on the hook first.** The hook is 80% of the video. If none of the 3 lands, ask for hooks from mechanics it hasn't used yet.
- **Set up `~/CLAUDE.md` first.** Without your voice and audience, every script sounds like everyone else's. The `anti-slop-interview` skill builds it in 30 minutes.

— Cris

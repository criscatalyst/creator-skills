---
name: script-writer
description: "Short-form video script writer for Reels, TikTok and Shorts. Turns an idea, a ramble or a reference reel into a script built for retention: 10 hooks across different mechanics scored and cut to the best 3, a beat map that re-hooks every 6-8 seconds and saves the payoff for the end, what's on screen for every line, and a quality gate that rewrites anything generic before delivery. Reads the creator's own voice and script rules and their freshest niche hooks first. Use when the user wants to write or rewrite a reel script, turn an idea into a script, write hooks, adapt a competitor reel to their page, or fix a script that feels flat."
---

# Short-form script writer

The job is a script the creator would post with confidence: a hook that stops the scroll in the first second, a reason to stay at every beat, and value the viewer can see, not just hear.

Three failure modes this skill exists to prevent:
- **Sameness.** Every script on the same five blocks with the same stock phrases. Here the format decides the structure (`references/formats.md`), and no two scripts in a batch share a hook mechanic.
- **Weak hooks.** Templates recycled from other niches. Here hooks come from mechanics plus the creator's freshest niche examples (`references/hook-engine.md`), never from a static list of old viral lines.
- **Attention that dies after second 3.** Here every script gets a beat map with open loops, re-hooks and a withheld payoff (`references/formats.md`), and a gate that checks it (`references/quality-gate.md`).

## Step 0: Load the creator (always, before writing a word)

1. **Voice and rules.** Read `~/CLAUDE.md` and follow what it points to for brand, voice, audience (ICP) and script rules. The creator's own rules **override** this skill wherever they conflict (tone, CTA style, how much to give away).
2. **Fresh hooks from the niche.** If the creator keeps a hook bank, recent outlier research or competitor transcripts (look for the files `~/CLAUDE.md` points to), read the newest. Real hooks that worked in the last weeks beat any library.
3. **The reference, if there is one.** If the user gives a reel to adapt, get its transcript first (a transcribe or video-breakdown skill if installed) and write down its mechanics before touching the topic.

If there's no `~/CLAUDE.md`, ask once for the audience and the goal, then proceed with smart defaults.

## Step 1: Pin the brief (don't interrogate)

Extract, and state in 3-4 lines before the script:
- **Topic and the one real specific**: the tool, number, result or story that only this creator has. No specific → ask for one, because it's what separates the script from everyone else's.
- **Viewer and their pain**, in their words.
- **Format** (`references/formats.md`): tool drop, list, test/experiment, contrarian, demo/transformation, story.
- **Length**: default 30-45s. Budget ~2.5 spoken words per second (40s ≈ 100 words).
- **CTA mechanic**: comment keyword, save, follow, link. Use the creator's standard if they have one.

## Step 2: Hooks (`references/hook-engine.md`)

Write **10 hooks across at least 6 different mechanics**. Each hook has three layers: spoken line, on-screen text, first frame. Score them, drop the weak, present the **best 3** with their scores and a one-line why. Write the script on the best one unless the user picks.

## Step 3: Beat map, then the script (`references/formats.md`)

Pick the format's beat map. Plan the beats first: the open loop, the re-hooks every 6-8s, the pattern interrupt, where the proof appears on screen, where the payoff lands. Then write the lines to fill the beats. The value is a **transformation the viewer can see** (before/after, input/output, number that moves), not a list of tips read aloud.

## Step 4: Quality gate (`references/quality-gate.md`)

Run every check. Any fail → rewrite that part and run the gate again. Don't deliver a script that fails, and don't show the gate unless something needed a trade-off.

## Output

```
BRIEF: topic · specific · viewer/pain · format · length · CTA

HOOKS (best 3)
1. [spoken] / [on-screen text] / [first frame]  · score · why
2. ...
3. ...

SCRIPT (spoken, clean, ready to read)
...

BEAT MAP
| time | line (short) | on screen | attention job |
|------|--------------|-----------|---------------|
| 0-2s | ...          | ...       | stop the scroll / open loop |
| ...  | ...          | ...       | re-hook / proof / interrupt / payoff / CTA |

CAPTION: first line = hook restated, 2-4 lines of value, CTA. Follow the creator's caption rules.

TO PREPARE: anything the script promises that must exist before filming (the DM resource, the screen recording, the number to verify).
```

Write the script in the language the creator posts in; talk to the user in their language.

## Iterating

- "Hook is weak" → back to Step 2 with mechanics not used yet, don't reword the same hook.
- "Too long" → cut a beat, not words inside every beat.
- "Sounds like AI" → re-run the quality gate's voice checks against the creator's own lines.
- Batch of scripts → no two share a hook mechanic or a format.

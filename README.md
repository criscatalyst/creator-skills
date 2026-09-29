# creator-skills

Claude Code skills for content creators. Research what works, write the script, check it reads well, decide what to sell. Everything runs on your machine, most of it free.

Built and used daily by [@criscatalyst](https://instagram.com/criscatalyst).

## The skills

| Skill | What it does | Needs |
|---|---|---|
| **Setup** | | |
| [anti-slop-interview](skills/anti-slop-interview/) | 30-min interview that loads your voice, anti-AI rules and offer into `~/CLAUDE.md`. Run it first: every other skill reads it. | nothing |
| [offer-builder](skills/offer-builder/) | 60-min interview to decide what to sell (course, product, tool, service). 3 tailored ideas + your one-liner. | nothing |
| **Research** | | |
| [outliers](skills/outliers/) | YouTube outlier detection on any topic (views vs channel median) + title variants for your niche. | free YouTube API key |
| [ig-competitor-research](skills/ig-competitor-research/) | Weekly IG competitor research via Chrome: reels ranked by views, first-3s hooks, transcripts, HTML report. | Claude in Chrome, dummy IG account |
| [video-breakdown](skills/video-breakdown/) | Any video split into timestamped frames, contact sheets and a local transcript. Study a reel shot by shot. | yt-dlp, ffmpeg, Whisper |
| [transcribe](skills/transcribe/) | Transcript of any video URL (IG, TikTok, YouTube, X...) with local Whisper. | yt-dlp, ffmpeg, Whisper |
| **Writing** | | |
| [script-writer](skills/script-writer/) | Video idea to short-form script: Hook, Build-Up, Value, Payoff, CTA. 100+ real viral hooks. | nothing |
| [daily-threads](skills/daily-threads/) | Brain-dump to a full day of ready-to-post Threads/X posts. | nothing |
| [hemingway](skills/hemingway/) | Sentence-by-sentence readability check calibrated to your voice rules, with a clean rewrite. | nothing |
| **Visuals** | | |
| [mindcraft](skills/mindcraft/) | Local AI images on Apple Silicon (MindCraft Studio + Z-Image Turbo). $0 per image, IG-ready 1080x1350. | Apple Silicon Mac, MindCraft Studio |

Each skill folder has its own README with setup details and examples.

## Install

### Option A: as plugins (recommended)

Inside Claude Code:

```
/plugin marketplace add criscatalyst/creator-skills
/plugin install hemingway@creator-skills
```

Install only the skills you want, one `/plugin install <name>@creator-skills` each. Update them all with `/plugin marketplace update creator-skills`.

Plugin skills are namespaced: you can call `/hemingway:hemingway`, or just ask in plain words ("check this script with hemingway") and Claude picks the skill.

### Option B: clone and symlink

```bash
git clone https://github.com/criscatalyst/creator-skills.git ~/creator-skills
mkdir -p ~/.claude/skills

# one skill
ln -s ~/creator-skills/skills/hemingway ~/.claude/skills/hemingway

# or all of them
for s in ~/creator-skills/skills/*/; do ln -s "$s" ~/.claude/skills/; done
```

`git -C ~/creator-skills pull` updates everything.

## Suggested order

1. `anti-slop-interview`: Claude learns how you talk.
2. `offer-builder`: you know what you are selling.
3. `outliers` / `ig-competitor-research`: find what already works in your niche.
4. `video-breakdown`: take apart the winners.
5. `script-writer`, then `hemingway` on the output.

## Moved here from single repos

These skills used to live in separate repos (`hemingway-skill`, `script-writer-skill`, ...). Those repos are archived and point here. This repo has the latest version of each.

## License

MIT. Use it, fork it, adapt it to your voice.

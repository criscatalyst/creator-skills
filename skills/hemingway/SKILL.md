---
name: hemingway
description: Sentence-by-sentence readability check on any text the user pastes (scripts, emails, sales pages, captions). Tags each sentence OK / ~ / X, gives a score, lists fixes for the weak ones, and offers a clean rewrite. Reads the user's personal Voice rules and Anti-slop rules from ~/CLAUDE.md and applies them — so the check is calibrated to how THEY write, not generic AI advice. Trigger when the user says "hemingway", "readability", "check this script", "is this clear?", "tighten this up", or pastes a draft and asks for feedback.
---

# Hemingway

A readability filter the user runs on any draft. Every sentence gets graded. Weak sentences get rewritten. Final clean version available on request.

The check is **personal**, not generic. It reads the user's `~/CLAUDE.md` (Voice rules, Anti-slop rules) and applies their own rules — not a one-size list of AI tells.

## When to use

- User pastes a draft (script, email, sales page, tweet, caption) and asks "is this clear?", "check this", "hemingway this", "tighten it up"
- User explicitly says `hemingway` or `readability`
- After generating any content for the user, if they ask "good?" — offer to run hemingway on it

**Do NOT trigger automatically** on every output. This is a manual filter the user invokes when they want it.

## How the check works

For every sentence in the text, grade it:

- `OK` — clear and direct. Reads cleanly out loud. Carries one idea.
- `~` — could be simpler. A bit long, has a filler word, or has a slightly awkward construction. **Suggest a tighter version.**
- `X` — needs to be rewritten. Too long, multiple clauses stacked, hard to follow on one read, or contains AI tells from the user's anti-slop list. **Rewrite it.**

### Personalization (read this first)

Before grading, check if `~/CLAUDE.md` exists and contains a "Voice rules" or "Anti-slop rules" section:

- If yes → load those rules and apply them. Their personal "avoid em dashes / max 18 words / no `unlock`" rules become hard constraints. A sentence that violates one of their rules is at minimum `~`, often `X`.
- If no → use sensible defaults (em dashes, "let's dive in", "in conclusion", "delve into", "unlock", "leverage", "harness", "robust", "it's worth noting", "embark on a journey" all flag the sentence; sentences over 25 words flag at minimum `~`).

If the user has no `~/CLAUDE.md` yet, mention it once at the end: *"Heads up — you don't have a `~/CLAUDE.md` yet, so I used generic anti-slop rules. The `anti-slop-interview` skill builds your personal one in 30 minutes."*

### Spoken vs written

Detect the format. If the text is a **spoken script** (reel, video, podcast), do not penalize natural connectors (`and`, `but`, `so`, `because`) that create flow when read aloud. The readability of a script is measured by listening, not reading. If unsure, ask the user once: "Spoken script or written copy?"

### Language

Auto-detect EN / IT (and others if obvious). Output in the same language as the input.

## Output format

Terminal-friendly, monospace. Use this exact format:

```
READABILITY CHECK
=================

  "First sentence of the text."                                       OK
  "Second sentence that's a bit long and could lose a clause."        ~  FIX BELOW
  "Third sentence that's perfectly fine."                             OK
  "Fourth sentence that uses an em dash and reads like AI wrote it."  X  FIX BELOW

SCORE: 12 OK | 4 ~ | 2 X
-----

FIX:
  ~ "Second sentence that's a bit long and could lose a clause."
    -> "Second sentence that's tight."

  X "Fourth sentence that uses an em dash and reads like AI wrote it."
    -> "Fourth sentence. No em dash. Sounds human."
```

Notes on format:
- Truncate long sentences to ~70 chars in the score table (full version goes in FIX). Trailing `...` if cut.
- Right-align the OK / ~ / X column.
- Score line: `OK | ~ | X`, in that order.
- After the FIX block, ask: *"Want the clean version with all fixes applied, ready to paste?"*

## Clean version (on request)

If the user says yes, output the full text with every `~` and `X` fix applied inline, formatted exactly as the original (line breaks, paragraphs, structure preserved). No tags, no markup — just the rewritten text ready to copy.

## Anti-patterns

- ❌ Don't grade word-by-word. Sentence is the unit.
- ❌ Don't suggest fixes that change the user's voice. Tighter ≠ different person speaking.
- ❌ Don't lecture. Show the fix, don't explain the rule.
- ❌ Don't apply rules that aren't in the user's CLAUDE.md and aren't in the standard anti-slop set. No personal taste.
- ❌ Don't run on text shorter than 2 sentences — there's nothing to check, just answer the user directly.

## Time budget

Under 30 seconds for a typical reel script (~150 words). Under 90 seconds for a sales page (~600 words).

## Why this skill exists

Most creators using AI ship the first draft. The first draft is where AI tells live. This skill catches them before publish — calibrated to *their* voice, not a generic "sound human" filter. Pair with `anti-slop-interview` (which builds the rules) for the full system.

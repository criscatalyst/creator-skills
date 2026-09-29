---
name: offer-builder
description: Guided 60-minute interview that helps a creator decide WHAT to sell — course, digital product, code/tool, or service. Outputs a recommendation with reasoning, 3 specific offer ideas tailored to the user's persona from ~/CLAUDE.md, and a final one-liner ("I help [ICP] [outcome] with [delivery type]") saved to disk. Trigger when the user says "build my offer", "what should I sell", "offer builder", "decide my offer", "I don't know what to sell", or is in M3-L1 of the Velocity Lab course.
---

# Offer Builder

A guided interview that takes a creator from "I don't know what to sell" to a written, pinned, defensible offer in 60 minutes. The hardest hour of the Velocity Lab journey, made conversational.

## Outcome

After this skill runs:

- The user has decided their offer **type**: course / digital product / code-tool / service-later
- The user has 3 specific offer **ideas** with positioning and price, tailored to their persona
- The user has picked one and written it as a single sentence: *"I help [ICP] [outcome] with [delivery type]"*
- That sentence is saved to `~/CLAUDE.md` under "Offer & goals" (replacing or merging with the existing line)
- Optionally pushed to Mission Control as the pinned offer

## Operating principles

1. **Stay neutral on offer type.** Don't bias toward any of the four. Let the user's answers drive the recommendation. The reasoning matters more than the verdict.
2. **One question at a time.** Five interview dimensions, asked one at a time, with follow-ups for vague answers.
3. **Read `~/CLAUDE.md` first.** If it exists, the persona context (niche, ICP, voice) feeds into the 3 offer ideas. If it doesn't exist, mention `anti-slop-interview` once but proceed.
4. **Honest pushback is welcome.** When the user pushes back on the recommendation ("what if I'm not technical?", "what if I want to ship in a week?"), recalculate openly and explain what changed.
5. **Don't write the file until the user has chosen one offer.** Hold everything in conversation.

## The four offer types (reference)

Use this table internally during reasoning. Don't dump it on the user — pull from it as needed.

| Type | Price range | Pros | Cons | Best for |
|---|---|---|---|---|
| **Course** | $97–997 | High perceived value, scalable once built | Slow to build, high refund rate, hard to deliver alone | Strong teachers with a proven framework |
| **Digital product** | $27–97 | Ships in days, low support burden | Low ticket, needs volume | Anyone who has a finished asset (template, swipe, pack) |
| **Code / tool** | $47–297 | High leverage, fast to ship with Claude Code | Requires technical comfort | Creators good with Claude Code who solve a repeatable workflow |
| **Service** | $1k+ | High ticket, fast cash | Doesn't scale, time-intensive | High-touch operators, only as a high-ticket later |

## The interview

### Step 0 — Read context

Quietly check for `~/CLAUDE.md`. If present, scan the "About me" / "Offer & goals" sections to understand:
- Their niche
- Their current ICP
- Anything they already sell or have considered

If absent, mention once: *"You don't have a `~/CLAUDE.md` yet — running the `anti-slop-interview` skill first would make my offer ideas way sharper. Want to do that first, or push through?"*

If they push through, keep going but flag at the end that the offer ideas are inferred from this conversation only.

### Step 1 — Unfair advantage

Ask: *"What's your unfair advantage? The thing you can do faster, better, or with more credibility than 95% of people in your niche?"*

Listen for:
- Technical skill ("I can build with Claude Code")
- Teaching skill ("I've taught X to N people")
- Lived experience ("I went from X to Y in 12 months")
- Process / framework ownership ("I've systematized X")
- Network / access ("I know the right people")

If the answer is vague ("I'm just hardworking"), follow up: *"More specifically — what have you done that most people in your niche couldn't replicate even if they tried?"*

### Step 2 — Time available per week

Ask: *"Realistically, how many hours per week can you dedicate to delivering an offer? Not building it — delivering. So if 5 customers ask questions, run into bugs, want feedback, etc."*

Calibrate against type:
- < 3 hrs/week → digital product or code/tool only
- 3–10 hrs/week → above + light course
- 10+ hrs/week → all four are on the table

### Step 3 — Technical comfort with Claude Code

Ask: *"On a scale where 1 is 'I can barely open Terminal' and 10 is 'I've built and shipped multiple Claude skills', where are you today?"*

Don't read this on a strict scale. Listen for:
- < 4 → code/tool is unrealistic short-term
- 4–6 → code/tool possible if scope is tight
- 7+ → code/tool is on the table, often best fit

If they say < 4 but their unfair advantage is technical, dig: *"Tell me about the most technical thing you've shipped — even if it was rough."*

### Step 4 — Audience size

Ask: *"How big is your audience today? Across all platforms — IG, X, YT, newsletter, whatever the main one is."*

Calibration:
- < 1k → digital product (low ticket, volume comes from cold) or code/tool (sells via demo, not audience size)
- 1k–10k → all four work, code/tool tends to convert best
- 10k+ → course makes sense, audience can support a launch
- 50k+ → all options, including high-ticket service later

### Step 5 — Delivery preference

Ask: *"Be honest — do you want to be on calls with customers helping them through stuff, or do you want to ship something and be hands-off?"*

This is the gut check on service vs everything else. Most creators say hands-off. If they say "calls are fine, I like coaching", that's a service signal — but only if combined with high audience + 10+ hrs/week + premium positioning.

### Step 6 — Recommendation + reasoning

Output, in this exact order:

```
RECOMMENDED: <type>

Reasoning:
- <unfair advantage> matches <type> because <specific reason>
- <time available> rules out <other type> because <specific reason>
- <technical comfort> supports <type> at <scope>
- <audience size> suggests <pricing strategy>
- <delivery preference> aligns with <type>
```

Then **3 specific offer ideas** for that type, each with:

```
1. <Working title>
   What it does: <1-line description>
   Who it's for: <ICP> (pulled from ~/CLAUDE.md if available)
   Price: $<X>
   Why this idea: <1 sentence on the angle>
```

Make the ideas **concrete and shippable**, not vague categories. "A productivity course" is bad. "30-day course teaching desk workers how to lift twice a week without a gym" is good.

### Step 7 — Pushback round

Tell the user: *"Push back. Tell me what doesn't feel right and I'll recalculate."*

Common pushbacks to anticipate:
- "I want to ship in a week" → push to digital product or tightly scoped tool
- "I'm not as technical as I said" → drop code, push course or product
- "Audience is smaller than I said" → push to digital product or tool, away from course
- "I don't want to teach" → drop course, push tool or product
- "I want recurring revenue" → membership digital product, or tool with subscription

When recalculating, **say what changed** in the inputs, not just the new output.

### Step 8 — Pick one

Once the user is happy with one of the 3 ideas, lock it in. Ask: *"Want me to write the one-liner and save it?"*

### Step 9 — One-liner format

Format: **"I help [ICP] [outcome] with [delivery type]."**

Examples:
- *"I help pre-revenue creators get their first $1k from content with a Claude scripting skill."*
- *"I help desk workers build strength in 20 minutes a day with a 90-day mobile-first program."*
- *"I help solopreneurs cut 5 hours of admin per week with a Notion + automation pack."*

The sentence does three jobs:
1. Names the buyer
2. Names the outcome
3. Names the delivery format

If the user can't fill all three slots clearly, the offer isn't tight enough — go back to step 6.

### Step 10 — Save

1. **Backup**: `cp ~/CLAUDE.md ~/CLAUDE.md.bak.$(date +%Y%m%d-%H%M%S) 2>/dev/null || true`
2. **Write to `~/CLAUDE.md`** under "Offer & goals" section. If section exists, replace its content. If not, append the section.
3. **Confirm** the file path written.

`~/CLAUDE.md` is the only home for the offer. Every other skill (script writers, hemingway, future content skills) reads this file at session start, so the one-liner propagates automatically across the whole content pipeline. No need to mirror it anywhere else.

## Anti-patterns

- ❌ Don't pre-bias toward code/tool just because it's trending. The right answer depends on the user's profile.
- ❌ Don't suggest courses if the user hasn't shown teaching ability AND time to build.
- ❌ Don't generate 3 ideas in totally different types — they must all be the recommended type, varying angle/scope/positioning instead.
- ❌ Don't accept a vague one-liner. "I help creators with content" is not an offer. Push for ICP + outcome + delivery.
- ❌ Don't save the file until the user explicitly says "yes, save it".

## Time budget

~60 minutes if the user pushes back honestly. ~30 minutes if they take the first recommendation.

## Why this skill exists

Most creators stay stuck on "what should I sell?" for years. They post content, build an audience, then panic when the audience asks. This skill forces the decision in one focused hour. Every other monetization step (lead magnet, sales page, email flow, funnel) compounds off this one sentence — wrong sentence here, wasted work everywhere downstream.

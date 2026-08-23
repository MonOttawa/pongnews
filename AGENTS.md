# AGENTS.md — pongnews.com

## Goal
Generate, review, and publish peer-reviewed research articles about table tennis and longevity to pongnews.com. Keep the voice human, evidence-led, and free of AI-isms.

## Pre-publish guardrail: avoid-ai-writing

**Required.** Before publishing any new article under `src/content/articles/`, run the avoid-ai-writing detector on the draft:

```bash
node -e "const D=require('${HOME}/.hermes/skills/writing/avoid-ai-writing/detector/patterns.js'); const fs=require('fs'); const r=D.analyzeText(fs.readFileSync(process.argv[1],'utf-8')); console.log('score:', r.score, '| label:', r.label, '| issues:', r.issues.length)" <draft.md>
```

**Target: score 0-5 ("Clean" or "Minimal AI signals").**

- score 0-5: ship it.
- score 6-10: load the `avoid-ai-writing` skill and apply targeted fixes.
- score >10: rewrite the draft (the skill's rewrite mode).

**Reminder:** the detector is a signal, not a verdict. Use the flagged issues as a checklist, not a block.

## Article audit cadence

Run the detector over every existing article monthly and after any batch rewrite. Report scores in the Windmill `f/hermes/pongnews_weekly_audit` summary.

## Other conventions

- One source citation per non-obvious factual claim (paper, journal, DOI, or PubMed ID).
- No emoji in headers. One bolded phrase per major section, max.
- Em dashes (—) banned; use commas, periods, or parentheses.
- Voice: confident, plain, evidence-led. No "delve," "leverage," "tapestry," "robust," "comprehensive," "seamless."

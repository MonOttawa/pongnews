# Pong News Regular Review & Maintenance Workflow

## Weekly Audit (Every Sunday 9am ET)

### 1. Performance Check
- Homepage load time (target < 200ms): `curl -sI https://pongnews.com/ | grep HTTP`
- Build size: `du -sh dist/` (target < 6MB)
- Image total: `du -sh public/images/` (target < 400KB)
- Lighthouse score (if available)

### 2. Content Quality Review
**Check all 19 articles for:**

| Check | Method |
|-------|--------|
| Dead links | Search for `url: null` in frontmatter |
| Retractions | Check `references/research-bank.md` retraction section |
| Image correctness | Vision model verify (random sample 3/week) |
| Category balance | Count articles per category (aim for ~4 each) |
| Date freshness | Oldest article age (target < 90 days) |

### 3. Image Audit (Monthly)
- Verify all images are table tennis (vision model batch)
- Check image file sizes (optimize if > 400KB)
- Check for duplicates: `md5sum *.jpg | uniq -d`

### 4. SEO Check (Weekly)
- Meta descriptions exist for all articles
- Title tags under 60 chars
- Internal links between related articles

## Daily Content Pipeline (Mon-Fri 8am ET)

Using the `pongnews-daily-content` skill:

1. Search PubMed for new table tennis studies (2025-2026)
2. Check `references/research-bank.md` to avoid duplicates
3. Select 1 high-quality study (meta-analysis > RCT > observational)
4. Verify citations via PubMed E-utilities or CrossRef
5. Find unique Pexels table tennis photo (vision verify)
6. Write article to `src/content/articles/`
7. Run `npx astro build` to verify
8. Commit and push to GitHub (auto-deploys to CF Pages)

**Article rotation (weekly schedule):**
- Monday: Longevity/mortality
- Tuesday: Cognitive health
- Wednesday: Physical health/aging
- Thursday: Rehabilitation
- Friday: Mental health/social
- Weekend: No new articles (review/maintenance)

## Monthly Deep Review

### 1. Citation Verification Audit
- Pick 5 random articles
- Verify ALL source URLs resolve (curl -I)
- Check for retractions in PubMed
- Update research-bank.md if needed

### 2. Analytics Review (when implemented)
- Top 10 articles by traffic
- Bounce rate (target < 50%)
- Time on page (target > 2 min)
- Source breakdown (direct, search, social)

### 3. Technical Health Check
- CF Pages deployment history (last 10 deploys)
- Error logs (CF Pages dashboard)
- SSL certificate expiration
- DNS health (Cloudflare dashboard)

## Alert Triggers

Send immediate alert to user if:
- Homepage load time > 500ms
- Build fails > 3 consecutive times
- Dead link found (404 on source URL)
- Image fails vision model verification
- Article has > 3 citations with `url: null`

## Windmill Cron Jobs

Create these schedules in Windmill:

| Schedule | Frequency | Purpose |
|----------|-----------|---------|
| `pongnews-weekly-audit` | Sun 9am ET | Full weekly audit (performance + content) |
| `pongnews-daily-content` | Mon-Fri 8am ET | Generate 1 new article |
| `pongnews-monthly-review` | 1st of month | Deep citation verification |
| `pongnews-performance-check` | Daily 6am ET | Quick performance ping |

## Quick Commands

```bash
# Quick stats
cd ~/Projects/pongnews
python content-pipeline.py stats

# Check for broken links
grep -r "url: null" src/content/articles/

# Check image sizes
ls -lh public/images/*.jpg | awk '{print $5, $9}' | sort -h

# Build and deploy
npx astro build
git add -A && git commit -m "..." && git push github main
```

## Content Refresh Rules

When to refresh old articles:
- Article is > 60 days old and covers a superseded study
- Citation is retracted (replace immediately)
- Better/more recent meta-analysis available on same topic
- Image audit finds wrong image (replace immediately)

When to KEEP old articles:
- Historical significance (landmark study)
- No better/more recent research on that exact topic
- Article still drives meaningful traffic
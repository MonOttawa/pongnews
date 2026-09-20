#!/usr/bin/env bash
# pongnews constraint checks — CONSTRAINTS.md is canonical; this script mirrors it.
# Usage: ./check.sh fast|content|deploy
set -u
cd "$(dirname "$0")"
FAIL=0
say() { printf '%s\n' "${1:-}"; }
gate() { # gate <name> <ok:0/1> <detail>
  if [ "$2" = "0" ]; then say "PASS  $1 — $3"; else say "FAIL  $1 — $3"; FAIL=1; fi
}


case "${1:-fast}" in

fast)
  # 1. build
  if out=$(npx astro build 2>&1); then
    gate "build" 0 "astro build exit 0"
  else
    gate "build" 1 "astro build failed: $(echo "$out" | tail -2 | tr '\n' ' ')"
    exit 1
  fi
  # 2. static overhead: dist minus images < 2.5MB
  kb=$(( $(du -sk dist/ | cut -f1) - $(du -sk dist/_astro 2>/dev/null | cut -f1 || echo 0) ))
  ikb=$(du -sk public/images/ | cut -f1)
  overhead=$(( $(du -sk dist/ | cut -f1) - ikb ))
  [ "$overhead" -lt 2560 ]; gate "build-overhead" $? "static overhead ${overhead}KB (limit 2560KB)"
  # 3. images: per-file <= 400KB, average <= 250KB/article
  nart=$(ls src/content/articles/*.md 2>/dev/null | wc -l)
  limit=$(( nart * 250 ))
  [ "$ikb" -le "$limit" ]; gate "images-avg" $? "${ikb}KB / ${nart} articles (limit ${limit}KB)"
  big=$(find public/images -type f -size +400k | wc -l)
  [ "$big" -eq 0 ]; gate "images-single" $? "$big file(s) over 400KB"
  # 4. stale tokens (word-boundary to avoid matching "Intervention")
  st=$(grep -rlE "Fraunces|\"Inter\"|'Inter'" dist/index.html dist/404.html 2>/dev/null | wc -l)
  [ "$st" -eq 0 ]; gate "stale-tokens" $? "$st dist file(s) reference removed fonts"
  # 5. dead links in content
  dl=$(grep -r "url: null" src/content/articles/ 2>/dev/null | wc -l)
  [ "$dl" -eq 0 ]; gate "dead-links" $? "$dl article(s) with url: null"
  ;;

content)
  # every article: avoid-ai-writing score <= 5
  bad=0; n=0
  for f in src/content/articles/*.md; do
    n=$((n+1))
    score=$(node -e "const D=require('$HOME/.hermes/skills/writing/avoid-ai-writing/detector/patterns.js');const fs=require('fs');try{const r=D.analyzeText(fs.readFileSync(process.argv[1],'utf8'));console.log(r.score)}catch(e){console.log(99)}" "$f")
    if [ "${score:-99}" -gt 5 ]; then say "FAIL  writing [$f] score=$score"; bad=$((bad+1)); fi
  done
  [ "$bad" -eq 0 ]; gate "writing-quality" $? "$bad of $n articles over threshold (score>5)"
  ;;

deploy)
  # deploy parity: live site serves a CSS bundle that exists in OUR dist
  live_css=$(curl -s -m 15 https://pongnews.com/ | grep -oE '/_astro/[^"]+\.css' | head -1)
  if [ -z "$live_css" ]; then gate "deploy-parity" 1 "no CSS bundle found in live HTML"
  elif [ -f "dist${live_css}" ]; then gate "deploy-parity" 0 "live serves ${live_css} (present in local dist)"
  else gate "deploy-parity" 1 "live serves ${live_css} — NOT in current dist (stale deploy)"; fi
  # performance: TTFB < 500ms
  ttfb=$(curl -s -o /dev/null -m 15 -w "%{time_starttransfer}" https://pongnews.com/)
  ok=$(python3 -c "print(0 if ${ttfb:-9} < 0.5 else 1)")
  gate "perf-ttfb" "$ok" "${ttfb}s (limit 0.5s)"
  ;;

*) echo "usage: ./check.sh fast|content|deploy"; exit 2;;
esac

exit $FAIL

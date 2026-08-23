#!/usr/bin/env bash
# Install avoid-ai-writing skill for Hermes Agent.
# Run once from any shell that has curl/git/node access.
# After it completes, run patterns.test.js to verify, then audit articles.
set -euo pipefail

SKILL_DIR="$HOME/.hermes/skills/writing/avoid-ai-writing"
REPO_URL="https://github.com/conorbronsdon/avoid-ai-writing"
RAW_URL="https://raw.githubusercontent.com/conorbronsdon/avoid-ai-writing/main/SKILL.md"
CLONE_DIR="/tmp/avoid-ai-writing"

echo "==> 1/5  Creating $SKILL_DIR"
mkdir -p "$SKILL_DIR"

echo "==> 2/5  Fetching SKILL.md from upstream"
curl --retry 3 --retry-delay 2 -sSfL -o "$SKILL_DIR/SKILL.md" "$RAW_URL"
bytes=$(wc -c < "$SKILL_DIR/SKILL.md")
echo "    SKILL.md = $bytes bytes"
if [ "$bytes" -lt 1000 ]; then
  echo "    !! SKILL.md looks too small -- network may have failed silently"
  exit 1
fi

echo "==> 3/5  Cloning repo for detector engine (zero-dep)"
rm -rf "$CLONE_DIR"
git clone --depth 1 "$REPO_URL" "$CLONE_DIR"

echo "==> 4/5  Copying detector engine into skill dir"
cp -r "$CLONE_DIR/detector" "$SKILL_DIR/detector"
ls "$SKILL_DIR/detector/"

echo "==> 5/5  Running fixture test"
cd "$SKILL_DIR/detector"
node patterns.test.js

echo ""
echo "==> node version:  $(node --version)"
echo "==> Skill installed at: $SKILL_DIR"
echo "==> Next: audit articles:"
echo "       node ~/.hermes/skills/writing/avoid-ai-writing/detector/patterns.js /home/mondy/Projects/pongnews/src/content/articles/<file>.md"

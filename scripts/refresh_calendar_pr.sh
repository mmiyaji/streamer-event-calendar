#!/usr/bin/env bash
set -euo pipefail

branch=automation/codex-sync
overlay=data/codex_synced_events.json
git fetch --prune origin
if [[ $(git rev-parse HEAD) != "$(git rev-parse origin/main)" ]]; then
  echo "main changed after validation. Retry against the new base." >&2
  exit 1
fi

if git show "origin/$branch:$overlay" 2>/dev/null | cmp -s - "$1"; then
  echo "The remote branch already contains the validated overlay."
else
  git switch -C "$branch" origin/main
  cp "$1" "$overlay"
  git config user.name "github-actions[bot]"
  git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
  git add -- "$overlay"
  git commit -m "chore(calendar): sync verified Codex event changes"
  git push --force-with-lease origin "HEAD:refs/heads/$branch"
fi

pr=$(gh pr list --head "$branch" --base main --state open --json number,isCrossRepository \
  --jq 'map(select(.isCrossRepository == false))[0].number // empty')
if [[ -z "$pr" ]]; then
  gh pr create --base main --head "$branch" \
    --title "Calendar: apply Codex-verified event changes" \
    --body "Automated data-only sync from Codex. Validation and the calendar build ran on trusted main code."
fi

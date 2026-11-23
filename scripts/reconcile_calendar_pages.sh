#!/usr/bin/env bash
set -euo pipefail

# GITHUB_TOKEN merges do not trigger the Pages push workflow. Check main even
# on polls with no new proposals, so a failed dispatch or deployment is retried.
git fetch origin main
target=$(git rev-parse FETCH_HEAD)
runs=(gh run list --workflow pages.yml --branch main --limit 1)
published=$("${runs[@]}" --status success --json headSha --jq '.[0].headSha // empty')
# These are the build inputs watched by pages.yml. Documentation-only commits
# after a deployment do not change what is served.
if [[ -n "$published" ]] && git diff --quiet "$published" "$target" -- data site scripts .github/workflows/pages.yml; then
  echo "Pages is up to date."
  exit 0
fi
status=$("${runs[@]}" --commit "$target" --json status --jq '.[0].status // empty')
if [[ -z "$status" || "$status" == completed ]]; then
  gh workflow run pages.yml --ref main
else
  echo "Pages publication for $target is $status."
fi

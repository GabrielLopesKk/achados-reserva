#!/usr/bin/env bash
# Verifica se os commits entre $1 e $2 seguem Conventional Commits.
set -euo pipefail
base="${1:-origin/main}"; head="${2:-HEAD}"
pattern='^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)(\([a-z0-9._-]+\))?!?: .+'
status=0
while IFS= read -r subject; do
  case "$subject" in Merge*) continue ;; esac
  if ! [[ "$subject" =~ $pattern ]]; then
    echo "Commit fora do padrão: $subject"; status=1
  fi
done < <(git log --format=%s "$base..$head")
exit $status

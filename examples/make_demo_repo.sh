#!/usr/bin/env bash
# Builds a small throwaway git repo for a fictional notes app, used by the examples and tests.
set -euo pipefail
dir="${1:-/tmp/jotter-demo}"
rm -rf "$dir"; mkdir -p "$dir"; cd "$dir"
git init -q -b main
c() { git add -A; git -c user.name=demo -c user.email=demo@example.invalid commit -qm "$1" ${2:+-m "$2"}; }
echo v1 > app.txt; c "initial"; git tag v1.4.0
mkdir -p src migrations
echo search > src/search.py; c "feat(search): search inside note attachments (#41)" "PDF and image text is now indexed. Search returns in about 0.4 s on 10000 notes, was 2.5 s."
echo t > src/test_search.py; c "test: cover attachment search (#42)"
echo exp > src/export.py; c "fix(export): keep line breaks when exporting to Markdown (#43)"
echo "ALTER TABLE notes ADD COLUMN pinned" > migrations/007_pinned.sql; echo pin > src/pin.py
c "feat!: pinned notes; sync server must be 2.0 or newer (#44)" "BREAKING: self-hosted sync servers older than 2.0 reject the new pinned field. Upgrade the server first."
echo r > src/util.py; c "refactor: split NoteStore into reader and writer (#45)"
echo ci > ci.yml; c "ci: cache wheels (#46)"
echo dark > src/theme.py; c "feat(settings): follow the system dark mode (#47)"
git tag v1.5.0
echo "$dir"

#!/bin/sh
# Brings work that was merged on GitHub main (pull requests) into the shared source folder.
# Run it after any PR merges, and before tools/push-github.sh. Then build and boot-test as usual.
# Usage: sh /mnt/project-files/one-piece-mod/tools/pull-github.sh [--dry-run]
# For each file GitHub changed since the last sync:
#   - shared copy still the old version (or missing)  -> takes GitHub's version (or deletes it if GitHub deleted it)
#   - shared copy edited too                          -> CONFLICT, left alone; merge it by hand
# When there are no conflicts it records GitHub main as the new sync point.
set -e
P=/mnt/project-files/one-piece-mod
URL=${OP_URL:-https://github.com/kingbloblob/one-piece-main-mod}
R=${OP_REPO:-/home/user/one-piece-main-mod}
SYNC=$P/.github-last-sync
DRY=0; [ "$1" = --dry-run ] && DRY=1
[ -d "$R/.git" ] || git clone "$URL" "$R"
cd "$R"
git fetch -q origin "+main:refs/remotes/origin/main"
LAST=$(cat "$SYNC" 2>/dev/null || true)
if [ -z "$LAST" ] || ! git cat-file -e "$LAST^{commit}" 2>/dev/null; then
	echo "No sync record. Do a full two-way merge first (see docs/github-sync.md)."; exit 1
fi
NEW=$(git rev-parse origin/main)
[ "$LAST" = "$NEW" ] && { echo "shared source already has everything from GitHub main"; exit 0; }
samepx() { git show "$2" | python3 -I -c '
import sys,io
from PIL import Image
a=Image.open(sys.argv[1]).convert("RGBA"); b=Image.open(io.BytesIO(sys.stdin.buffer.read())).convert("RGBA")
sys.exit(0 if a.size==b.size and a.tobytes()==b.tobytes() else 1)' "$1" 2>/dev/null; }
conf=0; took=0
for f in $(git diff --name-only "$LAST" "$NEW" -- . ':(exclude)docs/guides'); do
	case "$f" in tools/treasure/*) d=$P/source/$f;; tools/*) d=$P/$f;; *) d=$P/source/$f;; esac
	old=$(git rev-parse -q --verify "$LAST:$f" 2>/dev/null || echo none)
	cur=none; [ -f "$d" ] && cur=$(git hash-object "$d")
	new=$(git rev-parse -q --verify "$NEW:$f" 2>/dev/null || echo none)
	[ "$cur" = "$new" ] && continue
	# The project-files folder re-saves PNGs, so compare images by pixels, not bytes.
	case "$f" in *.png) if [ "$cur" != none ]; then
		[ "$new" != none ] && samepx "$d" "$NEW:$f" && continue
		[ "$old" != none ] && samepx "$d" "$LAST:$f" && cur=$old
	fi;; esac
	if [ "$cur" = "$old" ]; then
		took=$((took+1)); echo "take  $f"
		[ $DRY = 1 ] && continue
		if [ "$new" = none ]; then rm -f "$d"; else mkdir -p "$(dirname "$d")"; git show "$NEW:$f" > "$d"; fi
	else
		conf=$((conf+1)); echo "CONFLICT  $f  (changed in both places)"
	fi
done
echo "$took taken from GitHub, $conf conflicts"
if [ $DRY = 0 ] && [ $conf = 0 ]; then echo "$NEW" > "$SYNC"; echo "sync point is now $NEW"; fi
[ $conf = 0 ]

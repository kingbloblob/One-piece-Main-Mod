#!/bin/sh
# Backs up the current shared project to GitHub (github.com/kingbloblob/One-piece-Main-Mod;
# moved there from ryanmTCG/one-piece-mod on 2026-11-07).
# Copies source/ (minus build/, .gradle/, run/), tools/ and the guides into a local git checkout,
# then commits and pushes whatever changed. Run it after a successful build.
# Usage: sh /mnt/project-files/one-piece-mod/tools/push-github.sh "what changed" [branch]
#   branch defaults to main. Set OP_REPO to use another checkout folder.
#
# Drift guard: this script REPLACES the branch with the shared folder, so anything merged on GitHub
# but never copied into the shared source would be deleted. It remembers the last commit it pushed
# (in /mnt/project-files/one-piece-mod/.github-last-sync) and stops if GitHub changed files since then
# that the shared source does not have. Run `sh tools/pull-github.sh` first to bring them in.
# FORCE=1 skips the guard (only when you are sure GitHub's newer files should be thrown away).
set -e
P=/mnt/project-files/one-piece-mod
URL=${OP_URL:-https://github.com/kingbloblob/one-piece-main-mod}
R=${OP_REPO:-/home/user/one-piece-main-mod}
MSG=${1:-"Snapshot of the shared source"}
SYNC=$P/.github-last-sync
if [ ! -d "$R/.git" ]; then
	git clone "$URL" "$R"
fi
cd "$R"
B=${2:-main}
if git fetch -q origin "+$B:refs/remotes/origin/$B" 2>/dev/null; then
	git checkout -q -f -B "$B" "origin/$B"
else
	# Branch does not exist on GitHub yet (e.g. a brand new empty repo): start it fresh, nothing to guard.
	echo "GitHub has no $B branch yet; creating it from the shared source."
	git checkout -q --orphan "$B" 2>/dev/null || true
	FORCE=1
fi

# --- drift guard ---
if [ "$FORCE" != 1 ]; then
	LAST=$(cat "$SYNC" 2>/dev/null || true)
	if [ -z "$LAST" ] || ! git cat-file -e "$LAST^{commit}" 2>/dev/null; then
		echo "No record of the last sync with GitHub. Run tools/pull-github.sh first (or FORCE=1 if you know both sides match)."
		exit 1
	fi
	MISSING=""
	for f in $(git diff --name-only "$LAST" "origin/$B" -- . ':(exclude)docs/guides'); do
		case "$f" in tools/treasure/*) d=$P/source/$f;; tools/*) d=$P/$f;; *) d=$P/source/$f;; esac
		if git cat-file -e "origin/$B:$f" 2>/dev/null; then
			[ -f "$d" ] && [ "$(git hash-object "$d")" = "$(git rev-parse "origin/$B:$f")" ] || MISSING="$MISSING $f"
		fi
	done
	if [ -n "$MISSING" ]; then
		echo "STOPPED: GitHub $B has changes the shared source does not have (they would be deleted):"
		for f in $MISSING; do echo "  $f"; done
		echo "Run: sh $P/tools/pull-github.sh   then build, then push again."
		exit 1
	fi
fi

# Start from a clean tree so files deleted in source/ are deleted on GitHub too.
find . -mindepth 1 -maxdepth 1 ! -name .git -exec rm -rf {} +
tar -C $P/source --exclude=./build --exclude=./.gradle --exclude=./run --exclude=./out --exclude=./.idea -cf - . | tar --no-same-owner -xf -
mkdir -p tools && tar -C $P/tools --exclude=__pycache__ -cf - . | tar --no-same-owner -C tools -xf -
G=docs/guides && mkdir -p $G
cp $P/README.md $G/project-overview.md
cp $P/character-roles.md $P/structures.md $G/
for d in achievements balance biomes buildings characters cuisine cyborg deco endgame flora fruits furniture hideout lore pets release seatrain ships story weather worldevents; do
	[ -d $P/$d ] || continue
	mkdir -p $G/$d
	find $P/$d -maxdepth 1 -type f ! -name '*.png' ! -name '*.zip' ! -name '*.jar' -exec cp {} $G/$d/ \;
done
git add -A
if git diff --cached --quiet; then echo "nothing new to push"; git rev-parse HEAD > "$SYNC"; exit 0; fi
git commit -q -m "$MSG"
for i in 2 4 8 16 0; do
	git push -u origin "$B" && { echo "pushed to $B"; [ "$B" = main ] && git rev-parse HEAD > "$SYNC"; exit 0; }
	[ $i = 0 ] && break
	sleep $i
done
echo "push failed"; exit 1

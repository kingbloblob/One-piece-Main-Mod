#!/bin/sh
# Rebuilds one-piece-mod.zip from the shared source folder (top folder in the zip: one-piece-mod/).
# Also writes one-piece-mod-part1.zip, -part2.zip, ... (each under 9 MiB, so under 10 MB) for tools that can only fetch
# files up to ~10 MB. Unpack every part into the same place to get the full project back.
set -e
D=$(mktemp -d)
ln -s /mnt/project-files/one-piece-mod/source "$D/one-piece-mod"
cd "$D"
# Exit 18 = some files vanished while zipping (other threads building or deleting): keep going, just say how many.
set +e
zip -qrD -X out.zip one-piece-mod/ -x 'one-piece-mod/build/*' 'one-piece-mod/.gradle/*' 'one-piece-mod/run/*' 'one-piece-mod/runc/*' 'one-piece-mod/out/*' 2> zip.err
code=$?
set -e
if [ $code = 18 ]; then
	echo "zip warning: $(grep -c 'zip warning' zip.err) files changed while zipping and were skipped"
elif [ $code != 0 ]; then
	cat zip.err; exit $code
fi
cp out.zip /mnt/project-files/one-piece-mod/one-piece-mod.zip
python3 -I /mnt/project-files/one-piece-mod/tools/split-zip.py out.zip /mnt/project-files/one-piece-mod 9
cd / && rm -rf "$D"
echo "zip rebuilt"

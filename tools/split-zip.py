"""Splits one-piece-mod.zip into one-piece-mod-part1.zip, -part2.zip, ... each under the size limit.
Every part has the same top folder (one-piece-mod/), so unpacking all parts into one place gives back the full project.
Used by rebuild-zip.sh when the full zip is too big for tools that can only fetch files under 16 MB.
Usage: python3 split-zip.py <full zip> <output dir> [max MB, default 14]"""
import os
import sys
import zipfile

src, out = sys.argv[1], sys.argv[2]
limit = float(sys.argv[3] if len(sys.argv) > 3 else 14) * 1024 * 1024

for f in os.listdir(out):
	if f.startswith("one-piece-mod-part") and f.endswith(".zip"):
		os.remove(os.path.join(out, f))

with zipfile.ZipFile(src) as z:
	infos = sorted(z.infolist(), key=lambda i: i.filename)
	parts, cur, size = [], [], 0
	for i in infos:
		cost = i.compress_size + 100 + 2 * len(i.filename)  # data plus headers
		if cur and size + cost > limit:
			parts.append(cur)
			cur, size = [], 0
		cur.append(i)
		size += cost
	if cur:
		parts.append(cur)
	for n, part in enumerate(parts, 1):
		path = os.path.join(out, f"one-piece-mod-part{n}.zip")
		with zipfile.ZipFile(path, "w") as w:
			for i in part:
				w.writestr(i, z.read(i), compress_type=i.compress_type)
		print(f"{os.path.basename(path)}: {len(part)} files, {os.path.getsize(path) / 1024 / 1024:.1f} MB")

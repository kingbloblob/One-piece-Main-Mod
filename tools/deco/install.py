"""Copies the generator output into the shared mod source. Files under data/minecraft/tags are
union-merged with what other features already put there; everything else is ours and is replaced.
Usage: python3 install.py <out_dir> <mod_source_dir>"""
import json, os, shutil, sys

out, src = sys.argv[1], sys.argv[2]
merged = copied = 0
for root, _, files in os.walk(os.path.join(out, 'src')):
    for f in files:
        a = os.path.join(root, f)
        rel = os.path.relpath(a, out)
        b = os.path.join(src, rel)
        os.makedirs(os.path.dirname(b), exist_ok=True)
        if '/data/minecraft/tags/' in rel and os.path.exists(b):
            old = json.load(open(b)); new = json.load(open(a))
            vals = list(dict.fromkeys(old.get('values', []) + new['values']))
            old['values'] = vals
            with open(b, 'w') as fh:
                json.dump(old, fh, indent=2); fh.write('\n')
            merged += 1
        else:
            shutil.copyfile(a, b)
            copied += 1
print(f'copied {copied}, merged {merged} shared tag files')

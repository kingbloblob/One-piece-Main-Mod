"""One-off/rerunnable: converts structure templates to the 26.3 format (palette "Name"->"id",
"Properties"->"properties", DataVersion 5023). Without this, 26.3 places the entities but no blocks.
Usage: python3 fix_palette_format.py <structure dir>"""
import os, sys
from swap_blocks import load, save, get
n = 0
for fn in sorted(os.listdir(sys.argv[1])):
    if not fn.endswith('.nbt'): continue
    path = os.path.join(sys.argv[1], fn)
    name, root = load(path)
    changed = False
    for entry in get(root, 'palette')[2][1]:
        for e in entry:
            if e[0] == 'Name': e[0] = 'id'; changed = True
            if e[0] == 'Properties': e[0] = 'properties'; changed = True
    dv = get(root, 'DataVersion')
    if dv[2] != 5023: dv[2] = 5023; changed = True
    if changed: save(path, name, root); n += 1
print('converted', n, 'templates')

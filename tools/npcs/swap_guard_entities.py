"""Turns the vanilla stand-in guards inside structure templates into the mod's pirate and Marine NPCs.

Run:  PYTHONDONTWRITEBYTECODE=1 python3 swap_guard_entities.py [path to source/]
Every entity in data/onepiece/structure/**/*.nbt tagged onepiece_kit_<id> whose kit is a pirate or Marine
(NPC_MARINES / NPC_PIRATES in tools/worldgen/kits.py) gets its "id" changed to onepiece:marine or onepiece:sea_pirate.
Only entity ids change; blocks are left alone. Safe to run again (it only touches what still needs swapping).
New templates made with kit.py already use the right ids.
"""
import gzip
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'worldgen'))
from kits import NPC_MARINES, NPC_PIRATES

SRC = next((a for a in sys.argv[1:] if not a.startswith('--')), '/mnt/project-files/one-piece-mod/source')
ROOT = os.path.join(SRC, 'src/main/resources/data/onepiece/structure')
TARGET = {k: 'onepiece:marine' for k in NPC_MARINES}
TARGET.update({k: 'onepiece:sea_pirate' for k in NPC_PIRATES})


# --- a tiny NBT reader/writer that keeps every tag type exactly as it was ---
class R:
    def __init__(self, b): self.b, self.i = b, 0
    def take(self, n):
        v = self.b[self.i:self.i + n]; self.i += n; return v
    def u(self, fmt):
        n = struct.calcsize(fmt); return struct.unpack('>' + fmt, self.take(n))[0]
    def s(self): return self.take(self.u('H')).decode('utf-8')


def read_payload(r, t):
    if t == 1: return r.u('b')
    if t == 2: return r.u('h')
    if t == 3: return r.u('i')
    if t == 4: return r.u('q')
    if t == 5: return r.u('f')
    if t == 6: return r.u('d')
    if t == 7: return r.take(r.u('i'))
    if t == 8: return r.s()
    if t == 9:
        et = r.u('b'); n = r.u('i')
        return ('list', et, [read_payload(r, et) for _ in range(n)])
    if t == 10:
        d = []
        while True:
            tt = r.u('b')
            if tt == 0: return ('compound', d)
            name = r.s(); d.append((tt, name, read_payload(r, tt)))
    if t == 11: n = r.u('i'); return ('ints', [r.u('i') for _ in range(n)])
    if t == 12: n = r.u('i'); return ('longs', [r.u('q') for _ in range(n)])
    raise ValueError(t)


def write_payload(t, v):
    if t == 1: return struct.pack('>b', v)
    if t == 2: return struct.pack('>h', v)
    if t == 3: return struct.pack('>i', v)
    if t == 4: return struct.pack('>q', v)
    if t == 5: return struct.pack('>f', v)
    if t == 6: return struct.pack('>d', v)
    if t == 7: return struct.pack('>i', len(v)) + v
    if t == 8: b = v.encode('utf-8'); return struct.pack('>H', len(b)) + b
    if t == 9:
        _, et, items = v
        return struct.pack('>bi', et, len(items)) + b''.join(write_payload(et, e) for e in items)
    if t == 10:
        out = b''
        for (tt, name, val) in v[1]:
            nb = name.encode('utf-8')
            out += struct.pack('>bH', tt, len(nb)) + nb + write_payload(tt, val)
        return out + b'\x00'
    if t == 11: return struct.pack('>i', len(v[1])) + b''.join(struct.pack('>i', x) for x in v[1])
    if t == 12: return struct.pack('>i', len(v[1])) + b''.join(struct.pack('>q', x) for x in v[1])
    raise ValueError(t)


def get(comp, key):
    for (t, name, val) in comp[1]:
        if name == key: return t, val
    return None, None


def swap(path):
    raw = gzip.open(path).read()
    r = R(raw)
    rt = r.u('b'); rname = r.s(); root = read_payload(r, rt)
    t, ents = get(root, 'entities')
    if t != 9:
        return 0
    changed = 0
    for e in ents[2]:
        _, nbt = get(e, 'nbt')
        if nbt is None: continue
        _, tags = get(nbt, 'Tags')
        kit = None
        for tag in (tags[2] if tags else []):
            if isinstance(tag, str) and tag.startswith('onepiece_kit_'):
                kit = tag[len('onepiece_kit_'):]
        want = TARGET.get(kit)
        if not want: continue
        for i, (tt, name, val) in enumerate(nbt[1]):
            if name == 'id' and val != want:
                nbt[1][i] = (tt, name, want); changed += 1
    if changed:
        nb = rname.encode('utf-8')
        data = struct.pack('>bH', rt, len(nb)) + nb + write_payload(rt, root)
        with gzip.open(path, 'wb') as f:
            f.write(data)
    return changed


def main():
    total, files = 0, 0
    for dirpath, _, names in os.walk(ROOT):
        for n in sorted(names):
            if n.endswith('.nbt'):
                c = swap(os.path.join(dirpath, n))
                if c:
                    files += 1; total += c
                    print('  %-40s %d guards' % (os.path.relpath(os.path.join(dirpath, n), ROOT), c))
    print('swapped %d guards in %d templates' % (total, files))


if __name__ == '__main__':
    main()

"""Moves ship cannons into their gunports in structure templates (.nbt), so the barrels poke out of the hull.

A Cannon standing right behind a one-block hull wall (solid block in front, open sea/air beyond it) becomes
onepiece:cannon[mounted=true] IN that wall block (drawn as a dark gunport with the barrel sticking out and the
carriage on the deck behind), and its old deck cell becomes air. Cannons anywhere else are left alone.
Usage: python3 -I mount_cannons.py [--dry] file.nbt...   (files under a ships/ folder count the template edge as sea)
"""
import gzip, io, struct, sys

# ---- type-preserving NBT (each value is (tag, payload)) ----
def read(b):
    f = io.BytesIO(b)
    def r(fmt, n): return struct.unpack('>' + fmt, f.read(n))[0]
    def s(): return f.read(r('H', 2)).decode('utf8')
    def p(t):
        if t == 1: return r('b', 1)
        if t == 2: return r('h', 2)
        if t == 3: return r('i', 4)
        if t == 4: return r('q', 8)
        if t == 5: return r('f', 4)
        if t == 6: return r('d', 8)
        if t == 7: return f.read(r('i', 4))
        if t == 8: return s()
        if t == 9:
            et = r('b', 1); n = r('i', 4); return (et, [p(et) for _ in range(n)])
        if t == 10:
            d = {}
            while True:
                tt = r('b', 1)
                if tt == 0: return d
                k = s(); d[k] = (tt, p(tt))
        if t == 11: n = r('i', 4); return [r('i', 4) for _ in range(n)]
        if t == 12: n = r('i', 4); return [r('q', 8) for _ in range(n)]
    t = r('b', 1); name = s(); return name, (t, p(t))

def write(name, root):
    f = io.BytesIO()
    def w(fmt, v): f.write(struct.pack('>' + fmt, v))
    def s(v): e = v.encode('utf8'); w('H', len(e)); f.write(e)
    def p(t, v):
        if t == 1: w('b', v)
        elif t == 2: w('h', v)
        elif t == 3: w('i', v)
        elif t == 4: w('q', v)
        elif t == 5: w('f', v)
        elif t == 6: w('d', v)
        elif t == 7: w('i', len(v)); f.write(v)
        elif t == 8: s(v)
        elif t == 9:
            et, items = v
            if not items: et = 0
            w('b', et); w('i', len(items))
            for x in items: p(et, x)
        elif t == 10:
            for k, (tt, x) in v.items():
                w('b', tt); s(k); p(tt, x)
            w('b', 0)
        elif t == 11: w('i', len(v)); [w('i', x) for x in v]
        elif t == 12: w('i', len(v)); [w('q', x) for x in v]
    t, v = root; w('b', t); s(name); p(t, v)
    return f.getvalue()

NOT_WALL = ('fence', 'slab', 'stairs', 'pane', 'door', 'wall', 'lantern', 'air', 'water', 'chest', 'sign', 'banner',
            'button', 'torch', 'carpet', 'glass', 'onepiece:', 'rail', 'ladder', 'bars', 'chain', 'candle', 'pot',
            'head', 'skull', 'leaves', 'barrel', 'bed', 'table', 'lever', 'plate', 'rod', 'cake')
STEP = {'north': (0, -1), 'south': (0, 1), 'east': (1, 0), 'west': (-1, 0)}

def name_of(entry):
    c = entry
    return (c.get('Name') or c.get('id'))[1]

def props_key(entry):
    return 'Properties' if 'Properties' in entry else 'properties'

def patch(path, dry):
    raw = gzip.open(path).read()
    rootname, root = read(raw)
    d = root[1]
    palette = d['palette'][1][1]
    size = d['size'][1][1]
    blocks = d['blocks'][1][1]
    at = {tuple(b['pos'][1][1]): b for b in blocks}
    ship = '/ships/' in path.replace('\\', '/')

    def state(pos):
        b = at.get(pos)
        if b is None:
            inside = all(0 <= pos[i] < size[i] for i in range(3))
            return 'air' if (inside or ship) else None
        return name_of(palette[b['state'][1]])

    def pal_index(entry):
        for i, e in enumerate(palette):
            if e == entry:
                return i
        palette.append(entry)
        return len(palette) - 1

    idkey = 'id' if 'id' in palette[0] else 'Name'
    moved = 0
    for pos, b in list(at.items()):
        e = palette[b['state'][1]]
        if name_of(e) != 'onepiece:cannon':
            continue
        pk = props_key(e)
        props = dict(e.get(pk, (10, {}))[1])
        if props.get('mounted', (8, 'false'))[1] == 'true':
            continue
        facing = props.get('facing', (8, 'north'))[1]
        dx, dz = STEP[facing]
        front = (pos[0] + dx, pos[1], pos[2] + dz)
        beyond = (pos[0] + 2 * dx, pos[1], pos[2] + 2 * dz)
        fs, bs = state(front), state(beyond)
        if fs is None or bs is None or front not in at:
            continue
        if any(w in fs for w in NOT_WALL) or bs not in ('air', 'minecraft:air', 'minecraft:water', 'minecraft:cave_air'):
            continue
        fb = at[front]
        if 'nbt' in fb:
            continue
        mounted = {idkey: (8, 'onepiece:cannon'), pk: (10, {'facing': (8, facing), 'mounted': (8, 'true')})}
        fb['state'] = (3, pal_index(mounted))
        b['state'] = (3, pal_index({idkey: (8, 'minecraft:air')}))
        moved += 1
    if moved and not dry:
        d['palette'] = (9, (10, palette))
        with gzip.open(path, 'wb') as out:
            out.write(write(rootname, root))
    return moved

if __name__ == '__main__':
    dry = '--dry' in sys.argv
    total = 0
    for p in sys.argv[1:]:
        if p.startswith('--'):
            continue
        n = patch(p, dry)
        if n:
            print(f'{p}: {n} cannon(s) mounted in gunports')
        total += n
    print('total', total)

"""Swaps blocks in the structure templates' palettes, in place.

Usage: python3 swap_blocks.py <swaps.json> <structure dir>
swaps.json: {"structure name or *": {"minecraft:old_block": "onepiece:new_block[prop=value]"}}
Per-structure entries override "*". A block's state properties are kept when the new block has them
(read from its blockstate file), so stairs stay facing the same way. Mapping a block to itself cancels a "*" swap.
"""
import gzip, io, json, os, struct, sys

ASSETS = '/mnt/project-files/one-piece-mod/source/src/main/resources/assets'


# ---- tiny lossless NBT reader/writer: every tag is (type id, value) ----
def rd(f, t):
    if t == 1: return struct.unpack('>b', f.read(1))[0]
    if t == 2: return struct.unpack('>h', f.read(2))[0]
    if t == 3: return struct.unpack('>i', f.read(4))[0]
    if t == 4: return struct.unpack('>q', f.read(8))[0]
    if t == 5: return struct.unpack('>f', f.read(4))[0]
    if t == 6: return struct.unpack('>d', f.read(8))[0]
    if t == 7: n = struct.unpack('>i', f.read(4))[0]; return f.read(n)
    if t == 8: n = struct.unpack('>H', f.read(2))[0]; return f.read(n).decode('utf-8')
    if t == 9:
        et = f.read(1)[0]; n = struct.unpack('>i', f.read(4))[0]
        return (et, [rd(f, et) for _ in range(n)])
    if t == 10:
        out = []
        while True:
            ct = f.read(1)[0]
            if ct == 0: return out
            n = struct.unpack('>H', f.read(2))[0]; name = f.read(n).decode('utf-8')
            out.append([name, ct, rd(f, ct)])
    if t == 11: n = struct.unpack('>i', f.read(4))[0]; return list(struct.unpack('>%di' % n, f.read(4 * n)))
    if t == 12: n = struct.unpack('>i', f.read(4))[0]; return list(struct.unpack('>%dq' % n, f.read(8 * n)))
    raise ValueError(t)


def wr(f, t, v):
    if t == 1: f.write(struct.pack('>b', v))
    elif t == 2: f.write(struct.pack('>h', v))
    elif t == 3: f.write(struct.pack('>i', v))
    elif t == 4: f.write(struct.pack('>q', v))
    elif t == 5: f.write(struct.pack('>f', v))
    elif t == 6: f.write(struct.pack('>d', v))
    elif t == 7: f.write(struct.pack('>i', len(v))); f.write(v)
    elif t == 8: b = v.encode('utf-8'); f.write(struct.pack('>H', len(b))); f.write(b)
    elif t == 9:
        et, items = v; f.write(bytes([et])); f.write(struct.pack('>i', len(items)))
        for it in items: wr(f, et, it)
    elif t == 10:
        for name, ct, cv in v:
            f.write(bytes([ct])); b = name.encode('utf-8'); f.write(struct.pack('>H', len(b))); f.write(b); wr(f, ct, cv)
        f.write(b'\x00')
    elif t == 11: f.write(struct.pack('>i', len(v))); f.write(struct.pack('>%di' % len(v), *v))
    elif t == 12: f.write(struct.pack('>i', len(v))); f.write(struct.pack('>%dq' % len(v), *v))


def load(path):
    f = io.BytesIO(gzip.open(path).read())
    t = f.read(1)[0]; n = struct.unpack('>H', f.read(2))[0]; name = f.read(n).decode()
    return name, rd(f, t)


def save(path, name, root):
    f = io.BytesIO()
    f.write(b'\x0a'); b = name.encode(); f.write(struct.pack('>H', len(b))); f.write(b); wr(f, 10, root)
    with gzip.open(path, 'wb') as g:
        g.write(f.getvalue())


def get(comp, key):
    for e in comp:
        if e[0] == key: return e
    return None


_props = {}


def block_props(block_id):
    """Property names the block has, from its blockstate file ("variants" keys or "multipart" whens)."""
    if block_id in _props: return _props[block_id]
    ns, path = block_id.split(':')
    names = set()
    p = os.path.join(ASSETS, ns, 'blockstates', path + '.json')
    if os.path.exists(p):
        d = json.load(open(p))
        for key in d.get('variants', {}):
            for kv in key.split(','):
                if '=' in kv: names.add(kv.split('=')[0])
        for case in d.get('multipart', []):
            when = case.get('when', {})
            for w in when.get('OR', [when]) if 'OR' in when else [when]:
                names.update(k for k in w if k != 'OR')
    _props[block_id] = names
    return names


def main(swaps_path, struct_dir):
    swaps = json.load(open(swaps_path))
    every = swaps.get('*', {})
    total = 0
    for fn in sorted(os.listdir(struct_dir)):
        if not fn.endswith('.nbt'): continue
        sname = fn[:-4]
        table = dict(every); table.update(swaps.get(sname, {}))
        table = {k: v for k, v in table.items() if k != v}
        if not table: continue
        path = os.path.join(struct_dir, fn)
        name, root = load(path)
        pal = get(root, 'palette')
        changed = []
        for entry in pal[2][1]:
            ne = get(entry, 'id') or get(entry, 'Name')
            if ne[2] not in table: continue
            target = table[ne[2]]
            new_id, forced = target, {}
            if '[' in target:
                new_id = target[:target.index('[')]
                forced = dict(kv.split('=') for kv in target[target.index('[') + 1:-1].split(','))
            if not os.path.exists(os.path.join(ASSETS, new_id.split(':')[0], 'blockstates', new_id.split(':')[1] + '.json')) \
                    and not new_id.startswith('minecraft:'):
                print('  skip (no blockstate file):', sname, new_id); continue
            allowed = block_props(new_id)
            old_props = get(entry, 'properties') or get(entry, 'Properties')
            keep = [[k, 8, v] for k, t, v in (old_props[2] if old_props else []) if k in allowed and k not in forced]
            keep += [[k, 8, v] for k, v in forced.items()]
            changed.append('%s -> %s' % (ne[2], target))
            ne[0] = 'id'; ne[2] = new_id
            entry[:] = [e for e in entry if e[0] not in ('Properties', 'properties')]
            if keep:
                entry.append(['properties', 10, keep])
        if changed:
            save(path, name, root)
            total += len(changed)
            print(sname + ':', ', '.join(sorted(set(changed))))
    print('swapped', total, 'palette entries')


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])

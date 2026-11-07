"""Places a Poneglyph (2 blocks tall) on open ground near the middle of the structures that should have one.
Usage: python3 add_poneglyphs.py <structure dir>. Skips a structure that already has one."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import swap_blocks as nbt

STRUCTURES = ['mokomo_dukedom', 'whole_cake_chateau', 'onigashima', 'hachinosu',  # Road Poneglyphs
              'ohara_library', 'shandora', 'alubarna_palace', 'ryugu_palace', 'laugh_tale']  # history
SOFT = ('air', 'water', 'grass', 'fern', 'flower', 'snow', 'carpet', 'torch', 'lantern', 'leaves', 'vine', 'petals')


def place(path):
    name, root = nbt.load(path)
    pal = nbt.get(root, 'palette')[2][1]
    names = [(nbt.get(e, 'id') or nbt.get(e, 'Name'))[2] for e in pal]
    if 'onepiece:poneglyph' in names:
        return 'already has one'
    blocks = nbt.get(root, 'blocks')[2][1]
    size = nbt.get(root, 'size')[2][1]
    solid = {}
    for b in blocks:
        pos = tuple(nbt.get(b, 'pos')[2][1])
        n = names[nbt.get(b, 'state')[2]]
        solid[pos] = not any(s in n for s in SOFT)
    tops = {}
    for (x, y, z), s in solid.items():
        if s and y > tops.get((x, z), -1):
            tops[(x, z)] = y
    if not tops:
        return 'no ground found'
    ground = min(tops.values())
    cx, cz = size[0] / 2, size[2] / 2
    cands = [(abs(x - cx) + abs(z - cz), x, z, y) for (x, z), y in tops.items()
             if y <= ground + 1 and y + 2 < size[1] and 1 <= x < size[0] - 1 and 1 <= z < size[2] - 1]
    if not cands:
        return 'no open spot'
    _, x, z, y = min(cands)
    pal.append([['id', 8, 'onepiece:poneglyph']])
    idx = len(pal) - 1
    for dy in (1, 2):
        p = (x, y + dy, z)
        blocks[:] = [b for b in blocks if tuple(nbt.get(b, 'pos')[2][1]) != p]
        blocks.append([['pos', 9, (3, list(p))], ['state', 3, idx]])
    nbt.save(path, name, root)
    return 'placed at %d %d %d' % (x, y + 1, z)


if __name__ == '__main__':
    d = sys.argv[1]
    for s in STRUCTURES:
        print(s, place(os.path.join(d, s + '.nbt')))

"""Pack furnished houses onto free land (batch 14+ helper): random-order lots, nearest-to-a-focus first, each house on
a plinth from the lowest ground up to the highest corner so slopes become stacked tiers.

    pack_houses(bb, hy, ok, area, n, seed, tracker, pal, roofs, focus=(x, z), reserved=[(x1, z1, x2, z2)], ...)

hy(x, z) -> ground y (top block); ok(x, z) -> True where a house may stand (land, not a street). Returns the list of
placed lots (x0, z0, w, d, y, rot)."""
import numpy as np

from mcb.kit import AIR, seed_of, house_module, place_house


def _hits(r, lots, gap):
    x1, z1, x2, z2 = r
    for (a, b, c, d) in lots:
        if x1 <= c + gap and x2 >= a - gap and z1 <= d + gap and z2 >= b - gap:
            return True
    return False


FRONT = 3  # clear yard in front of each door (plus one more per block the plinth stands above the ground)
DOOR_OUT = {0: (0, 1), 1: (-1, 0), 2: (0, -1), 3: (1, 0)}  # place_house rot -> the way the door faces


def _front(r, rot, n):
    """The strip n deep in front of the door side of lot r."""
    x1, z1, x2, z2 = r
    dx, dz = DOOR_OUT[rot % 4]
    if dz > 0: return (x1, z2 + 1, x2, z2 + n)
    if dz < 0: return (x1, z1 - n, x2, z1 - 1)
    if dx > 0: return (x2 + 1, z1, x2 + n, z2)
    return (x1 - n, z1, x1 - 1, z2)


def door_steps(bb, hy, x, z, w, d, y, rot, block="minecraft:cobblestone", path="minecraft:dirt_path"):
    """Stairs from a house's door (house_module: door in the middle of the front, floor at y + 1) down off its plinth
    to the ground in front, then two blocks of path. ryan 2026-11-01: doors stood on plinths with no way up."""
    dx, dz = DOOR_OUT[rot % 4]
    mw = w if rot % 2 == 0 else d
    # the door cell, worked out like place_house: module (mw // 2, md - 1) turned rot times
    if dz > 0: door = (x + (mw // 2), z + d - 1)
    elif dz < 0: door = (x + w - 1 - (mw // 2), z)
    elif dx < 0: door = (x, z + (mw // 2))
    else: door = (x + w - 1, z + d - 1 - (mw // 2))
    toward = {(0, 1): "north", (0, -1): "south", (1, 0): "west", (-1, 0): "east"}[(dx, dz)]
    k, top = 1, y + 1  # the first step is the module's own stair at plinth level, right outside the door
    while k <= 12:
        cx, cz = door[0] + dx * k, door[1] + dz * k
        g = hy(cx, cz)
        if (y + 1 if k == 1 else top) <= g:
            break
        step = top if k > 1 else y + 1
        bb.fill(cx, g - 1, cz, cx, step - 1, cz, block)
        bb.set(cx, step, cz, f"minecraft:stone_brick_stairs[facing={toward},half=bottom]")
        bb.fill(cx, step + 1, cz, cx, step + 3, cz, AIR)
        top = step - 1 if k > 1 else y
        k += 1
    for j in range(k, k + 2):
        cx, cz = door[0] + dx * j, door[1] + dz * j
        g = hy(cx, cz)
        bb.set(cx, g, cz, path)
        bb.fill(cx, g + 1, cz, cx, g + 2, cz, AIR)


def pack_houses(bb, hy, ok, area, n, seed, tracker, pal, roofs, focus=None, reserved=(), sizes=(7, 10), floors=(1, 2),
                kinds=("bedroom", "kitchen", "dining"), gap=2, max_step=4, plinth="minecraft:cobblestone", fh=5, face=None,
                timber=True):
    rng = np.random.default_rng(seed)
    x1, z1, x2, z2 = area
    cands = [(int(rng.integers(x1, x2)), int(rng.integers(z1, z2))) for _ in range(n * 40)]
    if focus:
        cands.sort(key=lambda p: (p[0] - focus[0]) ** 2 + (p[1] - focus[1]) ** 2 + rng.random() * 400)
    taken = [tuple(r) for r in reserved]
    fronts = []
    placed = []
    for (x, z) in cands:
        if len(placed) >= n:
            break
        w, d = int(rng.integers(sizes[0], sizes[1] + 1)), int(rng.integers(sizes[0], sizes[1] + 1))
        if x + w > x2 or z + d > z2:
            continue
        r = (x, z, x + w - 1, z + d - 1)
        if _hits(r, taken, gap):
            continue
        cells = [(a, b) for a in range(x, x + w) for b in range(z, z + d)]
        if not all(ok(a, b) for (a, b) in cells):
            continue
        hs = [hy(a, b) for (a, b) in cells]
        if max(hs) - min(hs) > max_step:
            continue
        y = max(hs)
        rot = face(x + w / 2, z + d / 2) if face else int(rng.integers(4))
        # ryan 2026-11-01: doors must be easy to reach, so keep a yard in front of the door (room for the steps
        # down off the plinth and a path) clear of the other houses
        fr = _front(r, rot, y - min(hs) + FRONT)
        if _hits(fr, taken, 0) or _hits(r, [fr2 for fr2 in fronts], 0):
            continue
        mw, md = (w, d) if rot % 2 == 0 else (d, w)
        k = len(placed)
        mod, top, _ = house_module(seed_of("lot", seed, k), mw, md, int(rng.choice(floors)), roofs[k % len(roofs)], tracker,
                                   list(kinds), pal=pal[k % len(pal)] if isinstance(pal, list) else pal, fh=fh, kit=True,
                                   timber=timber)
        bb.fill(x, min(hs) - 2, z, x + w - 1, y, z + d - 1, plinth)
        place_house(bb, mod, mw, md, x, y + 1, z, rot)
        door_steps(bb, hy, x, z, w, d, y, rot, plinth)
        taken.append(r)
        fronts.append(fr)
        placed.append((x, z, w, d, y, rot))
    return placed

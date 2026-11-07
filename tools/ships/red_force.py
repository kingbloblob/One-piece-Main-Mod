"""Red Force: Shanks' flagship, the Red Hair Pirates' big red three-master (enemy, tiers 4-5).

Deep red hull (red terracotta with mangrove courses) over a dark bottom, gold trim along the wale and the rail cap,
a high rounded stern castle with gold-framed windows, three mangrove masts with big white sails (the Red Hair Jolly
Roger on the mainsail), red flags, and a huge red dragon figurehead whose neck rises from the stem and arches
forward to an open, white-toothed jaw under golden horns.

Layout (+x is the bow, CZ = 0, main deck at y 7, the stern deck rises to y 8, the bow deck to y 8):
  x -1       rudder under the round stern
  x  1..11   stern castle, tier 1: the captain's cabin (royal), roof at y 11 = the quarterdeck (Ship's Wheel at x 10)
  x  1..7    tier 2: Shanks' day cabin, roof at y 15 carrying the mizzen (x 4)
  x 12..37   main deck: mainmast x 20, foremast x 31, hatch + ladder at x 16, stairs up to the quarterdeck at z 4
  x 36..39   bow: anchor to port; the dragon's neck rises from the stem (x 39) to the head at x 43..51, y 13..22
  inside:    gun deck (floor y 3): 4 cannons a side behind black ports; the hold below (bottom y -2) with treasure chests
"""
from shipkit import *  # noqa: F401,F403

CZ = 0
X0, LEN = 0, 40
X1 = X0 + LEN - 1       # 39 = the stem
BEAM = 13
KEEL, DECK = -3, 7
GUN = 3                 # floor of the gun deck (cannons stand at y 4)
HOLD = -2               # bottom of the hold: the hull's own floor (chests stand at y -2)
T1, T2 = DECK + 4, DECK + 8     # roofs of the two castle tiers (11, 15)
MIZZEN_X, MAIN_X, FORE_X = 4, 20, 31
HATCH_X = 16
CUTS = (DECK + 1,)

RED_T = TERRACOTTA["red"]
MANG = "minecraft:mangrove_planks"
MANG_STAIRS = "minecraft:mangrove_stairs"
GOLD_T = TERRACOTTA["yellow"]
GOLD = "minecraft:gold_block"
DARK = "minecraft:dark_oak_planks"
SPRUCE = "minecraft:spruce_planks"
BLACK = CONCRETE["black"]
WHITE = CONCRETE["white"]
WINDOW = GLASS["light_blue"]
RAIL = fence("dark_oak")
SAIL = WOOL["white"]
BARREL = "onepiece:sake_barrel[axis=y]"
MAST_WOOD = "mangrove"

# Flags: red, with the Red Hair skull (three scars over its left eye) and crossed sabres; 13 x 8 for the mainmast,
# 9 x 6 for the other two.
FLAG_ROWS = [
    "RRRRRRRRRRRRR",
    "GRRWWBBWWWRRG",
    "RGWWKKWKKWWGR",
    "RRWWKKWKKWWRR",
    "RGWBBWKWWWWGR",
    "GRRWKWKWKWRRG",
    "RRRRWWWWWRRRR",
    "RRRRRRRRRRRRR",
]
SMALL_FLAG_ROWS = [
    "RRRRRRRRR",
    "RRWWWWWRR",
    "RRWKWKWRR",
    "RRWWWWWRR",
    "RRRWKWRRR",
    "RRRRRRRRR",
]
FLAG_PAL = {"R": WOOL["red"], "W": WOOL["white"], "K": WOOL["black"], "G": WOOL["light_gray"], "B": WOOL["brown"]}
RED_FLAG = (FLAG_ROWS, FLAG_PAL)
SMALL_RED_FLAG = (SMALL_FLAG_ROWS, FLAG_PAL)


def compose(w, h, parts, flip=False):
    """Blank w x h bitmap rows with each (rows, top_row) part pasted in, centred across, so the kit maps the sail
    bitmap 1:1 (no stretching). flip mirrors it: the kit lays columns along +z, which reads mirrored from the bow."""
    out = [["."] * w for _ in range(h)]
    for rows, top in parts:
        rw = max(len(r) for r in rows)
        left = (w - rw) // 2
        for j, r in enumerate(rows):
            if 0 <= top + j < h:
                for i, ch in enumerate(r):
                    if ch != "." and 0 <= left + i < w:
                        out[top + j][left + i] = ch
    return ["".join(reversed(r) if flip else r) for r in out]


def main_sail(half, y0, y1):
    """The mainsail: the Red Hair Jolly Roger, reading correctly from the bow."""
    w, h = 2 * half + 1, y1 - y0 + 1
    rows = compose(w, h, [(RED_HAIR_ROWS, 0)], flip=True)
    # black print on the white sail: black skull, white eye sockets / teeth gaps, red scars, dark grey sabres
    return (rows, {"W": WOOL["black"], "K": SAIL, "R": WOOL["red"], "G": WOOL["gray"]})


class RedShip(Ship):
    """Ship whose '<id>_front.png' really looks from the bow (the kit keeps the stern-most block per pixel)."""

    def elevation(self, out, axis="z", scale=8, title=None):
        import render
        from PIL import Image, ImageDraw
        pts = {}
        for (x, y, z), st in self.blocks.items():
            if st == AIR or st.split("[")[0] in render.SKIP:
                continue
            key, depth = ((x, y), z) if axis == "z" else ((-z, y), x)
            if key not in pts or depth > pts[key][0]:
                pts[key] = (depth, st)
        if not pts:
            return
        us = [k[0] for k in pts]
        vs = [k[1] for k in pts]
        u0, u1, v0, v1 = min(us), max(us), min(vs), max(vs)
        pad = 12
        W = (u1 - u0 + 1) * scale + 2 * pad
        H = (v1 - v0 + 1) * scale + 2 * pad + (30 if title else 0)
        img = Image.new("RGB", (W, H), (206, 224, 236))
        d = ImageDraw.Draw(img)
        sea_y = pad + (v1 - 0) * scale + (30 if title else 0)
        d.rectangle([0, sea_y + scale, W, H], fill=(96, 140, 210))
        depths = [p[0] for p in pts.values()]
        dmin, dmax = min(depths), max(depths)
        for (u, v), (depth, st) in pts.items():
            cols = render.block_colors(st)
            if cols is None:
                continue
            c = cols[1]
            t = 0.75 + 0.25 * ((depth - dmin) / max(1, dmax - dmin))
            c = tuple(int(min(255, cc * t)) for cc in c)
            px = pad + (u - u0) * scale
            py = pad + (v1 - v) * scale + (30 if title else 0)
            d.rectangle([px, py, px + scale - 1, py + scale - 1], fill=c)
        if title:
            d.text((pad, 8), title, fill=(30, 40, 60))
        img.save(out)
        return out


# ---------------------------------------------------------------- helpers
def outline(s, x):
    """(deck y, z cells of the hull deck at x); (None, []) off the hull."""
    if x < X0 or x > X1:
        return None, []
    dy = s.deck_y(x)
    return dy, [z for z in range(-9, 10) if s._inside(x, dy, z)]


def tier(s, x0, x1, y0, y1, inset, floor_x1=None):
    """One storey of the stern castle on the hull's deck outline shrunk by `inset` a side: red walls from y0 (or
    the deck, where the sheer lifts it) to y1-1, hollow, a roof at y1 of spruce where it is a walkable floor (inside,
    up to floor_x1) and gold at the rim, with one block of gold overhang around. Returns {x: set(z)}."""
    cells = {}
    for x in range(x0, x1 + 1):
        _, zs = outline(s, x)
        if inset:
            zs = zs[inset:len(zs) - inset]
        cells[x] = set(zs)
    for x, zs in cells.items():
        floor = s.deck_y(x) if (s.deck_y(x) is not None and y0 <= s.deck_y(x) + 1) else y0 - 1
        for z in zs:
            edge = (z - 1 not in zs) or (z + 1 not in zs) or (z not in cells.get(x - 1, ())) or (z not in cells.get(x + 1, ()))
            for y in range(y0, y1):
                if edge:
                    s.set(x, y, z, RED_T)
                elif y > floor:
                    s.set(x, y, z, AIR)
            walk = floor_x1 is not None and x <= floor_x1
            s.set(x, y1, z, SPRUCE if (walk and not edge) else GOLD_T)
    for x in range(x0 - 1, x1 + 1):
        for z in range(-9, 10):
            if z in cells.get(x, ()):
                continue
            if any(z + dz in cells.get(x + dx, ()) for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                s.set(x, y1, z, GOLD_T)
    return cells


def gold_windows(s, cells, y, skip=()):
    """Light-blue glass in gold frames: windows along the side walls every other block and across the end walls,
    each with a gold block above and below it (the frame)."""
    xs = sorted(cells)

    def win(x, z):
        if (x, z) in skip:
            return
        s.set(x, y, z, WINDOW)
        s.set(x, y + 1, z, GOLD_T)
        s.set(x, y - 1, z, GOLD_T)
    for x in xs:
        zs = cells[x]
        lo, hi = min(zs), max(zs)
        if x == xs[0]:
            for z in range(lo + 1, hi):
                if z % 2 == 0:
                    win(x, z)
        elif x == xs[-1]:
            for z in range(lo + 1, hi):
                if z % 2 == 0:
                    win(x, z)
        elif x % 2 == 1:
            win(x, lo)
            win(x, hi)


def loose_blocks(s):
    """(blocks not connected to the keel even diagonally, non-rope blocks without any face neighbour)."""
    solid = {p for p, b in s.blocks.items() if b != AIR}
    start = min(solid, key=lambda p: (p[1], abs(p[2]), abs(p[0] - LEN // 2)))
    seen = {start}
    stack = [start]
    while stack:
        x, y, z = stack.pop()
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    n = (x + dx, y + dy, z + dz)
                    if n in solid and n not in seen:
                        seen.add(n)
                        stack.append(n)
    faces = ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))
    unsupported = [p for p in solid if "fence" not in s.blocks[p]
                   and not any((p[0] + d[0], p[1] + d[1], p[2] + d[2]) in solid for d in faces)]
    return sorted(solid - seen), sorted(unsupported)


def brace_skin(s, unsupported):
    """Hull skin blocks that only touch the ship diagonally: fill the hollow cell next to them."""
    for (x, y, z) in unsupported:
        mat = s.blocks[(x, y, z)]
        for n in ((x, y, z - (1 if z > 0 else -1)), (x, y - 1, z), (x, y + 1, z)):
            if s._inside(*n) and s.get(*n) in (None, AIR):
                s.set(n[0], n[1], n[2], mat)
                break


def one_helm(s):
    """The interior furnisher may drop a Ship's Wheel in the captain's cabin: keep only s.helm's."""
    for p, b in list(s.blocks.items()):
        if "ships_wheel" in b and p != s.helm_pos:
            s.set(p[0], p[1], p[2], "onepiece:navigators_desk[facing=east]")


def dragon(s):
    """The figurehead: a red dragon whose neck rises from the stem and arches forward to the head; golden horns
    and a gold spine ridge, an open jaw with white teeth, black eyes."""
    # neck: a tube of overlapping lumps along a curve from the stem head up and forward
    path = [(38.5, 8.5), (39.3, 10.0), (40.2, 11.5), (41.2, 12.8), (42.4, 13.9), (43.7, 14.8), (45.0, 15.4)]
    for (px, py) in path:
        s.blob(px, py, CZ, 1.6, 1.6, 1.5, RED_T, power=2.0, hollow=True)
    # gold ridge along the back of the neck
    for i, (px, py) in enumerate(path[:-1]):
        if i % 2 == 0:
            s.set(round(px) - 1, round(py) + 1, CZ, GOLD_T)
            s.set(round(px) - 1, round(py) + 2, CZ, GOLD_T)
    # the head: a boxy lump 7 wide, the snout forward
    hx, hy = 46.0, 16.5
    s.blob(hx, hy, CZ, 3.0, 2.4, 3.4, RED_T, power=2.6, hollow=True)
    s.box(48, 16, -3, 49, 17, 3, RED_T)          # upper jaw / snout, broad at the cheeks
    s.box(50, 16, -2, 50, 17, 2, RED_T)
    s.box(51, 16, -1, 51, 17, 1, RED_T)          # the tip of the snout
    s.set(51, 16, -1, TERRACOTTA["brown"])       # small nostrils low on the snout front
    s.set(51, 16, 1, TERRACOTTA["brown"])
    # the mouth: upper teeth hanging under the snout, the lower jaw swung open with teeth standing on it
    for (x, z) in ((48, -2), (48, 2), (50, -2), (50, 2), (51, -1), (51, 1)):
        s.set(x, 15, z, WHITE)
    s.box(46, 12, -2, 47, 14, 2, RED_T)          # hinge of the lower jaw
    s.box(48, 12, -2, 50, 12, 2, RED_T)          # lower jaw, swung wide open
    s.box(51, 12, -1, 51, 12, 1, RED_T)
    for (x, z) in ((49, -2), (49, 2), (51, -1), (51, 1)):
        s.set(x, 13, z, WHITE)
    for y in range(12, 16):                      # red cheeks frame the mouth, so the teeth do not melt into the sails
        for z in (-3, 3):
            s.set(48, y, z, RED_T)
    s.set(49, 15, CZ, BLACK)                     # dark gap between the upper fangs
    s.set(50, 15, CZ, BLACK)
    for x in range(47, 51):                      # black throat behind the teeth
        for z in (-1, 0, 1):
            if s.get(x, 14, z) in (None, AIR):
                s.set(x, 14, z, BLACK)
    s.set(48, 13, CZ, WOOL["red"])               # tongue
    s.set(49, 13, CZ, WOOL["red"])
    # eyes high on the sides of the head, above the snout so they show from the bow and from the side
    for z in (-3, 3):
        for x in (47, 48):
            s.set(x, 18, z, BLACK)
            s.set(x, 19, z, GOLD_T)              # gold brow ridge
    # golden horns sweeping back, up and outward from the top of the head
    for sgn in (-1, 1):
        horn = [(45, 19, 1), (44, 19, 1), (44, 20, 1), (44, 20, 2), (43, 20, 2), (43, 21, 2), (43, 21, 3), (42, 21, 3), (42, 22, 3)]
        for i, (x, y, z) in enumerate(horn):
            s.set(x, y, z * sgn, GOLD if i >= len(horn) - 2 else GOLD_T)
    # crest spikes down the back of the head onto the neck
    s.set(44, 19, CZ, GOLD_T)
    s.set(43, 19, CZ, GOLD_T)
    s.set(43, 18, CZ, GOLD_T)


# ---------------------------------------------------------------- the ship
def build():
    s = RedShip("red_force", "Red Force", faction="pirate", tiers=[4, 5], crew="Red Hair Pirates")

    # ---- hull: deep red with mangrove courses, dark under water, gold wale; sharp bow, round high stern
    def paint(x, y, z, kind):
        if y < 1:
            return DARK
        if kind in ("side", "bow", "stern") and y in (2, 5):
            return MANG
        return None

    s.hull(x0=X0, length=LEN, cz=CZ, beam=BEAM, keel_y=KEEL, deck_y=DECK, side=RED_T, bottom=DARK, deck=SPRUCE,
           wale=GOLD_T, bow_len=12, stern_len=6, bow="sharp", stern="round", sheer_bow=1, sheer_stern=1,
           keel_rise_bow=3, keel_rise_stern=2, fullness=0.6, flat=0.35, bulwark=1, bulwark_mat=RED_T, rail=GOLD_T,
           paint=paint, inner_decks=[(GUN, MANG)])
    inside = s._inside
    # gold blocks set into the wale every few blocks
    for (x, y, z), b in list(s.blocks.items()):
        if b == GOLD_T and x in s._hull and y == s.deck_y(x) - 1 and x % 5 == 2:
            s.set(x, y, z, GOLD)

    def zedge(x):
        return s.halfwidth(x, s.deck_y(x))

    # rudder under the round stern
    for y in range(-2, DECK):
        s.set(X0 - 1, y, CZ, DARK if y <= 0 else MANG)
    s.set(X0, DECK + 1, CZ, AIR)                 # no bulwark nub on the stern tip: a lantern instead
    s.set(X0, DECK + 2, CZ, AIR)
    s.lamp(X0, DECK + 1, CZ)

    # ---- the gun deck: 4 cannons a side behind black ports in the red hull
    gun_xs = (12, 17, 22, 27)
    s.broadside(gun_xs, GUN + 1, CZ, lambda x: s.halfwidth(x, GUN + 1), gunport=BLACK)
    # hatch and ladder from the main deck down through the gun deck to the hold (post at x+1)
    s.open_hatch(HATCH_X, DECK, -2, ladder_facing="west", down_to=HOLD)
    for y in range(HOLD, DECK):
        if s.get(HATCH_X + 1, y, -2) in (None, AIR):
            s.set(HATCH_X + 1, y, -2, MANG)
    # lanterns under the beams
    for x in (13, 21, 29):
        s.lamp(x, GUN + 3, CZ, hanging=True)
        s.lamp(x, GUN - 1, CZ, hanging=True)
    # the hold: Shanks' treasure and sake
    s.chest(22, HOLD, -1, "treasure", facing="east")
    s.chest(22, HOLD, 1, "treasure", facing="east")
    s.chest(27, HOLD, CZ, "hard", facing="west")
    s.chest(10, HOLD, CZ, "treasure", facing="east")
    for (x, z) in ((13, -1), (13, 1), (14, 0), (25, 1), (26, -1), (31, 0), (32, -1), (32, 1)):
        s.set(x, HOLD, z, BARREL)
    s.set(18, GUN + 1, 1, BARREL)
    s.set(19, GUN + 1, 2, BARREL)
    s.chest(33, GUN + 1, CZ, "pirate", facing="west")
    s.set(30, GUN + 1, -2, "onepiece:rope_coil[facing=north]")

    # ---- weather deck gear
    for x in (13, 24, 33):
        for side in (-1, 1):
            s.lamp(x, DECK + 3, side * zedge(x))
    s.set(14, DECK + 1, -4, "onepiece:rope_coil[facing=north]")
    s.set(27, DECK + 1, 4, BARREL)
    s.set(27, DECK + 1, 3, BARREL)
    s.set(28, DECK + 1, 4, BARREL)
    s.set(35, DECK + 1, 2, "onepiece:rope_coil[facing=east]")
    s.anchor(36, s.deck_y(36) + 1, -(zedge(36) - 1), "north")
    s.chest(13, DECK + 1, -4, "pirate", facing="south")

    # ---- stern castle: two red tiers with gold-rimmed roofs and gold-framed windows
    c1 = tier(s, 1, 11, DECK + 1, T1, 0, floor_x1=11)
    c2 = tier(s, 1, 7, T1 + 1, T2, 1, floor_x1=7)
    gold_windows(s, c1, DECK + 2, skip=((11, 0),))
    gold_windows(s, c2, T1 + 2, skip=((7, 0),))
    # doors: main deck -> captain's cabin, quarterdeck -> day cabin
    s.set(11, DECK + 1, CZ, door("minecraft:mangrove_door", "east", "lower"))
    s.set(11, DECK + 2, CZ, door("minecraft:mangrove_door", "east", "upper"))
    s.set(7, T1 + 1, CZ, door("minecraft:mangrove_door", "east", "lower"))
    s.set(7, T1 + 2, CZ, door("minecraft:mangrove_door", "east", "upper"))
    # ladder from the cabin up to the day cabin and the top roof, along the stern wall
    for y in range(DECK + 2, T2 + 1):
        s.set(2, y, 1, ladder("east"))
    # the quarterdeck (tier-1 roof, x 8..11): rails, the Ship's Wheel, stairs down to the main deck to starboard
    for x in range(8, 12):
        for side in (-1, 1):
            s.set(x, T1 + 1, side * zedge(x), RAIL)
    for z in range(-zedge(11) + 1, zedge(11)):
        if z != 4:
            s.set(11, T1 + 1, z, RAIL)
    s.helm(10, T1 + 1, CZ)
    s.set(9, T1 + 1, CZ, AIR)
    s.stairs_run(15, DECK + 1, 4, 4, MANG_STAIRS, "west")
    for i, x in enumerate((15, 14, 13, 12)):
        for y in range(DECK + 1, DECK + 1 + i):
            s.set(x, y, 4, RED_T)
    s.lamp(11, T1 + 2, -zedge(11))
    s.lamp(11, T1 + 2, zedge(11))
    s.lamp(11, DECK + 3, -3)
    s.lamp(11, DECK + 3, 3)
    # stern lanterns on the tier-2 roof corners and a gold finial at the back
    for z in (-2, 2):
        s.lamp(2, T2 + 1, z)
    s.set(1, T2 + 1, CZ, GOLD)
    # the captain's cabin (royal) and Shanks' day cabin above it
    I.furnish(s, 4, DECK + 1, -5, 10, 5, 3, "captain", "royal", seed=7)
    s.chest(5, DECK + 1, -4, "treasure", facing="east")
    I.furnish(s, 2, T1 + 1, -3, 6, 3, 3, "study", "royal", seed=3)
    one_helm(s)
    for p, b in list(s.blocks.items()):                        # rugs cost blocks the budget needs elsewhere
        if b.endswith("_carpet"):
            s.set(p[0], p[1], p[2], AIR)
    for y in range(DECK + 2, T2 + 1):                          # the furnishers must not block the ladder
        s.set(2, y, 1, ladder("east"))
    s.set(2, T2 + 1, 1, AIR)
    s.set(2, T1 + 1, 1, AIR)

    # ---- masts (mangrove), yards, sails, rigging, red flags
    def mast(x, y0, top):
        for y in range(y0, top + 1):
            s.set(x, y, CZ, log(MAST_WOOD))
        return top
    FORE_TOP, MAIN_TOP, MIZZEN_TOP = DECK + 26, DECK + 31, T2 + 15
    # foremast: plain white sail + topsail
    mast(FORE_X, GUN + 1, FORE_TOP)
    s.square_sail(FORE_X + 1, CZ, DECK + 4, DECK + 9, 7, SAIL, belly=1, yard=MAST_WOOD)
    s.square_sail(FORE_X + 1, CZ, DECK + 12, DECK + 16, 4, SAIL, belly=1, yard=MAST_WOOD)
    s.flag(FORE_X, FORE_TOP + 1, CZ, SMALL_RED_FLAG)
    # mainmast: the Jolly Roger mainsail + topsail, crow's nest
    mast(MAIN_X, GUN + 1, MAIN_TOP)
    s.square_sail(MAIN_X + 1, CZ, DECK + 4, DECK + 16, 11, SAIL, belly=1, yard=MAST_WOOD,
                  bitmap=main_sail(11, DECK + 4, DECK + 16))
    s.square_sail(MAIN_X + 1, CZ, DECK + 19, DECK + 24, 5, SAIL, belly=1, yard=MAST_WOOD)
    s.crows_nest(MAIN_X, DECK + 27, CZ, 1.5, MAST_WOOD)
    s.flag(MAIN_X, MAIN_TOP + 1, CZ, RED_FLAG)
    # mizzen on the day-cabin roof: one sail
    mast(MIZZEN_X, T2 + 1, MIZZEN_TOP)
    s.square_sail(MIZZEN_X + 1, CZ, T2 + 3, T2 + 10, 6, SAIL, belly=1, yard=MAST_WOOD)
    s.flag(MIZZEN_X, MIZZEN_TOP + 1, CZ, SMALL_RED_FLAG)
    # shrouds a block abaft each mast down to the rails; stays between the mast heads
    for (mx, my, ry, n) in ((FORE_X, DECK + 13, DECK + 2, 1), (MAIN_X, DECK + 18, DECK + 2, 2), (MIZZEN_X, T2 + 12, T2 + 1, 1)):
        for k in range(n):
            dx = -1 - 2 * k
            for side in (-1, 1):
                zz = side * (zedge(mx + dx) if mx + dx >= 12 else (max(c2[mx + dx]) if mx + dx in c2 else 4))
                s.rope((mx - 1, my, CZ), (mx + dx, ry, zz))
    s.rope((MAIN_X, MAIN_TOP, CZ), (FORE_X, FORE_TOP, CZ))
    s.rope((MIZZEN_X, MIZZEN_TOP, CZ), (MAIN_X, MAIN_TOP, CZ))
    s.rope((FORE_X, FORE_TOP - 2, CZ), (X1 + 1, DECK + 4, CZ))      # forestay down to the stem
    s.lamp(MAIN_X + 1, DECK + 2, CZ)
    s.lamp(FORE_X + 1, DECK + 2, CZ)

    # ---- the figurehead
    dragon(s)

    loose, unsupported = loose_blocks(s)
    if unsupported:
        brace_skin(s, unsupported)
        loose, unsupported = loose_blocks(s)
    if loose:
        print(f"  !! {len(loose)} loose blocks, e.g. {loose[:16]}")
    if unsupported:
        print(f"  !! {len(unsupported)} blocks without a face neighbour, e.g. {unsupported[:16]}")
    return s

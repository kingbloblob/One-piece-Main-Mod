"""Victoria Punk: Eustass Kid's ship, the Kid Pirates' dark, spiky, iron-plated raider (enemy, tiers 3-5).

Dark oak hull with blackstone courses and a red wale, armoured with iron plates, iron-bar spikes along the rail, a tall
two-tier stern castle, two tall dark masts with dark red sails that carry Kid's mark (and black KID flags), a gun deck
with four cannons a side, a forge below, scrap metal on deck, and a giant bone-white skull figurehead with glowing red
eyes, a spiky metal crest like Kid's hair and its jaws open over the stem.

Layout (+x is the bow, CZ = 0, main deck at y 6, stern deck y 7, bow deck y 8):
  x -1       rudder under the flat transom
  x  1..10   stern castle tier 1: the captain's cabin (pirate), roof y 10 = the quarterdeck (Ship's Wheel at x 9)
  x  1..6    tier 2: Kid's den, roof y 14 with spikes and lanterns
  x 11..30   main deck: mainmast x 16, foremast x 26, hatch + ladder at x 21, stairs up to the quarterdeck at z 4
  x 29..33   bow: anchor to port; the skull sits on the stem (x 33), head x 34..41, jaw hinged at the cheeks and
             dropped to y 5 (mouth open y 6..8 over the blackstone stem), crest fanning out to z +-6, up to y 21
  masts      21 x 14 dark red courses with Kid's mark in a red field, plain topsails, small black KID flags (11x9, 9x7)
  inside:    gun deck (floor y 2): 4 cannons a side behind black ports, the forge forward; the hold below with "hard" loot
"""
from shipkit import *  # noqa: F401,F403

CZ = 0
X0, LEN = 0, 34
X1 = X0 + LEN - 1       # 33 = the stem
BEAM = 13
KEEL, DECK = -3, 6
GUN = 2                 # floor of the gun deck (cannons stand at y 3)
HOLD = -2               # floor of the hold (the hull's own bottom)
T1, T2 = DECK + 4, DECK + 8     # roofs of the two castle tiers (10, 14)
MAIN_X, FORE_X = 16, 26
HATCH_X = 21
CUTS = (DECK + 1,)

DARK = "minecraft:dark_oak_planks"
DARK_STAIRS = "minecraft:dark_oak_stairs"
BLACKSTONE = "minecraft:blackstone"
PBLACK = "minecraft:polished_blackstone"
PBRICK = "minecraft:polished_blackstone_bricks"
IRON = "minecraft:iron_block"
BARS = "minecraft:iron_bars"
RED_T = TERRACOTTA["red"]
SPRUCE = "minecraft:spruce_planks"
BLACK = CONCRETE["black"]
WHITE = CONCRETE["white"]
BONE = "minecraft:bone_block[axis=y]"
REDSTONE = "minecraft:redstone_block"
WINDOW = pane("red")
SAIL = WOOL["red"]
BARREL = "minecraft:barrel[facing=up,open=false]"
ANVIL = "minecraft:anvil[facing=north]"
CHAIN = "minecraft:chain[axis=y]"
MAST_WOOD = "dark_oak"

GUN_XS = (8, 13, 18, 23)  # cannons every 5 x, each behind a riveted iron plate
# Iron plates riveted on the hull sides: (x, y, w, h), the same on both sides. A regular belt of equal 3x2 plates at
# y 2-3 between the blackstone courses (y 1 and 4), every 5 x with dark oak between (one round each gun port), and a
# bigger plate on each bow flare.
PLATES = tuple((x, 2, 3, 2) for x in (3, 7, 12, 17, 22)) + ((27, 2, 4, 3),)

# Kid's mark scaled down for the flags (9 x 7): red hair spikes, a grey goggles band with crossbone tips, a white
# skull with black eye holes and a nose hole, teeth, the crossbones' lower ends.
KID_SMALL = [
    "R.R.R.R.R",
    ".RRRRRRR.",
    "W.GGGGG.W",
    ".WWKWKWW.",
    "..WWKWW..",
    ".W.WWW.W.",
    "W..W.W..W",
]


def compose(w, h, parts, fill=".", flip=False):
    """Blank w x h bitmap rows (filled with `fill`) with each (rows, top_row) part pasted in, centred across, so the
    kit maps the sail bitmap 1:1. flip mirrors it: the kit lays columns along +z, which reads mirrored from the bow."""
    out = [[fill] * w for _ in range(h)]
    for rows, top in parts:
        rw = max(len(r) for r in rows)
        left = (w - rw) // 2
        for j, r in enumerate(rows):
            if 0 <= top + j < h:
                for i, ch in enumerate(r):
                    if ch != "." and 0 <= left + i < w:
                        out[top + j][left + i] = ch
    return ["".join(reversed(r) if flip else r) for r in out]


def hair_outline(rows):
    """Kid's red hair would vanish on a red sail and, filled black, merges with the goggles into one black slab: keep
    only its outline. Hair cells on the top row (the spikes) and hair cells touching the empty field become 'O' (black),
    the hair's interior is left as sail red."""
    h, w = len(rows), max(len(r) for r in rows)
    grid = [list(r.ljust(w, ".")) for r in rows]

    def empty(i, j):
        return not (0 <= j < h and 0 <= i < w) or grid[j][i] == "."
    out = []
    for j in range(h):
        row = ""
        for i in range(w):
            ch = grid[j][i]
            if ch == "R":
                edge = j == 0 or any(empty(i + di, j + dj) for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)))
                ch = "O" if edge else "."
            row += ch
        out.append(row)
    return out


def kid_sail(half, y0, y1):
    """A dark red sail with Kid's mark (black goggles, white skull and crossbones, the hair as a black spiky outline)
    centred with a red field around it, reading correctly from the bow."""
    w, h = 2 * half + 1, y1 - y0 + 1
    mark = hair_outline(KID_ROWS)
    rows = compose(w, h, [(mark, (h - len(mark)) // 2)], flip=True)
    pal = {"W": WOOL["white"], "K": WOOL["black"], "O": WOOL["black"]}
    return (rows, pal)


def kid_flag(w, h):
    """Black flag with the small Kid's mark centred."""
    rows = compose(w, h, [(KID_SMALL, (h - len(KID_SMALL)) // 2)], fill="B")
    pal = {"W": WOOL["white"], "K": WOOL["black"], "R": WOOL["red"], "G": WOOL["light_gray"], "B": WOOL["black"]}
    return (rows, pal)


class PunkShip(Ship):
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
    """One storey of the stern castle on the hull's deck outline shrunk by `inset` a side: dark walls from y0 (or the
    deck, where the sheer lifts it) to y1-1, hollow, a roof at y1 of spruce where it is a walkable floor (inside, up to
    floor_x1) and polished blackstone at the rim, with one block of blackstone overhang around. Returns {x: set(z)}."""
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
                    s.set(x, y, z, IRON if (x + z + y) % 7 == 0 else DARK)
                elif y > floor:
                    s.set(x, y, z, AIR)
            walk = floor_x1 is not None and x <= floor_x1
            s.set(x, y1, z, SPRUCE if (walk and not edge) else PBLACK)
    for x in range(x0 - 1, x1 + 1):
        for z in range(-9, 10):
            if z in cells.get(x, ()):
                continue
            if any(z + dz in cells.get(x + dx, ()) for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                s.set(x, y1, z, PBLACK)
    return cells


def windows(s, cells, y, skip=()):
    """Red glass panes along the side walls every other block and across the end walls."""
    xs = sorted(cells)

    def win(x, z):
        if (x, z) in skip:
            return
        s.set(x, y, z, WINDOW)
    for x in xs:
        zs = cells[x]
        lo, hi = min(zs), max(zs)
        if x in (xs[0], xs[-1]):
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
    unsupported = [p for p in solid if "fence" not in s.blocks[p] and "chain" not in s.blocks[p]
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


def step_line(s, p0, p1, mat, first=None):
    """A line of blocks from p0 to p1 whose blocks all touch face to face (a diagonal step gets a filler block, the
    vertical move first). first = material of the root block. Returns the list of points."""
    (x0, y0, z0), (x1, y1, z1) = p0, p1
    n = max(abs(x1 - x0), abs(y1 - y0), abs(z1 - z0))
    pts = []
    prev = None
    for i in range(n + 1):
        t = i / max(1, n)
        p = (round(x0 + (x1 - x0) * t), round(y0 + (y1 - y0) * t), round(z0 + (z1 - z0) * t))
        if prev is not None:
            cur = list(prev)
            for ax in (1, 0, 2):                     # y first, then x, then z: one axis at a time
                if cur[ax] != p[ax]:
                    cur[ax] = p[ax]
                    if tuple(cur) != p:
                        pts.append(tuple(cur))
        pts.append(p)
        prev = p
    for k, q in enumerate(pts):
        s.set(q[0], q[1], q[2], first if (k == 0 and first) else mat)
    return pts


def skull(s):
    """The figurehead: a giant bone-white skull sitting on the stem, glowing red eyes, a black nose hole, upper teeth
    under the brow, the lower jaw swung open around the stem head, and a crest of blackstone and iron-bar spikes
    swept back over the top like Kid's hair."""
    # the stem head: a blackstone neck from the hull's bow up into the skull
    s.box(33, 9, -1, 35, 10, 1, BLACKSTONE)
    s.box(34, 8, -1, 34, 8, 1, BLACKSTONE)
    # cranium: a hollow rounded lump, x 34..41, y 9..15
    s.blob(37.5, 12.0, CZ, 3.5, 3.4, 3.2, BONE, power=2.4, hollow=True)
    s.set(35, 11, CZ, BONE)                      # solid core behind the back tip so it has a face neighbour
    s.set(35, 12, CZ, BONE)
    # brow / upper jaw: a solid band under the eyes with the teeth hanging below it
    s.box(38, 10, -2, 40, 10, 2, BONE)
    s.box(37, 10, -1, 37, 10, 1, BONE)
    for (x, z) in ((40, -2), (40, 0), (40, 2), (39, -2), (39, 2), (38, -2), (38, 2)):
        s.set(x, 9, z, WHITE)
    # eyes: 2 x 2 glowing red in black sockets on the face, a black nose hole between them
    for z in (-2, -1, 1, 2):
        s.set(40, 12, z, REDSTONE)
        s.set(40, 13, z, REDSTONE)
    s.set(41, 12, CZ, BONE)
    s.set(41, 13, CZ, BONE)
    s.set(40, 11, CZ, BLACK)
    for z in (-1, 1):                                    # angry black brows slanting down to the nose
        s.set(40, 14, z, BLACK)
        s.set(39, 14, 2 * z, BLACK)
    # the lower jaw: hinged at the cheeks (x 33..34, y 8) and swung wide open, its arms dropping forward along both
    # sides of the stem to a bar at y 5 with the lower teeth standing on it, so the mouth gapes y 6..8 over the stem
    for z in (-2, 2):
        s.set(33, 8, z, BONE)
        step_line(s, (34, 8, z), (39, 5, z), BONE)
    s.box(39, 5, -1, 40, 5, 1, BONE)
    s.set(40, 5, -2, BONE)
    s.set(40, 5, 2, BONE)
    for (x, z) in ((40, -1), (40, 1), (40, -2), (40, 2), (39, -2), (39, 2)):
        s.set(x, 6, z, WHITE)
    # the blackstone stem / cutwater runs forward and up through the open mouth
    s.box(34, 5, CZ, 36, 8, CZ, BLACKSTONE)
    s.set(37, 5, CZ, BLACKSTONE)
    s.set(38, 5, CZ, BLACKSTONE)
    # crest: Kid's hair, 7 long spikes fanning up, out and back from the cranium top; iron roots, polished
    # blackstone shafts, iron-bar tips
    spikes = [((38, 15, 0), (36, 20, 0)),
              ((39, 15, -1), (39, 19, -3)), ((39, 15, 1), (39, 19, 3)),
              ((37, 15, -2), (35, 20, -5)), ((37, 15, 2), (35, 20, 5)),
              ((35, 14, -2), (32, 18, -6)), ((35, 14, 2), (32, 18, 6))]
    for a, b in spikes:
        pts = step_line(s, a, b, PBLACK, first=IRON)
        x, y, z = pts[-1]
        s.set(x, y + 1, z, BARS)
    # a few iron rivets on the cheeks
    for z in (-3, 3):
        s.set(38, 12, z, IRON)
        s.set(36, 12, z, IRON)


# ---------------------------------------------------------------- the ship
def build():
    s = PunkShip("victoria_punk", "Victoria Punk", faction="pirate", tiers=[3, 4, 5], crew="Kid Pirates")

    # ---- hull: dark oak with blackstone courses, iron plates, a red wale; dark bottom; sharp bow, flat tall stern
    def plated(x, y):
        return any(px <= x < px + w and py <= y < py + h for (px, py, w, h) in PLATES)

    def paint(x, y, z, kind):
        if kind == "bottom" or y < 1:
            return BLACKSTONE
        if kind == "stern":
            return PBRICK if y <= 4 else DARK
        if kind in ("side", "bow"):
            if plated(x, y):
                return IRON
            if y in (1, 4):
                return BLACKSTONE
        if kind == "bulwark" and x % 10 == 2:
            return IRON
        return None

    s.hull(x0=X0, length=LEN, cz=CZ, beam=BEAM, keel_y=KEEL, deck_y=DECK, side=DARK, bottom=BLACKSTONE, deck=SPRUCE,
           wale=RED_T, bow_len=11, stern_len=5, bow="sharp", stern="transom", sheer_bow=2, sheer_stern=1,
           keel_rise_bow=3, keel_rise_stern=2, fullness=0.6, flat=0.35, bulwark=1, bulwark_mat=DARK, rail=BARS,
           paint=paint, inner_decks=[(GUN, DARK)])

    def zedge(x):
        return s.halfwidth(x, s.deck_y(x))

    # rudder under the transom
    for y in range(-2, DECK + 1):
        s.set(X0 - 1, y, CZ, BLACKSTONE if y <= 0 else DARK)
    s.set(X0 - 1, 3, CZ, IRON)

    # ---- the gun deck: 4 cannons a side behind black ports in the hull
    s.broadside(GUN_XS, GUN + 1, CZ, lambda x: s.halfwidth(x, GUN + 1), gunport=BLACK)
    # hatch and ladder from the main deck down through the gun deck to the hold (post at x+1)
    s.open_hatch(HATCH_X, DECK, -2, ladder_facing="west", down_to=HOLD)
    for y in range(HOLD, DECK):
        if s.get(HATCH_X + 1, y, -2) in (None, AIR):
            s.set(HATCH_X + 1, y, -2, DARK)
    for x in (10, 17, 23):
        s.lamp(x, GUN + 3, CZ, hanging=True)
        s.lamp(x, GUN - 1, CZ, hanging=True)
    # the hold: Kid's loot and barrels
    s.chest(17, HOLD, -1, "hard", facing="east")
    s.chest(17, HOLD, 1, "hard", facing="east")
    s.chest(9, HOLD, CZ, "treasure", facing="east")
    s.chest(26, HOLD, CZ, "hard", facing="west")
    for (x, z) in ((11, -1), (11, 1), (12, 0), (22, 1), (23, -1), (23, 1)):
        s.set(x, HOLD, z, BARREL)
    # the forge: blast furnaces, an anvil and a smithing table on the gun deck forward, chains from the beams
    s.set(29, GUN + 1, CZ, "minecraft:blast_furnace[facing=west,lit=true]")
    s.set(29, GUN + 1, -1, "minecraft:blast_furnace[facing=west,lit=true]")
    s.set(29, GUN + 1, 1, "minecraft:blast_furnace[facing=west,lit=false]")
    s.set(29, GUN + 2, -1, PBLACK)
    s.set(29, GUN + 2, CZ, PBLACK)
    s.set(29, GUN + 2, 1, PBLACK)
    s.set(27, GUN + 1, -2, ANVIL)
    s.set(27, GUN + 1, 2, "minecraft:smithing_table")
    s.set(26, GUN + 1, 2, "minecraft:grindstone[face=floor,facing=west]")
    s.set(25, GUN + 1, 3, "minecraft:cauldron")
    for z in (-2, 2):
        s.set(28, GUN + 3, z, CHAIN)
        s.set(28, GUN + 2, z, CHAIN)
    s.chest(28, GUN + 1, 3, "hard", facing="west")
    s.set(26, GUN + 1, -3, BARREL)
    s.set(16, GUN + 1, 3, BARREL)
    s.set(15, GUN + 1, 3, BARREL)
    s.set(10, GUN + 1, -3, "onepiece:rope_coil[facing=north]")

    # ---- weather deck gear: lanterns on the spiked rail, scrap metal (anvils, chains, iron), rope coils, the anchor
    for x in (12, 21, 29):
        for side in (-1, 1):
            s.lamp(x, DECK + 3, side * zedge(x))
    s.set(12, DECK + 1, -4, ANVIL)
    s.set(13, DECK + 1, -4, IRON)
    s.set(13, DECK + 2, -4, "minecraft:chipped_anvil[facing=east]")
    s.set(12, DECK + 1, -3, "minecraft:cauldron")
    s.set(14, DECK + 1, -4, "minecraft:chain[axis=x]")          # a heap of chain beside the anvil
    s.set(15, DECK + 1, -4, "minecraft:chain[axis=x]")
    s.set(23, DECK + 1, 4, ANVIL)
    s.set(24, DECK + 1, 4, IRON)
    s.set(24, DECK + 1, 3, "minecraft:grindstone[face=floor,facing=north]")
    s.set(25, DECK + 1, 4, "minecraft:damaged_anvil[facing=east]")
    s.set(19, DECK + 1, 4, BARREL)
    s.set(19, DECK + 1, 3, BARREL)
    s.set(14, DECK + 1, 3, "onepiece:rope_coil[facing=north]")
    s.set(28, DECK + 1, -2, "onepiece:rope_coil[facing=east]")
    s.anchor(30, s.deck_y(30) + 1, -(zedge(30) - 1), "north")
    s.chest(12, DECK + 1, 4, "pirate", facing="north")

    # ---- stern castle: two dark tiers with iron patches, blackstone roofs rimmed with spikes, red windows
    c1 = tier(s, 1, 10, DECK + 1, T1, 0, floor_x1=10)
    c2 = tier(s, 1, 6, T1 + 1, T2, 1, floor_x1=6)
    windows(s, c1, DECK + 2, skip=((10, 0),))
    windows(s, c2, T1 + 2, skip=((6, 0),))
    # doors: main deck -> captain's cabin, quarterdeck -> the den
    s.set(10, DECK + 1, CZ, door("minecraft:dark_oak_door", "east", "lower"))
    s.set(10, DECK + 2, CZ, door("minecraft:dark_oak_door", "east", "upper"))
    s.set(6, T1 + 1, CZ, door("minecraft:dark_oak_door", "east", "lower"))
    s.set(6, T1 + 2, CZ, door("minecraft:dark_oak_door", "east", "upper"))
    # ladder from the cabin up to the den and the top roof, along the stern wall
    for y in range(DECK + 2, T2 + 1):
        s.set(2, y, 1, ladder("east"))
    # the quarterdeck (tier-1 roof, x 7..10): spiked rails, the Ship's Wheel, stairs down to the main deck at z 4
    for x in range(7, 11):
        for side in (-1, 1):
            s.set(x, T1 + 1, side * zedge(x), BARS)
    for z in range(-zedge(10) + 1, zedge(10)):
        if z != 4:
            s.set(10, T1 + 1, z, BARS)
    s.helm(9, T1 + 1, CZ)
    s.set(8, T1 + 1, CZ, AIR)
    s.stairs_run(14, DECK + 1, 4, 4, DARK_STAIRS, "west")
    for i, x in enumerate((14, 13, 12, 11)):
        for y in range(DECK + 1, DECK + 1 + i):
            s.set(x, y, 4, DARK)
    s.lamp(10, T1 + 2, -zedge(10))
    s.lamp(10, T1 + 2, zedge(10))
    s.lamp(10, DECK + 3, -3)
    s.lamp(10, DECK + 3, 3)
    # tier-2 roof: a ring of iron-bar spikes, lanterns at the back corners, a tall spike at the stern
    for x in range(1, 7):
        _, zs = outline(s, x)
        zs = zs[1:len(zs) - 1]
        for z in (min(zs), max(zs)):
            if (x + z) % 2 == 0:
                s.set(x, T2 + 1, z, BARS)
    for z in (-2, 2):
        s.lamp(1, T2 + 1, z)
    s.set(1, T2 + 1, CZ, PBLACK)
    s.set(1, T2 + 2, CZ, BARS)
    # the captain's cabin (pirate) and Kid's den above it
    I.furnish(s, 3, DECK + 1, -4, 9, 4, 3, "captain", "pirate", seed=11)
    s.chest(4, DECK + 1, -3, "hard", facing="east")
    I.furnish(s, 2, T1 + 1, -3, 5, 3, 3, "workshop", "pirate", seed=5)
    one_helm(s)
    for p, b in list(s.blocks.items()):                        # rugs cost blocks the budget needs elsewhere
        if b.endswith("_carpet"):
            s.set(p[0], p[1], p[2], AIR)
    for y in range(DECK + 2, T2 + 1):                          # the furnishers must not block the ladder
        s.set(2, y, 1, ladder("east"))
    s.set(2, T2 + 1, 1, AIR)
    s.set(2, T1 + 1, 1, AIR)
    s.set(2, T1, 1, AIR)
    s.set(2, DECK + 1, 1, AIR)

    # ---- masts (dark oak), yards, dark red sails with Kid's mark, black KID flags, rigging
    def mast(x, y0, top):
        for y in range(y0, top + 1):
            s.set(x, y, CZ, log(MAST_WOOD))
        return top
    MAIN_TOP, FORE_TOP = DECK + 31, DECK + 27
    C0, C1, CH = DECK + 3, DECK + 16, 10          # the courses: 21 x 14 with a red field around the 16 x 11 mark
    # mainmast: the big KID course + a plain topsail, crow's nest, the black flag
    mast(MAIN_X, GUN + 1, MAIN_TOP)
    s.square_sail(MAIN_X + 1, CZ, C0, C1, CH, SAIL, belly=1, yard=MAST_WOOD, bitmap=kid_sail(CH, C0, C1))
    s.square_sail(MAIN_X + 1, CZ, C1 + 3, C1 + 8, 5, SAIL, belly=1, yard=MAST_WOOD)
    s.crows_nest(MAIN_X, C1 + 11, CZ, 1.5, MAST_WOOD)
    s.flag(MAIN_X, MAIN_TOP + 1, CZ, kid_flag(11, 9))
    # foremast: a KID course + topsail, a smaller black flag
    mast(FORE_X, GUN + 1, FORE_TOP)
    s.square_sail(FORE_X + 1, CZ, C0, C1, CH, SAIL, belly=1, yard=MAST_WOOD, bitmap=kid_sail(CH, C0, C1))
    s.square_sail(FORE_X + 1, CZ, C1 + 3, C1 + 7, 4, SAIL, belly=1, yard=MAST_WOOD)
    s.flag(FORE_X, FORE_TOP + 1, CZ, kid_flag(9, 7))
    # lanterns hanging under the main yard ends
    for z in (-CH - 1, CH + 1):
        s.lamp(MAIN_X + 1, C1, z, hanging=True)
    # shrouds a block abaft each mast down to the rails; stays between the mast heads and down to the skull
    for (mx, my, ry, n) in ((MAIN_X, C1 + 1, DECK + 2, 2), (FORE_X, C1 + 1, DECK + 2, 1)):
        for k in range(n):
            dx = -1 - 2 * k
            for side in (-1, 1):
                s.rope((mx - 1, my, CZ), (mx + dx, ry, side * zedge(mx + dx)))
    s.rope((MAIN_X, MAIN_TOP, CZ), (FORE_X, FORE_TOP, CZ))
    s.rope((FORE_X, FORE_TOP, CZ), (35, 20, CZ))                   # forestay down to the skull's crest
    s.rope((MAIN_X, MAIN_TOP - 3, CZ), (3, T2 + 1, CZ))            # backstay to the stern roof
    s.lamp(MAIN_X + 1, DECK + 2, CZ)
    s.lamp(FORE_X + 1, DECK + 2, CZ)

    # ---- the figurehead
    skull(s)

    loose, unsupported = loose_blocks(s)
    if unsupported:
        brace_skin(s, unsupported)
        loose, unsupported = loose_blocks(s)
    if loose:
        print(f"  !! {len(loose)} loose blocks, e.g. {loose[:16]}")
    if unsupported:
        print(f"  !! {len(unsupported)} blocks without a face neighbour, e.g. {unsupported[:16]}")
    return s

"""Polar Tang: Trafalgar Law's yellow submarine (the Heart Pirates), surfaced.

Layout (+x is the bow, CZ = 0, body x 0..35, deck at y 7):
  body      a rounded cigar built from a superellipse section (BODY_* below): 9 wide, keel y -2, flat spruce deck
            on top at y 7 (x 2..31) with a rail; yellow above the water, lime below, grey riveted bands every 8.
  x -2..-1  stern fins (rudder + dive planes) and the propeller ring.
  x 14..18  the conning tower (yellow, 5 x 5, y 8..12) with portholes, a door aft, the roof hatch and ladder,
            the Ship's Wheel, the periscope and the short mast with the black smiley sail and the flag.
  x 33..35  the rounded nose with the two black torpedo tubes.
  inside    floor y 1, headroom y 2..6: crew room aft (x 2..12), control room under the tower (x 14..18),
            the sick bay forward (x 20..30) with the "medicine" chests.
"""
import math
from shipkit import *  # noqa: F401,F403

CUTS = (8,)       # one cut just above the deck: shows the deck layout and the tower base

CZ = 0
X0, X1 = 0, 35                    # body from the stern cap to the nose
BODY_CY, BODY_RY, BODY_RZ, BODY_P = 3.0, 5.0, 4.8, 2.2   # section centre height, half height, half width, exponent
DECK = 7                          # the flat deck on top of the body
FLOOR = 1                         # inside floor
BANDS = (8, 16, 24, 32)           # grey riveted rings
TOWER_X0, TOWER_X1 = 14, 18       # conning tower footprint (z -2..2)
TOWER_Y0, TOWER_Y1 = DECK + 1, DECK + 4   # walls y 8..11, roof at 12
ROOF = TOWER_Y1 + 1               # 12
MAST_X = 15

YELLOW = CONCRETE["yellow"]
LIME = CONCRETE["lime"]
GRAY = CONCRETE["gray"]
TUBE_RIM = CONCRETE["light_gray"]  # the torpedo tubes' rims, lighter than the dark riveted bands round the nose
BLACK = CONCRETE["black"]
WOOL_K = WOOL["black"]
WOOL_W = WOOL["white"]
WOOL_Y = WOOL["yellow"]
SPRUCE = "minecraft:spruce_planks"
RAIL = fence("spruce")
BARREL = "minecraft:barrel[facing=up,open=false]"
CHAIN = "minecraft:iron_chain[axis=y]"
BARS = pane_of("minecraft:iron_bars")
SICK_BED_FOOT = "minecraft:white_bed[facing=east,occupied=false,part=foot]"
SICK_BED_HEAD = "minecraft:white_bed[facing=east,occupied=false,part=head]"

# The Heart Pirates' smiley, compact: 15 x 7 for the body sides (y 0..6, under the deck rim), 11 x 7 for the sail/flag.
# Spikes on the left/right edges and the corners, the eyes kept clear of the outline, and a U-shaped smile (corners one
# row higher than its middle) with a free row between it and the bottom of the ring, so it never merges into the outline.
SMILEY15 = [
    ".K.KKKKKKKKK.K.",
    "..K.........K..",
    "KK...K...K...KK",
    ".K.K.......K.K.",
    "KK..KKKKKKK..KK",
    "..K.........K..",
    ".K.KKKKKKKKK.K.",
]
SMILEY11 = [
    "K.KKKKKKK.K",
    ".K.......K.",
    "K...K.K...K",
    "K.K.....K.K",
    "K..KKKKK..K",
    ".K.......K.",
    "K.KKKKKKK.K",
]
SAIL_BITMAP = (SMILEY11, {"K": WOOL_W})
FLAG_BITMAP = (SMILEY11, {"K": WOOL_W, ".": WOOL_K})


class SubShip(Ship):
    """Ship whose '<id>_front.png' really looks from the bow (the kit keeps the block nearest the stern)."""

    def elevation(self, out, axis="z", scale=8, title=None):
        import render
        from PIL import Image, ImageDraw
        pts = {}
        for (x, y, z), s in self.blocks.items():
            if s == AIR or s.split("[")[0] in render.SKIP:
                continue
            if axis == "z":
                key, depth = (x, y), z
            else:
                key, depth = (-z, y), x
            if key not in pts or depth > pts[key][0]:
                pts[key] = (depth, s)
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
        for (u, v), (depth, s) in pts.items():
            cols = render.block_colors(s)
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


# ---------------------------------------------------------------- the body shape
def body_k(x):
    """Scale of the section at x: 1 amidships, shrinking into the rounded stern (x 0..6) and the nose (x 27..35)."""
    if x < X0 or x > X1:
        return 0.0
    k = 1.0
    if x <= 6:
        t = (6 - x) / 7.0
        k = math.sqrt(max(0.0, 1 - t ** 2.0))
    if x >= 27:
        t = (x - 26) / 9.6
        k = min(k, math.sqrt(max(0.0, 1 - t ** 2.2)))
    return k


def body_inside(x, y, z):
    k = body_k(x)
    if k <= 0.0:
        return False
    ry, rz = BODY_RY * k, BODY_RZ * k
    return (abs((y - BODY_CY) / ry) ** BODY_P + abs((z - CZ) / rz) ** BODY_P) <= 1.0


def body_cells():
    """All (x, y, z) cells of the solid cigar, with the top cut off above the deck."""
    cells = set()
    for x in range(X0, X1 + 1):
        for y in range(-3, DECK + 1):
            for z in range(-6, 7):
                if body_inside(x, y, z):
                    cells.add((x, y, z))
    return cells


def loose_blocks(s):
    """Blocks not connected (26-neighbourhood) to the keel: should be empty."""
    solid = {p for p, b in s.blocks.items() if b != AIR}
    start = min(solid, key=lambda p: (p[1], abs(p[2]), abs(p[0] - 16)))
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
    return sorted(solid - seen)


def soft_rope(s, p0, p1):
    """A rope (fence line) from p0 to p1 that only fills empty cells, so it never cuts the sail or the mast."""
    (x0, y0, z0), (x1, y1, z1) = p0, p1
    n = max(abs(x1 - x0), abs(y1 - y0), abs(z1 - z0))
    for i in range(n + 1):
        t = i / max(1, n)
        p = (round(x0 + (x1 - x0) * t), round(y0 + (y1 - y0) * t), round(z0 + (z1 - z0) * t))
        if s.blocks.get(p, AIR) == AIR:
            s.set(*p, RAIL)


# ---------------------------------------------------------------- the ship
def build():
    s = SubShip("polar_tang", "Polar Tang", faction="pirate", tiers=[2, 3], crew="Heart Pirates")

    # ------------------------------------------------------------------ the cigar body: a hollow shell + the deck
    cells = body_cells()
    DIRS6 = ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))
    shell = set()
    deck = set()
    for (x, y, z) in cells:
        if y == DECK:
            deck.add((x, y, z))
            continue
        if any((x + dx, y + dy, z + dz) not in cells for (dx, dy, dz) in DIRS6):
            shell.add((x, y, z))
    for (x, y, z) in shell:
        if x in BANDS:
            mat = GRAY
        elif y <= 0:
            mat = LIME
        else:
            mat = YELLOW
        s.set(x, y, z, mat)
    deck_edge = set()
    for (x, y, z) in deck:
        edge = any((x + dx, y, z + dz) not in deck for (dx, dz) in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        if edge:
            deck_edge.add((x, z))
            s.set(x, y, z, GRAY if x in BANDS else YELLOW)
        else:
            s.set(x, y, z, SPRUCE)
    # hollow inside: make sure interior cells are air, then lay the floor
    interior = cells - shell - deck
    for (x, y, z) in interior:
        s.set(x, y, z, AIR)
    for (x, y, z) in interior:
        if y == FLOOR:
            s.set(x, y, z, SPRUCE)
    inside = lambda x, y, z: (x, y, z) in interior and y > FLOOR   # noqa: E731  free room inside the hull

    # ------------------------------------------------------------------ the smiley on both sides of the body
    def paint_side(x0, y0, rows, side):
        h = len(rows)
        for j, row in enumerate(rows):
            y = y0 + h - 1 - j
            for i, ch in enumerate(row):
                x = x0 + i
                # the outermost block of the body at (x, y) on this side
                # (never the deck rim, never a cell with more body outboard of it, i.e. the top shoulder)
                zs = [z for z in range(0, 7) if (x, y, side * z) in shell and (x, y, side * z) not in deck
                      and not body_inside(x, y, side * (z + 1))]
                if not zs:
                    continue
                z = side * max(zs)
                s.set(x, y, z, WOOL_K if ch == "K" else YELLOW)
    for side in (1, -1):
        paint_side(12, 0, SMILEY15, side)      # x 12..26, y 0..6: aft of the nose taper, below the deck rim
    # round portholes along the aft body, both sides
    for x in (3, 5, 10):
        for side in (1, -1):
            w = max(z for z in range(0, 7) if (x, 4, side * z) in shell)
            s.set(x, 4, side * w, f"onepiece:porthole[facing={'south' if side > 0 else 'north'}]")

    # ------------------------------------------------------------------ rail, deck gear
    for (x, z) in deck_edge:
        if TOWER_X0 <= x <= TOWER_X1 and abs(z) <= 3:
            continue                                        # the walkway squeezes past the tower here
        s.set(x, DECK + 1, z, RAIL)
    # two cannons a side on the deck, firing through gaps in the rail
    for x in (9, 24):
        for side in (1, -1):
            s.cannon(x, DECK + 1, side * 2, "south" if side > 0 else "north")
            s.set(x, DECK + 1, side * 3, AIR)
    # a deck hatch forward with a ladder down to the sick bay
    s.open_hatch(27, DECK, CZ, ladder_facing="west", down_to=FLOOR + 1)
    s.set(28, DECK + 1, CZ, trapdoor("minecraft:spruce_trapdoor", "west", "bottom", "true"))
    for y in range(FLOOR + 1, DECK):
        s.set(28, y, CZ, SPRUCE)                            # backing post for the ladder
    for x in (5, 29):
        for side in (1, -1):
            z = side * max(zz for (xx, zz) in deck_edge if xx == x and zz * side > 0)
            s.lamp(x, DECK + 2, z)
    s.set(4, DECK + 1, 2, "onepiece:rope_coil[facing=south]")
    s.set(4, DECK + 1, -2, BARREL)
    s.set(22, DECK + 1, -2, "onepiece:rope_coil[facing=north]")
    s.anchor(30, DECK + 1, -1, "north")

    # ------------------------------------------------------------------ stern: fins and the propeller ring; bow planes
    for y in range(0, DECK + 1):
        s.set(X0 - 1, y, CZ, GRAY)                          # rudder
    for z in range(-3, 4):
        s.set(X0 - 1, 3, z, GRAY)                           # stern dive planes
    s.ring(X0 - 2, 3, CZ, 1.6, GRAY, axis="x")              # propeller shroud
    s.set(X0 - 2, 3, CZ, "minecraft:iron_block")            # hub
    for x in (32, 33):
        for side in (1, -1):
            w = max(z for z in range(0, 7) if (x, 2, side * z) in shell)
            s.set(x, 2, side * (w + 1), GRAY)
            if x == 32:
                s.set(x, 2, side * (w + 2), GRAY)

    # ------------------------------------------------------------------ bow: two torpedo tubes in the nose
    # each a black mouth with a light grey rim round it, on the frontmost shell cell of each (y, z)
    def nose_face(y, z):
        xs = [x for x in range(28, X1 + 1) if (x, y, z) in shell]
        return max(xs) if xs else None
    for tz in (-2, 2):
        for (dy, dz) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx = nose_face(3 + dy, tz + dz)
            if nx is not None:
                s.set(nx, 3 + dy, tz + dz, TUBE_RIM)
        nx = nose_face(3, tz)
        s.set(nx, 3, tz, BLACK)

    # ------------------------------------------------------------------ the conning tower
    s.box(TOWER_X0, TOWER_Y0, -2, TOWER_X1, TOWER_Y1, 2, YELLOW)
    s.box(TOWER_X0 + 1, TOWER_Y0, -1, TOWER_X1 - 1, TOWER_Y1, 1, AIR)
    s.box(TOWER_X0, ROOF, -2, TOWER_X1, ROOF, 2, GRAY)
    s.box(TOWER_X0 + 1, ROOF, -1, TOWER_X1 - 1, ROOF, 1, SPRUCE)
    # the tower stands on the deck: open the deck under it so the ladder runs straight down into the hull
    for x in range(TOWER_X0 + 1, TOWER_X1):
        for z in (-1, 0, 1):
            s.set(x, DECK, z, SPRUCE)
    s.open_hatch(16, DECK, -1, ladder_facing="south", down_to=FLOOR + 1)
    s.open_hatch(16, ROOF, -1, ladder_facing="south", down_to=DECK + 1)
    for y in range(FLOOR + 1, DECK):
        s.set(16, y, -2, SPRUCE)                            # the ladder's backing post inside the hull
    # portholes on every side, a door aft onto the deck
    for x in (15, 17):
        s.set(x, TOWER_Y0 + 2, -2, "onepiece:porthole[facing=north]")
        s.set(x, TOWER_Y0 + 2, 2, "onepiece:porthole[facing=south]")
    for z in (-1, 1):
        s.set(TOWER_X1, TOWER_Y0 + 2, z, "onepiece:porthole[facing=east]")
    s.set(TOWER_X0, TOWER_Y0 + 2, 1, "onepiece:porthole[facing=west]")
    s.set(TOWER_X0, TOWER_Y0, -1, AIR)
    s.set(TOWER_X0, TOWER_Y0 + 1, -1, AIR)
    s.set(TOWER_X0, TOWER_Y0, -1, door("minecraft:spruce_door", "west", "lower"))
    s.set(TOWER_X0, TOWER_Y0 + 1, -1, door("minecraft:spruce_door", "west", "upper"))
    s.lamp(16, TOWER_Y1, 1, hanging=True)
    # the bridge on the roof: rail round the edge, the Ship's Wheel at the front, the periscope, lamps
    for x in range(TOWER_X0, TOWER_X1 + 1):
        for z in range(-2, 3):
            if x in (TOWER_X0, TOWER_X1) or z in (-2, 2):
                s.set(x, ROOF + 1, z, RAIL)
    s.helm(TOWER_X1 - 1, ROOF + 1, CZ)
    for y in range(ROOF + 1, ROOF + 5):
        s.set(TOWER_X0 + 1, y, 1, CHAIN)                    # periscope
    s.set(TOWER_X0 + 1, ROOF + 5, 1, "minecraft:iron_block")
    s.set(TOWER_X0 + 2, ROOF + 5, 1, BARS)
    s.lamp(TOWER_X0, ROOF + 2, -2)
    s.lamp(TOWER_X1, ROOF + 2, 2)

    # ------------------------------------------------------------------ the short mast, the black smiley sail, the flag
    sail_y0, sail_y1 = ROOF + 4, ROOF + 10                  # y 16..22, 7 rows: clear of the wheel by 3
    s.square_sail(MAST_X + 1, CZ, sail_y0, sail_y1, 5, WOOL_K, belly=0, yard="spruce", bitmap=SAIL_BITMAP)  # flat, so the smiley reads
    mast_top = s.mast(MAST_X, CZ, ROOF + 1, (sail_y1 + 0) - ROOF, wood="spruce")   # y 13..22, a short pole
    s.flag(MAST_X, mast_top + 1, CZ, FLAG_BITMAP)                                    # right above the sail
    yard_y = sail_y1 + 1
    # a compact tent of rigging over the tower: shrouds from the masthead to the aft roof rail corners, and sheets from
    # the sail's foot corners to the forward ones (nothing reaches the deck)
    for side in (1, -1):
        soft_rope(s, (MAST_X, yard_y, CZ), (TOWER_X0, ROOF + 1, side * 2))
        soft_rope(s, (MAST_X + 1, sail_y0, side * 5), (TOWER_X1, ROOF + 1, side * 2))

    # ------------------------------------------------------------------ inside: crew room aft, control room, sick bay forward
    for x in (13, 19):
        for y in range(FLOOR + 1, DECK):
            for z in range(-4, 5):
                if inside(x, y, z) and z != CZ:
                    s.set(x, y, z, SPRUCE)
    I.furnish(s, 2, FLOOR + 1, -3, 12, 3, DECK - FLOOR - 1, "barracks", "pirate", seed=7)
    s.chest(3, FLOOR + 1, 0, "pirate", facing="east")
    s.set(12, FLOOR + 1, 3, BARREL)
    s.set(12, FLOOR + 1, -3, "onepiece:sake_barrel[axis=y]")
    s.lamp(7, DECK - 1, CZ, hanging=True)
    # control room under the tower: the ladder lands here
    s.set(15, FLOOR + 1, 1, "minecraft:crafting_table")
    s.set(17, FLOOR + 1, 1, "minecraft:lectern[facing=north,has_book=false,powered=false]")
    s.lamp(16, DECK - 1, 1, hanging=True)
    # sick bay: beds, brewing stands, the medicine chests
    I.furnish(s, 20, FLOOR + 1, -3, 30, 3, DECK - FLOOR - 1, "lab", "pirate", seed=3)
    for z in (-3, 3):
        s.set(22, FLOOR + 1, z, SICK_BED_FOOT)
        s.set(23, FLOOR + 1, z, SICK_BED_HEAD)
    s.chest(29, FLOOR + 1, 2, "medicine", facing="west")
    s.chest(29, FLOOR + 1, -2, "medicine", facing="west")
    s.chest(25, FLOOR + 1, 3, "medium", facing="north")
    s.lamp(24, DECK - 1, CZ, hanging=True)

    loose = loose_blocks(s)
    if loose:
        print(f"  !! {len(loose)} loose blocks, e.g. {loose[:12]}")
    # four Ballast Tanks set into the floor along the keel: they make her a real submarine in the mod (deepsea.ShipDive)
    for x in (5, 10, 21, 27):
        s.set(x, FLOOR, CZ, "onepiece:ballast_tank")

    return s

"""Marine Warship: the Navy's standard two-masted warship. White hull, royal-blue band, a seagull on the bow.

Layout (+x is the bow, CZ = 0, hull x 0..29, weather deck at y 6):
  x  0..7    stern castle, two storeys: officers' mess (y 7..9) and the captain's cabin (y 11..13) with the stern
             balcony; the bridge on the blue roof (y 15) with the Ship's Wheel. Brig in the hull below it.
  x  8..28   weather deck: main mast at x 12, hatch at x 16, foremast at x 23, 2 deck cannons a side.
  gun deck   y 3..5 inside the hull (floor y 2): barracks x 8..17 and the armory x 19..23, 4 gun ports a side.
  x 29..36   the seagull figurehead on the stem, wings swept back along the bow sides to x 22.
"""
from shipkit import *  # noqa: F401,F403

CUTS = (7,)       # one cut just above the weather deck: shows the deck layout

CZ = 0
X0, LEN = 0, 30
X1 = X0 + LEN - 1                 # 29 = the stem
BEAM = 11
KEEL, DECK = -2, 6
HOLD = 2                          # gun deck floor
CASTLE_X1 = 7                     # last column of the stern castle
MID = 10                          # floor of the upper storey (the lower blue roof / balcony level)
ROOF = 14                         # the blue roof = the bridge floor
MAIN_X, FORE_X = 12, 23

WHITE = CONCRETE["white"]
BLUE = CONCRETE["blue"]
BLUE_T = TERRACOTTA["blue"]
LBLUE = CONCRETE["light_blue"]
GRAY = CONCRETE["gray"]
BLACK = CONCRETE["black"]
YELLOW = CONCRETE["yellow"]
BIRCH = "minecraft:birch_planks"
WOOL_W = WOOL["white"]
WOOL_B = WOOL["blue"]
RAIL = fence("birch")
WINDOW = pane("light_blue")
BARS = pane_of("onepiece:prison_bars")
LGRAY = CONCRETE["light_gray"]
BARREL = "minecraft:barrel[facing=up,open=false]"

# The Marine gull, 19 wide, for the mainsail (drawn at the sail's own size so every block maps 1:1).
GULL19_ROWS = [
    ".....BB.....BB.....",
    "...BBBBB...BBBBB...",
    ".BBBBBBBBBBBBBBBBB.",
    "BBBBBBBBBBBBBBBBBBB",
    "......BBBBBBB......",
    ".......BBBBB.......",
    ".........B.........",
]
# A smaller gull, 11 wide, for the foresail.
GULL11_ROWS = [
    "..BB...BB..",
    ".BBBBBBBBB.",
    "BBBBBBBBBBB",
    "....BBB....",
    ".....B.....",
]
# White flag with the blue gull, 9 x 6 (the pole is drawn by flag()).
FLAG_ROWS = [
    "WWWWWWWWW",
    "WBBWWWBBW",
    "BBBBBBBBB",
    "WWBBBBBWW",
    "WWWWBWWWW",
    "WWWWWWWWW",
]
FLAG = (FLAG_ROWS, {"W": WOOL_W, "B": WOOL_B})
PAL = {"B": WOOL_B, "#": WOOL_B}


def mainsail_bitmap():
    """23 wide x 13 tall: the gull over the word MARINE (3x5 letters, 23 wide)."""
    rows = [".." + r + ".." for r in GULL19_ROWS]
    rows.append("." * 23)
    # hand-drawn letters: the kit's 3x5 M reads as H, so M is 5 wide and I is 1 wide (5+3+3+1+3+3 + 5 gaps = 23)
    glyphs = [
        ["#...#", "##.##", "#.#.#", "#...#", "#...#"],   # M
        [".#.", "#.#", "###", "#.#", "#.#"],             # A
        ["##.", "#.#", "##.", "#.#", "#.#"],             # R
        ["#", "#", "#", "#", "#"],                       # I
        ["##.", "#.#", "#.#", "#.#", "#.#"],             # N
        ["###", "#..", "##.", "#..", "###"],             # E
    ]
    rows += [".".join(g[r] for g in glyphs) for r in range(5)]
    assert all(len(r) == 23 for r in rows)
    return ([r[::-1] for r in rows], PAL)        # mirrored: column 0 lands at +z, so it reads from the bow


def foresail_bitmap():
    """13 wide x 6 tall: the small gull on its own."""
    rows = ["." * 13] + ["." + r + "." for r in GULL11_ROWS]
    return (rows, PAL)


class MarineShip(Ship):
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


# ---------------------------------------------------------------- helpers
BOW_LEN = 10
SHEER_BOW = 2


def deck_at(x):
    """Deck height at x, the same sheer the kit's hull() lofts (no sheer at the stern)."""
    f = x - X0
    if f >= LEN - BOW_LEN:
        t = min(1.0, (f - (LEN - BOW_LEN)) / max(1, BOW_LEN - 1))
        return DECK + int(round(SHEER_BOW * t ** 1.4))
    return DECK


def hull_paint(x, y, z, kind):
    """White hull, two blue courses just under the deck, light-blue trim at the waterline, grey under water."""
    if kind == "bulwark":
        return WHITE
    if kind in ("side", "bow", "stern"):
        if y <= 0:
            return GRAY
        if y == 1:
            return LBLUE
        dy = deck_at(x)
        if dy - 2 <= y <= dy - 1:
            return BLUE
        return WHITE
    return None


def deck_cells(s, x):
    """(deck y, z cells of the hull deck at x)."""
    if x < X0 or x > X1:
        return None, []
    dy = s.deck_y(x)
    return dy, [z for z in range(-7, 8) if s._inside(x, dy, z)]


def castle_storey(s, x0, x1, y_from, top, wall, floor, band=None, ledge=None, ledge_sides=True):
    """Walls on the hull's deck outline from y_from to top-1, a floor at `top` over the footprint (its outer edge in
    `band`, so a coloured course runs round the castle), and a ledge (an overhanging course of `ledge`) along the stern
    and, with ledge_sides, both sides. Returns the floor cells."""
    cells = set()
    foot = {}
    for x in range(x0, x1 + 1):
        dy, zs = deck_cells(s, x)
        foot[x] = set(zs)
    for x in range(x0, x1 + 1):
        zs = foot[x]
        prev = foot.get(x - 1, set()) if x > x0 else set()
        nxt = foot.get(x + 1, set()) if x < x1 else set()
        for z in zs:
            edge = (z + 1 not in zs) or (z - 1 not in zs) or (z not in prev) or (z not in nxt)
            if edge:
                for y in range(y_from, top):
                    s.set(x, y, z, wall)
            s.set(x, top, z, (band or floor) if edge else floor)
            cells.add((x, z))
    if ledge:
        ring = set()
        for (x, z) in cells:
            for (dx, dz) in ((0, 1), (0, -1), (-1, 0), (1, 0)):
                if (x + dx, z + dz) in cells or x + dx > x1:
                    continue
                if x + dx < x0 or (ledge_sides and dx == 0):
                    ring.add((x + dx, z + dz))
        for (x, z) in ring:
            s.set(x, top, z, ledge)
        cells |= ring
    return cells


def rail_z(s, x):
    """Half width of the deck outline at x: where the bulwark and rail stand."""
    return max(deck_cells(s, x)[1])


ROPE = fence("oak")


def shrouds(s, mast_x, top_y, xs):
    """Tan ropes from the mast at top_y down to the rail on both sides, one per x in xs, abaft the sail.
    They never overwrite a block already there (the aft feet end on the castle wall)."""
    for x in xs:
        for side in (-1, 1):
            p0, p1 = (mast_x - 1, top_y, CZ), (x, s.deck_y(x) + 2, side * rail_z(s, x))
            n = max(abs(a - b) for a, b in zip(p0, p1))
            for i in range(n + 1):
                q = tuple(round(a + (b - a) * i / max(1, n)) for a, b in zip(p0, p1))
                if s.get(*q) in (None, AIR):
                    s.set(*q, ROPE)


def stay(s, p0, p1):
    """A stay in the x-y plane at z = CZ, stepped so every fence post shares a face with the next one."""
    (x0, y0, _), (x1, y1, _) = p0, p1
    n = max(abs(x1 - x0), abs(y1 - y0))
    prev = None
    for i in range(n + 1):
        x = round(x0 + (x1 - x0) * i / max(1, n))
        y = round(y0 + (y1 - y0) * i / max(1, n))
        if prev and prev[0] != x and prev[1] != y:
            if s.get(x, prev[1], CZ) in (None, AIR):
                s.set(x, prev[1], CZ, ROPE)
        if s.get(x, y, CZ) in (None, AIR):
            s.set(x, y, CZ, ROPE)
        prev = (x, y)


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


# ---------------------------------------------------------------- the ship
def build():
    s = MarineShip("marine_warship", "Marine Warship", faction="marine", tiers=[0, 1, 2], crew="Marines")

    # ------------------------------------------------------------------ hull
    s.hull(x0=X0, length=LEN, cz=CZ, beam=BEAM, keel_y=KEEL, deck_y=DECK, side=WHITE, bottom=GRAY, deck=BIRCH,
           bow_len=BOW_LEN, stern_len=4, bow="sharp", stern="transom", sheer_bow=SHEER_BOW, sheer_stern=0,
           fullness=0.7, flat=0.35, bulwark=1, bulwark_mat=WHITE, rail=RAIL, paint=hull_paint)
    inside = s._inside
    # gun deck floor (the kit only lays it where the hull is hollow), from the brig to the armory
    for x in range(X0 + 1, 25):
        for z in range(-6, 7):
            if inside(x, HOLD, z) and inside(x, HOLD - 1, z) and s.get(x, HOLD, z) == AIR:
                s.set(x, HOLD, z, BIRCH)
    # the stern bottom tapers so steeply that the hollowed skin only touches diagonally: fill it solid
    for x in range(X0, X0 + 3):
        for y in range(KEEL, 1):
            for z in range(-4, 5):
                if inside(x, y, z) and s.get(x, y, z) == AIR:
                    s.set(x, y, z, GRAY)
    # rudder post hanging off the transom, down into the water
    for y in range(KEEL, DECK):
        s.set(X0 - 1, y, CZ, GRAY if y <= 0 else WHITE)

    # ------------------------------------------------------------------ stern castle: two storeys + the bridge
    castle_storey(s, X0, CASTLE_X1, DECK + 1, MID, WHITE, BIRCH, band=BLUE, ledge=BLUE, ledge_sides=False)  # mess
    castle_storey(s, X0, CASTLE_X1, MID + 1, ROOF, WHITE, BLUE, band=BLUE, ledge=BLUE)     # captain's deck, blue roof y 14
    # the bridge: a birch rail round the roof edge, the Ship's Wheel at the front looking over the main deck
    roof_cells = {(x, z) for (x, y, z), b in s.blocks.items() if y == ROOF and b in (BLUE, BLUE_T) and x <= CASTLE_X1}
    for (x, z) in roof_cells:
        nbrs = ((x + 1, z), (x - 1, z), (x, z + 1), (x, z - 1))
        if any(n not in roof_cells for n in nbrs):
            s.set(x, ROOF + 1, z, RAIL)
    s.set(CASTLE_X1, ROOF + 1, CZ, AIR)
    s.helm(CASTLE_X1 - 1, ROOF + 1, CZ)
    s.set(CASTLE_X1, ROOF + 1, CZ, RAIL)
    s.lamp(X0 - 1, ROOF + 2, -3)
    s.lamp(X0 - 1, ROOF + 2, 3)
    s.lamp(CASTLE_X1, ROOF + 2, -5)
    s.lamp(CASTLE_X1, ROOF + 2, 5)
    # windows: rows of light-blue panes along both storeys, the stern face, and the front wall
    for x in (1, 3, 5):
        for y in (DECK + 2, MID + 2):
            dy, zs = deck_cells(s, x)
            s.set(x, y, min(zs), WINDOW)
            s.set(x, y, max(zs), WINDOW)
    for z in (-2, 0, 2):
        s.set(X0, DECK + 2, z, WINDOW)
    for z in (-2, 2):
        s.set(X0, MID + 2, z, WINDOW)
        s.set(CASTLE_X1, DECK + 2, z, WINDOW)
        s.set(CASTLE_X1, MID + 2, z, WINDOW)
    # the stern balcony on the lower ledge, with a rail and a door from the captain's cabin
    for z in range(-3, 4):
        s.set(X0 - 1, MID, z, BLUE)
    for z in range(-4, 5):
        if s.get(X0 - 1, MID, z) == BLUE or s.get(X0, MID, z) == BLUE:
            s.set(X0 - 1, MID + 1, z, RAIL)
    for z in (-4, 4):
        s.set(X0, MID + 1, z, RAIL)
    s.set(X0, MID + 1, CZ, door("minecraft:birch_door", "west", "lower"))
    s.set(X0, MID + 2, CZ, door("minecraft:birch_door", "west", "upper"))
    # door from the mess onto the main deck, a ladder up the front wall to the bridge
    s.set(CASTLE_X1, DECK + 1, CZ, door("minecraft:birch_door", "east", "lower"))
    s.set(CASTLE_X1, DECK + 2, CZ, door("minecraft:birch_door", "east", "upper"))
    s.ladder_up(CASTLE_X1 + 1, 3, DECK + 1, ROOF, facing="east")
    s.set(CASTLE_X1, ROOF + 1, 3, AIR)
    # inside: ladder from the mess up to the captain's cabin; the officers' mess below, the cabin above
    s.open_hatch(1, MID, -1, ladder_facing="east", down_to=DECK + 1)
    s.table_set(4, DECK + 1, -1, "birch", "blue")
    s.table_set(4, DECK + 1, 1, "birch", "blue")
    s.set(6, DECK + 1, -3, BARREL)
    s.set(7, DECK + 1, -3, "onepiece:sake_barrel[axis=y]")
    s.set(2, DECK + 1, 3, "minecraft:bookshelf")
    s.set(4, DECK + 3, CZ, lantern(hanging=True))
    I.furnish(s, 1, MID + 1, -3, CASTLE_X1 - 1, 3, 3, "captain", "marine", seed=5)
    s.lamp(CASTLE_X1 + 1, DECK + 1, -4)
    s.lamp(CASTLE_X1 + 1, DECK + 1, 4)

    # ------------------------------------------------------------------ gun deck: brig, barracks, armory
    s.broadside((10, 13, 16, 19), HOLD + 1, CZ, lambda x: s.halfwidth(x, HOLD + 1), gunport=BLACK)
    # brig under the castle: a wall of prison bars at x 8 with a barred door gap
    for y in range(HOLD + 1, DECK):
        for z in range(-4, 5):
            if inside(CASTLE_X1, y, z) and s.get(CASTLE_X1, y, z) == AIR:
                s.set(CASTLE_X1, y, z, BARS)
    s.set(CASTLE_X1, HOLD + 1, CZ, door("minecraft:iron_door", "east", "lower"))
    s.set(CASTLE_X1, HOLD + 2, CZ, door("minecraft:iron_door", "east", "upper"))
    s.set(2, HOLD + 1, -2, "minecraft:white_bed[facing=west,occupied=false,part=foot]")
    s.set(1, HOLD + 1, -2, "minecraft:white_bed[facing=west,occupied=false,part=head]")
    s.set(2, HOLD + 1, 2, "minecraft:cauldron")
    s.set(5, HOLD + 1, 3, "minecraft:iron_chain[axis=y]")
    s.set(5, HOLD + 2, 3, "minecraft:iron_chain[axis=y]")
    s.lamp(4, DECK - 1, CZ, hanging=True)
    # bulkhead between the barracks and the armory, with a doorway
    for y in range(HOLD + 1, DECK):
        for z in range(-4, 5):
            if inside(18, y, z) and s.get(18, y, z) == AIR and z != CZ:
                s.set(18, y, z, BIRCH)
    # hatch from the weather deck down to the barracks
    s.open_hatch(16, DECK, CZ, ladder_facing="west", down_to=HOLD + 1)
    for y in range(HOLD + 1, DECK):
        s.set(17, y, CZ, BIRCH)
    I.furnish(s, CASTLE_X1 + 1, HOLD + 1, -3, 17, 3, 3, "barracks", "marine", seed=11)
    I.furnish(s, 19, HOLD + 1, -3, 23, 3, 3, "armory", "marine", seed=13)
    s.chest(23, HOLD + 1, 2, "marine", facing="west")
    s.chest(23, HOLD + 1, -2, "marine", facing="west")
    s.chest(12, HOLD + 1, 3, "marine", facing="north")
    s.lamp(13, DECK - 1, CZ, hanging=True)
    s.lamp(21, DECK - 1, CZ, hanging=True)

    # ------------------------------------------------------------------ weather deck
    # two deck cannons a side, firing through embrasures cut in the bulwark
    for x in (17, 20):
        hw = rail_z(s, x)
        dy = s.deck_y(x)
        s.cannon(x, dy + 1, CZ + hw - 1, "south")
        s.cannon(x, dy + 1, CZ - hw + 1, "north")
        s.set(x, dy + 1, CZ + hw, AIR)
        s.set(x, dy + 1, CZ - hw, AIR)
    s.anchor(22, DECK + 1, -4, "north")
    s.set(10, DECK + 1, -4, "onepiece:rope_coil[facing=north]")
    s.set(21, DECK + 1, 4, "onepiece:rope_coil[facing=south]")
    s.set(10, DECK + 1, 4, BARREL)
    s.set(11, DECK + 1, 4, BARREL)
    s.lamp(16, DECK + 2, -5)
    s.lamp(16, DECK + 2, 5)

    # ------------------------------------------------------------------ masts, sails, flags, rigging
    # main mast: the big MARINE sail, white flag with the gull on top
    main_sail = mainsail_bitmap()
    sy0, sy1 = DECK + 9, DECK + 21                                  # y 15..27, 13 rows: clears the foresail
    s.square_sail(MAIN_X + 1, CZ, sy0, sy1, 11, WOOL_W, belly=0, yard="birch", bitmap=main_sail)
    main_top = s.mast(MAIN_X, CZ, HOLD + 1, (sy1 + 5) - HOLD, wood="birch")   # y 3..29
    s.flag(MAIN_X, main_top + 1, CZ, FLAG)
    yard_y = sy1 + 1
    shrouds(s, MAIN_X, yard_y, (MAIN_X - 2, MAIN_X - 5))
    # foremast: a smaller sail with the gull alone
    fy0, fy1 = DECK + 3, DECK + 8                                   # y 9..14, 6 rows
    s.square_sail(FORE_X + 1, CZ, fy0, fy1, 6, WOOL_W, belly=0, yard="birch", bitmap=foresail_bitmap())
    fore_top = s.mast(FORE_X, CZ, HOLD + 1, (fy1 + 4) - HOLD, wood="birch")  # y 3..22
    s.flag(FORE_X, fore_top + 1, CZ, FLAG, axis="x")     # flies forward, so it never hides the MARINE sail
    fyard = fy1 + 1
    shrouds(s, FORE_X, fyard, (FORE_X - 2, FORE_X - 4))
    # stays: main top -> fore top, fore top -> the stem head
    stay(s, (MAIN_X + 1, main_top - 1, CZ), (FORE_X - 1, fore_top - 1, CZ))
    stay(s, (FORE_X + 1, fore_top - 1, CZ), (X1, DECK + 6, CZ))

    # ------------------------------------------------------------------ the figurehead: a white seagull
    # body on top of the stem (x 31..34, y 9..11), tail fan up at the back, neck, head with eyes, yellow beak
    s.blob(X1 + 1.5, 10.0, CZ, 2.3, 1.6, 1.6, WOOL_W, power=2.5)
    s.set(X1 - 1, DECK + 4, CZ, WOOL_W)
    s.set(X1 - 1, DECK + 5, CZ, WOOL_W)
    s.set(X1 - 1, DECK + 6, CZ, WOOL_W)
    s.set(X1 + 4, DECK + 5, CZ, WOOL_W)                              # neck
    s.box(X1 + 4, DECK + 6, -1, X1 + 5, DECK + 7, 1, WOOL_W)         # head
    s.set(X1 + 5, DECK + 7, -1, BLACK)
    s.set(X1 + 5, DECK + 7, 1, BLACK)
    s.set(X1 + 6, DECK + 6, CZ, YELLOW)                              # beak
    s.set(X1 + 7, DECK + 6, CZ, YELLOW)
    # the raked cutwater under the gull: the stem leans forward 1 block every 3 rows (x 29..31), a second step to x 32
    # under the gull's breast; painted like the hull (light-blue trim, the blue band, white)
    band = (deck_at(X1) - 2, deck_at(X1) - 1)
    for y in range(1, 10):
        reach = X1 + (y - 1) // 3 + (1 if y >= 8 else 0)
        for x in range(X1, reach + 1):
            if s.get(x, y, CZ) in (None, AIR):
                s.set(x, y, CZ, LBLUE if y == 1 else BLUE if y in band else WHITE)
    # wings: laid flush on the bow sides over the blue band, swept back from a 6-tall shoulder at the stem to a
    # 1-block tip at x 22; 2 blocks proud at the shoulder (x 27..29) so they show from the bow. White wool, with
    # light-grey primary feathers hanging under every second column from the tip.
    tip_x, root_top, root_bot, tip_y = X1 - 7, deck_at(X1) + 2, deck_at(X1) - 3, deck_at(X1 - 7) - 1
    for x in range(tip_x, X1 + 1):
        t = (X1 - x) / (X1 - tip_x)                     # 0 at the shoulder, 1 at the tip
        top = round(root_top + (tip_y - root_top) * t)
        bot = round(root_bot + (tip_y - root_bot) * t)
        for y in range(bot, top + 1):
            w = s.halfwidth(x, min(y, s.deck_y(x)))
            outer = x >= X1 - 2 and bot < y < top          # the rounded shoulder, 2 blocks proud
            for side in (-1, 1):
                for d in ((1, 2) if outer else (1,)):
                    s.set(x, y, side * (w + d), WOOL_W)
        if (x - tip_x) % 2 == 1 and x < X1 - 1:          # feather fingers on the trailing edge
            w = s.halfwidth(x, bot - 1)
            for side in (-1, 1):
                s.set(x, bot - 1, side * (w + 1), LGRAY)

    loose = loose_blocks(s)
    if loose:
        print(f"  !! {len(loose)} loose blocks, e.g. {loose[:12]}")
    return s

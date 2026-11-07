"""Marine Battleship: the Navy's big three-master (enemy, tiers 3-5). White hull with a royal-blue band and a grey
bottom, a three-storey white stern castle with blue roofs, two rows of gun ports, three birch masts with white
sails ("MARINE" under the gull on the mainsail) and a white seagull figurehead with its wings swept back along
both sides of the bow.

Layout (+x is the bow, CZ = 0, main deck at y 8, the bow deck rises to y 9):
  x -2..-1  stern balcony (y 12) under the barracks windows; the rudder below
  x  0..12  stern castle: tier 1 captain's cabin (y 9..11), tier 2 crew barracks (x 0..8, y 13..15), tier 3 chart
            room (x 0..5, y 17..19); the bridge on the tier-3 roof (y 21) with the Ship's Wheel under a blue canopy;
            the quarterdeck strip x 9..12 on the tier-1 roof (y 12) with the mizzen (x 10)
  x 13..36  main deck: mainmast x 22, foremast x 36, hatch + ladder at x 18, four weather-deck guns a side
  x 37..41  bow deck (y 9): anchor; the gull's wings lie flat along both bulwarks (x 35..41)
  x 41..48  the gull: breast on a raked white cutwater, a narrow head x 43..46 with black eyes, hooked yellow beak to x 48
  sails:    fore course y 19..26 + topsail, main course y 14..26 (MARINE at y 14..18, spaced MAR _ INE around the
            gull's head so it reads from the bow) + topsail + crow's nest, mizzen course + topsail; tops main > fore > mizzen
  inside:   upper gun deck (floor y 4): the brig aft behind prison bars, 6 guns a side, armory forward
            the hold (y -1..3): 7 guns a side on catwalks (y 1) along the hull, stores and loot on the bottom

NOTE for build.py: tools/landmarks/marine_battleship.py (a landmark) shares this module name and shipkit puts
tools/landmarks ahead of tools/ships on sys.path, so `python3 build.py marine_battleship` imports the landmark
unless this file is loaded first (e.g. importlib.util.spec_from_file_location + sys.modules["marine_battleship"]).
"""
from shipkit import *  # noqa: F401,F403

CZ = 0
X0, LEN = 0, 42
X1 = X0 + LEN - 1    # 41 = the stem
BEAM = 13
KEEL, DECK = -2, 8
UPPER = 4            # floor of the upper gun deck
WALK = 1             # catwalks of the lower gun row (guns at y 2, ports in the white hull under the blue band)
T1, T2, T3 = DECK + 4, DECK + 8, DECK + 12   # roofs of the three castle tiers (12, 16, 20)
MIZZEN_X, MAIN_X, FORE_X = 10, 22, 36
HATCH_X = 18
CUTS = (DECK + 1,)   # just above the main deck: the deck layout

WHITE = CONCRETE["white"]
BLUE = CONCRETE["blue"]
LIGHT_BLUE = CONCRETE["light_blue"]
GRAY = CONCRETE["gray"]
BLACK = CONCRETE["black"]
YELLOW = CONCRETE["yellow"]
BIRCH = "minecraft:birch_planks"
BIRCH_STAIRS = "minecraft:birch_stairs"
BRAIL = fence("birch")
WOOL_W = WOOL["white"]
WOOL_B = WOOL["blue"]
WINDOW = pane("light_blue")
BARREL = "minecraft:barrel[facing=up,open=false]"
BARS = "onepiece:prison_bars"

# Flags: the blue gull on white, 9 x 6 for the mainmast and 7 x 5 for the others.
FLAG_ROWS = [
    "WWWWWWWWW",
    "WBBWWWBBW",
    "BBBBWBBBB",
    "WWBBBBBWW",
    "WWWBBBWWW",
    "WWWWBWWWW",
]
SMALL_FLAG_ROWS = [
    "WWWWWWW",
    "WBWWWBW",
    "BBBWBBB",
    "WWBBBWW",
    "WWWBWWW",
]
FLAG_PAL = {"W": WOOL_W, "B": WOOL_B}
MARINE_FLAG = (FLAG_ROWS, FLAG_PAL)
SMALL_FLAG = (SMALL_FLAG_ROWS, FLAG_PAL)
GULL_PAL = {"B": WOOL_B, "#": WOOL_B}


def compose(w, h, parts, flip=False):
    """Blank w x h bitmap rows with each (rows, top_row) part pasted in, centred across. Every sail bitmap is
    made at the sail's own size so the kit maps it 1:1 (no stretching). flip mirrors it (the kit lays columns
    along +z, which reads mirrored from the bow)."""
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


def gull_sail(half, y0, y1):
    """Plain white sail bitmap with the gull on it."""
    w, h = 2 * half + 1, y1 - y0 + 1
    return (compose(w, h, [(GULL_ROWS, (h - 7) // 2)]), GULL_PAL)


def marine_sail(half, y0, y1):
    """The mainsail: the gull with MARINE under it, reading correctly from the bow. The word is spread to 25 wide
    with a 3-column gap between MAR and INE, the width of the figurehead's head that stands in front of it."""
    w, h = 2 * half + 1, y1 - y0 + 1
    left = [r[:-1] for r in text_rows("MAR")]                 # 11 wide, 5 tall (drop the trailing gap column)
    right = [r[:-1] for r in text_rows("INE")]
    word = [a + "..." + b for a, b in zip(left, right)]       # 25 wide
    return (compose(w, h, [(GULL_ROWS, 0), (word, 8)], flip=True), GULL_PAL)


class MarineShip(Ship):
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
    """One storey of the stern castle on the hull's deck outline shrunk by `inset` a side: white walls y0..y1-1,
    hollow, a roof at y1: blue (with one block of overhang on the sides and the stern), except birch where the
    roof is a floor (inside, up to floor_x1). Returns {x: set(z)}."""
    cells = {}
    for x in range(x0, x1 + 1):
        _, zs = outline(s, x)
        if inset:
            zs = zs[inset:len(zs) - inset]
        cells[x] = set(zs)
    for x, zs in cells.items():
        for z in zs:
            edge = (z - 1 not in zs) or (z + 1 not in zs) or (z not in cells.get(x - 1, ())) or (z not in cells.get(x + 1, ()))
            for y in range(y0, y1):
                s.set(x, y, z, WHITE if edge else AIR)
            walk = floor_x1 is not None and x <= floor_x1
            s.set(x, y1, z, BIRCH if (walk and not edge) else BLUE)
    for x in range(x0 - 1, x1 + 1):
        for z in range(-9, 10):
            if z in cells.get(x, ()):
                continue
            if any(z + dz in cells.get(x + dx, ()) for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                s.set(x, y1, z, BLUE)
    return cells


def tier_windows(s, cells, y, skip=()):
    """Light-blue panes every other block along the side walls and across the end walls of a tier."""
    xs = sorted(cells)
    for x in xs:
        zs = cells[x]
        lo, hi = min(zs), max(zs)
        if x in (xs[0], xs[-1]):
            for z in range(lo + 1, hi):
                if z % 2 == 0 and (x, z) not in skip:
                    s.set(x, y, z, WINDOW)
        elif x % 2 == 0:
            s.set(x, y, lo, WINDOW)
            s.set(x, y, hi, WINDOW)


def loose_blocks(s):
    """(blocks not connected to the keel even diagonally, non-rope blocks without any face neighbour): both should
    be empty. Fence 'ropes' may run diagonally, everything else must touch the ship face to face."""
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
    """Hull skin blocks that only touch the ship diagonally (the kit hollows their inside neighbours at a tight
    curve): fill the hollow cell next to them, toward the centre line first, then below, then above."""
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


# ---------------------------------------------------------------- the ship
def build():
    s = MarineShip("marine_battleship", "Marine Battleship", faction="marine", tiers=[3, 4, 5], crew="Marines")

    # ---- hull: white, sharp bow, flat stern, grey under water; the upper gun deck floor inside
    s.hull(x0=X0, length=LEN, cz=CZ, beam=BEAM, keel_y=KEEL, deck_y=DECK, side=WHITE, bottom=GRAY, deck=BIRCH,
           bow_len=12, stern_len=5, bow="sharp", stern="transom", sheer_bow=1, sheer_stern=0, keel_rise_bow=2,
           keel_rise_stern=1, fullness=0.6, flat=0.3, bulwark=1, bulwark_mat=WHITE, rail=BRAIL,
           inner_decks=[(UPPER, BIRCH)])
    inside = s._inside
    # the royal-blue band (two courses under the deck edge) and the light-blue waterline trim
    for (x, y, z), b in list(s.blocks.items()):
        if b != WHITE or x not in s._hull:
            continue
        dy = s.deck_y(x)
        if y in (dy - 1, dy - 2):
            s.set(x, y, z, BLUE)
        elif y == 1:
            s.set(x, y, z, LIGHT_BLUE)

    def zedge(x):
        return s.halfwidth(x, s.deck_y(x))

    # rudder under the transom (grey below the water, white above)
    for y in range(-1, DECK):
        s.set(X0 - 1, y, CZ, GRAY if y <= 0 else WHITE)

    # ---- guns: two rows of black ports in the white hull with cannons behind, plus the weather deck
    lower_xs = (9, 13, 17, 21, 25, 29, 33)
    upper_xs = (11, 15, 19, 23, 27, 31)
    s.broadside(lower_xs, WALK + 1, CZ, lambda x: s.halfwidth(x, WALK + 1), gunport=BLACK)
    s.broadside(upper_xs, UPPER + 1, CZ, lambda x: s.halfwidth(x, UPPER + 1), gunport=BLACK)
    # catwalk ledges along both sides of the hold under the lower guns
    for gx in lower_xs:
        for x in (gx,):
            hw = s.halfwidth(x, WALK + 1)
            for z in (hw - 1, -(hw - 1)):
                if inside(x, WALK, z) and s.get(x, WALK, z) == AIR:
                    s.set(x, WALK, z, BIRCH)

    def bulkhead(x, y0, y1, mat, door_z=None):
        for y in range(y0, y1 + 1):
            for z in range(-7, 8):
                if inside(x, y, z) and s.get(x, y, z) == AIR and z != door_z:
                    s.set(x, y, z, mat)
    bulkhead(8, UPPER + 1, UPPER + 2, BARS, door_z=CZ)         # the brig | upper battery
    s.set(8, UPPER + 1, CZ, door("minecraft:iron_door", "east", "lower"))
    s.set(8, UPPER + 2, CZ, door("minecraft:iron_door", "east", "upper"))
    bulkhead(32, UPPER + 1, UPPER + 2, BIRCH, door_z=CZ)       # upper battery | armory
    # hatch and ladder from the main deck down through the gun deck to the bottom of the hold (post at x+1)
    s.open_hatch(HATCH_X, DECK, -2, ladder_facing="west", down_to=KEEL + 1)   # the ladder is the hole in the gun deck floor too
    for y in range(KEEL + 1, DECK):
        if s.get(HATCH_X + 1, y, -2) in (None, AIR):
            s.set(HATCH_X + 1, y, -2, BIRCH)
    # lanterns under the beams
    for x in (12, 22, 31):
        s.lamp(x, UPPER + 3, CZ, hanging=True)
        s.lamp(x, UPPER - 1, CZ, hanging=True)
    # the hold: loot and stores on the bottom
    s.chest(23, KEEL + 1, -1, "marine", facing="east")
    s.chest(23, KEEL + 1, 1, "marine", facing="east")
    s.chest(28, KEEL + 1, CZ, "hard", facing="west")
    for (x, z) in ((14, -1), (27, -1)):
        s.set(x, KEEL + 1, z, BARREL)
    s.chest(35, KEEL + 1, CZ, "marine", facing="west")
    # the brig (aft, upper gun deck) and the armory (forward)
    I.furnish(s, 1, UPPER + 1, -4, 7, 4, 2, "cell", "marine", seed=9)
    I.furnish(s, 33, UPPER + 1, -4, 39, 4, 2, "armory", "marine", seed=5)
    s.chest(38, UPPER + 1, CZ, "marine", facing="west")

    # ---- weather deck: guns through the bulwark, gear, lanterns
    weather_xs = (15, 20, 26, 30)
    s.broadside(weather_xs, DECK + 1, CZ, lambda x: zedge(x), gunport=BLACK)
    for x in (13, 24, 32):
        for side in (-1, 1):
            s.lamp(x, DECK + 3, side * zedge(x))
    s.set(14, DECK + 1, -4, "onepiece:rope_coil[facing=north]")
    s.set(30, DECK + 1, 3, BARREL)
    s.set(30, DECK + 1, 4, BARREL)
    s.set(37, s.deck_y(37) + 1, 2, "onepiece:rope_coil[facing=east]")
    s.anchor(38, s.deck_y(38) + 1, -(zedge(38) - 1), "north")

    # ---- stern castle: three white tiers with blue roofs
    c1 = tier(s, 0, 12, DECK + 1, T1, 0, floor_x1=12)
    c2 = tier(s, 0, 8, T1 + 1, T2, 1, floor_x1=5)
    c3 = tier(s, 0, 5, T2 + 1, T3, 2, floor_x1=5)
    tier_windows(s, c1, DECK + 2, skip=((12, 0),))
    tier_windows(s, c2, T1 + 2, skip=((0, 0), (8, 0)))
    tier_windows(s, c3, T2 + 2)
    # doors: main deck -> captain's cabin, quarterdeck -> barracks, barracks -> stern balcony
    s.set(12, DECK + 1, CZ, door("minecraft:birch_door", "east", "lower"))
    s.set(12, DECK + 2, CZ, door("minecraft:birch_door", "east", "upper"))
    s.set(8, T1 + 1, CZ, door("minecraft:birch_door", "east", "lower"))
    s.set(8, T1 + 2, CZ, door("minecraft:birch_door", "east", "upper"))
    s.set(0, T1 + 1, CZ, door("minecraft:birch_door", "west", "lower"))
    s.set(0, T1 + 2, CZ, door("minecraft:birch_door", "west", "upper"))
    # ladders up through the tiers along the stern wall (hatches in each roof) to the bridge
    for y in range(DECK + 1, T3 + 1):
        s.set(1, y, 1, ladder("east"))
    # quarterdeck strip (x 9..12 on the tier-1 roof): rails, stairs down to the main deck on the starboard side
    for x in range(9, 13):
        for side in (-1, 1):
            s.set(x, T1 + 1, side * zedge(x), BRAIL)
    for z in range(-zedge(12) + 1, zedge(12)):
        if z != 5:
            s.set(12, T1 + 1, z, BRAIL)
    s.stairs_run(16, DECK + 1, 5, 3, BIRCH_STAIRS, "west")
    s.set(13, T1, 5, BIRCH)
    for i, x in enumerate((15, 14, 13)):
        for y in range(DECK + 1, DECK + 2 + i):
            s.set(x, y, 5, WHITE)
    s.lamp(12, T1 + 1, -zedge(12))
    s.lamp(12, T1 + 1, zedge(12))
    s.lamp(12, DECK + 3, -3)
    s.lamp(12, DECK + 3, 3)
    # stern balcony behind the barracks
    for z in range(-3, 4):
        s.set(-1, T1, z, BIRCH)
        s.set(-2, T1, z, BIRCH)
        s.set(-2, T1 + 1, z, BRAIL)
    s.set(-1, T1 + 1, -3, BRAIL)
    s.set(-1, T1 + 1, 3, BRAIL)
    s.lamp(-2, T1 + 2, -3)
    s.lamp(-2, T1 + 2, 3)
    # the bridge on the tier-3 roof: rail, the Ship's Wheel, a blue canopy on birch posts
    for x in sorted(c3):
        zs = c3[x]
        for z in zs:
            if (z - 1 not in zs) or (z + 1 not in zs) or x == 0 or x == 5:
                s.set(x, T3 + 1, z, BRAIL)
    s.set(1, T3 + 1, 1, AIR)                                   # the ladder arrives here
    s.set(4, T3 + 1, CZ, AIR)
    s.set(5, T3 + 1, CZ, AIR)
    s.helm(4, T3 + 1, CZ)
    for (x, z) in ((0, -2), (0, 2), (5, -2), (5, 2)):
        for y in range(T3 + 1, T3 + 4):
            s.set(x, y, z, BRAIL)
    s.box(0, T3 + 4, -2, 5, T3 + 4, 2, BLUE)
    s.lamp(2, T3 + 3, -2, hanging=True)
    s.lamp(2, T3 + 3, 2, hanging=True)
    # cabins: captain (tier 1), barracks (tier 2), chart room (tier 3)
    I.furnish(s, 1, DECK + 1, -5, 11, 5, 3, "captain", "marine", seed=11)
    s.chest(3, DECK + 1, -3, "hard", facing="east")
    I.furnish(s, 1, T1 + 1, -4, 7, 4, 3, "barracks", "marine", seed=13)
    # the chart room on tier 3, furnished by hand (the furnisher's book walls cost too many blocks here)
    s.set(3, T2 + 1, -2, "onepiece:navigators_desk[facing=south]")
    s.set(4, T2 + 1, -2, "minecraft:cartography_table")
    s.set(2, T2 + 1, -2, "minecraft:lectern[facing=south,has_book=false,powered=false]")
    s.set(4, T2 + 1, 2, "minecraft:bookshelf")
    s.set(3, T2 + 1, 2, "minecraft:bookshelf")
    s.lamp(3, T3 - 1, CZ, hanging=True)
    one_helm(s)
    for p, b in list(s.blocks.items()):                        # rugs and tall shelf walls cost blocks the budget needs
        if b.endswith("_carpet") or b.startswith("minecraft:decorated_pot") or \
                (p[0] in (1, 11) and DECK + 1 < p[1] < T1 and "bookshelf" in b):
            s.set(p[0], p[1], p[2], AIR)
    for y in range(DECK + 1, T3 + 1):                          # the furnishers must not block the ladder
        s.set(1, y, 1, ladder("east"))
    s.set(1, T3 + 1, 1, AIR)

    # ---- masts (birch), sails, yards, rigging, flags
    def mast(x, y0, top):
        for y in range(y0, top + 1):
            s.set(x, y, CZ, log("birch"))
        return top
    FORE_TOP, MAIN_TOP, MIZZEN_TOP = DECK + 26, DECK + 31, DECK + 22     # main > fore > mizzen
    # foremast: gull course set high (its foot clears the MARINE word on the mainsail behind it) + a plain topsail
    mast(FORE_X, DECK, FORE_TOP)
    s.square_sail(FORE_X + 1, CZ, DECK + 11, DECK + 18, 10, WOOL_W, belly=1, yard="birch",
                  bitmap=gull_sail(10, DECK + 11, DECK + 18))
    s.square_sail(FORE_X + 1, CZ, DECK + 20, DECK + 23, 3, WOOL_W, belly=1, yard="birch")
    s.flag(FORE_X, FORE_TOP + 1, CZ, SMALL_FLAG)
    # mainmast: MARINE sail + topsail, crow's nest
    mast(MAIN_X, DECK, MAIN_TOP)
    s.square_sail(MAIN_X + 1, CZ, DECK + 6, DECK + 18, 12, WOOL_W, belly=1, yard="birch",
                  bitmap=marine_sail(12, DECK + 6, DECK + 18))
    s.square_sail(MAIN_X + 1, CZ, DECK + 21, DECK + 24, 4, WOOL_W, belly=1, yard="birch")
    s.crows_nest(MAIN_X, DECK + 27, CZ, 1.5, "birch")
    s.flag(MAIN_X, MAIN_TOP + 1, CZ, MARINE_FLAG)
    # mizzen on the quarterdeck: gull sail
    mast(MIZZEN_X, DECK + 1, MIZZEN_TOP)
    s.square_sail(MIZZEN_X + 1, CZ, DECK + 11, DECK + 17, 9, WOOL_W, belly=1, yard="birch",
                  bitmap=gull_sail(9, DECK + 11, DECK + 17))
    s.square_sail(MIZZEN_X + 1, CZ, DECK + 19, DECK + 21, 3, WOOL_W, belly=1, yard="birch")
    s.flag(MIZZEN_X, MIZZEN_TOP + 1, CZ, SMALL_FLAG)
    # shrouds, one block abaft each mast so they miss the sails, down to the rails; stays between the mast heads
    # fore shrouds: out from the masthead behind the fore course, then straight down the gap between MAR and the
    # head at z +-5 to the rail, so from the bow they don't cross the MARINE word on the mainsail
    for side in (-1, 1):
        s.rope((FORE_X - 1, DECK + 17, CZ), (FORE_X - 1, DECK + 12, side * 5))
        s.rope((FORE_X - 1, DECK + 11, side * 5), (FORE_X - 2, DECK + 2, side * zedge(FORE_X - 2)))
    for (mx, my, ry, dxs) in ((MAIN_X, DECK + 16, DECK + 2, (-1,)),
                              (MIZZEN_X, DECK + 19, T1 + 1, (-1,))):
        for dx in dxs:
            for side in (-1, 1):
                s.rope((mx - 1, my, CZ), (mx - 1 + dx, ry, side * zedge(mx - 1 + dx)))
    s.rope((MAIN_X, MAIN_TOP, CZ), (FORE_X, FORE_TOP, CZ))
    s.rope((MIZZEN_X, MIZZEN_TOP, CZ), (MAIN_X, MAIN_TOP, CZ))
    s.lamp(MAIN_X + 1, DECK + 2, CZ)
    s.lamp(FORE_X + 1, DECK + 2, CZ)

    # ---- the figurehead: a white seagull on a raked cutwater, wings swept back along the bow
    # the cutwater: a solid white stem on the centre line, raked forward as it rises (blue band, light-blue trim)
    stem_dy = s.deck_y(X1)
    for y in range(0, DECK + 2):
        cx = X1 + 1 + y // 3
        mat = BLUE if y in (stem_dy - 1, stem_dy - 2) else LIGHT_BLUE if y == 1 else GRAY if y <= 0 else WHITE
        s.line((X1, y, CZ), (cx, y, CZ), mat)
    # breast and back along the stem head
    s.blob(X1 + 1.0, DECK + 3.5, CZ, 2.5, 1.8, 1.8, WHITE, power=2.2)
    # head: a rounded 4 x 4 x 3 lump in front of and above the breast (narrow, so MARINE reads past it)
    hx = X1 + 2
    s.blob(hx + 1.5, DECK + 6.5, CZ, 2.3, 2.0, 1.9, WHITE, power=2.6)
    s.box(hx, DECK + 5, -1, hx + 1, DECK + 5, 1, WHITE)        # the neck under the back of the head
    # eyes at the front corners (seen from the front and from the side)
    for z in (-1, 1):
        s.set(hx + 3, DECK + 7, z, BLACK)
    # the hooked beak: upper mandible 3 long curving down at the tip, short lower jaw, red spot between,
    # a 3-wide root that tapers to the 1-wide hook seen from the front
    for x in range(hx + 4, hx + 7):
        s.set(x, DECK + 6, CZ, YELLOW)
    s.set(hx + 6, DECK + 5, CZ, YELLOW)
    s.set(hx + 4, DECK + 5, CZ, YELLOW)
    s.set(hx + 5, DECK + 5, CZ, CONCRETE["red"])
    for z in (-1, 1):
        s.set(hx + 4, DECK + 5, z, YELLOW)
        s.set(hx + 4, DECK + 6, z, YELLOW)
    # wings: one clean plane of feathers against the outside of each bulwark, the trailing edge stepping down
    # toward the stern; light-grey quills on the lower and trailing edges
    EDGE = CONCRETE["light_gray"]
    W0, W1 = X1 - 6, X1

    def wing_top(x):
        return DECK + 6 - (W1 - x) // 2 if W0 <= x <= W1 else DECK
    for x in range(W0, W1 + 1):
        yb = wing_top(x) - DECK
        ze = zedge(x)
        for y in range(DECK + 1, DECK + yb + 1):
            trailing = y > wing_top(x - 1)
            mat = EDGE if (y == DECK + 1 or trailing) else WHITE
            s.set(x, y, ze + 1, mat)
            s.set(x, y, -(ze + 1), mat)

    loose, unsupported = loose_blocks(s)
    if unsupported:
        brace_skin(s, unsupported)
        loose, unsupported = loose_blocks(s)
    if loose:
        print(f"  !! {len(loose)} loose blocks, e.g. {loose[:16]}")
    if unsupported:
        print(f"  !! {len(unsupported)} blocks without a face neighbour, e.g. {unsupported[:16]}")
    return s

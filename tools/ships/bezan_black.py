"""Bezan Black: Captain Kuro's ship, the Black Cat Pirates' raider from Syrup Village (enemy, tier 1).

A black ship with a cat's head. Black hull (black concrete with dark oak courses) with a purple wale, a dark spruce
deck, a one-storey stern castle with the Ship's Wheel on its roof, two masts with black sails carrying the Black Cat
Jolly Roger and black cat flags, three cannons a side, a hold with "medium" loot, and a big black cat head on the stem
with pointed ears, yellow eyes, white whiskers and fangs.

Layout (+x is the bow, CZ = 0, main deck at y 4, the sheer lifts the bow deck to y 6):
  x -1       rudder under the flat transom
  x  0..7    stern castle: Kuro's cabin (door at x 7), roof y 8 = the poop deck with the Ship's Wheel at x 7
  x  8..26   main deck: mainmast x 14 (yard y 19, top y 23), foremast x 24 two lower (yard y 17, top y 20),
             hatch + ladder down to the hold at (9, 3), cannons at x 11/17/22
  x 27..31   bow: anchor to port; the cat head sits on the stem (x 31), head x 32..36 with the muzzle at x 37,
             ears to y 16, the forestay runs from the foremast head down to the cat's crown
  inside:    the hold (floor y 0, x 8..23) with the loot chests and barrels
Rigging: the shrouds run from just above each yard aft to the rails, so no rope crosses a sail; build() asserts
that no fence sits on either sail and drops any block not joined face to face to the hull.
"""
from shipkit import *  # noqa: F401,F403

CZ = 0
X0, LEN = 0, 32
X1 = X0 + LEN - 1                 # 31 = the stem
BEAM = 11                         # half width 5 -> deck z -5..5, 9 blocks of open deck between the bulwarks
KEEL, DECK = -3, 4
HOLD = 0                          # floor of the hold
POOP = DECK + 4                   # roof of the stern castle = the poop deck floor (y 8)
CASTLE_X1 = 7
MAIN_X, FORE_X = 14, 24
HATCH_X = 9
CUTS = (DECK, DECK + 1, HOLD + 1)   # the deck, the deck with its gear, the hold

BLACK = CONCRETE["black"]
DARK = "minecraft:dark_oak_planks"
SPRUCE = "minecraft:spruce_planks"
PURPLE = TERRACOTTA["purple"]
PURPLE_W = WOOL["purple"]
YELLOW = CONCRETE["yellow"]
WHITE = CONCRETE["white"]
GREY = CONCRETE["gray"]
PINK = TERRACOTTA["pink"]
BLACK_W = WOOL["black"]
WHITE_W = WOOL["white"]
RAIL = fence("dark_oak")
BARREL = "minecraft:barrel[facing=up,open=false]"
SAKE = "onepiece:sake_barrel[axis=y]"
WINDOW = pane("purple")
MAST_WOOD = "dark_oak"

# The Black Cat Jolly Roger redrawn 15 wide x 9 tall so it maps 1:1 onto the 15-wide, 9-tall mainsail
# (the kit's BLACK_CAT is 16 wide): cat skull with pointed ears, black eyes, a nose, teeth and crossbones, white on black.
SAIL_ROWS = [
    "W.WW.......WW.W",
    ".WWWW.....WWWW.",
    "..WWWWWWWWWWW..",
    "...WKKWWWKKW...",
    "...WKKWWWKKW...",
    "..WWWWWWWWWWW..",
    "..W.WWWKWWW.W..",
    ".W..WKWKWKW..W.",
    "W....WWWWW....W",
]


def framed(rows, pad=1, vpad=None):
    """The bitmap with `pad` columns (and `vpad` rows, default = pad) of plain sail round it, so the emblem has a
    border of sail colour."""
    vpad = pad if vpad is None else vpad
    w = max(len(r) for r in rows) + 2 * pad
    return ["." * w] * vpad + ["." * pad + r + "." * pad for r in rows] + ["." * w] * vpad


SAIL_MARK = (framed(SAIL_ROWS), {"W": WHITE_W, "K": BLACK_W})      # 17 x 11

# An 11 x 8 cat skull for the flags and the foresail.
FLAG_ROWS = [
    "W.W.....W.W",
    ".WWW...WWW.",
    "..WWWWWWW..",
    "..WKKWKKW..",
    "..WWWWWWW..",
    ".W.WWKWW.W.",
    "W..WKWKW..W",
    "....WWW....",
]
CAT_FLAG = (FLAG_ROWS, {"W": WHITE_W, "K": BLACK_W})
FORE_MARK = (framed(FLAG_ROWS, pad=1, vpad=0), {"W": WHITE_W, "K": BLACK_W})   # 13 x 8: maps 1:1 on the 13 x 8 foresail
BLACK_FLAG = (["K" * 11] * 8, {"K": BLACK_W})
SMALL_FLAG_ROWS = [
    "W.W.W.W",
    ".WWWWW.",
    ".WKWKW.",
    ".WWWWW.",
    "..WKW..",
]
SMALL_FLAG = (SMALL_FLAG_ROWS, {"W": WHITE_W, "K": BLACK_W})
SMALL_BLACK = (["K" * 7] * 5, {"K": BLACK_W})


N6 = ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))


def solid_shell(cx, cy, cz, rx, ry, rz, power):
    """The blocks of a hollow superellipsoid whose shell is joined face to face: the kit's hollow blob only touches
    diagonally in places, so this adds the fewest inner blocks that bridge the pieces into one."""
    def ins(x, y, z):
        return abs((x - cx) / rx) ** power + abs((y - cy) / ry) ** power + abs((z - cz) / rz) ** power <= 1.0
    pts = [(x, y, z) for x in range(int(cx - rx) - 1, int(cx + rx) + 2) for y in range(int(cy - ry) - 1, int(cy + ry) + 2)
           for z in range(int(cz - rz) - 1, int(cz + rz) + 2) if ins(x, y, z)]
    shell = {q for q in pts if not all(ins(q[0] + d[0], q[1] + d[1], q[2] + d[2]) for d in N6)}
    inner = [q for q in pts if q not in shell]

    def components(cells):
        comp, k = {}, 0
        for c in cells:
            if c in comp:
                continue
            stack = [c]
            comp[c] = k
            while stack:
                q = stack.pop()
                for d in N6:
                    n = (q[0] + d[0], q[1] + d[1], q[2] + d[2])
                    if n in cells and n not in comp:
                        comp[n] = k
                        stack.append(n)
            k += 1
        return comp, k
    while True:
        comp, k = components(shell)
        if k <= 1:
            return shell
        best, score = None, 1
        for q in inner:
            if q in shell:
                continue
            ids = {comp[n] for n in ((q[0] + d[0], q[1] + d[1], q[2] + d[2]) for d in N6) if n in comp}
            if len(ids) > score:
                best, score = q, len(ids)
        if best is None:
            return shell
        shell.add(best)


def stair_rope(s, p0, p1, mat=None):
    """A rope that steps one axis at a time, so every block touches the next by a face (no diagonal-only links)."""
    x, y, z = p0
    mat = mat or fence("dark_oak")
    s.set(x, y, z, mat)
    while (x, y, z) != tuple(p1):
        dx, dy, dz = p1[0] - x, p1[1] - y, p1[2] - z
        ax = max((abs(dx), 0), (abs(dy), 1), (abs(dz), 2))[1]
        if ax == 0:
            x += 1 if dx > 0 else -1
        elif ax == 1:
            y += 1 if dy > 0 else -1
        else:
            z += 1 if dz > 0 else -1
        s.set(x, y, z, mat)


def face_rope(s, p0, p1, mat=None):
    """A straight rope (like s.rope) whose blocks all touch face to face: every diagonal step of the line gets the
    in-between blocks. It only fills empty cells, so it never cuts through a sail, a lamp or the rail."""
    mat = mat or fence("dark_oak")
    (x0, y0, z0), (x1, y1, z1) = p0, p1
    n = max(abs(x1 - x0), abs(y1 - y0), abs(z1 - z0))
    pts = [(round(x0 + (x1 - x0) * i / max(1, n)), round(y0 + (y1 - y0) * i / max(1, n)), round(z0 + (z1 - z0) * i / max(1, n)))
           for i in range(n + 1)]
    path = [pts[0]]
    for q in pts[1:]:
        cur = list(path[-1])
        for ax in (1, 2, 0):                 # drop / spread first, then step fore-and-aft
            if cur[ax] != q[ax]:
                cur[ax] = q[ax]
                path.append(tuple(cur))
    for (x, y, z) in path:
        if s.get(x, y, z) in (None, AIR):
            s.set(x, y, z, mat)


def sail_cells(x, y0, y1, half):
    """Every cell a square sail at x (belly 1) can occupy, mast column excluded."""
    return [(xx, y, z) for xx in (x, x + 1) for y in range(y0, y1 + 1) for z in range(CZ - half, CZ + half + 1) if z != CZ]


def drop_strays(s):
    """6-neighbour flood fill from the hull: any other piece would float, so it is removed (and reported)."""
    cells = {p for p, v in s.blocks.items() if v != AIR}
    start = min(cells, key=lambda p: (p[1], p[0], p[2]))   # a keel block
    seen, stack = {start}, [start]
    while stack:
        q = stack.pop()
        for d in N6:
            n = (q[0] + d[0], q[1] + d[1], q[2] + d[2])
            if n in cells and n not in seen:
                seen.add(n)
                stack.append(n)
    strays = cells - seen
    if strays:
        print(f"  bezan_black: removed {len(strays)} floating blocks: {sorted(strays)}")
        for p in strays:
            s.set(*p, AIR)
    return strays


def hull_paint(x, y, z, kind):
    """Black sides with a dark oak course, dark wood under water, black bulwark; the purple wale is painted after."""
    if kind == "bulwark":
        return BLACK
    if kind in ("side", "bow", "stern"):
        if y <= 0:
            return DARK
        return DARK if y == 2 else BLACK
    return None


def build():
    s = Ship("bezan_black", "Bezan Black", faction="pirate", tiers=[1], crew="Black Cat Pirates")

    # ------------------------------------------------------------------ hull
    s.hull(x0=X0, length=LEN, cz=CZ, beam=BEAM, keel_y=KEEL, deck_y=DECK, side=BLACK, bottom=DARK, deck=SPRUCE,
           bow_len=10, stern_len=4, bow="sharp", stern="transom", sheer_bow=2, sheer_stern=0,
           fullness=0.6, flat=0.35, bulwark=1, bulwark_mat=BLACK, rail=RAIL, paint=hull_paint,
           inner_decks=[(HOLD, SPRUCE)])
    inside = s._inside

    def footprint(x):
        return [z for z in range(CZ - 7, CZ + 8) if inside(x, DECK, z)]

    def is_edge(x, z):
        return not (inside(x, DECK, z + 1) and inside(x, DECK, z - 1) and inside(x + 1, DECK, z) and inside(x - 1, DECK, z))

    def edge_z(x):
        """z of the bulwark on the starboard side at x (the port side is -edge_z)."""
        return s.halfwidth(x, DECK)

    # the purple wale all the way round: the course just under the deck edge, bow and transom included
    for x in range(X0, X1 + 1):
        dy = s.deck_y(x)
        for z in range(-7, 8):
            if s.get(x, dy - 1, z) not in (BLACK, DARK):
                continue
            if not all(inside(x + d[0], dy - 1, z + d[1]) for d in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                s.set(x, dy - 1, z, PURPLE)
    # the hollowed skin only touches diagonally where the bottom steps up toward the bow and stern: fill the step corners
    steps = [(x, y, z) for x in range(X0, X1 + 1) for y in range(KEEL, 1) for z in range(-6, 7)
             if inside(x, y, z) and s.get(x, y, z) == AIR and s.get(x, y - 1, z) not in (None, AIR)
             and (s.get(x + 1, y, z) not in (None, AIR) or s.get(x - 1, y, z) not in (None, AIR))]
    for (x, y, z) in steps:
        s.set(x, y, z, DARK)
    # the hold floor only where the hold is used (x 8..23, under the main deck): under the cabin and the bow it is
    # sealed off and never seen, so it is left out to keep the budget for the figurehead and the rigging
    for x in list(range(X0, HATCH_X - 1)) + list(range(FORE_X, X1 + 1)):
        for z in range(-7, 8):
            if s.get(x, HOLD, z) == SPRUCE:
                s.set(x, HOLD, z, AIR)
    # rudder hanging off the transom, down under the water
    for y in range(KEEL + 1, DECK + 1):
        s.set(X0 - 1, y, CZ, DARK)

    # ------------------------------------------------------------------ stern castle (Kuro's cabin) + poop deck
    for x in range(X0, CASTLE_X1 + 1):
        for z in footprint(x):
            if is_edge(x, z) or x == CASTLE_X1:
                for y in range(DECK + 1, POOP):
                    s.set(x, y, z, BLACK if y < POOP - 1 else PURPLE)     # purple band under the roof edge
                s.set(x, POOP, z, DARK)                                  # dark roof trim
                s.set(x, POOP + 1, z, RAIL)                              # rail round the poop deck
            else:
                s.set(x, POOP, z, SPRUCE)                                # roof = poop deck floor
    # windows: transom and the sides of the cabin
    for z in (-2, 2):
        s.set(X0, DECK + 2, z, WINDOW)
    for x in (2, 5):
        hw = edge_z(x)
        s.set(x, DECK + 2, hw, WINDOW)
        s.set(x, DECK + 2, -hw, WINDOW)
    # cabin door onto the main deck
    s.set(CASTLE_X1, DECK + 1, CZ, AIR)
    s.set(CASTLE_X1, DECK + 2, CZ, AIR)
    I.furnish(s, X0 + 1, DECK + 1, -3, CASTLE_X1 - 1, 3, 3, "captain", "pirate", seed=7)
    s.set(CASTLE_X1, DECK + 1, CZ, door("minecraft:dark_oak_door", "west", "lower"))
    s.set(CASTLE_X1, DECK + 2, CZ, door("minecraft:dark_oak_door", "west", "upper"))
    s.lamp(CASTLE_X1 + 1, POOP - 1, CZ, hanging=True)
    # ladder up the front wall of the castle to the poop deck (port side)
    s.ladder_up(CASTLE_X1 + 1, -3, DECK + 1, POOP, facing="east")
    s.set(CASTLE_X1, POOP + 1, -3, AIR)                      # gap in the front rail where the ladder arrives
    # the Ship's Wheel at the front edge of the poop deck, facing the bow
    s.set(CASTLE_X1, POOP + 1, CZ, AIR)
    s.helm(CASTLE_X1, POOP + 1, CZ)
    s.lamp(CASTLE_X1, POOP + 2, -4)
    s.lamp(CASTLE_X1, POOP + 2, 4)
    s.lamp(X0, POOP + 2, -3)
    s.lamp(X0, POOP + 2, 3)
    s.set(2, POOP + 1, 2, BARREL)
    s.set(2, POOP + 1, 3, SAKE)
    s.set(3, POOP + 1, -2, "onepiece:rope_coil[facing=east]")

    # ------------------------------------------------------------------ main deck
    # hatch down to the hold beside the castle; the ladder leans on the cabin's front wall
    s.open_hatch(HATCH_X, DECK, 3, w=1, ladder_facing="east", down_to=HOLD + 1)
    for y in range(HOLD + 1, DECK):
        s.set(HATCH_X - 1, y, 3, DARK)                       # post the ladder hangs on
    # three cannons a side, open embrasures in the bulwark
    s.broadside([11, 17, 22], DECK + 1, CZ, edge_z, gunport=AIR)
    s.set(12, DECK + 1, -3, BARREL)
    s.set(16, DECK + 1, 3, SAKE)
    s.set(18, DECK + 1, 3, BARREL)
    s.set(21, DECK + 1, -3, "onepiece:rope_coil[facing=north]")
    for x in (11, 17, 22):
        s.lamp(x - 1, DECK + 3, edge_z(x - 1))
        s.lamp(x - 1, DECK + 3, -edge_z(x - 1))

    # ------------------------------------------------------------------ masts, sails, flags, rigging
    # mainmast: a 17 x 11 black mainsail with the cat mark mapped 1:1, the big cat flag on top
    sail_y0, sail_y1 = DECK + 4, DECK + 14                       # y 8..18, 17 wide: the framed mark maps 1:1
    s.square_sail(MAIN_X, CZ, sail_y0, sail_y1, 8, BLACK_W, belly=1, yard=MAST_WOOD, bitmap=SAIL_MARK)
    yard_y = sail_y1 + 1                                         # 19
    top = s.mast(MAIN_X, CZ, DECK + 1, yard_y + 4 - DECK, wood=MAST_WOOD)   # y 5..23
    s.flag(MAIN_X, top + 1, CZ, BLACK_FLAG, w=11, h=8)
    s.flag(MAIN_X, top + 1, CZ, CAT_FLAG, w=11, h=8)
    s.lamp(MAIN_X, yard_y - 1, 9, hanging=True)
    s.lamp(MAIN_X, yard_y - 1, -9, hanging=True)
    # foremast: 2 lower than the main (yard y 17 vs 19, top y 20 vs 23), a 13 x 8 black foresail with the cat skull
    fy0, fy1 = DECK + 5, DECK + 12                               # y 9..16, 13 wide: FORE_MARK maps 1:1
    s.square_sail(FORE_X, CZ, fy0, fy1, 6, BLACK_W, belly=1, yard=MAST_WOOD, bitmap=FORE_MARK)
    fyard = fy1 + 1                                              # 17
    fdeck = s.deck_y(FORE_X)
    ftop = s.mast(FORE_X, CZ, fdeck + 1, fyard + 3 - fdeck, wood=MAST_WOOD)
    s.flag(FORE_X, ftop + 1, CZ, SMALL_BLACK, w=7, h=5)
    s.flag(FORE_X, ftop + 1, CZ, SMALL_FLAG, w=7, h=5)
    # shrouds: from just above each yard, behind the mast, aft and down to the rails, so no rope crosses a sail
    # (the sails fill x MAST..MAST+1); face_rope only fills empty cells and joins every step face to face
    for side in (-1, 1):
        face_rope(s, (MAIN_X - 1, yard_y + 1, CZ), (MAIN_X - 3, DECK + 2, side * edge_z(MAIN_X - 3)))
        face_rope(s, (FORE_X - 1, fyard + 1, CZ), (FORE_X - 3, fdeck + 2, side * edge_z(FORE_X - 3)))
    MAIN_SAIL = sail_cells(MAIN_X, sail_y0, sail_y1, 8)
    FORE_SAIL = sail_cells(FORE_X, fy0, fy1, 6)

    # ------------------------------------------------------------------ foredeck
    s.anchor(28, s.deck_y(28), -(edge_z(28) + 1), "north")       # hangs on the port bow
    s.set(27, s.deck_y(27) + 1, 2, BARREL)
    s.set(29, s.deck_y(29) + 1, 0, "onepiece:rope_coil[facing=east]")
    for side in (-1, 1):
        s.lamp(27, s.deck_y(27) + 3, side * edge_z(27))          # lanterns on the rail posts

    # ------------------------------------------------------------------ the figurehead: the black cat head
    # A broad, flat-faced black cat head on the stem: 7 tall, 9 wide, pointed ears with pink insides,
    # slanted yellow eyes with black slit pupils, a pink nose, a grey mouth with two white fangs, white whiskers.
    bow_deck = s.deck_y(X1)                                      # 6
    hx, hy = X1 + 3.0, bow_deck + 4.0                            # head centre (34, 10)
    head = set()

    def head_mat(x, y, z):
        head.add((x, y, z))
        return BLACK
    for (x, y, z) in solid_shell(hx, hy, CZ, 2.6, 3.2, 4.3, 3.0):
        s.set(x, y, z, head_mat(x, y, z))
    cap_y = max(y for (x, y, z) in head)
    low_y = min(y for (x, y, z) in head)
    # neck: a solid post from the stem top up to the underside of the head (the head itself stays hollow)
    for x in range(X1 - 1, int(hx)):
        for y in range(bow_deck, low_y + 1):
            for z in (-1, 0, 1):
                if (x, y, z) in head:
                    continue
                if x > X1 or inside(x, DECK, z) or x == X1:
                    cur = s.get(x, y, z)
                    if cur in (None, AIR) or "fence" in (cur or "") or cur == BLACK:
                        s.set(x, y, z, BLACK)

    def face_x(y, z):
        """x of the front of the face at (y, z), or None."""
        xs = [xx for (xx, yy, zz) in head if yy == y and zz == z]
        return max(xs) if xs else None

    def paint_face(y, z, mat):
        fx = face_x(y, z)
        if fx is not None:
            s.set(fx, y, z, mat)
        return fx

    eye_y = int(hy) + 1                                          # 11
    fx0 = face_x(eye_y, CZ)                                      # 36: the flat face plane
    # a flat cat crown: square off the top two rows of the head out to z +-4, behind the face plane
    for y in (cap_y - 1, cap_y):
        for z in (3, 4):
            for x in (int(hx) - 1, int(hx)):
                for side in (-1, 1):
                    if s.get(x, y, side * z) in (None, AIR):
                        s.set(x, y, side * z, BLACK)
                        head.add((x, y, side * z))
    # slope the back of the head: drop the rear top corners and close the hollow behind them
    for z in (-2, 2):
        s.set(int(hx) - 2, cap_y - 1, z, AIR)
        head.discard((int(hx) - 2, cap_y - 1, z))
        if s.get(int(hx) - 1, cap_y - 1, z) in (None, AIR):
            s.set(int(hx) - 1, cap_y - 1, z, BLACK)
    # pointed ears on the outer corners of the crown, set back and leaning back: 3 rows, the top one 1 deep,
    # pink inner ear on the bow side
    ex = int(hx)                                                 # 34
    ear_rows = ((1, (1, 2, 3, 4), (2, 3), (ex - 2, ex - 1)), (2, (2, 3, 4), (3,), (ex - 2, ex - 1)), (3, (4,), (), (ex - 2,)))
    for side in (-1, 1):
        for (dy, zs, pinks, xs) in ear_rows:
            for z in zs:
                for x in xs:
                    front = x == xs[-1] and len(xs) > 1
                    s.set(x, cap_y + dy, side * z, PINK if (front and z in pinks) else BLACK)
    # eyes: slanted almonds, yellow with a black slit pupil
    for side in (-1, 1):
        for (dy, z) in ((1, 2), (1, 3), (0, 1), (0, 3), (-1, 1), (-1, 2)):
            paint_face(eye_y + dy, side * z, YELLOW)
        paint_face(eye_y, side * 2, BLACK)
    # the muzzle: a 3 x 2 snout in front of the face plane, pink nose on top, grey mouth below, fangs under it
    for y in (eye_y - 3, eye_y - 2):
        for z in (-1, 0, 1):
            s.set(fx0 + 1, y, z, BLACK)
    s.set(fx0 + 1, eye_y - 2, CZ, PINK)                          # nose
    for z in (-1, 1):
        s.set(fx0 + 1, eye_y - 3, z, GREY)                       # mouth: a grey "w" across the muzzle ...
        paint_face(eye_y - 3, 2 * z, GREY)                       # ... running out to the cheeks
        s.set(fx0 + 1, eye_y - 4, z, WHITE)                      # fangs hanging under the muzzle
    # whiskers: two thin white whiskers per side with a row of sky between them, fanned up and down
    for side in (-1, 1):
        for (y, dy) in ((eye_y - 2, 1), (eye_y - 4, -1)):        # from the nose row up, from the jaw down
            zmax = max(abs(zz) for (xx, yy, zz) in head if yy == y and zz * side > 0)
            wx = face_x(y, side * zmax)
            for (k, ky) in ((1, 0), (2, 0), (2, dy), (3, dy)):   # 2 level, then a step out to the tip
                s.set(wx, y + ky, side * (zmax + k), WHITE)

    # the forestay: from the foremast head forward over the foresail, then down to the cat's crown
    for x in (FORE_X + 1, FORE_X + 2):
        s.set(x, fyard + 1, CZ, RAIL)
    stair_rope(s, (FORE_X + 3, fyard + 1, CZ), (X1 + 1, cap_y, CZ))

    # ------------------------------------------------------------------ the hold: loot and barrels
    hy0 = HOLD + 1
    s.chest(12, hy0, -3, "medium", facing="south")
    s.chest(13, hy0, -3, "pirate", facing="south")
    s.chest(19, hy0, 3, "medium", facing="north")
    s.set(15, hy0, 3, BARREL)
    s.set(16, hy0, 3, BARREL)
    s.set(17, hy0, 3, SAKE)
    s.set(21, hy0, -3, BARREL)
    s.set(22, hy0, -3, SAKE)
    s.lamp(12, DECK - 1, CZ, hanging=True)
    s.lamp(20, DECK - 1, CZ, hanging=True)

    # ------------------------------------------------------------------ checks
    for name, cells in (("mainsail", MAIN_SAIL), ("foresail", FORE_SAIL)):
        holes = [p for p in cells if "fence" in (s.get(*p) or "")]
        assert not holes, f"rigging cuts the {name}: {holes}"
    drop_strays(s)
    return s

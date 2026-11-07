"""Big Top: Buggy the Clown's ship. A floating circus: a loud mustard-yellow hull with a red wale and blue bulwarks, a
big red-and-white striped circus tent amidships, one mast with Buggy's mark on the sail and an elephant head on the bow.

Layout (x = 0 stern .. 29 bow, z across the ship, CZ = 0, main deck at y 4):
  x 0..6    stern castle: Buggy's cabin (door at x 6), the poop deck on its roof (y 8) with the Ship's Wheel at the
            front edge, Richie's cage and barrels.
  x 7..20   main deck: the big top (centre x 14, 11 across at the wall, 13 at the eave, wall y 5-8, peak y 17) with the ring, the
            Buggy Ball cannon and loot inside; cannons at x 8 and x 20 on both sides; hatch down to the hold at (7, 3).
  x 21..29  foredeck (the sheer lifts it to y 5-6): the mast at x 22 with the sail, the anchor, and the elephant head
            on top of the stem (x 29..36) with the trunk curling down to the water.
"""
import math
from shipkit import *  # noqa: F401,F403

CUTS = (5,)       # one cut just above the main deck: shows the ring inside the tent and the deck layout

CZ = 0
X0, LEN = 0, 30
X1 = X0 + LEN - 1                 # 29 = the stem
BEAM = 13                         # half width 6 -> deck z -6..6, 11 blocks of open deck between the bulwarks
KEEL, DECK = -3, 4
POOP = DECK + 4                   # roof of the castle = floor of the poop deck (y 8)
TENT_X = 14                       # centre of the big top
TENT_R = 5.0                      # radius of the striped wall (11 across)
EAVE_R = 6.2                      # radius of the eave / foot of the cone (13 across)
TENT_WALL_Y0, TENT_WALL_Y1 = DECK + 1, DECK + 4     # striped wall y 5..8: stands a course clear of the rail
EAVE_Y = DECK + 5                                   # the yellow scalloped eave at y 9, the cone rises from there
CONE_H = 8                                          # eave -> peak (y 17, under the yard at y 18)
SECTORS = 8                                         # 4 red + 4 white stripes round the tent
MAST_X = 22
CASTLE_X1 = 6

YELLOW = TERRACOTTA["yellow"]
RED = CONCRETE["red"]
BLUE = CONCRETE["blue"]
WHITE = CONCRETE["white"]
BLACK = CONCRETE["black"]
DARK = "minecraft:dark_oak_planks"
OAK = "minecraft:oak_planks"
SPRUCE = "minecraft:spruce_planks"
RED_W = WOOL["red"]
WHITE_W = WOOL["white"]
YELLOW_W = WOOL["yellow"]
GREY = CONCRETE["light_gray"]
DGREY = CONCRETE["gray"]
RAIL = fence("oak")
BARREL = "minecraft:barrel[facing=up,open=false]"
SAKE = "onepiece:sake_barrel[axis=y]"
BARS = "minecraft:iron_bars[east=false,north=false,south=false,waterlogged=false,west=false]"
WINDOW = pane("light_blue")
POLE = log("spruce")

# Buggy's mark redrawn 15 wide x 10 tall so it maps 1:1 onto the 15-wide sail (the kit's BUGGY is 16 wide).
SAIL_ROWS = [
    "...RWRWRWRWR...",
    "...WWWWWWWWW...",
    "W..WWWWWWWWW..W",
    ".W.WKKWWWKKW.W.",
    "..WWKKWWWKKWW..",
    "...WWWRRRWWW...",
    "...WWWRRRWWW...",
    "..W.WWWWWWW.W..",
    ".W..WKWKWKW..W.",
    "W....WWWWW....W",
]
SAIL_MARK = (SAIL_ROWS, {"W": WHITE_W, "K": WOOL["black"], "R": RED_W})

# An 11x8 Buggy skull for the flag at the mast head: striped hat, black eyes, big red nose, crossbones, on black.
FLAG_ROWS = [
    "..RRWWRRW..",
    "..WWWWWWW..",
    "W.WKKWKKW.W",
    ".WWKKWKKWW.",
    "..WWRRRWW..",
    ".WWWRRRWWW.",
    "W.WKWKWKW.W",
    "...WWWWW...",
]
BUGGY_FLAG = (FLAG_ROWS, {"W": WHITE_W, "K": WOOL["black"], "R": RED_W})
BLACK_FLAG = (["K" * 11] * 8, {"K": WOOL["black"]})
PENNANT = (["RWR", "WRW"], {"W": WHITE_W, "R": RED_W})


def hull_paint(x, y, z, kind):
    """Mustard yellow sides, blue bulwark, dark wood under water (the red wale is added after, all the way round)."""
    if kind == "bulwark":
        return BLUE
    if kind in ("side", "bow", "stern"):
        return DARK if y <= 0 else YELLOW
    return None


def tent_stripe(x, z):
    """Red or white: vertical stripes round the tent, SECTORS of them."""
    a = math.atan2(z - CZ, x - TENT_X)
    k = int(((a + math.pi) / (2 * math.pi)) * SECTORS) % SECTORS
    return RED_W if k % 2 == 0 else WHITE_W


def build():
    s = Ship("big_top", "Big Top", faction="pirate", tiers=[0, 1], crew="Buggy Pirates")

    # ------------------------------------------------------------------ hull
    s.hull(x0=X0, length=LEN, cz=CZ, beam=BEAM, keel_y=KEEL, deck_y=DECK, side=YELLOW, bottom=DARK, deck=OAK,
           bow_len=9, stern_len=4, bow="sharp", stern="transom", sheer_bow=2, sheer_stern=0,
           fullness=0.6, flat=0.35, bulwark=1, bulwark_mat=BLUE, rail=RAIL, paint=hull_paint)
    inside = s._inside

    def footprint(x):
        return [z for z in range(CZ - 8, CZ + 9) if inside(x, DECK, z)]

    def is_edge(x, z):
        return not (inside(x, DECK, z + 1) and inside(x, DECK, z - 1) and inside(x + 1, DECK, z) and inside(x - 1, DECK, z))

    def edge_z(x):
        """z of the bulwark on the starboard side at x (the port side is -edge_z)."""
        return s.halfwidth(x, DECK)

    # the red wale all the way round: the course just under the deck edge, bow and transom included
    for x in range(X0, X1 + 1):
        dy = s.deck_y(x)
        for z in range(-8, 9):
            if s.get(x, dy - 1, z) == YELLOW:
                s.set(x, dy - 1, z, RED)
    # the hollowed skin only touches diagonally where the bottom steps up toward the bow and stern: fill the step corners
    steps = [(x, y, z) for x in range(X0, X1 + 1) for y in range(KEEL, 1) for z in range(-7, 8)
             if inside(x, y, z) and s.get(x, y, z) == AIR and s.get(x, y - 1, z) not in (None, AIR)
             and (s.get(x + 1, y, z) not in (None, AIR) or s.get(x - 1, y, z) not in (None, AIR))]
    for (x, y, z) in steps:
        s.set(x, y, z, DARK)
    # rudder hanging off the transom, down under the water
    for y in range(KEEL + 1, DECK + 1):
        s.set(X0 - 1, y, CZ, DARK)

    # ------------------------------------------------------------------ stern castle (Buggy's cabin) + poop deck
    for x in range(X0, CASTLE_X1 + 1):
        for z in footprint(x):
            if is_edge(x, z) or x == CASTLE_X1:
                for y in range(DECK + 1, POOP):
                    s.set(x, y, z, YELLOW if y < POOP - 1 else RED)      # red band under the roof edge
                s.set(x, POOP, z, BLUE)                                  # blue roof trim
                s.set(x, POOP + 1, z, RAIL)                              # rail round the poop deck
            else:
                s.set(x, POOP, z, OAK)                                   # roof = poop deck floor
    # windows: transom and the sides of the cabin
    for z in (-2, 2):
        s.set(X0, DECK + 2, z, WINDOW)
    for x in (2, 4):
        hw = edge_z(x)
        s.set(x, DECK + 2, hw, WINDOW)
        s.set(x, DECK + 2, -hw, WINDOW)
    # cabin door onto the main deck with a striped awning over it
    s.set(CASTLE_X1, DECK + 1, CZ, AIR)
    s.set(CASTLE_X1, DECK + 2, CZ, AIR)
    I.furnish(s, X0 + 1, DECK + 1, -3, CASTLE_X1 - 1, 3, 3, "captain", "pirate", seed=11)
    s.set(CASTLE_X1, DECK + 1, CZ, door("minecraft:oak_door", "west", "lower"))
    s.set(CASTLE_X1, DECK + 2, CZ, door("minecraft:oak_door", "west", "upper"))
    for z in (-1, 0, 1):
        s.set(CASTLE_X1 + 1, POOP, z, RED_W if z else WHITE_W)
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
    # Richie's cage on the poop deck: iron bars with a dark roof, a hay bale inside
    for x in range(1, 4):
        for z in range(-3, 0):
            if x in (1, 3) or z in (-3, -1):
                s.set(x, POOP + 1, z, BARS)
                s.set(x, POOP + 2, z, BARS)
            s.set(x, POOP + 3, z, slab("minecraft:dark_oak_slab", "bottom"))
    s.set(2, POOP + 1, -2, "minecraft:hay_block[axis=y]")
    s.set(2, POOP + 1, 2, BARREL)
    s.set(2, POOP + 1, 3, SAKE)
    s.set(3, POOP + 1, 3, BARREL)

    # ------------------------------------------------------------------ main deck
    # hatch down to the hold beside the castle; the ladder leans on a post against the cabin front
    for y in range(KEEL + 1, DECK):
        s.set(CASTLE_X1, y, 3, OAK)
    s.open_hatch(CASTLE_X1 + 1, DECK, 3, w=1, ladder_facing="east", down_to=KEEL + 2)
    # cannons fore and aft of the tent on both sides
    s.broadside([8, 20], DECK + 1, CZ, lambda x: 6)
    s.set(8, DECK + 1, -3, BARREL)
    s.set(20, DECK + 1, 3, BARREL)
    s.set(20, DECK + 1, 2, SAKE)
    s.set(9, DECK + 1, 4, "onepiece:rope_coil[facing=north]")
    s.lamp(8, DECK + 2, 6)
    s.lamp(8, DECK + 2, -6)
    s.lamp(20, DECK + 2, 6)
    s.lamp(20, DECK + 2, -6)

    # ------------------------------------------------------------------ the circus tent
    # striped wall, 4 high, 11 across
    for y in range(TENT_WALL_Y0, TENT_WALL_Y1 + 1):
        for x in range(TENT_X - 7, TENT_X + 8):
            for z in range(CZ - 7, CZ + 8):
                d = math.hypot(x - TENT_X, z - CZ)
                if TENT_R - 0.5 <= d <= TENT_R + 0.5:
                    s.set(x, y, z, tent_stripe(x, z))
    # doors front and back, 3 high under a striped lintel
    for z in (-1, 0, 1):
        for y in range(TENT_WALL_Y0, TENT_WALL_Y0 + 3):
            s.set(TENT_X + 5, y, z, AIR)
            s.set(TENT_X - 5, y, z, AIR)
    # the cone: a watertight striped shell from the eave (radius EAVE_R) up to the peak, the eave course yellow,
    # and a yellow scalloped edge hanging under the eave

    def cone_top(d):
        return EAVE_Y + int((EAVE_R - d) * CONE_H / EAVE_R)
    peak_y = cone_top(0)
    # The shell is one stepped layer: each column starts a block above its lowest face neighbour's top (a closed
    # stair-step, like a pyramid roof). Columns are laid outer (low) to inner (high), and a column that would only
    # touch the ones already laid at a corner reaches one block lower, so the whole cone stays joined face to face.
    tops = {}
    for x in range(TENT_X - 7, TENT_X + 8):
        for z in range(CZ - 7, CZ + 8):
            d = math.hypot(x - TENT_X, z - CZ)
            if d <= EAVE_R:
                tops[(x, z)] = cone_top(d)
    laid = set()
    for (x, z) in sorted(tops, key=lambda c: tops[c]):
        top = tops[(x, z)]
        nbrs = [(x + dx, z + dz) for (dx, dz) in ((1, 0), (-1, 0), (0, 1), (0, -1))]
        low = max(EAVE_Y, min(tops.get(n, EAVE_Y - 1) for n in nbrs) + 1)
        if low > EAVE_Y and not any((n[0], y, n[1]) in laid for n in nbrs for y in range(low, top + 1)):
            low -= 1
        for y in range(low, top + 1):
            s.set(x, y, z, YELLOW_W if y == EAVE_Y else tent_stripe(x, z))
            laid.add((x, y, z))
        if math.hypot(x - TENT_X, z - CZ) > EAVE_R - 1 and (x + z) % 2 == 0:
            s.set(x, EAVE_Y - 1, z, YELLOW_W)
    # centre pole from the deck through the peak, with a little pennant on top
    for y in range(DECK + 1, peak_y + 2):
        s.set(TENT_X, y, CZ, POLE)
    s.flag(TENT_X, peak_y + 2, CZ, PENNANT, w=3, h=2)
    # inside: the ring on the floor, the Buggy Ball cannon, loot, lanterns
    s.ring(TENT_X, DECK, CZ, 3, RED_W, axis="y")
    s.cannon(TENT_X + 2, DECK + 1, CZ, "east")
    s.chest(TENT_X - 2, DECK + 1, -3, "treasure", facing="south")
    s.chest(TENT_X - 2, DECK + 1, 3, "pirate", facing="north")
    s.set(TENT_X - 3, DECK + 1, 0, SAKE)
    s.set(TENT_X + 1, DECK + 1, 3, "minecraft:tnt")
    s.set(TENT_X + 1, DECK + 1, -3, RED_W)                 # a Buggy Ball
    for lx in (TENT_X - 2, TENT_X + 2):                    # lanterns hanging from the underside of the cone
        s.lamp(lx, min(y for (x, y, z) in laid if x == lx and z == CZ) - 1, CZ, hanging=True)

    # ------------------------------------------------------------------ mast, sail, flag, rigging
    sail_y0, sail_y1 = DECK + 4, DECK + 13                       # y 8..17, 15 wide: the emblem maps 1:1
    s.square_sail(MAST_X, CZ, sail_y0, sail_y1, 7, WHITE_W, belly=1, yard="spruce", bitmap=SAIL_MARK)
    yard_y = sail_y1 + 1                                         # 18
    top = s.mast(MAST_X, CZ, DECK + 1, yard_y + 4 - DECK, wood="spruce")   # y 5..22
    s.flag(MAST_X, top + 1, CZ, BLACK_FLAG, w=11, h=8)
    s.flag(MAST_X, top + 1, CZ, BUGGY_FLAG, w=11, h=8)
    for side in (-1, 1):                                         # shrouds aft of the sail down to the rails on both sides
        s.rope((MAST_X, yard_y - 1, CZ), (MAST_X - 2, DECK + 2, side * edge_z(MAST_X - 2)))
    s.rope((MAST_X + 1, top, CZ), (X1, DECK + 5, CZ))             # forestay down into the elephant's neck
    s.lamp(MAST_X, yard_y - 1, 8, hanging=True)
    s.lamp(MAST_X, yard_y - 1, -8, hanging=True)

    # ------------------------------------------------------------------ foredeck
    s.anchor(25, s.deck_y(25), -(edge_z(25) + 1), "north")       # hangs on the port bow
    s.set(24, s.deck_y(24) + 1, 2, BARREL)
    s.set(26, s.deck_y(26) + 1, 0, "onepiece:rope_coil[facing=east]")
    for side in (-1, 1):
        s.lamp(26, s.deck_y(26) + 3, side * edge_z(26))          # lanterns on the rail posts

    # ------------------------------------------------------------------ the figurehead: the elephant head
    bow_deck = s.deck_y(X1)                                      # 6
    hx, hy = X1 + 2.5, bow_deck + 3.2                            # head centre (31.5, 9.2)
    band_y = int(hy + 1.8)                                       # red circus headband round the crown (y 11)
    head = set()

    def head_mat(x, y, z):
        head.add((x, y, z))
        return RED if y == band_y else GREY
    s.blob(hx, hy, CZ, 3.0, 3.2, 3.0, head_mat, power=2.4, hollow=True)
    cap_y = max(y for (x, y, z) in head)
    for (x, y, z) in list(head):                                 # the crown is one layer: give it something to sit on
        if y == cap_y and s.get(x, y - 1, z) in (None, AIR):
            s.set(x, y - 1, z, GREY)
    # neck: solid fill between the stem top and the head
    for x in (X1, X1 + 1):
        for y in range(bow_deck, bow_deck + 4):
            for z in (-1, 0, 1):
                if (x, y, z) not in head and (inside(x, DECK, z) or x == X1 + 1):
                    if s.get(x, y, z) in (None, AIR, RAIL, BLUE) or "fence" in (s.get(x, y, z) or ""):
                        s.set(x, y, z, GREY)
    top_y = max(y for (x, y, z) in head)
    eye_y = int(hy + 0.8)                                        # 10
    face_x = max(x for (x, y, z) in head if z == 0 and y == eye_y)   # the front of the face (34)
    # a flat face plate so the face reads 5 wide from the bow (the blob tapers to 3 at the front)
    for y in range(bow_deck + 1, band_y):
        for z in range(-2, 3):
            s.set(face_x, y, z, GREY)
    # a dark edge round the crown so the light head stands out against the white sail behind it
    for y in (cap_y, cap_y - 1):
        row = [(x, z) for (x, yy, z), b in s.blocks.items() if yy == y and b == GREY and x > X1]
        for x in set(x for (x, z) in row):
            zs = [z for (xx, z) in row if xx == x]
            m = max(abs(z) for z in zs)
            for z in zs:
                if abs(z) == m:
                    s.set(x, y, z, DGREY)
    # eyes: two black blocks at the sides of the face, under the headband
    for z in (-2, 2):
        s.set(face_x, eye_y, z, BLACK)
    # ears: big two-tone flaps either side of the head, taller than wide, lobed at the bottom, the outer edge swept back
    for side in (-1, 1):
        s.disc(X1 + 1, hy + 0.3, side * 4.5, 2.9, GREY, axis="x")
        s.disc(X1 + 1, hy + 0.3, side * 4.5, 1.8, DGREY, axis="x")      # the darker inner ear
        s.set(X1 + 1, int(hy) - 3, side * 4, GREY)                       # the hanging lobe
        ey = int(hy + 0.3)                                               # disc centre row (9): the ear is y 7..11, |z| 2..6
        s.set(X1 + 1, ey + 2, side * 6, AIR)                             # round off the top outer corner
        for y in range(ey - 2, ey + 2):                                  # the outer column (|z| 6) sweeps back one x
            s.set(X1 + 1, y, side * 6, AIR)
            s.set(X1, y, side * 6, GREY)
        for y in (ey - 1, ey):                                           # joins the swept edge to the flap
            s.set(X1, y, side * 5, GREY)
        s.set(X1 + 2, int(hy + 0.3), side * 3, GREY)                     # the ear root, so it is 2 thick where it joins
    # tusks: white, out of the cheeks beside the trunk root (well below the eyes), curving up and forward
    for side in (-2, 2):
        cheek_x = max(x for (x, y, z), b in s.blocks.items() if z == side and y == eye_y - 3 and b == GREY and x > X1)
        s.set(cheek_x + 1, eye_y - 3, side, WHITE)
        s.set(cheek_x + 2, eye_y - 3, side, WHITE)
        s.set(cheek_x + 2, eye_y - 2, side, WHITE)
    # trunk: 3 wide at the face, tapering to 2 then 1 as it hangs down, the tip curling forward and up at the water
    ty = eye_y - 3                                               # 7: the root, just under the face
    for z in (-1, 0, 1):
        s.set(face_x, ty, z, GREY)
        s.set(face_x, ty - 1, z, GREY)
        s.set(face_x + 1, ty - 1, z, GREY)
    for y in (ty - 2, ty - 3):                                   # y 5..4: 2 deep
        s.set(face_x + 1, y, CZ, GREY)
        s.set(face_x + 2, y, CZ, GREY)
    for z in (-1, 1):
        s.set(face_x + 1, ty - 2, z, GREY)
    trunk = [(face_x + 2, ty - 4), (face_x + 2, ty - 5), (face_x + 2, ty - 6),   # y 3..1: 1 block
             (face_x + 3, ty - 6), (face_x + 4, ty - 6), (face_x + 4, ty - 5)]   # the tip curls forward and up
    for (x, y) in trunk:
        s.set(x, y, CZ, GREY)
    # a little pom-pom on top of the headband
    s.set(int(hx), top_y + 1, CZ, YELLOW_W)
    s.set(int(hx), top_y + 2, CZ, RED_W)

    # ------------------------------------------------------------------ the hold: loot and barrels down on the keel
    hy0 = KEEL + 1
    s.chest(10, hy0, -2, "pirate", facing="south")
    s.chest(11, hy0, -2, "easy", facing="south")
    s.chest(16, hy0, 2, "medium", facing="north")
    s.set(13, hy0, 2, BARREL)
    s.set(14, hy0, 2, BARREL)
    s.set(15, hy0, 2, SAKE)
    s.set(17, hy0, -2, RED_W)                                    # Buggy Balls stacked in the hold
    s.set(18, hy0, -2, RED_W)
    s.set(17, hy0 + 1, -2, RED_W)
    s.set(19, hy0, 1, "minecraft:tnt")
    s.lamp(10, 3, CZ, hanging=True)
    s.lamp(17, 3, CZ, hanging=True)
    return s

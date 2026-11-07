"""Shells Town: the East Blue Marine base (153rd Branch) once run by Axe-Hand Morgan, and the town below it. A walled
base with the tall white HQ building (MARINE across its top floor, the blue gull over the entrance, pilasters and
blue floor bands) with Morgan's huge stone statue, axe-hand raised, on the roof; the dirt yard inside the walls with
the wooden cross Zoro was tied to, the flagpole and training posts; the barracks, armory and store wings; and the
town around it with Rika's family restaurant, shops and houses. ~88 x 88. Ground = y 0, sea to the east."""
import math, random
from canvas import *
import interiors as I
import townkit as T

SID = "shells_town"
TITLE = "Shells Town Marine Base"
CUTS = [3, 12]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")

N = 88
SEA_X = 78
WHITE = "onepiece:marine_bricks"
BLUE = "minecraft:light_blue_concrete"
DBLUE = "minecraft:blue_concrete"
MAR = I.THEMES["marine"]

# the Marine gull emblem (rows top to bottom), 17 wide
GULL = ("##.............##",
        ".###.........###.",
        "..####.....####..",
        "...#####.#####...",
        ".....#######.....",
        ".......###.......")


def gull(b, xc, ytop, z, s):
    for r, row in enumerate(GULL):
        for c, ch in enumerate(row):
            if ch == "#": b.set(xc - 8 + c, ytop - r, z, s)


def morgan_statue(b, sx, y0, sz):
    """Axe-Hand Morgan in stone, facing south over the yard: a plinth, boots, the Marine coat, the steel jaw and the
    axe that replaces his right hand raised over his head. About 20 blocks tall."""
    ST, DK, IRON = "minecraft:stone", "minecraft:polished_andesite", "minecraft:iron_block"
    b.box(sx - 3, y0, sz - 2, sx + 3, y0 + 1, sz + 2, DK)
    for x in range(sx - 3, sx + 4):
        b.set(x, y0 + 1, sz + 3, stairs("minecraft:polished_andesite_stairs", "north"))
    y = y0 + 2
    for x in (sx - 2, sx - 1, sx + 1, sx + 2):                     # legs and boots
        for z in (sz - 1, sz): b.column(x, z, y, y + 4, ST)
        b.set(x, y, sz + 1, DK)
    b.box(sx - 2, y + 5, sz - 1, sx + 2, y + 5, sz, ST)             # hips
    b.box(sx - 3, y + 6, sz - 1, sx + 3, y + 10, sz + 1, ST)        # chest under the coat
    b.box(sx - 3, y + 2, sz - 2, sx + 3, y + 10, sz - 2, "minecraft:smooth_stone")  # the coat hanging down the back
    b.box(sx - 4, y + 10, sz - 1, sx + 4, y + 10, sz + 1, ST)       # shoulders
    b.box(sx - 1, y + 11, sz - 1, sx + 1, y + 13, sz + 1, ST)       # head
    for x in range(sx - 1, sx + 2): b.set(x, y + 11, sz + 1, IRON)   # the steel jaw
    b.set(sx - 1, y + 12, sz + 1, DK); b.set(sx + 1, y + 12, sz + 1, DK)  # eyes
    # facing south, his right hand is on the west (-x) side
    b.column(sx + 4, sz, y + 6, y + 9, ST)                          # left arm down by his side
    b.column(sx - 4, sz, y + 11, y + 14, ST)                        # right arm raised...
    b.box(sx - 6, y + 14, sz, sx - 5, y + 18, sz, IRON)             # ...ending in the axe blade
    b.box(sx - 4, y + 15, sz, sx - 4, y + 17, sz, IRON)
    b.set(sx - 7, y + 15, sz, IRON); b.set(sx - 7, y + 16, sz, IRON); b.set(sx - 7, y + 17, sz, IRON)


def build():
    rnd = random.Random(221)
    b = B()
    T.ground(b, N, N, rnd)
    T.sea(b, N, N, lambda x, z: x > SEA_X + 2 * math.sin(z * 0.13))
    # ---------------- the base: walls 39 x 35 round a dirt yard, buttressed outside
    W0, W1, Z0, Z1 = 8, 46, 8, 42
    for x in range(W0, W1 + 1):
        for z in range(Z0, Z1 + 1):
            if x in (W0, W1) or z in (Z0, Z1):
                for y in range(1, 8): b.set(x, y, z, WHITE if y < 7 else "onepiece:marine_tiles")
                if (x + z) % 2 == 0: b.set(x, 8, z, "onepiece:marine_brick_wall")
            else:
                r = (x * 7 + z * 13) % 11
                b.set(x, 0, z, "minecraft:coarse_dirt" if r < 5 else "minecraft:dirt" if r < 8 else "minecraft:gravel")
    for (cells, (ox, oz)) in (([(x, Z0) for x in range(W0, W1 + 1)], (0, -1)), ([(x, Z1) for x in range(W0, W1 + 1)], (0, 1)),
                              ([(W0, z) for z in range(Z0, Z1 + 1)], (-1, 0)), ([(W1, z) for z in range(Z0, Z1 + 1)], (1, 0))):
        for k, (x, z) in enumerate(cells):
            if k % 6 != 0 or (oz == 1 and 22 <= x <= 32): continue
            for y in range(1, 7): b.set(x + ox, y, z + oz, WHITE)
            b.set(x + ox, 7, z + oz, BLUE)
    for x in range(W0, W1 + 1):
        for z in (Z0, Z1): b.set(x, 6, z, BLUE)
    for z in range(Z0, Z1 + 1):
        for x in (W0, W1): b.set(x, 6, z, BLUE)
    for x in range(25, 30):  # gate
        for y in range(1, 6): b.set(x, y, Z1, AIR)
    for x in (24, 30): b.column(x, Z1 + 1, 1, 9, BLUE, cap="minecraft:lantern[hanging=false,waterlogged=false]")
    for x in range(24, 31): b.set(x, 9, Z1, BLUE); b.set(x, 9, Z1 + 1, BLUE)
    # ---------------- the HQ building: 4 floors, 25 x 13
    TX0, TX1, TZ0, TZ1 = 15, 39, 12, 24
    FL = (1, 7, 13, 19)
    top = 25
    CXT = (TX0 + TX1) // 2
    WALL = "minecraft:white_concrete"
    b.walls(TX0, 1, TZ0, TX1, top, TZ1, WALL)
    b.box(TX0 + 1, 1, TZ0 + 1, TX1 - 1, top, TZ1 - 1, AIR)
    for f in FL[1:]: b.box(TX0 + 1, f - 1, TZ0 + 1, TX1 - 1, f - 1, TZ1 - 1, "minecraft:birch_planks")
    b.box(TX0, top, TZ0, TX1, top, TZ1, "onepiece:marine_tiles")
    b.box(TX0 - 1, 0, TZ0 - 1, TX1 + 1, 0, TZ1 + 1, "minecraft:polished_andesite")
    faces = (("south", [(x, TZ1) for x in range(TX0, TX1 + 1)], (0, 1)), ("north", [(x, TZ0) for x in range(TX0, TX1 + 1)], (0, -1)),
             ("west", [(TX0, z) for z in range(TZ0, TZ1 + 1)], (-1, 0)), ("east", [(TX1, z) for z in range(TZ0, TZ1 + 1)], (1, 0)))
    for (f, cells, (ox, oz)) in faces:
        long_face = f in ("south", "north")
        for k, (x, z) in enumerate(cells):
            for yb in (FL[1] - 1, FL[2] - 1, FL[3] - 1, top): b.set(x, yb, z, BLUE)  # blue floor bands and cornice
            b.set(x, top + 1, z, WHITE)
            if k % 2 == 0: b.set(x, top + 2, z, "onepiece:marine_brick_wall")
            if long_face:
                pil = k in (0, 3, len(cells) - 4, len(cells) - 1)
                ph = FL[3] - 1                                       # the top floor is the MARINE band
            else:
                pil = k % 4 == 0
                ph = top - 1
            if pil:
                for y in range(1, ph + 1): b.set(x + ox, y, z + oz, WHITE)
                b.set(x + ox, ph + 1, z + oz, stairs("minecraft:quartz_stairs", OPP[f], "top"))
                continue
            for fi, fy in enumerate(FL):
                if long_face:
                    centre = 4 <= k <= len(cells) - 5
                    if fi == 3: continue
                    if centre and fi > 0: continue                  # the gull panel
                    if centre and fi == 0 and k % 2: continue
                    if not centre and k not in (1, 2, len(cells) - 3, len(cells) - 2): continue
                elif k % 4 != 2: continue
                if f == "south" and fi == 0 and abs(x - CXT) <= 2: continue  # the entrance
                for y in (fy + 1, fy + 2, fy + 3): b.set(x, y, z, pane_of("minecraft:glass_pane"))
                b.set(x + ox, fy, z + oz, stairs("minecraft:quartz_stairs", OPP[f], "top"))
                b.set(x, fy + 4, z, "minecraft:smooth_quartz") if fy + 4 != FL[1] - 1 and fy + 4 not in (12, 18) else None
    # MARINE across the top floor on both long faces, the gull over the entrance and on the back
    b.text(CXT - 11, FL[3] + 1, TZ1, "MARINE", DBLUE, axis="x", step=1)
    b.text(CXT + 11, FL[3] + 1, TZ0, "MARINE", DBLUE, axis="x", step=-1)
    gull(b, CXT, 16, TZ1, DBLUE); gull(b, CXT, 16, TZ0, DBLUE)
    # the entrance: a 3-wide doorway under a blue canopy on two quartz columns
    for x in range(CXT - 1, CXT + 2):
        for y in (1, 2, 3): b.set(x, y, TZ1, AIR)
        b.set(x, 4, TZ1, "minecraft:smooth_quartz")
    for x in (CXT - 3, CXT + 3): b.column(x, TZ1 + 3, 1, 4, "minecraft:quartz_pillar[axis=y]")
    for x in range(CXT - 4, CXT + 5):
        for z in range(TZ1 + 1, TZ1 + 4): b.set(x, 5, z, BLUE)
    # Morgan's statue with his axe hand on the roof
    SX, SZ = CXT, 18
    morgan_statue(b, SX, top + 1, SZ)
    # floors: mess hall + kitchen, barracks, armory + records, captain's office
    SX0 = TX1 - 3
    for f, nf in zip(FL, FL[1:]):
        for i in range(nf - f):
            for w in (0, 1): b.set(SX0 + w, f + i, TZ0 + 1 + i, stairs("minecraft:birch_stairs", "south"))
            for w in (0, 1):
                for k in (1, 2, 3):
                    c = b.get(SX0 + w, f + i + k, TZ0 + 1 + i)
                    if c not in (None, AIR) and "birch_stairs" not in c: b.set(SX0 + w, f + i + k, TZ0 + 1 + i, AIR)
    KEEP = ((SX0 - 1, TZ0 + 1, SX0 + 2, TZ0 + 8), (CXT - 2, TZ1 - 2, CXT + 2, TZ1 - 1))
    I.subdivide(b, TX0 + 1, FL[0], TZ0 + 1, TX1 - 1, TZ1 - 1, 5, "minecraft:white_concrete", ("dining", "kitchen", "armory"), MAR, cell=7, keepout=KEEP, seed=1)
    I.subdivide(b, TX0 + 1, FL[1], TZ0 + 1, TX1 - 1, TZ1 - 1, 5, "minecraft:white_concrete", ("barracks", "barracks", "barracks"), MAR, cell=7, keepout=KEEP[:1], seed=2)
    I.subdivide(b, TX0 + 1, FL[2], TZ0 + 1, TX1 - 1, TZ1 - 1, 5, "minecraft:white_concrete", ("armory", "library", "storage"), MAR, cell=7, keepout=KEEP[:1], seed=3)
    r = I.furnish(b, TX0 + 1, FL[3], TZ0 + 1, TX1 - 1, TZ1 - 1, 5, "captain", MAR)
    # wings inside the walls: barracks (south-west), armory (north-east, behind the HQ), stores (south-east)
    for (x0, z0, x1, z1, kind, dpos) in ((W0 + 1, Z0 + 18, W0 + 9, Z1 - 1, "barracks", (W0 + 9, Z0 + 26, "x")),
                                         (TX1 + 2, Z0 + 1, W1 - 1, TZ1, "armory", (TX1 + 4, TZ1, "z")),
                                         (W1 - 9, Z0 + 18, W1 - 1, Z1 - 1, "storage", (W1 - 9, Z0 + 26, "x"))):
        b.walls(x0, 1, z0, x1, 5, z1, WHITE); b.box(x0 + 1, 1, z0 + 1, x1 - 1, 5, z1 - 1, AIR)
        b.box(x0, 6, z0, x1, 6, z1, "onepiece:marine_tiles")
        for x in range(x0, x1 + 1):
            for z in (z0, z1): b.set(x, 5, z, BLUE)
        for z in range(z0, z1 + 1):
            for x in (x0, x1): b.set(x, 5, z, BLUE)
        dx, dz, ax = dpos
        for y in (1, 2): b.set(dx, y, dz, AIR)
        # windows onto the yard
        if ax == "x":
            for z in range(z0 + 2, z1 - 1, 3):
                if abs(z - dz) > 1: b.set(dx, 2, z, pane_of("minecraft:glass_pane")); b.set(dx, 3, z, pane_of("minecraft:glass_pane"))
        else:
            for x in range(x0 + 2, x1 - 1, 2):
                if x != dx: b.set(x, 2, dz, pane_of("minecraft:glass_pane")); b.set(x, 3, dz, pane_of("minecraft:glass_pane"))
        I.furnish(b, x0 + 1, 1, z0 + 1, x1 - 1, z1 - 1, 4, kind, MAR)
    # the yard: the wooden cross Zoro was tied to, the flagpole with the Marine flag, training posts
    ZX, ZZ = CXT, 34
    b.column(ZX, ZZ, 1, 7, "minecraft:spruce_log[axis=y]", base="minecraft:coarse_dirt")
    for x in range(ZX - 2, ZX + 3):
        if x != ZX: b.set(x, 5, ZZ, "minecraft:spruce_log[axis=x]")
    for (x, y) in ((ZX - 1, 4), (ZX + 1, 4), (ZX, 3)): b.set(x, y, ZZ, fence("spruce")) if x != ZX else None
    for y in range(1, 16): b.set(36, y, 29, "minecraft:white_concrete" if y < 3 else "minecraft:iron_bars[east=false,north=false,south=false,west=false,waterlogged=false]")
    for y in (12, 13, 14):
        for k in range(1, 5): b.set(36 - k, y, 29, BLUE if y == 13 else "minecraft:white_wool")
    for i in range(6): b.set(19, 1, 28 + i * 2, "onepiece:training_post[facing=east]")
    # ---------------- the town outside the base
    spots = [(52, 8, "tavern", "minecraft:red_wool"), (64, 8, None, None), (52, 22, None, None), (64, 22, "kitchen", "minecraft:yellow_wool"),
             (52, 36, None, None), (64, 36, None, None), (8, 52, None, None), (20, 52, "dining", "minecraft:orange_wool"),
             (32, 52, None, None), (44, 52, None, None), (56, 54, "workshop", "minecraft:blue_wool"), (8, 66, None, None),
             (22, 68, None, None), (36, 68, None, None), (50, 70, None, None), (64, 68, None, None)]
    for (x0, z0, kind, sign) in spots:
        w, d = rnd.randint(7, 9), rnd.randint(6, 8)
        floors = 2 if kind else rnd.choice((1, 2))
        T.house(b, x0, z0, w, d, floors, rnd.choice(("plaster", "east_blue", "brick")), rnd, kinds=[kind, "bedroom"] if kind else None,
                door="south" if z0 < 50 else "north", sign=sign)
    T.path(b, [(27, Z1 + 1), (27, 60), (76, 60)], w=1, s="minecraft:stone_bricks", alt="minecraft:cobblestone")
    T.path(b, [(48, 4), (48, 60)], w=1, s="minecraft:stone_bricks", alt="minecraft:cobblestone")
    for z in range(10, 76, 10): T.lamp_post(b, 49, z)
    T.well(b, 70, 50)
    T.pier(b, SEA_X - 2, 40, 12, axis="x")
    T.pier(b, SEA_X - 2, 20, 10, axis="x")
    for (x, z) in ((4, 80), (14, 82), (30, 82), (60, 82), (74, 80)): T.tree(b, x, z)
    # ---------------- people and loot
    b.npc(28, FL[3], 18, "koby", False)
    b.chest(TX0 + 2, FL[3], TZ0 + 2, "marine", "east")
    b.guards("marine_recruit", ((22, 34), (32, 34), (27, Z1 + 3), (12, 20)))
    T.landscape(b, 0, 0, N - 1, N - 1, rnd, amp=4, cell=16, edge=8)  # the open ground rolls (guide 9b.1, 11a); last, so it knows where everything stands
    return b, 0

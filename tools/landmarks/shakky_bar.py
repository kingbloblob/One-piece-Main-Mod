"""Shakky's Rip-off Bar in Grove 13 of the Sabaody Archipelago, the lawless zone: a cosy two-storey timber bar
nestled against the arching roots of a giant Yarukiman mangrove with the grove number 13 painted on its trunk.
The bar has a timber frame with framed, shuttered windows, a deep gable roof with the big SHAKKY'S sign on the
front and BAR on the west gable, and inside the dim bar room with its long counter (bottles and barrels behind,
stools in front, where Rayleigh sits), tables, Rayleigh's room upstairs and the rum cellar below. Outside: the
terrace tables under the roots, bubble lamps, soap bubbles welling up from the roots, a ship coating workshop and
a dock on the mangrove channel. ~72 x 72. Ground = y 0."""
import math, random
from canvas import *
import interiors as I
import townkit as T
import sabaody_kit as S

SID = "shakky_bar"
TITLE = "Shakky's Rip-off Bar (Sabaody)"
CUTS = [2, 8]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")

N = 72
BAR = dict(wood="mangrove", rug="red", rug2="black", bed="red", light="onepiece:bubble_lamp[hanging=true]", accent="minecraft:copper_block",
           banner="red", candle="red")
POST = "minecraft:dark_oak_log[axis=y]"
INFILL = ("minecraft:mangrove_planks", "minecraft:mangrove_planks", "minecraft:mangrove_planks", "minecraft:stripped_mangrove_wood[axis=y]")
BASE = "minecraft:mud_bricks"
WIN = pane_of("minecraft:glass_pane")
LOOSE = ("minecraft:short_grass", "minecraft:fern", "minecraft:moss_carpet")


def paint_number(b, tx, tz, y0, msg, phi, rnd=None, sy=2, s="minecraft:white_concrete"):
    """Paint big numbers flush onto a round trunk (the grove number), letters 2 blocks tall per font pixel, facing
    the direction phi (radians, 0 = east, pi/2 = south), reading left to right from that side."""
    cols = []
    for ch in msg:
        g = FONT.get(ch, FONT[" "])
        for c in range(len(g[0])): cols.append([row[c] for row in g])
        cols.append(["0"] * 5)
    cols = cols[:-1]
    cx = (len(cols) - 1) / 2
    for u, col in enumerate(cols):
        for v, bit in enumerate(col):
            if bit != "1": continue
            for k in range(sy):
                y = y0 + (4 - v) * sy + k
                for rr in (7.0, 6.5, 6.0, 5.5, 5.0, 4.5, 4.0, 3.5, 3.0):  # find the bark on this ray
                    th = phi + (cx - u) / rr
                    x, z = round(tx + rr * math.cos(th)), round(tz + rr * math.sin(th))
                    if (b.get(x, y, z) or "").startswith("onepiece:yarukiman_log"):
                        b.set(x, y, z, s); break


def bubble(b, x, z, rnd, n=1):
    """A soap bubble welling up from the ground or a root, still sitting where it formed, sometimes with a
    smaller one lifting off its top."""
    y = 9
    while y > 0 and b.get(x, y - 1, z) in (None, AIR): y -= 1
    if y <= 0 and b.get(x, 0, z) in (None, AIR): return
    for i in range(n):
        r = rnd.choice((1.5, 2.0, 2.0, 2.5)) if i == 0 else 1.0
        cy = y + int(r)
        b.sphere(x, cy, z, r, S.BUB, hollow=True)
        y = cy + int(r) + 1
        x += rnd.choice((-1, 0, 1)); z += rnd.choice((-1, 0, 1))


def bar_house(b, rnd, X0, Z0, X1, Z1):
    """The bar: walls X0..X1 / Z0..Z1, ground floor y 1-5, upper floor y 7-10, roof from y 12. The timber frame
    (posts and beams) stands one block proud of the plank infill."""
    px = (X0, X0 + 4, X0 + 8, X0 + 13, X0 + 17, X1)          # posts along the long (south/north) faces
    pz = (Z0, Z0 + 4, Z0 + 8, Z1)                              # posts along the gable (west/east) faces
    MX = (X0 + X1) / 2
    for y in range(0, 12):  # clear the site
        for x in range(X0 - 1, X1 + 2):
            for z in range(Z0 - 1, Z1 + 2): b.set(x, y, z, AIR if y else "minecraft:mud_bricks")
    # infill walls with a mud-brick base course
    for y in range(1, 11):
        for x in range(X0, X1 + 1):
            for z in range(Z0, Z1 + 1):
                if x in (X0, X1) or z in (Z0, Z1):
                    b.set(x, y, z, BASE if y == 1 else "minecraft:dark_oak_planks" if y in (6, 11) else rnd.choice(INFILL))
    b.box(X0 + 1, 0, Z0 + 1, X1 - 1, 0, Z1 - 1, "minecraft:spruce_planks")
    b.box(X0 + 1, 6, Z0 + 1, X1 - 1, 6, Z1 - 1, "minecraft:spruce_planks")
    for x in range(X0 + 2, X1 - 1, 3): b.box(x, 5, Z0 + 1, x, 5, Z1 - 1, "minecraft:stripped_dark_oak_log[axis=z]")  # ceiling beams
    # the frame, proud of the wall: posts, a beam at the first floor and a top plate
    ring = [(x, Z0 - 1, "north") for x in range(X0 - 1, X1 + 2)] + [(x, Z1 + 1, "south") for x in range(X0 - 1, X1 + 2)] + \
           [(X0 - 1, z, "west") for z in range(Z0, Z1 + 1)] + [(X1 + 1, z, "east") for z in range(Z0, Z1 + 1)]
    for (x, z, f) in ring:
        b.set(x, 6, z, "minecraft:dark_oak_log[axis=x]" if f in ("north", "south") else "minecraft:dark_oak_log[axis=z]")
        b.set(x, 11, z, "minecraft:dark_oak_log[axis=x]" if f in ("north", "south") else "minecraft:dark_oak_log[axis=z]")
        b.set(x, 1, z, slab("minecraft:mud_brick_slab"))
    for x in px:
        for z in (Z0 - 1, Z1 + 1): b.column(x, z, 1, 10, POST)
    for z in pz:
        for x in (X0 - 1, X1 + 1): b.column(x, z, 1, 10, POST)
    # windows: in each bay a framed window (one or two 2-tall panes) with open shutters, a sill below, a head above
    def window(x, z, f, y, w=1):
        ox, oz = {"north": (0, -1), "south": (0, 1), "west": (-1, 0), "east": (1, 0)}[f]
        ax, az = (1, 0) if f in ("north", "south") else (0, 1)
        for k in range(w):
            wx, wz = x + ax * k, z + az * k
            for yy in (y, y + 1): b.set(wx, yy, wz, WIN)
            b.set(wx + ox, y - 1, wz + oz, stairs("minecraft:dark_oak_stairs", OPP[f], "top") if y < 6 else f"onepiece:flower_box[facing={f}]")
            b.set(wx + ox, y + 2, wz + oz, slab("minecraft:dark_oak_slab", "top"))
        for k in (-1, w):
            for yy in (y, y + 1): b.set(x + ox + ax * k, yy, z + oz + az * k, trapdoor("minecraft:spruce_trapdoor", f, "bottom", "true"))
    door_x = (X0 + 10, X0 + 11)
    for (a, c) in zip(px, px[1:]):
        mid, w = ((a + c) // 2, 1) if (c - a) % 2 == 0 else ((a + c) // 2, 2)
        for (z, f) in ((Z0, "north"), (Z1, "south")):
            if not (f == "south" and X0 + 4 < mid < X1 - 4): window(mid, z, f, 8, w)   # the BAR letters fill the middle upstairs
            if not (f == "south" and mid in door_x): window(mid, z, f, 2, w)
    for (a, c) in zip(pz, pz[1:]):
        mid = (a + c) // 2
        for (x, f) in ((X0, "west"), (X1, "east")):
            window(x, mid, f, 2); window(x, mid, f, 8)
    # the front door: a double door under a beam, an awning on brackets and a wall lamp each side
    for x in door_x:
        b.set(x, 1, Z1, door("minecraft:dark_oak_door", "south", "lower", "left" if x == door_x[0] else "right"))
        b.set(x, 2, Z1, door("minecraft:dark_oak_door", "south", "upper", "left" if x == door_x[0] else "right"))
        b.set(x, 3, Z1, "minecraft:dark_oak_log[axis=x]")
        b.set(x, 1, Z1 + 1, AIR)
        b.set(x, 0, Z1 + 1, "minecraft:mud_bricks"); b.set(x, 0, Z1 + 2, "minecraft:mangrove_planks")
    for x in range(door_x[0] - 2, door_x[1] + 3):
        b.set(x, 4, Z1 + 1, "minecraft:dark_oak_planks"); b.set(x, 4, Z1 + 2, slab("minecraft:dark_oak_slab", "top")) if X0 <= x <= X1 else None
    for x in (door_x[0] - 2, door_x[1] + 2): b.set(x, 3, Z1 + 2, stairs("minecraft:dark_oak_stairs", "north", "top"))
    for x in (door_x[0] - 1, door_x[1] + 1): b.set(x, 3, Z1 + 1, "onepiece:wall_lamp[facing=south]")
    # the roof: dark oak gables over the frame with deep eaves and brackets
    top = b.gable_roof(X0 - 1, Z0 - 1, X1 + 1, Z1 + 1, 12, "minecraft:dark_oak_stairs", "minecraft:dark_oak_planks", gable_wall="minecraft:mangrove_planks")
    for z in range(Z0 - 1, Z1 + 2):  # a trim beam over each gable end
        for x in (X0 - 1, X1 + 1):
            if (b.get(x, 12, z) or "").startswith("minecraft:mangrove_planks"): b.set(x, 12, z, "minecraft:dark_oak_log[axis=z]")
    for x in range(X0 - 2, X1 + 3, 2):
        for (z, f) in ((Z0 - 2, "south"), (Z1 + 2, "north")): b.set(x, 11, z, stairs("minecraft:dark_oak_stairs", f, "top"))
    # a chimney up the back wall, smoking
    for y in range(1, top + 2): b.set(X0 + 2, y, Z0 - 2, "minecraft:bricks" if y > 1 else BASE)
    b.set(X0 + 2, top + 2, Z0 - 2, "minecraft:campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
    # the big SHAKKY'S board on the front of the roof (framed, two blocks thick, the back plain timber)
    w = sum(len(FONT[c][0]) + 1 for c in "SHAKKY'S") - 1
    bx0 = int(MX - w / 2) - 2; bx1 = bx0 + w + 3
    for x in range(bx0, bx1 + 1):
        for y in range(13, 20):
            frame = y in (13, 19) or x in (bx0, bx1)
            b.set(x, y, Z1 + 1, "minecraft:dark_oak_planks" if frame else "minecraft:black_concrete")
            b.set(x, y, Z1, "minecraft:dark_oak_planks")                                              # a plain timber back
    b.text(bx0 + 2, 14, Z1 + 2, "SHAKKY'S", "minecraft:yellow_concrete", axis="x", step=1)            # reads from the south
    # BAR in big red letters across the upper floor, on a black panel between the end bays
    for x in range(X0 + 5, X1 - 4):
        for y in range(7, 12): b.set(x, y, Z1 + 1, "minecraft:black_concrete")
    b.text(int(MX) - 5, 7, Z1 + 2, "BAR", "minecraft:red_concrete", axis="x", step=1)
    return top


def build():
    rnd = random.Random(451)
    b = B()
    S.ground(b, N, N, rnd)
    T.sea(b, N, N, lambda x, z: z > 58 + 2 * math.sin(x * 0.2), depth=4, floor="minecraft:mud")
    # ---------------- the giant mangrove of Grove 13, its number painted big on the trunk
    TX, TZ = 50, 24
    S.yarukiman(b, TX, TZ, rnd, r=5, h=34)
    paint_number(b, TX, TZ, 12, "13", math.pi / 2)        # facing south, over the terrace
    paint_number(b, TX, TZ, 12, "13", math.pi)            # facing west, towards the bar
    for (x, z, r, h) in ((10, 12, 3.5, 26), (14, 50, 3, 24), (64, 52, 3, 22)): S.yarukiman(b, x, z, rnd, r=r, h=h)
    # ---------------- the bar, two storeys of mangrove timber
    BX0, BZ0, BW, BD = 18, 22, 22, 13
    X0, Z0, X1, Z1 = BX0, BZ0, BX0 + BW - 1, BZ0 + BD - 1
    bar_house(b, rnd, X0, Z0, X1, Z1)
    # the bar room: the long counter across the back, bottles and barrels behind it, stools in front, tables
    CZ_ = Z0 + 3
    for x in range(X0 + 4, X1 - 2):
        b.set(x, 1, CZ_, "minecraft:dark_oak_planks" if x in (X0 + 4, X1 - 3) else stairs("minecraft:dark_oak_stairs", "south", "top"))
        b.set(x, 2, CZ_, slab("minecraft:spruce_slab", "bottom")) if x in (X0 + 4, X1 - 3) else None
        b.set(x, 1, Z0 + 1, "minecraft:barrel[facing=south,open=false]" if x % 3 else "minecraft:smoker[facing=south,lit=false]")
        b.set(x, 2, Z0 + 1, ("minecraft:brewing_stand[has_bottle_0=true,has_bottle_1=true,has_bottle_2=false]", candle("red", 2), "minecraft:decorated_pot")[x % 3])
        b.set(x, 3, Z0 + 1, "minecraft:dark_oak_slab[type=top,waterlogged=false]")
        b.set(x, 4, Z0 + 1, ("minecraft:flower_pot", "minecraft:brewing_stand[has_bottle_0=true,has_bottle_1=false,has_bottle_2=true]", "minecraft:decorated_pot")[x % 3])
        if x % 2 == 0 and X0 + 5 <= x <= X1 - 4:
            b.set(x, 1, CZ_ + 1, fence("dark_oak")); b.set(x, 2, CZ_ + 1, "minecraft:red_carpet")
        if x % 4 == 1: b.set(x, 2, CZ_, ("minecraft:brewing_stand[has_bottle_0=true,has_bottle_1=true,has_bottle_2=true]", candle("white", 3))[x % 2])
    for (x, z) in ((X0 + 4, Z1 - 3), (X0 + 9, Z1 - 4), (X0 + 15, Z1 - 3)): b.table_set(x, 1, z, wood="mangrove", cloth="red")
    b.set(X1 - 1, 1, Z1 - 1, "minecraft:jukebox"); b.set(X0 + 1, 1, Z1 - 1, BARREL)
    for y in range(1, 7): b.set(X0 + 1, y, Z0 + 1, "minecraft:ladder[facing=south,waterlogged=false]")
    # Rayleigh's room and the store rooms upstairs
    I.subdivide(b, X0 + 1, 7, Z0 + 1, X1 - 1, Z1 - 1, 3, "minecraft:mangrove_planks", ("bedroom", "study", "storage"), BAR, cell=8,
                keepout=((X0 + 1, Z0 + 1, X0 + 2, Z0 + 2),), seed=62)
    for y in range(7, 9): b.set(X0 + 1, y, Z0 + 1, AIR)
    # the cellar of rum
    b.box(X0 + 3, -4, Z0 + 3, X0 + 10, -1, Z0 + 8, AIR)
    b.walls(X0 + 2, -5, Z0 + 2, X0 + 11, -1, Z0 + 9, "minecraft:mud_bricks"); b.box(X0 + 3, -5, Z0 + 3, X0 + 10, -5, Z0 + 8, "minecraft:mud_bricks")
    I.furnish(b, X0 + 3, -4, Z0 + 3, X0 + 10, Z0 + 8, 3, "storage", BAR, seed=63)
    for y in range(-4, 0): b.set(X0 + 3, y, Z0 + 8, "minecraft:ladder[facing=east,waterlogged=false]")   # the hatch, clear of the counter
    b.set(X0 + 3, 0, Z0 + 8, "minecraft:mangrove_trapdoor[facing=east,half=bottom,open=true,powered=false,waterlogged=false]")
    # the terrace: tables under the roots, bubble lamps along the edge
    for (x, z) in ((X0 + 3, Z1 + 5), (X0 + 9, Z1 + 6), (X0 + 15, Z1 + 5)):
        b.table_set(x, 1, z, wood="mangrove", cloth="red")
    for x in range(X0 - 2, X1 + 3, 4):
        if b.get(x, 1, Z1 + 9) in (None, AIR) or (b.get(x, 1, Z1 + 9) or "").startswith(LOOSE):
            b.set(x, 1, Z1 + 9, "minecraft:mangrove_fence"); b.set(x, 2, Z1 + 9, "minecraft:mangrove_fence"); b.set(x, 3, Z1 + 9, "onepiece:bubble_lamp[hanging=false]")
    # ---------------- the coating workshop and the dock
    CX0, CZ0 = 44, 43
    T.house(b, CX0, CZ0, 12, 9, 1, "shack", rnd, kinds=["workshop"], theme="shipyard", door="south", flat_roof=False)
    for k in range(3): b.set(CX0 + 2 + 3 * k, 1, CZ0 - 1, "minecraft:barrel[facing=up,open=false]"); b.set(CX0 + 2 + 3 * k, 2, CZ0 - 1, "onepiece:bubble_glass")
    T.pier(b, 28, 54, 10, axis="z", boat=True)
    T.path(b, [(X0 + 10, Z1 + 2), (X0 + 10, 52), (30, 54)], w=1, s="minecraft:mangrove_planks")
    # ---------------- soap bubbles welling up from the roots
    for (tx, tz, n) in ((TX, TZ, 6), (10, 12, 3), (14, 50, 3), (64, 52, 3)):
        for k in range(n):
            a = rnd.uniform(0, 2 * math.pi); d = rnd.uniform(7, 11)
            x, z = round(tx + d * math.cos(a)), round(tz + d * math.sin(a))
            if 2 <= x < N - 2 and 2 <= z < 56 and not (X0 - 3 <= x <= X1 + 3 and Z0 - 3 <= z <= Z1 + 10):
                bubble(b, x, z, rnd, n=rnd.choice((1, 2)))
    # ---------------- Rayleigh at the counter, and the loot
    b.npc(BX0 + 5, 1, BZ0 + 5, "rayleigh", False)
    b.chest(BX0 + 4, -4, BZ0 + 4, "pirate", "east")
    return b, 0

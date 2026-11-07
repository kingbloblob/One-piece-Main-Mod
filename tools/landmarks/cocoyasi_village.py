"""Cocoyasi Village: Nami's home village on the Conomi Islands. Bellemere's little house on the hill inside her
tangerine grove (Nojiko still tends the trees), Bellemere's grave on the cliff over the sea, the village houses
round the square with Genzo's pinwheels, the clinic of Doctor Nako, the fishing pier and the bright orange and
blue cottages of the East Blue. ~84 x 84. Ground = y 0, the sea to the west."""
import math, random
from canvas import *
import interiors as I
import townkit as T

SID = "cocoyasi_village"
TITLE = "Cocoyasi Village (Tangerine Grove)"
CUTS = [3]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")

N = 84
SEA_X = 8


def hill(x, z):
    d = math.hypot(x - 62, z - 22)
    return max(0, int(6 - d / 4)) if d < 24 else 0


def headland(x, z):
    """The grassy cliff top over the sea north-west of the village, where Bellemere's grave looks out to sea. Only the
    seaward (west) side is a cliff: inland it slopes down to the village, and over the last eight blocks before the
    tile's north edge it eases down to the ground level, so the land beyond the tile meets it without a wall."""
    if z > 30 or x > 34: return 0
    fx = min(1.0, max(0.0, (34 - x) / 10))
    fz = min(1.0, max(0.0, (30 - z) / 8))
    fn = min(1.0, max(0.0, z / 8))
    return int(round(5 * fx * fz * fn))


def is_sea(x, z):
    return x < SEA_X + 3 * math.sin(z * 0.17)


def ground_h(x, z):
    return 0 if is_sea(x, z) else max(hill(x, z), headland(x, z))


def pinwheel(b, x, y, z, col, col2="white"):
    """Genzo's pinwheel (the kazaguruma he wears in his hat for Nami): a hooked four-blade wheel on a pole."""
    b.column(x, z, y, y + 4, fence("birch"))
    hub = (x, y + 4, z + 1)
    b.set(*hub, "minecraft:yellow_wool")
    blades = (((0, 1), (0, 2), (1, 2)), ((-1, 0), (-2, 0), (-2, 1)), ((0, -1), (0, -2), (-1, -2)), ((1, 0), (2, 0), (2, -1)))
    for i, blade in enumerate(blades):
        for (dx, dy) in blade: b.set(x + dx, y + 4 + dy, z + 1, f"minecraft:{col if i % 2 == 0 else col2}_wool")


def build():
    rnd = random.Random(241)
    b = B()
    for x in range(N):
        for z in range(N):
            h = ground_h(x, z)
            cliff = headland(x, z) > 0 and x < SEA_X + 8 + 3 * math.sin(z * 0.17)
            for y in range(-3, h + 1):
                if y == h: s_ = "minecraft:grass_block"
                elif cliff and y < h - 1: s_ = ("minecraft:stone", "minecraft:andesite", "minecraft:stone", "minecraft:cobblestone")[(x * 3 + y * 5 + z * 7) % 4]
                else: s_ = "minecraft:dirt"
                b.set(x, y, z, s_)
            if rnd.random() < 0.05 and b.get(x, h + 1, z) is None: b.set(x, h + 1, z, rnd.choice(("minecraft:short_grass", "minecraft:dandelion", "minecraft:oxeye_daisy")))
    T.sea(b, N, N, is_sea, depth=5)
    for x in range(N):
        for z in range(N):
            if b.get(x, 0, z) == "minecraft:grass_block" and x < SEA_X + 5 + 3 * math.sin(z * 0.17):
                b.set(x, 0, z, "minecraft:sand")
                if b.get(x, 1, z): b.set(x, 1, z, AIR)
    # ---------------- Bellemere's house and the tangerine grove on the hill
    hx, hz = 60, 20
    hy = hill(hx, hz)
    T.house(b, hx, hz, 8, 7, 1, "orange", rnd, kinds=["kitchen"], y=hy, door="south")
    for i in range(22):
        tx, tz = 46 + (i % 6) * 5 + (i // 6) % 2 * 2, 6 + (i // 6) * 6
        if hx - 2 <= tx <= hx + 9 and hz - 2 <= tz <= hz + 8: continue
        if 0 <= tx < N and 0 <= tz < N: T.orchard_tree(b, tx, tz, y=hill(tx, tz))
    for x in range(44, 80, 2):
        b.set(x, hill(x, 4) + 1, 4, fence("oak")); b.set(x, hill(x, 40) + 1, 40, fence("oak"))
    for (x, z) in ((hx - 2, hz + 9), (hx + 4, hz + 10), (hx + 8, hz + 9)): b.set(x, hill(x, z) + 1, z, "onepiece:mikan_crate")
    # Bellemere's grave on the cliff top looking out to sea, with tangerine trees round it
    gz = 12
    gx = int(SEA_X + 3 * math.sin(gz * 0.17)) + 3
    gy = ground_h(gx, gz)
    b.set(gx, gy + 1, gz, "minecraft:stone_brick_wall"); b.set(gx, gy + 2, gz, "minecraft:stone_brick_wall"); b.set(gx, gy + 3, gz, "minecraft:stone_brick_slab[type=bottom,waterlogged=false]")
    b.set(gx, gy + 1, gz + 1, "minecraft:potted_orange_tulip"); b.set(gx, gy + 1, gz - 1, "minecraft:potted_red_tulip")
    b.set(gx + 1, gy + 1, gz, "minecraft:orange_tulip")
    for (tx, tz) in ((gx + 5, gz - 5), (gx + 6, gz + 4), (gx + 11, gz - 1), (gx + 12, gz + 7), (gx + 4, gz + 10)):
        T.orchard_tree(b, tx, tz, y=ground_h(tx, tz))
    # ---------------- village square with Genzo's pinwheels
    for x in range(26, 44):
        for z in range(44, 60): b.set(x, 0, z, "minecraft:stone_bricks" if (x + z) % 4 else "minecraft:mossy_stone_bricks")
    T.well(b, 35, 52)
    for (x, z, c) in ((28, 46, "red"), (42, 46, "yellow"), (28, 58, "blue"), (42, 58, "lime"), (35, 45, "orange")): pinwheel(b, x, 1, z, c)
    T.path(b, [(35, 60), (35, 80)], w=1, alt="minecraft:coarse_dirt")
    T.path(b, [(26, 52), (12, 52)], w=1, alt="minecraft:coarse_dirt")
    T.path(b, [(44, 52), (60, 52), (64, hz + 8)], w=1, alt="minecraft:coarse_dirt")
    spots = [(16, 36, None), (28, 34, "tavern"), (40, 34, None), (50, 44, None), (50, 58, "lab"), (16, 62, None), (26, 66, None),
             (40, 66, None), (52, 70, None), (66, 60, None), (66, 72, "kitchen"), (20, 76, None)]
    for (x0, z0, kind) in spots:
        w, d = rnd.randint(7, 8), rnd.randint(6, 7)
        T.house(b, x0, z0, w, d, 2 if kind else rnd.choice((1, 1, 2)), rnd.choice(("orange", "east_blue", "plaster", "orange")), rnd,
                kinds=[kind, "bedroom"] if kind else None, door="south" if z0 < 50 else "north",
                sign={"tavern": "minecraft:red_wool", "lab": "minecraft:white_wool", "kitchen": "minecraft:yellow_wool"}.get(kind))
    for i in range(8): T.tree(b, 74 + (i % 2) * 5, 46 + i * 4, h=rnd.randint(4, 6)) if 46 + i * 4 < N - 3 else None
    T.pier(b, SEA_X - 10, 50, 14, axis="x")
    # ---------------- people and loot
    b.npc(hx + 3, ground_h(hx + 3, hz + 9) + 1, hz + 9, "nami", False)
    b.chest(hx + 2, hy + 1, hz + 2, "easy", "south")
    T.landscape(b, 0, 0, N - 1, N - 1, rnd, amp=4, cell=16, edge=8)  # the open ground rolls (guide 9b.1, 11a); last, so it knows where everything stands
    return b, 0

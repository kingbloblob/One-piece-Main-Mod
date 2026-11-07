"""The Mokomo Dukedom on Zou, the Mink kingdom on the back of the thousand-year elephant Zunesha. A forest of
giant trees with round tree houses linked by rope bridges: the Whale Tree (the Duke's palace in the hollow of
the greatest tree), Kurau City's market and houses on the forest floor, the Right Flank guard post with Nekomamushi's
night camp, the Mink dojo, lantern-lit walkways, all on Zunesha's back.
~100 x 100. Ground = y 0."""
import math, random
from canvas import *
import interiors as I
import townkit as T

SID = "mokomo_dukedom"
TITLE = "Mokomo Dukedom (Zou)"
CUTS = [3, 14]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")

N = 100
MINK = dict(wood="jungle", rug="orange", rug2="lime", bed="orange", light="minecraft:lantern", accent="minecraft:moss_block",
            banner="lime", candle="orange")
LEAF = "minecraft:jungle_leaves[distance=7,persistent=true,waterlogged=false]"


def giant_tree(b, x, z, r, h, rnd):
    for y in range(-2, h):
        rr = r * (1.4 if y < 2 else 1.0) - y * 0.01
        b.cyl(x, z, rr, y, y, "minecraft:jungle_log[axis=y]")
    for k in range(6):
        a = k * 1.05 + rnd.uniform(-0.2, 0.2)
        for t in range(int(r), int(r) + 6):
            b.cyl(x + t * math.cos(a), z + t * math.sin(a), 1.2, 0, max(0, 3 - (t - int(r))), "minecraft:jungle_wood")
    b.sphere(x, h + 3, z, r * 3.2, LEAF, ry=r * 1.5)
    for k in range(5):
        a = k * 1.26 + 0.4
        b.line((x, h - 2, z), (x + r * 2.5 * math.cos(a), h + 3, z + r * 2.5 * math.sin(a)), "minecraft:jungle_wood")


def tree_house(b, x, z, r, y, rnd, kind):
    """A round house wrapped round a trunk at height y, with a deck."""
    b.cyl(x, z, r + 3, y, y, "minecraft:jungle_planks")
    b.cyl(x, z, r + 3.4, y + 1, y + 1, "minecraft:jungle_fence", hollow=True)
    b.cyl(x, z, r + 2, y + 1, y + 4, "minecraft:stripped_jungle_log[axis=y]" if rnd.random() < 0.5 else "minecraft:orange_terracotta", hollow=True)
    b.cyl(x, z, r + 1.2, y + 1, y + 4, AIR)
    b.cyl(x, z, r - 0.4, y + 1, y + 4, "minecraft:jungle_log[axis=y]")
    for a in (30, 150, 270):
        t = math.radians(a)
        b.set(round(x + (r + 2) * math.cos(t)), y + 2, round(z + (r + 2) * math.sin(t)), "minecraft:glass_pane")
    t = math.radians(90)
    dx, dz = round((r + 2) * math.cos(t)), round((r + 2) * math.sin(t))
    for yy in (y + 1, y + 2): b.set(x + dx, yy, z + dz, AIR)
    for k in range(4):
        b.cyl(x, z, r + 3.5 - k, y + 5 + k, y + 5 + k, "minecraft:moss_block" if k % 2 else "minecraft:hay_block[axis=y]", hollow=k < 3)
    # a little furnished room on the side of the ring
    I.furnish(b, x + round(r) + 1 - 1, y + 1, z - 1, x + round(r) + 1, z + 1, 3, kind, MINK, seed=x * 3 + y)
    b.set(x - round(r) - 1, y + 3, z, "minecraft:lantern[hanging=true,waterlogged=false]")
    return (x + dx, y, z + dz + 1)


def build():
    rnd = random.Random(591)
    b = B()
    T.ground(b, N, N, rnd, deco=0.2, decos=("minecraft:short_grass", "minecraft:fern", "minecraft:short_grass", "minecraft:large_fern[half=lower]"))
    for x in range(N):
        for z in range(N):
            if b.get(x, 1, z) == "minecraft:large_fern[half=lower]": b.set(x, 2, z, "minecraft:large_fern[half=upper]")
    # ---------------- the Whale Tree: the Duke's palace
    WX, WZ = 30, 30
    giant_tree(b, WX, WZ, 7, 40, rnd)
    b.cyl(WX, WZ, 5.5, 1, 18, AIR)  # hollow inside
    for y in (1, 7, 13): b.cyl(WX, WZ, 5.5, y - 1, y - 1, "minecraft:jungle_planks")
    for y in range(1, 19): b.set(WX - 5, y, WZ, "minecraft:ladder[facing=east,waterlogged=false]")
    for y in (6, 12): b.set(WX - 5, y, WZ, "minecraft:ladder[facing=east,waterlogged=false]")
    for y in (1, 2, 3):
        for dx in (-1, 0, 1): b.set(WX + dx, y, WZ + 6, AIR); b.set(WX + dx, y, WZ + 7, AIR)
    I.furnish(b, WX - 3, 1, WZ - 3, WX + 3, WZ + 3, 5, "throne", MINK, seed=1)
    I.furnish(b, WX - 3, 7, WZ - 3, WX + 3, WZ + 3, 5, "library", MINK, seed=2)
    I.furnish(b, WX - 3, 13, WZ - 3, WX + 3, WZ + 3, 5, "bedroom", MINK, seed=3)
    for y in (4, 10, 16):
        for a in (0, 90, 180):
            t = math.radians(a)
            b.set(round(WX + 7 * math.cos(t)), y, round(WZ + 7 * math.sin(t)), "minecraft:glass_pane")
    # ---------------- more giant trees with tree houses and rope bridges
    trees = ((70, 24, 4, 32), (24, 72, 4, 30), (62, 62, 3.5, 28), (82, 50, 3, 24), (50, 10, 3, 22))
    decks = []
    for i, (x, z, r, h) in enumerate(trees):
        giant_tree(b, x, z, r, h, rnd)
        y = 10 + (i % 2) * 4
        decks.append((x, z, r, y))
        tree_house(b, x, z, r, y, rnd, ("kitchen", "bedroom", "storage", "dining", "bedroom")[i])
        for yy in range(1, y): b.set(x, yy, z - round(r) - 3, "minecraft:ladder[facing=north,waterlogged=false]")
    def bridge(p, q):
        (x0, z0, r0, y0), (x1, z1, r1, y1) = p, q
        L = math.hypot(x1 - x0, z1 - z0)
        ux, uz = (x1 - x0) / L, (z1 - z0) / L
        s0 = (x0 + ux * (r0 + 3), z0 + uz * (r0 + 3)); s1 = (x1 - ux * (r1 + 3), z1 - uz * (r1 + 3))
        n = int(math.hypot(s1[0] - s0[0], s1[1] - s0[1])) * 2 + 1
        for i in range(n + 1):
            t = i / n
            bx, bz = s0[0] + (s1[0] - s0[0]) * t, s0[1] + (s1[1] - s0[1]) * t
            by = round(y0 + (y1 - y0) * t - 2 * math.sin(t * math.pi))
            b.set(round(bx), by, round(bz), "minecraft:jungle_slab[type=top,waterlogged=false]")
            if i % 4 == 0: b.set(round(bx - uz), by + 1, round(bz + ux), "minecraft:jungle_fence"); b.set(round(bx + uz), by + 1, round(bz - ux), "minecraft:jungle_fence")
    for (i, j) in ((0, 2), (2, 1), (2, 3), (0, 4)): bridge(decks[i], decks[j])
    # ---------------- Kurau City on the forest floor: houses, market, dojo
    kinds = ("kitchen", "dining", "bedroom", "storage", "tavern", "bedroom")
    for i, (x0, z0) in enumerate(((44, 36), (44, 50), (56, 40), (12, 48), (10, 86), (40, 84))):
        T.house(b, x0, z0, 9, 8, 1 + i % 2, "orange", rnd, kinds=[kinds[i], "bedroom"], theme=MINK, door="south")
    for i, x in enumerate(range(40, 66, 6)):
        T.stall(b, x, 26, ("orange", "lime", "yellow", "brown", "white")[i], (("minecraft:melon", "minecraft:sweet_berry_bush[age=3]", None), ("minecraft:hay_block[axis=y]", "minecraft:barrel[facing=up,open=false]", None))[i % 2])
    T.house(b, 56, 80, 14, 9, 1, "cottage", rnd, kinds=["barracks"], theme=MINK, door="north")
    for x in range(58, 70, 3): b.set(x, 1, 78, "onepiece:training_post[facing=north]")
    # Nekomamushi's night camp (Right Flank)
    b.cyl(84, 14, 2, 0, 0, "minecraft:cobblestone"); b.set(84, 1, 14, "minecraft:campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
    for (dx, dz) in ((-4, 0), (4, 0), (0, 4)): b.set(84 + dx, 1, 14 + dz, "minecraft:jungle_log[axis=x]" if dz == 0 else "minecraft:jungle_log[axis=z]")
    T.path(b, [(WX, WZ + 8), (WX, 50), (48, 60), (70, 72)], w=1, s="minecraft:dirt_path")
    T.path(b, [(WX + 8, WZ), (50, 28), (84, 18)], w=1, s="minecraft:dirt_path")
    for (x, z) in ((36, 44), (52, 56), (64, 32), (20, 60)): T.lamp_post(b, x, z)
    # ---------------- loot and Minks (none are hostile)
    b.chest(WX + 2, 13, WZ - 2, "medium", "west"); b.chest(WX - 2, 1, WZ + 2, "easy", "east")
    return b, 0

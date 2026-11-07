"""Weatheria, the sky island of weather science where Nami trained with old Haredas: a cluster of small cloud
islets tied together by chains and rope bridges, each carrying a round domed lab of white and sky blue. Weather
balls float on tethers everywhere, a tall weathervane tower with the observatory crowns the main islet, and the
Weather Library holds the science of the skies. Inside: Haredas' lab, the great library, the observatory,
bedrooms and a kitchen garden. ~84 x 84, floats at a fixed height (canvas y 0 = world y 168)."""
import math, random
from canvas import *
import interiors as I

SID = "weatheria"
TITLE = "Weatheria (weather science island)"
CUTS = [2, 14]
TILER = dict(terrain="none", sky_y=168)

N = 84
CLOUD = "onepiece:island_cloud"
PUFF = "onepiece:cloud_puff"
SCI = dict(wood="birch", rug="light_blue", rug2="white", bed="light_blue", light="minecraft:sea_lantern", accent="minecraft:light_blue_glazed_terracotta",
           banner="light_blue", candle="light_blue")
ISLETS = ((40, 40, 17), (12, 14, 8), (70, 14, 9), (12, 70, 9), (70, 68, 8))


def islet(b, x, z, r, rnd):
    for y in range(0, -int(r * 0.9) - 1, -1):
        rr = r * math.sqrt(max(0, 1 - (y / (r * 0.9 + 0.5)) ** 2))
        b.cyl(x, z, rr, y, y, CLOUD)
    b.cyl(x, z, r + 0.6, 0, 0, PUFF, hollow=True)
    for i in range(int(r)):
        a = rnd.uniform(0, 2 * math.pi)
        b.sphere(x + (r - 1) * math.cos(a), -2, z + (r - 1) * math.sin(a), rnd.uniform(1.2, 2.4), PUFF, ry=1)


def lab(b, x, z, r, h, kind, seed, door="south"):
    b.cyl(x, z, r, 1, h, "minecraft:white_concrete", hollow=True)
    b.cyl(x, z, r - 1, 1, h, AIR)
    b.cyl(x, z, r - 1, 0, 0, "minecraft:birch_planks")
    for a in range(0, 360, 30):
        t = math.radians(a)
        b.set(round(x + r * math.cos(t)), 3, round(z + r * math.sin(t)), "minecraft:light_blue_stained_glass_pane")
    b.cyl(x, z, r + 0.5, h + 1, h + 1, "minecraft:light_blue_concrete")
    b.dome(x, z, h + 2, r, s="minecraft:white_concrete", tip=None, hollow=False)
    b.dome(x, z, h + 2, r - 1, h=r - 1, s=AIR, tip=None, hollow=False)
    b.cyl(x, z, r - 1, h + 1, h + 1, AIR)
    dz = r if door == "south" else -r
    for y in (1, 2): b.set(x, y, z + dz, AIR)
    q = max(2, int((r - 1) / 1.42))
    I.furnish(b, x - q, 1, z - q, x + q, z + q, min(h, 5), kind, SCI, seed=seed)


def weather_ball(b, x, y0, z, top, c):
    for y in range(y0, top): b.set(x, y, z, "minecraft:chain[axis=y,waterlogged=false]")
    b.sphere(x, top + 1, z, 1.6, f"minecraft:{c}_stained_glass")
    b.set(x, top + 1, z, "minecraft:sea_lantern" if c != "gray" else "minecraft:lightning_rod[facing=up,powered=false,waterlogged=false]")


def build():
    rnd = random.Random(431)
    b = B()
    for (x, z, r) in ISLETS: islet(b, x, z, r, rnd)
    # rope bridges from the main islet to the four small ones: a 3-wide birch deck that sags gently in half-block
    # steps (so it is walkable), on rope rails (birch fence) with a post and a lantern every few blocks. Each runs
    # straight out along x, then along z, so the rails join up (fences can't join on a diagonal).
    for (x, z, r) in ISLETS[1:]:
        sx = 1 if x > 40 else -1
        sz = 1 if z > 40 else -1
        path = [(40 + sx * i, 40) for i in range(abs(x - 40) + 1)] + [(x, 40 + sz * j) for j in range(1, abs(z - 40) + 1)]
        L = len(path) - 1
        for i, (px, pz) in enumerate(path):
            if b.get(px, 0, pz) not in (None, AIR) and b.get(px, 1, pz) in (None, AIR):
                continue  # still on the islet
            h = -int(round(3 * math.sin(i / L * math.pi)))  # sag in half blocks
            y, half = (h - 1) // 2, "top" if (h - 1) % 2 else "bottom"
            along_x = i <= abs(x - 40)
            for w in (-1, 0, 1):
                cx, cz = (px, pz + w) if along_x else (px + w, pz)
                if b.get(cx, y, cz) in (None, AIR):
                    b.set(cx, y, cz, f"minecraft:birch_slab[type={half},waterlogged=false]" if w == 0 else "minecraft:stripped_birch_log[axis=%s]" % ("x" if along_x else "z"))
                if w != 0 and b.get(cx, y + 1, cz) in (None, AIR):
                    b.set(cx, y + 1, cz, fence("birch"))
                    if i % 6 == 3:
                        b.set(cx, y + 2, cz, fence("birch"))
                        b.set(cx, y + 3, cz, "minecraft:lantern[hanging=false,waterlogged=false]")
    # ---------------- the main islet: Haredas' lab, the library and the weathervane observatory
    lab(b, 34, 32, 7, 6, "lab", 1)
    lab(b, 48, 46, 7, 9, "library", 2, door="north")
    for y in range(6, 9):  # a mezzanine of books in the library
        pass
    b.cyl(48, 46, 6, 6, 6, "minecraft:birch_planks", hollow=True)
    lab(b, 32, 48, 4, 4, "bedroom", 3, door="north")
    lab(b, 48, 30, 4, 4, "kitchen", 4)
    OX, OZ = 41, 40  # the observatory tower
    b.cyl(OX, OZ, 3, 1, 24, "minecraft:white_concrete", hollow=True)
    for y in range(1, 24): b.set(OX, y, OZ - 2, "minecraft:ladder[facing=south,waterlogged=false]")
    for y in range(4, 24, 4):
        for (dx, dz) in ((3, 0), (-3, 0), (0, 3)): b.set(OX + dx, y, OZ + dz, "minecraft:light_blue_stained_glass_pane")
    b.cyl(OX, OZ, 5, 24, 24, "minecraft:birch_planks")
    b.cyl(OX, OZ, 5.4, 25, 25, "minecraft:birch_fence", hollow=True)
    b.set(OX, 24, OZ - 2, "minecraft:ladder[facing=south,waterlogged=false]")
    b.set(OX + 2, 25, OZ, "minecraft:lectern[facing=west,has_book=true,powered=false]")
    b.set(OX - 2, 25, OZ + 1, "minecraft:spyglass" if False else "minecraft:lightning_rod[facing=east,powered=false,waterlogged=false]")
    for y in range(25, 34): b.set(OX, y, OZ, "minecraft:iron_bars[east=false,north=false,south=false,west=false,waterlogged=false]")
    for k in range(-3, 4):  # the weathervane arrow
        b.set(OX + k, 34, OZ, "minecraft:copper_block" if abs(k) < 3 else "minecraft:waxed_cut_copper")
    b.set(OX - 4, 34, OZ, "minecraft:waxed_cut_copper_stairs[facing=east,half=bottom,shape=straight,waterlogged=false]")
    for (dx, dz) in ((0, 2), (0, -2)): b.set(OX + 3, 34, OZ + dz // 2, "minecraft:waxed_cut_copper_slab[type=bottom,waterlogged=false]")
    b.set(OX, 35, OZ, "minecraft:lightning_rod[facing=up,powered=false,waterlogged=false]")
    # kitchen garden
    for x in range(26, 32):
        for z in range(38, 44):
            b.set(x, 0, z, "minecraft:farmland[moisture=7]"); b.set(x, 1, z, rnd.choice(("minecraft:wheat[age=7]", "minecraft:carrots[age=7]", "minecraft:beetroots[age=3]")))
    # ---------------- the four little islets: testing stations
    stations = (("workshop", "white"), ("storage", "gray"), ("study", "light_blue"), ("bedroom", "yellow"))
    for i, ((x, z, r), (kind, c)) in enumerate(zip(ISLETS[1:], stations)):
        lab(b, x, z, 4, 4, kind, 10 + i, door="south" if z < 40 else "north")
        for a in (30, 150, 270):
            t = math.radians(a + i * 20)
            weather_ball(b, round(x + (r - 2) * math.cos(t)), 1, round(z + (r - 2) * math.sin(t)), 5 + (a // 30) % 4, c)
    # weather balls round the main islet
    for k in range(12):
        t = math.radians(k * 30 + 10)
        x, z = round(40 + 15 * math.cos(t)), round(40 + 15 * math.sin(t))
        if b.get(x, 1, z) is None: weather_ball(b, x, 1, z, rnd.randint(5, 10), ("white", "light_blue", "gray", "yellow", "orange")[k % 5])
    # ---------------- loot
    b.chest(36, 1, 30, "lab", "west"); b.chest(46, 1, 48, "library", "east")
    b.chest(12, 1, 16, "sky_treasure", "south")
    return b, 0

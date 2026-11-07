"""Giant Jack, the colossal beanstalk of Upper Yard: a twisting vine as thick as a tower, wound with lesser vines and
leaf pads, rising from the sacred jungle of Upper Yard to a cloud platform high above. A spiral path of vine
steps and rope bridges climbs it; on the way up are the Sky Priests' ordeal shrines (Ball, Swamp, String and
Iron), and at the top the priests' shrine with the offering hall and the sky treasure. At the foot: giant
Upper Yard trees, the sacrificial altar and an old Shandian ruin. ~80 x 80, ~118 high. Ground = y 0."""
import math, random
from canvas import *
import interiors as I

SID = "giant_jack"
TITLE = "Giant Jack (the giant beanstalk)"
CUTS = [3, 60]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")

N = 80
CX, CZ = 40, 40
TOP = 104
VINE = "minecraft:moss_block"
VINE2 = "minecraft:green_concrete"
LEAF = "minecraft:jungle_leaves[distance=7,persistent=true,waterlogged=false]"
RUIN = "onepiece:shandian_ruin_stone"
PRIEST = dict(wood="jungle", rug="green", rug2="yellow", bed="green", light="minecraft:lantern", accent="onepiece:shandora_gold_bricks",
              banner="green", candle="yellow")


def stalk_center(y):
    a = y / 14.0
    return CX + 4 * math.cos(a), CZ + 4 * math.sin(a)


def build():
    rnd = random.Random(421)
    b = B()
    for x in range(N):
        for z in range(N):
            for y in (-3, -2, -1): b.set(x, y, z, "minecraft:dirt")
            b.set(x, 0, z, "minecraft:moss_block" if (x * 3 + z) % 4 == 0 else "minecraft:grass_block")
            if rnd.random() < 0.15: b.set(x, 1, z, rnd.choice(("minecraft:fern", "minecraft:short_grass", "minecraft:moss_carpet")))
    # ---------------- the giant beanstalk
    for y in range(-2, TOP):
        cx, cz = stalk_center(y)
        r = 7.5 - 3.5 * y / TOP + (3 if y < 4 else 0) - (0 if y >= 0 else -1)
        b.cyl(cx, cz, r, y, y, VINE if (y // 5) % 2 else VINE2)
        for k in range(3):  # lesser vines wound round it
            a = y / 6.0 + k * 2.09
            vx, vz = cx + r * math.cos(a), cz + r * math.sin(a)
            b.cyl(vx, vz, 1.3, y, y, "minecraft:green_terracotta")
        if y % 9 == 4 and y > 6:  # big leaf pads sticking out
            a = y * 0.7
            for t in range(4, 13):
                lx, lz = cx + (r + t * 0.8) * math.cos(a), cz + (r + t * 0.8) * math.sin(a)
                b.cyl(lx, lz, 2.6 - abs(t - 8) * 0.25, y, y, LEAF)
    # roots fanning across the ground
    for k in range(9):
        a = k * 0.7 + 0.3
        for t in range(6, 30):
            rx, rz = CX + t * math.cos(a), CZ + t * math.sin(a)
            yy = max(0, int(3 - t / 7))
            b.cyl(rx, rz, max(0.8, 2.2 - t * 0.05), 0, yy, "minecraft:green_terracotta" if t % 5 else VINE)
    # ---------------- the spiral climbing path of vine steps
    for y in range(1, TOP):
        cx, cz = stalk_center(y)
        r = 7.5 - 3.5 * y / TOP + (3 if y < 4 else 0)
        a = y / 3.2
        for w in (1.0, 2.0):
            px, pz = round(cx + (r + w) * math.cos(a)), round(cz + (r + w) * math.sin(a))
            b.set(px, y, pz, "minecraft:jungle_planks")
            for h in (1, 2, 3): b.set(px, y + h, pz, AIR)
        ox, oz = round(cx + (r + 3) * math.cos(a)), round(cz + (r + 3) * math.sin(a))
        if y % 2 == 0: b.set(ox, y + 1, oz, fence("jungle"))
        if y % 12 == 0: b.set(ox, y + 2, oz, lantern())
    # ---------------- the four ordeal shrines on leaf platforms
    ordeals = ((22, "Ball", "minecraft:white_concrete"), (44, "Swamp", "minecraft:mud"), (66, "String", "minecraft:cobweb"), (86, "Iron", "minecraft:iron_block"))
    for (y, name, mark) in ordeals:
        cx, cz = stalk_center(y)
        a = y / 3.2 + math.pi
        px, pz = round(cx + 13 * math.cos(a)), round(cz + 13 * math.sin(a))
        b.cyl(px, pz, 5.5, y, y, "minecraft:jungle_planks"); b.cyl(px, pz, 5.5, y - 1, y - 1, LEAF)
        b.cyl(px, pz, 4, y + 1, y + 5, RUIN, hollow=True); b.cyl(px, pz, 3, y + 1, y + 5, AIR)
        for yy in (y + 1, y + 2, y + 3):
            for k in range(-1, 2): b.set(px + k, yy, pz + 4, AIR); b.set(px + k, yy, pz - 4, AIR)
        b.pagoda_roof(px, pz, 5, 5, y + 6, "minecraft:jungle_stairs", "minecraft:jungle_planks", layers=2)
        I.furnish(b, px - 2, y + 1, pz - 2, px + 2, pz + 2, 4, "shrine", PRIEST, seed=y)
        b.set(px, y + 1, pz, mark)
        bx, bz = round(cx + (7.5 - 3.5 * y / TOP + 1) * math.cos(a)), round(cz + (7.5 - 3.5 * y / TOP + 1) * math.sin(a))  # rope bridge to the stalk
        b.line((bx, y, bz), (px, y, pz), "minecraft:jungle_slab[type=top,waterlogged=false]")
    # ---------------- the cloud platform and the priests' shrine at the top
    tx, tz = stalk_center(TOP)
    tx, tz = round(tx), round(tz)
    for y, rr in ((TOP, 17), (TOP - 1, 15), (TOP - 2, 11), (TOP - 3, 6)):
        b.cyl(tx, tz, rr, y, y, "onepiece:island_cloud")
    b.cyl(tx, tz, 17.5, TOP + 1, TOP + 1, "onepiece:cloud_puff", hollow=True)
    S0, S1 = tx - 7, tx + 7
    b.box(S0, TOP + 1, tz - 6, S1, TOP + 1, tz + 6, RUIN)
    b.walls(S0, TOP + 2, tz - 6, S1, TOP + 8, tz + 6, RUIN); b.box(S0 + 1, TOP + 2, tz - 5, S1 - 1, TOP + 8, tz + 5, AIR)
    for x in range(S0, S1 + 1, 2):
        for z in (tz - 6, tz + 6):
            b.column(x, z, TOP + 2, TOP + 8, "onepiece:shandora_gold_bricks") if x in (S0, S1) else b.set(x, TOP + 4, z, "minecraft:yellow_stained_glass_pane")
    for y in (TOP + 2, TOP + 3, TOP + 4):
        for z in (tz - 1, tz, tz + 1): b.set(S1, y, z, AIR)
    b.pagoda_roof(tx, tz, 9, 8, TOP + 9, "onepiece:shandora_gold_brick_stairs", "onepiece:shandora_gold_bricks", layers=3)
    I.furnish(b, S0 + 1, TOP + 2, tz - 5, S1 - 1, tz + 5, 6, "chapel", PRIEST, seed=7)
    for (dx, dz) in ((-12, -8), (-12, 8), (11, -10), (11, 10)):  # torii-like posts of gold round the platform
        b.column(tx + dx, tz + dz, TOP + 2, TOP + 7, "onepiece:shandora_gold_bricks")
        b.set(tx + dx, TOP + 8, tz + dz, lantern())
    # ---------------- Upper Yard at the foot: giant trees, the altar and a ruin
    for i in range(30):
        x, z = rnd.randint(3, N - 4), rnd.randint(3, N - 4)
        if math.hypot(x - CX, z - CZ) < 18: continue
        h = rnd.randint(16, 26); r = rnd.uniform(1.2, 2.0)
        b.cyl(x, z, r, 1, h, "minecraft:jungle_log[axis=y]")
        b.sphere(x, h + 1, z, rnd.uniform(4.5, 6.5), LEAF, ry=3)
        for k in range(4):
            vx, vz = x + rnd.randint(-4, 4), z + rnd.randint(-4, 4)
            for y in range(h - 2, h - 2 - rnd.randint(4, 10), -1): b.fill_if(vx, y, vz, "minecraft:vine[east=false,north=true,south=false,up=false,west=false]")
    ax, az = 12, 66  # the sacrificial altar
    b.box(ax - 4, 1, az - 4, ax + 4, 1, az + 4, RUIN); b.box(ax - 3, 2, az - 3, ax + 3, 2, az + 3, RUIN); b.box(ax - 1, 3, az - 1, ax + 1, 3, az + 1, "onepiece:shandora_gold_bricks")
    for (dx, dz) in ((-4, -4), (4, -4), (-4, 4), (4, 4)): b.column(ax + dx, az + dz, 2, 6, "onepiece:shandian_ruin_stone_wall")
    rx, rz = 64, 14  # old Shandian ruin
    for (dx, dz, h) in ((0, 0, 7), (5, 0, 4), (0, 5, 9), (5, 5, 3), (10, 2, 6)): b.column(rx + dx, rz + dz, 1, h, RUIN)
    b.box(rx, 8, rz, rx + 5, 8, rz + 1, "onepiece:shandian_ruin_stone_slab[type=bottom,waterlogged=false]")
    # ---------------- loot and priests
    b.chest(tx - 5, TOP + 2, tz, "sky_treasure", "east")
    b.chest(ax, 4, az, "medium", "north")
    b.guards("sky_priest", ((tx - 2, tz - 3), (tx + 2, tz + 3)), y=TOP + 2)
    b.guards("sky_priest", ((ax + 2, az + 6),))
    return b, 0

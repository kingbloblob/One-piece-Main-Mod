"""Mock Town on Jaya: the lawless pirate town of dreamers-be-damned. Crooked, patched timber buildings two and three
storeys high crowd muddy streets: the Tavern of Bellamy's gang with the bar brawl hall, rowdy bars, a
gunsmith, an inn, a pawn shop, the town hall burnt black, the gallows, and the harbour full of pirate ships.
~100 x 96. Ground = y 0, sea to the west."""
import math, random
from canvas import *
import interiors as I
import townkit as T

SID = "mock_town"
TITLE = "Mock Town (Jaya)"
CUTS = [3]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")

NX, NZ = 114, 96
SEA_X = 30
PIRATE = I.THEMES["pirate"]


def crooked(b, x0, z0, w, d, floors, rnd, kind):
    """A ramshackle pirate building: each floor overhangs a bit and uses a different patched wood."""
    woods = ("spruce", "dark_oak", "oak", "mangrove", "jungle")
    y = 0
    for f in range(floors):
        wd = rnd.choice(woods)
        ox = 1 if f and rnd.random() < 0.5 else 0
        bx0, bx1 = x0 - ox, x0 + w - 1 + ox
        b.box(bx0, y, z0, bx1, y, z0 + d - 1, f"minecraft:{wd}_planks")
        b.walls(bx0, y + 1, z0, bx1, y + 4, z0 + d - 1, f"minecraft:{wd}_planks")
        b.box(bx0 + 1, y + 1, z0 + 1, bx1 - 1, y + 4, z0 + d - 2, AIR)
        for (px, pz) in ((bx0, z0), (bx1, z0), (bx0, z0 + d - 1), (bx1, z0 + d - 1)): b.column(px, pz, y + 1, y + 4, f"minecraft:{wd}_log[axis=y]" if wd != "mangrove" else "minecraft:mangrove_log[axis=y]")
        for x in range(bx0 + 2, bx1 - 1, 3):
            for z in (z0, z0 + d - 1): b.set(x, y + 2, z, rnd.choice(("minecraft:glass_pane", "minecraft:spruce_trapdoor[facing=south,half=top,open=true,powered=false,waterlogged=false]", f"minecraft:{wd}_planks")))
        for i in range(3):  # patches
            b.set(rnd.randint(bx0, bx1), y + rnd.randint(1, 4), rnd.choice((z0, z0 + d - 1)), rnd.choice(("minecraft:spruce_planks", "minecraft:oak_planks", "minecraft:barrel[facing=north,open=false]")))
        I.furnish(b, bx0 + 1, y + 1, z0 + 1, bx1 - 1, z0 + d - 2, 3, kind if f == 0 else rnd.choice(("bedroom", "barracks", "storage")), PIRATE, seed=rnd.randint(0, 99999))
        if f < floors - 1:
            b.set(bx0 + 1, y + 4, z0 + 1, AIR)
            for k in range(1, 5): b.set(bx0 + 1, y + k, z0 + 1, "minecraft:ladder[facing=south,waterlogged=false]")
        y += 5
    mx = x0 + w // 2
    for yy in (1, 2): b.set(mx, yy, z0 + d - 1, AIR)
    b.gable_roof(x0 - 1, z0, x0 + w, z0 + d - 1, y, rnd.choice(("minecraft:spruce_stairs", "minecraft:dark_oak_stairs")), "minecraft:dark_oak_planks")
    return y


def build():
    rnd = random.Random(321)
    b = B()
    T.ground(b, NX, NZ, rnd, top="minecraft:coarse_dirt", deco=0.03, decos=("minecraft:dead_bush", "minecraft:short_grass"))
    for x in range(NX):
        for z in range(NZ):
            if (x * 7 + z * 3) % 5 == 0: b.set(x, 0, z, "minecraft:mud")
            elif (x + z) % 4 == 0: b.set(x, 0, z, "minecraft:packed_mud")
    T.sea(b, NX, NZ, lambda x, z: x < SEA_X + 2 * math.sin(z * 0.2), depth=6)
    # wooden quay and piers with moored pirate ships
    for z in range(NZ):
        for x in (SEA_X + 2, SEA_X + 3): b.set(x, 0, z, "minecraft:spruce_planks")
    for (z0, L) in ((10, 26), (44, 30), (78, 24)):
        T.pier(b, SEA_X - 12, z0, 14, axis="x", boat=False)
        b.ship(1, -3, z0 + 4, L, 9, masts=((L // 2, 14),), sail="minecraft:black_wool", cabin=(5, 3, "minecraft:dark_oak_planks"))
    # streets
    for z in (30, 62):
        for x in range(SEA_X + 4, NX - 2):
            for dz in (-1, 0, 1): b.set(x, 0, z + dz, "minecraft:dirt_path" if (x + dz) % 3 else "minecraft:gravel")
    for x in (54, 86):
        for z in range(2, NZ - 2):
            for dx in (-1, 0, 1): b.set(x + dx, 0, z, "minecraft:dirt_path" if (z + dx) % 3 else "minecraft:gravel")
    # buildings
    kinds = ("tavern", "tavern", "armory", "bedroom", "storage", "tavern", "workshop", "kitchen", "dining", "bedroom", "tavern", "storage")
    k = 0
    for z0 in (4, 18, 34, 48, 66, 80):
        for x0 in (34, 42, 58, 68, 76, 90, 100):
            w, d = rnd.randint(7, 9), rnd.randint(7, 9)
            if z0 + d >= 28 and z0 <= 32 or z0 + d >= 60 and z0 <= 64: d = min(d, (28 if z0 < 30 else 60) - z0 - 1)
            if d < 6 or x0 + w >= NX - 1 or z0 + d >= NZ - 1: continue
            if any(abs(x - xr) <= 1 for xr in (54, 86) for x in range(x0 - 1, x0 + w + 1)): continue
            crooked(b, x0, z0, w, d, rnd.choice((2, 2, 3)), rnd, kinds[k % len(kinds)]); k += 1
    # the big tavern where Bellamy's gang drinks (on the main crossing)
    tx0, tz0 = 58, 34
    if b.get(tx0 + 5, 2, tz0 + 5) is None:
        crooked(b, tx0, tz0, 14, 12, 2, rnd, "tavern")
    # the gallows on the square and wanted posters
    gx, gz = 88, 46
    for y in range(1, 7): b.set(gx, y, gz, "minecraft:dark_oak_log[axis=y]"); b.set(gx + 4, y, gz, "minecraft:dark_oak_log[axis=y]")
    for x in range(gx, gx + 5): b.set(x, 7, gz, "minecraft:dark_oak_log[axis=x]")
    b.box(gx, 1, gz - 1, gx + 4, 2, gz + 1, "minecraft:dark_oak_planks")
    for x in range(gx + 1, gx + 4): b.set(x, 6, gz, "minecraft:dark_oak_fence")
    for (x, z) in ((54, 28), (86, 28), (54, 64), (86, 64)): T.lamp_post(b, x + 2, z)
    for i in range(12):  # barrels and crates in the alleys
        x, z = rnd.randint(34, NX - 4), rnd.randint(2, NZ - 3)
        if b.get(x, 1, z) is None: b.set(x, 1, z, rnd.choice(("minecraft:barrel[facing=up,open=false]", "onepiece:sake_barrel[axis=y]", "minecraft:hay_block[axis=y]")))
    # ---------------- loot and pirates
    b.chest(tx0 + 2, 1, tz0 + 2, "pirate", "east")
    b.guards("pirate", ((54, 40), (70, 30), (86, 34), (74, 62)))
    b.guards("pirate_gunner", ((86, 50), (SEA_X + 3, 44)))
    T.landscape(b, 0, 0, NX - 1, NZ - 1, rnd, amp=4, cell=16, edge=8, top="minecraft:coarse_dirt")  # the open ground rolls (guide 9b.1, 11a); last
    return b, 0

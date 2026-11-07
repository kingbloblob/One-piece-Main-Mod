"""Mary Geoise, the Holy Land on top of the Red Line. A sheer wall of red rock rises from the Red Port, where the
Bondola lift and the long cliff stair climb to the top. Up there, behind the Holy Gate: Pangaea Castle in white
marble and gold, with its domes, the great hall of the Empty Throne and the Five Elders' chamber, and the secret
flower room above; the gleaming mansions of the Celestial Dragons with their gardens, fountains and statues, and
the slave quarters hidden behind them. ~112 x 112. Ground = y 0, the top of the Red Line at y 40."""
import math, random
from canvas import *
import interiors as I
import townkit as T

SID = "mary_geoise"
TITLE = "Mary Geoise (the Holy Land on the Red Line)"
CUTS = [44, 54]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")

N = 112
TOP = 40
CLIFF_Z = 86
RED = "minecraft:red_terracotta"
Q = "minecraft:quartz_block"
QB = "minecraft:quartz_bricks"
SQ = "minecraft:smooth_quartz"
GOLD = "minecraft:gold_block"
HOLY = dict(wood="birch", rug="white", rug2="yellow", bed="white", light="minecraft:lantern", accent="minecraft:gold_block",
            banner="white", candle="yellow")


def mansion(b, x0, z0, w, d, rnd, kinds, seed):
    y = TOP + 1
    b.box(x0 - 2, TOP, z0 - 2, x0 + w + 1, TOP, z0 + d + 1, SQ)
    b.walls(x0, y, z0, x0 + w - 1, y + 11, z0 + d - 1, QB)
    b.box(x0 + 1, y, z0 + 1, x0 + w - 2, y + 11, z0 + d - 2, AIR)
    b.box(x0 + 1, y + 6, z0 + 1, x0 + w - 2, y + 6, z0 + d - 2, "minecraft:birch_planks")
    for x in range(x0, x0 + w, 3):
        for z in (z0, z0 + d - 1): b.column(x, z, y, y + 11, "minecraft:quartz_pillar[axis=y]")
    for x in range(x0 + 1, x0 + w - 1, 3):
        for z in (z0, z0 + d - 1):
            for yy in (y + 2, y + 3, y + 8, y + 9): b.set(x, yy, z, "minecraft:glass_pane"); b.set(x + 1, yy, z, "minecraft:glass_pane")
    b.hip_roof(x0, z0, x0 + w - 1, z0 + d - 1, y + 12, "minecraft:smooth_quartz_stairs", SQ, top=GOLD)
    for (cx, cz) in ((x0, z0), (x0 + w - 1, z0), (x0, z0 + d - 1), (x0 + w - 1, z0 + d - 1)):
        b.dome(cx, cz, y + 12, 2, s=GOLD, tip=None, hollow=False)
    mx = x0 + w // 2
    for yy in range(y, y + 4):
        for dx in (-1, 0, 1): b.set(mx + dx, yy, z0 + d - 1, AIR)
    I.furnish(b, x0 + 1, y, z0 + 1, x0 + w - 2, z0 + d - 2, 5, kinds[0], "royal", seed=seed)
    I.furnish(b, x0 + 1, y + 7, z0 + 1, x0 + w - 2, z0 + d - 2, 4, kinds[1], HOLY, seed=seed + 1)
    for yy in range(y, y + 7): b.set(x0 + 1, yy, z0 + 1, "minecraft:ladder[facing=south,waterlogged=false]")
    return mx, z0 + d


def build():
    rnd = random.Random(611)
    b = B()
    # ---------------- the Red Line: a wall of red rock, banded, with the Red Port below
    for x in range(N):
        for z in range(N):
            edge = CLIFF_Z + round(2 * math.sin(x * 0.21) + 1.5 * math.sin(x * 0.07))
            if z <= edge:
                for y in range(-2, TOP + 1):
                    b.set(x, y, z, RED if (y // 5) % 3 else ("minecraft:orange_terracotta" if (y // 5) % 2 else "minecraft:terracotta"))
            else:
                for y in (-2, -1): b.set(x, y, z, "minecraft:red_sandstone")
                b.set(x, 0, z, "minecraft:smooth_red_sandstone" if (x + z) % 3 else "minecraft:cut_red_sandstone")
    # ledges and crags on the cliff face
    for i in range(40):
        x = rnd.randint(2, N - 3); y = rnd.randint(4, TOP - 4)
        z = CLIFF_Z + round(2 * math.sin(x * 0.21) + 1.5 * math.sin(x * 0.07)) + 1
        b.box(x - rnd.randint(1, 3), y, z, x + rnd.randint(1, 3), y, z + rnd.randint(0, 1), "minecraft:orange_terracotta")
    # ---------------- the Red Port at the foot: dock buildings and the Bondola lift
    PZ = CLIFF_Z + 6
    for x0 in (6, 22, 78, 94):
        T.house(b, x0, PZ + 2, 12, 9, 1, "plaster", rnd, kinds=["storage"], theme="marine", door="south", flat_roof=True)
    LX = 56
    for (dx) in (-4, 4):  # the lift tower against the cliff
        b.column(LX + dx, PZ, 1, TOP + 6, "minecraft:white_concrete")
    for y in range(1, TOP + 7, 6):
        for x in range(LX - 4, LX + 5): b.set(x, y, PZ, "minecraft:white_concrete")
    b.box(LX - 3, 1, PZ - 3, LX + 3, 1, PZ + 3, SQ)
    b.box(LX - 2, 18, PZ - 2, LX + 2, 22, PZ + 2, GOLD); b.box(LX - 1, 19, PZ - 1, LX + 1, 21, PZ + 1, AIR)  # the Bondola cabin halfway up
    for y in range(23, TOP + 7): b.set(LX, y, PZ, "minecraft:chain[axis=y,waterlogged=false]")
    # the long cliff stair zig-zagging up the face (for those without a lift)
    x, y, dirx = 10, 1, 1
    while y < TOP:
        for k in range(14):
            if y >= TOP: break
            zc = CLIFF_Z + round(2 * math.sin(x * 0.21) + 1.5 * math.sin(x * 0.07)) + 1
            for dz in (0, 1): b.set(x, y, zc + dz, "minecraft:red_sandstone_stairs[facing=%s,half=bottom,shape=straight,waterlogged=false]" % ("east" if dirx > 0 else "west"))
            b.set(x, y + 1, zc + 2, "minecraft:red_sandstone_wall")
            for h in (1, 2, 3):
                for dz in (0, 1): b.set(x, y + h, zc + dz, AIR)
            x += dirx; y += 1
        dirx = -dirx
    # ---------------- on top: the Holy Gate
    GZ = CLIFF_Z - 4
    b.box(0, TOP, 0, N - 1, TOP, CLIFF_Z - 2, SQ)
    for xx in range(0, N):
        for zz in range(0, CLIFF_Z - 1):
            if (xx // 4 + zz // 4) % 2 == 0: b.set(xx, TOP, zz, "minecraft:white_concrete")
    for (dx) in (-10, 10):
        b.round_column(LX + dx, GZ, 2, TOP + 1, TOP + 20, "minecraft:quartz_pillar[axis=y]")
        b.dome(LX + dx, GZ, TOP + 21, 3, s=GOLD, tip=None)
    b.box(LX - 12, TOP + 18, GZ - 1, LX + 12, TOP + 20, GZ + 1, QB)
    for k in range(6): b.box(LX - 11 + k * 2, TOP + 21 + k, GZ, LX + 11 - k * 2, TOP + 21 + k, GZ, QB)
    b.box(LX - 3, TOP + 22, GZ + 1, LX + 3, TOP + 24, GZ + 1, GOLD)
    for z in range(16, GZ):
        for x in (LX - 2, LX - 1, LX, LX + 1, LX + 2): b.set(x, TOP, z, "minecraft:red_concrete" if abs(x - LX) < 2 else GOLD)
    # ---------------- Pangaea Castle (north)
    CX, CZ0, CZ1 = LX, 6, 40
    X0, X1 = CX - 22, CX + 22
    y = TOP + 1
    b.walls(X0, y, CZ0, X1, y + 22, CZ1, Q)
    b.box(X0 + 1, y, CZ0 + 1, X1 - 1, y + 22, CZ1 - 1, AIR)
    for yy in (y + 8, y + 15): b.box(X0 + 1, yy, CZ0 + 1, X1 - 1, yy, CZ1 - 1, "minecraft:birch_planks")
    for x in range(X0, X1 + 1, 4):
        for z in (CZ0, CZ1): b.column(x, z, y, y + 22, "minecraft:quartz_pillar[axis=y]")
    for x in range(X0 + 2, X1 - 1, 4):
        for z in (CZ0, CZ1):
            for yy in list(range(y + 2, y + 7)) + list(range(y + 10, y + 13)) + list(range(y + 17, y + 20)): b.set(x, yy, z, "minecraft:yellow_stained_glass_pane")
    b.box(X0, y + 23, CZ0, X1, y + 23, CZ1, SQ)
    for x in range(X0, X1 + 1, 2): b.set(x, y + 24, CZ0, GOLD); b.set(x, y + 24, CZ1, GOLD)
    b.dome(CX, (CZ0 + CZ1) // 2, y + 24, 12, s=SQ, tip=GOLD)
    b.cyl(CX, (CZ0 + CZ1) // 2, 12.5, y + 24, y + 25, GOLD, hollow=True)
    for (tx, tz) in ((X0, CZ0), (X1, CZ0), (X0, CZ1), (X1, CZ1)):
        b.cyl(tx, tz, 4, y, y + 32, QB); b.dome(tx, tz, y + 33, 4, s=GOLD, onion=True, tip=GOLD)
    for x in range(CX - 3, CX + 4):
        for yy in range(y, y + 7): b.set(x, yy, CZ1, AIR)
    for k in range(4): b.box(CX - 4, TOP + 1 + 0, CZ1 + 1 + k, CX + 4, TOP + 1, CZ1 + 1 + k, "minecraft:quartz_stairs[facing=south,half=bottom,shape=straight,waterlogged=false]" if k == 3 else SQ)
    # inside: the hall of the Empty Throne, the Five Elders' chamber, the flower room above
    for z in range(CZ0 + 1, CZ1):
        for yy in range(y, y + 8): b.set(CX - 10, yy, z, QB); b.set(CX + 10, yy, z, QB)
    for yy in (y, y + 1, y + 2): b.set(CX - 10, yy, CZ1 - 4, AIR); b.set(CX + 10, yy, CZ1 - 4, AIR)
    r = I.furnish(b, CX - 9, y, CZ0 + 1, CX + 9, CZ1 - 1, 7, "throne", "royal", seed=1)
    for z in range(CZ0 + 3, CZ1 - 2, 4):  # the twenty swords round the throne
        b.set(CX - 7, y, z, "minecraft:iron_bars[east=false,north=false,south=false,west=false,waterlogged=false]"); b.set(CX + 7, y, z, "minecraft:iron_bars[east=false,north=false,south=false,west=false,waterlogged=false]")
    I.furnish(b, X0 + 1, y, CZ0 + 1, CX - 11, CZ1 - 1, 7, "study", HOLY, seed=2)
    I.furnish(b, CX + 11, y, CZ0 + 1, X1 - 1, CZ1 - 1, 7, "library", HOLY, seed=3)
    I.subdivide(b, X0 + 1, y + 9, CZ0 + 1, X1 - 1, CZ1 - 1, 5, QB, ("dining", "bedroom", "bath", "bedroom", "kitchen", "treasure"), "royal", cell=13, corridor=3,
                keepout=((X0 + 1, CZ0 + 1, X0 + 3, CZ0 + 3),), seed=4)
    # the secret flower room under the dome: a garden of flowers and ice
    fy = y + 16
    for xx in range(X0 + 1, X1):
        for zz in range(CZ0 + 1, CZ1):
            b.set(xx, fy - 1, zz, "minecraft:moss_block" if (xx + zz) % 3 else "minecraft:packed_ice")
            if rnd.random() < 0.5: b.set(xx, fy, zz, rnd.choice(("minecraft:white_tulip", "minecraft:lily_of_the_valley", "minecraft:oxeye_daisy", "minecraft:azure_bluet", "minecraft:blue_orchid")))
    b.set(CX, fy, (CZ0 + CZ1) // 2, "minecraft:obsidian"); b.set(CX, fy + 1, (CZ0 + CZ1) // 2, "minecraft:crying_obsidian")
    for yy in range(y, y + 16): b.set(X0 + 2, yy, CZ0 + 2, "minecraft:ladder[facing=south,waterlogged=false]")
    for yy in (y + 8, y + 15): b.set(X0 + 2, yy, CZ0 + 2, "minecraft:ladder[facing=south,waterlogged=false]")
    # ---------------- the Celestial Dragons' mansions, gardens and statues
    spots = ((6, 50, 20, 14, ("dining", "bedroom")), (86, 50, 20, 14, ("tavern", "bedroom")), (6, 66, 18, 12, ("hall", "bedroom")), (88, 66, 18, 12, ("treasure", "bedroom")))
    for i, (x0, z0, w, d, kinds) in enumerate(spots):
        mansion(b, x0, z0, w, d, rnd, kinds, 10 + i * 3)
    for (fx, fz) in ((LX - 16, 60), (LX + 16, 60), (LX, 70)):
        b.cyl(fx, fz, 4, TOP + 1, TOP + 1, QB); b.cyl(fx, fz, 3, TOP + 1, TOP + 1, WATER)
        b.column(fx, fz, TOP + 1, TOP + 4, "minecraft:quartz_pillar[axis=y]"); b.set(fx, TOP + 5, fz, GOLD)
    for (sx, sz) in ((LX - 8, 50), (LX + 8, 50)):  # statues of the founding kings
        b.box(sx - 1, TOP + 1, sz - 1, sx + 1, TOP + 2, sz + 1, SQ)
        b.column(sx, sz, TOP + 3, TOP + 8, Q); b.set(sx - 1, TOP + 6, sz, Q); b.set(sx + 1, TOP + 6, sz, Q); b.set(sx, TOP + 9, sz, GOLD)
    for i in range(30):
        x, z = rnd.randint(3, N - 4), rnd.randint(44, CLIFF_Z - 6)
        if b.get(x, TOP + 1, z) is None and abs(x - LX) > 4:
            b.set(x, TOP + 1, z, rnd.choice(("minecraft:rose_bush[half=lower]", "minecraft:flowering_azalea", "minecraft:peony[half=lower]")))
            if "[half=lower]" in (b.get(x, TOP + 1, z) or ""): b.set(x, TOP + 2, z, b.get(x, TOP + 1, z).replace("lower", "upper"))
    # the slave quarters behind the mansions, cut into the rock
    b.box(28, TOP - 6, 60, 44, TOP - 1, 74, AIR)
    I.subdivide(b, 28, TOP - 6, 60, 44, 74, 4, "minecraft:polished_deepslate", ("cell", "cell", "cell", "storage"), "justice", cell=8, corridor=2, seed=30)
    for yy in range(TOP - 6, TOP + 1): b.set(44, yy, 67, "minecraft:ladder[facing=west,waterlogged=false]")
    b.set(44, TOP, 67, "minecraft:iron_trapdoor[facing=west,half=bottom,open=false,powered=false,waterlogged=false]")
    # ---------------- loot and guards
    b.chest(CX - 3, y, CZ0 + 3, "legendary", "south"); b.chest(CX + 3, y, CZ0 + 3, "celestial", "south")
    b.chest(CX, fy, (CZ0 + CZ1) // 2 + 2, "treasure", "south"); b.chest(10, TOP + 1, 52, "celestial", "east")
    b.guards("cp0_agent", ((CX - 4, CZ1 + 6), (CX + 4, CZ1 + 6), (CX, 24)), y=TOP + 1)
    b.guards("vice_admiral", ((LX, GZ - 4),), y=TOP + 1)
    b.guards("pacifista", ((LX - 14, GZ - 2), (LX + 14, GZ - 2)), y=TOP + 1)
    b.guards("marine", ((LX - 5, PZ + 4), (LX + 5, PZ + 4)))
    return b, 0

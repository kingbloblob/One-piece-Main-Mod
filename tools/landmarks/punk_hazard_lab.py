"""Punk Hazard, the island cut in two: the west half frozen solid (snow, ice, frozen lake and wrecked tanks), the
east half burning (scorched rock, lava streams, smoking vents). Between them stands Caesar Clown's laboratory
complex, Research Building R-66: a long white three-storey lab with a domed hall, the gas tanks, the glass
'Biscuit Room' where the children were kept, the SAD tank chamber, Caesar's office, Vegapunk's old archive and
the stores. ~108 x 96. Ground = y 0."""
import math, random
from canvas import *
import interiors as I

SID = "punk_hazard_lab"
TITLE = "Punk Hazard Laboratory"
CUTS = [2, 9, 16]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")

NX, NZ = 108, 96
MIDX = 54
LAB = dict(wood="birch", rug="cyan", rug2="white", bed="white", light="onepiece:lab_light", accent="onepiece:lab_panel",
           banner="cyan", candle="white")
KIDS = dict(wood="cherry", rug="pink", rug2="yellow", bed="pink", light="minecraft:pearlescent_froglight[axis=y]", accent="onepiece:candy_cane_block",
            banner="pink", candle="pink")
WHITE = "minecraft:white_concrete"
X0, X1, Z0, Z1 = 28, 80, 30, 62


def build():
    rnd = random.Random(531)
    b = B()
    for x in range(NX):
        for z in range(NZ):
            cold = x + 4 * math.sin(z * 0.15) < MIDX
            for y in (-3, -2, -1): b.set(x, y, z, "minecraft:packed_ice" if cold else "minecraft:basalt[axis=y]")
            if cold:
                b.set(x, 0, z, "minecraft:snow_block" if (x + z) % 7 else "minecraft:packed_ice")
                if rnd.random() < 0.2: b.set(x, 1, z, "minecraft:snow[layers=%d]" % rnd.randint(1, 3))
            else:
                b.set(x, 0, z, rnd.choice(("minecraft:blackstone", "minecraft:basalt[axis=y]", "onepiece:scorched_stone", "minecraft:magma_block" if rnd.random() < 0.2 else "minecraft:blackstone")))
    # the frozen side: ice spikes, a frozen lake, wrecked tanks
    for i in range(12):
        x, z = rnd.randint(2, MIDX - 10), rnd.choice((rnd.randint(2, 24), rnd.randint(68, NZ - 3)))
        h = rnd.randint(5, 14)
        for y in range(1, h): b.cyl(x, z, max(0.5, 1.6 * (1 - y / h)), y, y, "minecraft:packed_ice")
    for x in range(6, 22):
        for z in range(40, 58):
            if ((x - 14) / 8) ** 2 + ((z - 49) / 9) ** 2 < 1: b.set(x, 0, z, "minecraft:ice"); b.set(x, 1, z, AIR)
    for (x, z) in ((18, 72), (10, 20)):
        b.box(x, 1, z, x + 6, 3, z + 3, "minecraft:gray_concrete"); b.box(x + 2, 4, z + 1, x + 4, 4, z + 2, "minecraft:gray_concrete")
        for xx in range(x + 4, x + 10): b.set(xx, 4, z + 1, "minecraft:iron_block")
        b.set(x + 3, 4, z + 3, "minecraft:snow_block")
    # the burning side: lava streams and smoking vents
    for i in range(3):
        z = 10 + i * 34
        for x in range(MIDX + 30, NX):
            zz = round(z + 3 * math.sin(x * 0.3))
            for dz in (-1, 0, 1): b.set(x, 0, zz + dz, "minecraft:lava[level=0]" if dz == 0 else "minecraft:magma_block")
    for i in range(10):
        x, z = rnd.randint(MIDX + 30, NX - 3), rnd.randint(3, NZ - 3)
        b.set(x, 1, z, "minecraft:campfire[facing=north,lit=true,signal_fire=true,waterlogged=false]")
        b.cyl(x, z, 1.5, 0, 0, "minecraft:basalt[axis=y]")
    # ---------------- Research Building R-66
    FL = (1, 8, 15)
    b.box(X0 - 2, 0, Z0 - 2, X1 + 2, 0, Z1 + 2, "minecraft:polished_andesite")
    b.walls(X0, 1, Z0, X1, 21, Z1, WHITE)
    b.box(X0 + 1, 1, Z0 + 1, X1 - 1, 21, Z1 - 1, AIR)
    for y in (7, 14):
        b.box(X0 + 1, y, Z0 + 1, X1 - 1, y, Z1 - 1, "minecraft:smooth_stone")
        for x in range(X0, X1 + 1): b.set(x, y, Z0, "minecraft:cyan_concrete"); b.set(x, y, Z1, "minecraft:cyan_concrete")
    b.box(X0, 22, Z0, X1, 22, Z1, "minecraft:light_gray_concrete")
    for x in range(X0 + 2, X1 - 1, 4):
        for z in (Z0, Z1):
            for fy in FL:
                for y in (fy + 2, fy + 3): b.set(x, y, z, "minecraft:light_blue_stained_glass_pane"); b.set(x + 1, y, z, "minecraft:light_blue_stained_glass_pane")
    for z in range(Z0 + 3, Z1 - 2, 4):
        for x in (X0, X1):
            for fy in FL:
                for y in (fy + 2, fy + 3): b.set(x, y, z, "minecraft:light_blue_stained_glass_pane"); b.set(x, y, z + 1, "minecraft:light_blue_stained_glass_pane")
        for x in (X0, X1): b.set(x, 7, z, "minecraft:cyan_concrete"); b.set(x, 14, z, "minecraft:cyan_concrete")
    for z in range(Z0, Z1 + 1):
        for x in (X0, X1): b.set(x, 7, z, "minecraft:cyan_concrete"); b.set(x, 14, z, "minecraft:cyan_concrete")
    for (cx, cz) in ((X0, Z0), (X1, Z0), (X0, Z1), (X1, Z1)): b.column(cx, cz, 1, 23, "minecraft:cyan_concrete")
    MX, MZ = (X0 + X1) // 2, (Z0 + Z1) // 2
    b.dome(MX, MZ, 23, 13, s="minecraft:white_concrete", tip=None)
    b.cyl(MX, MZ, 13.5, 23, 23, "minecraft:cyan_concrete", hollow=True)
    for x in range(MX - 3, MX + 4):
        for y in (1, 2, 3, 4): b.set(x, y, Z1, AIR)
    b.text(MX - 3, 16, Z1 + 1, "R-66", "minecraft:cyan_concrete")
    # stairs: ladder shafts at both ends
    for (lx, f) in ((X0 + 1, "east"), (X1 - 1, "west")):
        for y in range(1, 21): b.set(lx, y, MZ, f"minecraft:ladder[facing={f},waterlogged=false]")
        for y in (7, 14): b.set(lx, y, MZ, f"minecraft:ladder[facing={f},waterlogged=false]")
    # ground floor: entrance hall, SAD chamber, stores and the gas works
    I.furnish(b, MX - 8, 1, MZ + 2, MX + 8, Z1 - 1, 5, "hall", LAB, seed=1)
    sx, sz = MX, MZ - 6  # the SAD tank chamber
    b.walls(sx - 7, 1, Z0 + 1, sx + 7, 6, MZ, "onepiece:lab_panel"); b.box(sx - 6, 1, Z0 + 2, sx + 6, 6, MZ - 1, AIR)
    b.cyl(sx, sz, 3, 1, 6, "minecraft:purple_stained_glass", hollow=True); b.cyl(sx, sz, 2, 1, 5, "minecraft:purple_concrete_powder" if False else "minecraft:amethyst_block")
    b.cyl(sx, sz, 2, 6, 6, "minecraft:iron_block")
    for (dx, dz) in ((-5, -2), (5, -2), (-5, 3), (5, 3)): b.column(sx + dx, sz + dz, 1, 4, "minecraft:iron_bars[east=false,north=false,south=false,west=false,waterlogged=false]"); b.set(sx + dx, sz + dz, 5, "onepiece:lab_light") if False else b.set(sx + dx, 5, sz + dz, "onepiece:lab_light")
    for y in (1, 2): b.set(sx, y, MZ, AIR)
    I.subdivide(b, X0 + 2, 1, Z0 + 1, MX - 9, Z1 - 1, 5, "onepiece:lab_panel", ("storage", "workshop", "lab"), LAB, cell=10, corridor=2, seed=2)
    I.subdivide(b, MX + 9, 1, Z0 + 1, X1 - 2, Z1 - 1, 5, "onepiece:lab_panel", ("lab", "storage", "kitchen"), LAB, cell=10, corridor=2, seed=3)
    # first floor: the Biscuit Room (the children's room) and labs
    kx0, kx1 = MX - 12, MX + 12
    b.walls(kx0, 8, Z0 + 1, kx1, 13, Z1 - 1, "minecraft:glass")
    b.box(kx0 + 1, 8, Z0 + 2, kx1 - 1, 13, Z1 - 2, AIR)
    for (x0, x1, z0, z1, kind) in ((kx0 + 1, MX - 1, Z0 + 2, MZ, "bedroom"), (MX + 1, kx1 - 1, Z0 + 2, MZ, "bedroom"), (kx0 + 1, kx1 - 1, MZ + 1, Z1 - 2, "dining")):
        I.furnish(b, x0, 8, z0, x1, z1, 5, kind, KIDS, seed=x0 + z0)
    for y in (8, 9): b.set(MX, y, Z1 - 1, AIR)
    I.subdivide(b, X0 + 2, 8, Z0 + 1, kx0 - 1, Z1 - 1, 5, "onepiece:lab_panel", ("lab", "library"), LAB, cell=10, corridor=2, seed=4)
    I.subdivide(b, kx1 + 1, 8, Z0 + 1, X1 - 2, Z1 - 1, 5, "onepiece:lab_panel", ("lab", "cell"), LAB, cell=10, corridor=2, seed=5)
    # second floor: Caesar's office, Vegapunk's archive, the control room
    I.subdivide(b, X0 + 2, 15, Z0 + 1, X1 - 2, Z1 - 1, 6, "onepiece:lab_panel", ("study", "library", "lab", "treasure", "lab", "bedroom"), LAB, cell=12, corridor=3, seed=6)
    # gas tanks outside
    for (tx, tz) in ((X0 - 8, Z0 + 4), (X0 - 8, Z0 + 14), (X1 + 8, Z0 + 4), (X1 + 8, Z0 + 14)):
        b.cyl(tx, tz, 3, 1, 9, "minecraft:white_concrete"); b.dome(tx, tz, 10, 3, s="minecraft:white_concrete", tip=None, hollow=False)
        b.cyl(tx, tz, 3.4, 5, 5, "minecraft:purple_concrete", hollow=True)
        b.line((tx, 8, tz), (X0 if tx < MX else X1, 12, tz), "minecraft:iron_block")
    # ---------------- people and loot
    b.npc(X0 + 6, 15, Z0 + 5, "vegapunk", False); b.npc(MX + 3, 1, Z1 - 4, "law", False)
    b.chest(X1 - 4, 1, Z0 + 3, "lab", "west"); b.chest(X0 + 4, 15, Z1 - 3, "lab", "east")
    b.guards("frost_soldier", ((MX - 4, Z1 + 4), (MX + 4, Z1 + 4), (20, 60), (MX, MZ + 5)))
    return b, 0

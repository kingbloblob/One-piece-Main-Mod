"""The Prisoner Mine of Udon in Wano: Kaido's labour camp. Behind a palisade and gate towers on the surface, a huge
open pit is dug down in terraces to the sumo ring at the bottom. Barred cells are cut into every terrace,
walkways and ladders link the levels, mine tunnels with rails and carts run off into the rock past veins of ore,
and the headliner's watch office with its windows and a giant cauldron of red-bean soup sit on the rim.
~96 x 96. Ground = y 0, the pit 28 deep."""
import math, random
from canvas import *
import interiors as I
import townkit as T
import kamazo_hideout as KH

SID = "udon_prison"
TITLE = "Udon Prisoner Mine"
CUTS = [2, -9, -19]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")

N = 96
CX, CZ = 48, 50
ROCK = "minecraft:cobbled_deepslate"
BARS = "onepiece:prison_bars"
DEPTH = 28
TERR = 7  # levels
GUARD = dict(wood="dark_oak", rug="purple", rug2="black", bed="purple", light="onepiece:paper_lantern[hanging=true]", accent="onepiece:wano_lacquer_planks",
             banner="purple", candle="purple")


def terrace_r(level):
    return 30 - level * 3.2


def build():
    rnd = random.Random(631)
    b = B()
    T.ground(b, N, N, rnd, top="minecraft:coarse_dirt", deco=0.04, decos=("minecraft:dead_bush",))
    for x in range(N):
        for z in range(N):
            for y in range(-DEPTH - 8, -3): b.set(x, y, z, "minecraft:deepslate" if y < -14 else "minecraft:stone")
            for y in (-3, -2, -1): b.set(x, y, z, "minecraft:dirt")
    # ---------------- the open pit, in terraces
    step = DEPTH // TERR
    for x in range(N):
        for z in range(N):
            d = math.hypot(x - CX, z - CZ)
            for lv in range(TERR + 1):
                if d < terrace_r(lv):
                    top = -lv * step
                    for y in range(top, 2): b.set(x, y, z, AIR)
                    b.set(x, top - 1, z, "minecraft:gravel" if (x + z) % 5 == 0 else ROCK) if lv < TERR else b.set(x, top - 1, z, "minecraft:packed_mud")
    # barred cells cut into each terrace wall, with a walkway rail on the edge
    for lv in range(1, TERR):
        y0 = -lv * step
        r = terrace_r(lv)
        for k in range(int(2 * math.pi * r / 6)):
            a = k * 6 / r
            ox, oz = CX + (r + 0.5) * math.cos(a), CZ + (r + 0.5) * math.sin(a)
            ix, iz = round(ox), round(oz)
            for dd in (1, 2, 3):
                cx2, cz2 = round(CX + (r + dd) * math.cos(a)), round(CZ + (r + dd) * math.sin(a))
                for y in (y0, y0 + 1, y0 + 2): b.set(cx2, y, cz2, AIR)
                b.set(cx2, y0 - 1, cz2, "minecraft:gravel" if False else ROCK)
            for y in (y0, y0 + 1, y0 + 2): b.set(ix, y, iz, BARS)
            ex, ez = round(CX + (r + 3) * math.cos(a)), round(CZ + (r + 3) * math.sin(a))
            b.set(ex, y0, ez, rnd.choice(("minecraft:brown_carpet", "minecraft:cobweb", "minecraft:hay_block[axis=y]", "minecraft:iron_chain[axis=y]")))
        for a in range(0, 360, 30):  # lanterns on posts along the walkway
            t = math.radians(a + lv * 7)
            b.set(round(CX + (r - 1) * math.cos(t)), y0, round(CZ + (r - 1) * math.sin(t)), "minecraft:dark_oak_fence")
            b.set(round(CX + (r - 1) * math.cos(t)), y0 + 1, round(CZ + (r - 1) * math.sin(t)), "onepiece:paper_lantern[hanging=false]")
    # ladders linking the terraces (south side)
    for lv in range(TERR):
        y0 = -(lv + 1) * step
        r = terrace_r(lv + 1)
        lz = round(CZ + r + 0.5)
        for y in range(y0, y0 + step + 1): b.set(CX, y, lz, "minecraft:ladder[facing=north,waterlogged=false]")
        if b.get(CX, y0, lz + 1) is None: b.set(CX, y0, lz + 1, ROCK)
    # mine tunnels with rails, carts and ore veins
    for (lv, ang) in ((2, 0.3), (4, 2.4), (5, 4.1), (3, 5.2)):
        y0 = -lv * step
        r0 = terrace_r(lv) + 3
        for t in range(0, 22):
            x, z = CX + (r0 + t) * math.cos(ang), CZ + (r0 + t) * math.sin(ang)
            if not (2 < x < N - 3 and 2 < z < N - 3): break
            for dx in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    for y in (y0, y0 + 1, y0 + 2): b.set(round(x + dx), y, round(z + dz), AIR)
            b.set(round(x), y0, round(z), "minecraft:rail[shape=north_south,waterlogged=false]" if abs(math.sin(ang)) > 0.7 else "minecraft:rail[shape=east_west,waterlogged=false]")
            if t % 5 == 0:
                for (dx, dz) in ((-2, 0), (2, 0), (0, -2), (0, 2)): b.fill_if(round(x + dx), y0 + 2, round(z + dz), "minecraft:spruce_log[axis=y]", only_empty=False) if False else None
                b.set(round(x), y0 + 3, round(z), "minecraft:spruce_planks")
                b.set(round(x) + 1, y0 + 2, round(z), "minecraft:lantern[hanging=true,waterlogged=false]")
            if rnd.random() < 0.35:
                ox, oz = round(x + rnd.choice((-2, 2))), round(z + rnd.choice((-2, 2)))
                b.set(ox, y0 + rnd.randint(0, 2), oz, rnd.choice(("minecraft:deepslate_coal_ore", "minecraft:deepslate_iron_ore", "minecraft:deepslate_gold_ore", "onepiece:deepslate_kokuto_ore")))
        b.set(round(CX + (r0 + 2) * math.cos(ang)), y0 + 1, round(CZ + (r0 + 2) * math.sin(ang)), "minecraft:chest_minecart" if False else "minecraft:barrel[facing=up,open=false]")
    # the sumo ring at the bottom
    yb = -TERR * step
    b.cyl(CX, CZ, 6, yb - 1, yb - 1, "minecraft:sand" if False else "minecraft:smooth_sandstone")
    b.cyl(CX, CZ, 6, yb, yb, "minecraft:hay_block[axis=y]", hollow=True)
    for (dx, dz) in ((-8, -8), (8, -8), (-8, 8), (8, 8)):
        b.column(CX + dx, CZ + dz, yb, yb + 8, "minecraft:dark_oak_log[axis=y]")
    for x in range(CX - 8, CX + 9):
        b.set(x, yb + 9, CZ - 8, "minecraft:purple_wool"); b.set(x, yb + 9, CZ + 8, "minecraft:purple_wool")
    for z in range(CZ - 8, CZ + 9):
        b.set(CX - 8, yb + 9, z, "minecraft:purple_wool"); b.set(CX + 8, yb + 9, z, "minecraft:purple_wool")
    # ---------------- on the surface: palisade, gate towers, the watch office and the soup cauldron
    for a in range(0, 360, 2):
        t = math.radians(a)
        x, z = round(CX + 40 * math.cos(t)), round(CZ + 40 * math.sin(t))
        if 0 <= x < N and 0 <= z < N:
            for y in range(1, 6): b.set(x, y, z, "minecraft:stripped_spruce_log[axis=y]" if y < 5 else "minecraft:spruce_fence")
    for x in range(CX - 3, CX + 4):
        for y in range(1, 6): b.set(x, y, CZ + 40, AIR) if CZ + 40 < N else None
    for dx in (-5, 5):
        gx, gz = CX + dx, min(N - 3, CZ + 40)
        b.box(gx - 1, 1, gz - 1, gx + 1, 10, gz + 1, "minecraft:dark_oak_planks"); b.box(gx - 2, 11, gz - 2, gx + 2, 11, gz + 2, "onepiece:wano_lacquer_planks")
        b.pagoda_roof(gx, gz, 3, 3, 12, "onepiece:wano_roof_tile_stairs", "onepiece:wano_roof_tiles", layers=1)
    ox, oz = KH.wano_house(b, CX - 12, 2, CX + 12, 14, 5, roof_layers=2, door_side="south")
    I.furnish(b, CX - 11, 2, 3, CX - 1, 13, 5, "study", GUARD, seed=1)
    I.furnish(b, CX + 1, 2, 3, CX + 11, 13, 5, "barracks", GUARD, seed=2)
    for z in range(3, 14):
        for y in range(2, 7): b.set(CX, y, z, "onepiece:shoji_screen")
    b.set(CX, 2, 8, AIR); b.set(CX, 3, 8, AIR)
    b.cyl(CX + 22, 14, 3, 1, 3, "minecraft:iron_block", hollow=True); b.cyl(CX + 22, 14, 2, 1, 2, "minecraft:red_concrete"); b.cyl(CX + 22, 14, 3.5, 0, 0, "minecraft:magma_block")
    for (x, z) in ((CX - 28, 20), (CX + 28, 24)):
        b.box(x - 4, 1, z - 3, x + 4, 4, z + 3, "minecraft:spruce_planks"); b.box(x - 3, 1, z - 2, x + 3, 4, z + 2, AIR)
        b.box(x - 4, 5, z - 3, x + 4, 5, z + 3, "minecraft:spruce_slab[type=bottom,waterlogged=false]")
        b.set(x, 1, z + 3, AIR); b.set(x, 2, z + 3, AIR)
        I.furnish(b, x - 3, 1, z - 2, x + 3, z + 2, 3, "storage", GUARD, seed=x)
    # ---------------- loot and guards
    b.chest(CX - 9, 2, 4, "hard", "east"); b.chest(CX + 4, yb, CZ + 4, "hard", "north"); b.chest(CX - 4, yb, CZ - 4, "wano", "south")
    b.guards("gifter", ((CX - 6, CZ + 34), (CX + 6, CZ + 34), (CX - 20, 24)), y=1)
    b.guards("gifter", ((CX + int(terrace_r(3)) - 2, CZ), (CX - int(terrace_r(3)) + 2, CZ)), y=-3 * step)
    b.guards("headliner", ((CX, CZ - 4),), y=yb)
    b.guards("war_beast", ((CX + 4, CZ),), y=yb)
    return b, 0

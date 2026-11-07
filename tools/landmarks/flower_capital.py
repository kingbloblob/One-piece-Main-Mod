"""The Flower Capital of Wano: the shogun's great castle towering at the north end on its high, battered stone base
(ishigaki), five white storeys under sweeping dark-tiled eaves with triangular gables, gold-tipped ridges and golden
shachihoko on the top roof, ringed by its moat and red bridge. Below it the city: a grid of streets lined with
two-storey timber houses and shops (the teahouse of the oiran Komurasaki, the sake brewery, the sword smith, the soba
stall, the bathhouse) with posts and beams on their fronts, noren curtains, tiled awnings and gabled roofs, red
lacquered teahouses among them, sakura along the canal, paper lanterns strung over the main avenue and the red torii at
the city gate. ~116 x 116. Ground = y 0."""
import math, random
from canvas import *
import interiors as I
import townkit as T
import kamazo_hideout as KH
import onigashima as OG
import wano_house as WH

SID = "flower_capital"
TITLE = "Flower Capital (Wano)"
CUTS = [3, 20]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")

N = 116
CX = 58
PLAST = "minecraft:white_concrete"
ROOF = "onepiece:wano_roof_tiles"
ROOF_ST = "onepiece:wano_roof_tile_stairs"
POST = "minecraft:dark_oak_log[axis=y]"
LAQ = "onepiece:wano_lacquer_planks"
TSLAB = "onepiece:wano_roof_tile_slab"
BEAM_BR = "minecraft:dark_oak_planks"
STONES = ("minecraft:stone_bricks", "minecraft:stone_bricks", "minecraft:stone_bricks", "minecraft:mossy_stone_bricks", "minecraft:cracked_stone_bricks", "minecraft:andesite")


def low_gable(b, x0, z0, x1, z1, y, wall):
    """A shallow tiled gable roof (half pitch, in slab steps) with its ridge along x, overhanging one block all round.
    Returns the ridge height."""
    za, zb = z0 - 1, z1 + 1
    n = (zb - za) // 2
    for i in range(n + 1):
        yy = y + i // 2
        kind = "bottom" if i % 2 == 0 else "top"
        for x in range(x0 - 1, x1 + 2):
            for z in {za + i, zb - i}:
                b.set(x, yy, z, slab(TSLAB, kind))
                for k in range(y, yy): b.set(x, k, z, ROOF if x0 < x < x1 else wall if x in (x0, x1) else ROOF)
    for x in range(x0 - 1, x1 + 2): b.set(x, y + n // 2, za + n, ROOF)  # the ridge
    return y + n // 2


def machiya(b, x0, z0, w, d, rnd, kinds, door="south"):
    """A two-storey Wano town house / shop: timber frame with posts and beams on the front, an open shop front with a
    noren curtain under a tiled awning, latticed shoji upstairs, and a gabled tiled roof overhanging all round."""
    x1, z1 = x0 + w - 1, z0 + d - 1
    red = rnd.random() < 0.22   # a red lacquered teahouse
    wallm = LAQ if red else rnd.choice((PLAST, PLAST, "minecraft:spruce_planks", "minecraft:stripped_spruce_log[axis=y]"))
    b.box(x0, 0, z0, x1, 0, z1, "minecraft:stone_bricks")
    b.box(x0, 1, z0, x1, 1, z1, "minecraft:spruce_planks")
    b.walls(x0, 2, z0, x1, 9, z1, wallm)
    b.walls(x0, 2, z0, x1, 3, z1, "minecraft:dark_oak_planks")  # dark boarding along the foot of the walls
    b.box(x0 + 1, 2, z0 + 1, x1 - 1, 9, z1 - 1, AIR)
    for x in range(x0, x1 + 1, 3):
        b.column(x, z0, 2, 9, POST); b.column(x, z1, 2, 9, POST)
    for (px, pz) in ((x1, z0), (x1, z1)): b.column(px, pz, 2, 9, POST)
    for z in (z0 + d // 2,): b.column(x0, z, 2, 9, POST); b.column(x1, z, 2, 9, POST)
    for x in range(x0, x1 + 1): b.set(x, 6, z0, "minecraft:dark_oak_planks"); b.set(x, 6, z1, "minecraft:dark_oak_planks")
    for z in range(z0, z1 + 1): b.set(x0, 6, z, "minecraft:dark_oak_planks"); b.set(x1, 6, z, "minecraft:dark_oak_planks")
    b.box(x0 + 1, 6, z0 + 1, x1 - 1, 6, z1 - 1, "minecraft:dark_oak_planks")
    fz = z1 if door == "south" else z0
    out = 1 if door == "south" else -1
    cloth = rnd.choice(("minecraft:blue_wool", "minecraft:red_wool", "minecraft:white_wool", "minecraft:purple_wool"))
    for x in range(x0 + 1, x1):
        if (x - x0) % 3 == 0: continue  # keep the posts
        for y in (2, 3, 4): b.set(x, y, fz, AIR)
        b.set(x, 5, fz, cloth)  # noren
        b.set(x, 7, fz, "onepiece:shoji_screen"); b.set(x, 8, fz, "onepiece:shoji_screen")
    for x in range(x0 - 1, x1 + 2):  # tiled awning (hisashi) over the shop front, stepping down to the street
        b.set(x, 6, fz + out, stairs(ROOF_ST, OPP[door])); b.set(x, 5, fz + out * 2, stairs(ROOF_ST, OPP[door]))
    for y in range(2, 8): b.set(x0 + 1, y, z0 + 1 if door == "south" else z1 - 1, "minecraft:ladder[facing=%s,waterlogged=false]" % ("south" if door == "south" else "north"))
    I.furnish(b, x0 + 1, 2, z0 + 1, x1 - 1, z1 - 1, 3, kinds[0], "wano", seed=x0 * 7 + z0)
    I.furnish(b, x0 + 1, 7, z0 + 1, x1 - 1, z1 - 1, 2, kinds[1], "wano", seed=x0 * 11 + z0)
    top = low_gable(b, x0, z0, x1, z1, 10, wallm)
    b.set(x0 - 1, top + 1, z0 + d // 2, ROOF); b.set(x1 + 1, top + 1, z0 + d // 2, ROOF)  # ridge-end tiles
    for x in (x0 + 2, x1 - 2): b.set(x, 4, fz + out * 2, "onepiece:paper_lantern[hanging=true]")  # hung under the awning
    if red:
        for x in range(x0, x1 + 1, 3): b.set(x, 1, fz + out, "minecraft:red_carpet")


def build():
    rnd = random.Random(571)
    b = B()
    T.ground(b, N, N, rnd, deco=0.04)
    # ---------------- the shogun's castle on its battered stone base (north)
    KX, KZ = CX, 24
    BH = 12                      # height of the stone base
    bx, bz = 22, 16              # half size of the base at the ground
    for y in range(1, BH + 1):   # ishigaki: curved, battered walls, steeper toward the top
        ins = int(round(5 * (y / BH) ** 1.5))
        for x in range(KX - bx + ins, KX + bx - ins + 1):
            for z in range(KZ - bz + ins, KZ + bz - ins + 1):
                edge = x in (KX - bx + ins, KX + bx - ins) or z in (KZ - bz + ins, KZ + bz - ins)
                corner = x in (KX - bx + ins, KX + bx - ins) and z in (KZ - bz + ins, KZ + bz - ins)
                if corner: s_ = "minecraft:polished_andesite" if y % 2 else "minecraft:smooth_stone"   # long-and-short corner stones
                elif edge: s_ = STONES[(x * 31 + z * 17 + y * 7) % len(STONES)]
                else: s_ = "minecraft:stone"
                b.set(x, y, z, s_)
    tw, tz = bx - 5, bz - 5      # the platform on top of the base
    b.box(KX - tw, BH, KZ - tz, KX + tw, BH, KZ + tz, "minecraft:gravel")
    for x in range(KX - tw, KX + tw + 1):  # low white wall with a tiled cap round the top of the base
        for z in (KZ - tz, KZ + tz):
            if abs(x - KX) > 3 or z == KZ - tz: b.set(x, BH + 1, z, PLAST); b.set(x, BH + 2, z, ROOF)
    for z in range(KZ - tz, KZ + tz + 1):
        for x in (KX - tw, KX + tw): b.set(x, BH + 1, z, PLAST); b.set(x, BH + 2, z, ROOF)
    # the keep: five storeys, each under a sweeping eave, triangular gables on the city side, gold on the top roof
    tiers = ((14, 9, 9), (12, 8, 8), (10, 6, 7), (8, 5, 7), (6, 4, 6))
    y = BH + 1
    ty = []
    for i, (hw, hd, h) in enumerate(tiers):
        OG.tier(b, KX - hw, KX + hw, KZ - hd, KZ + hd, y, h, floor="minecraft:dark_oak_planks" if i else None, lower=None, sparse=True)
        if i == 0: b.box(KX - hw + 1, y - 1, KZ - hd + 1, KX + hw - 1, y - 1, KZ + hd - 1, "minecraft:dark_oak_planks")
        top = y + h - 1
        ty.append((hw, hd, y, h))
        if i < len(tiers) - 1:
            b.box(KX - hw, top + 1, KZ - hd, KX + hw, top + 1, KZ + hd, ROOF)
            OG.eave(b, KX - hw, KX + hw, KZ - hd, KZ + hd, top, depth=2)
        if i in (1, 3):
            OG.chidori(b, KX, KZ + hd, top, 4 if i == 1 else 3, side=1)
            OG.chidori(b, KX, KZ - hd, top, 4 if i == 1 else 3, side=-1)
        if i == 2:  # paired gables on the east and west of the middle storey
            for sx in (-1, 1): OG.chidori(b, KX + sx * 6, KZ + hd, top, 2, side=1)
        y = top + 2
    hw, hd, y0, h = ty[-1]
    b.hip_roof(KX - hw, KZ - hd, KX + hw, KZ + hd, y0 + h, ROOF_ST, ROOF, overhang=3)
    ridge = y0 + h + (2 * hd + 6) // 2 + 1
    for sx in (-1, 1):  # golden shachihoko at the ends of the ridge
        b.set(KX + sx * 3, ridge, KZ, "minecraft:gold_block"); b.set(KX + sx * 3, ridge + 1, KZ, "minecraft:gold_block")
        b.set(KX + sx * 3, ridge + 2, KZ, stairs("minecraft:smooth_sandstone_stairs", "east" if sx < 0 else "west"))
    # the gate of the keep on the city side, and the grand stair up the stone base
    gz = KZ + tiers[0][1]
    for x in range(KX - 2, KX + 3):
        for yy in range(BH + 1, BH + 5): b.set(x, yy, gz, AIR)
    for yy in range(BH + 1, BH + 6): b.set(KX - 3, yy, gz + 1, LAQ); b.set(KX + 3, yy, gz + 1, LAQ)
    for x in range(KX - 3, KX + 4): b.set(x, BH + 5, gz + 1, LAQ)
    b.stairs_up(KX - 3, 1, KZ + bz + 6, BH + 0, "minecraft:stone_brick_stairs", "north", w=7, clear=4)
    for k in range(1, BH):  # solid under the steps
        for x in range(KX - 3, KX + 4):
            for yy in range(1, 1 + k): b.set(x, yy, KZ + bz + 6 - k, "minecraft:stone_bricks")
    for k in range(BH):  # side walls of the stair cut
        for sx in (-4, 4):
            for yy in range(1, k + 3): b.set(KX + sx, yy, KZ + bz + 6 - k, STONES[(k + yy) % len(STONES)])
    for (x, z) in ((KX - 7, KZ + bz + 5), (KX + 7, KZ + bz + 5)): KH.stone_lantern(b, x, z)
    # one ladder up through every storey
    for yy in range(BH + 1, ty[-1][2] + 1):
        b.set(KX - 4, yy, KZ - 1, "minecraft:dark_oak_planks"); b.set(KX - 4, yy, KZ, "minecraft:ladder[facing=south,waterlogged=false]")
    base = BH
    for i, (hw, hd, y0, h) in enumerate(ty):
        kind = ("throne", "hall", "armory", "library", "treasure")[i]
        I.furnish(b, KX - hw + 1, y0, KZ - hd + 1, KX + hw - 1, KZ + hd - 1, h - 1, kind, "kaido" if i == 0 else "wano", seed=i)
    # the castle's outer wall with corner turrets, and the castle garden
    for x in range(4, N - 4):
        for z in (4,):
            for yy in range(1, 6): b.set(x, yy, z, PLAST if yy > 1 else "minecraft:stone_bricks")
            b.set(x, 6, z, ROOF)
    for z in range(4, KZ + 25):
        for x in (4, N - 5):
            for yy in range(1, 6): b.set(x, yy, z, PLAST if yy > 1 else "minecraft:stone_bricks")
            b.set(x, 6, z, ROOF)
    for (tx, tz) in ((7, 7), (N - 8, 7)):
        OG.pagoda(b, tx, tz, 3, 2)
    for (x, z) in ((12, 18), (14, 36), (N - 13, 18), (N - 15, 36), (24, 44), (N - 25, 44)): WH.sakura(b, x, z, rnd, h=6)
    for (x, z) in ((KX - 9, KZ + 21), (KX + 9, KZ + 21)): KH.stone_lantern(b, x, z)
    bx0 = 8
    KH.wano_house(b, bx0, 26, bx0 + 14, 40, 4, roof_layers=1, door_side="south") if False else None
    # the moat and red bridge
    MZ = KZ + 28
    for x in range(4, N - 4):
        for dz in range(-2, 3):
            b.set(x, 0, MZ + dz, WATER); b.set(x, -1, MZ + dz, WATER); b.set(x, -2, MZ + dz, "minecraft:clay")
            b.set(x, 1, MZ + dz, AIR)
        b.set(x, 0, MZ - 3, "minecraft:stone_bricks"); b.set(x, 0, MZ + 3, "minecraft:stone_bricks")
    for z in range(MZ - 4, MZ + 5):
        dy = 1 if abs(z - MZ) < 3 else 0
        for x in range(KX - 2, KX + 3): b.set(x, dy + 1, z, "minecraft:red_concrete" if dy else "minecraft:spruce_planks")
        b.set(KX - 3, dy + 2, z, "minecraft:red_concrete"); b.set(KX + 3, dy + 2, z, "minecraft:red_concrete")
    for x in range(4, N - 4, 8):
        WH.sakura(b, x, MZ + 5, rnd, h=5) if abs(x - KX) > 8 else None
    # ---------------- the city grid of machiya
    streets_z = (MZ + 9, MZ + 33, MZ + 57)
    for z in streets_z:
        for x in range(4, N - 4):
            for dz in (-1, 0, 1): b.set(x, 0, z + dz, "minecraft:gravel" if (x + dz) % 5 else "minecraft:packed_mud")
    for x in (CX - 1, CX, CX + 1):
        for z in range(MZ + 3, N - 2): b.set(x, 0, z, "minecraft:stone_bricks" if (x + z) % 2 else "minecraft:polished_andesite")
    shops = (("tavern", "bedroom"), ("kitchen", "bedroom"), ("armory", "storage"), ("dining", "bedroom"), ("bath", "bedroom"), ("storage", "study"),
             ("workshop", "bedroom"), ("dining", "storage"), ("tavern", "bedroom"), ("kitchen", "study"))
    k = 0
    rows = ((streets_z[0] + 2, "north"), (streets_z[1] - 11, "south"), (streets_z[1] + 2, "north"), (streets_z[2] - 11, "south"))
    for (z0, door) in rows:
        for x0 in range(5, N - 12, 13):
            if abs(x0 + 5 - CX) < 8: continue
            machiya(b, x0, z0, 10, 9, rnd, shops[k % len(shops)], door=door); k += 1
    # lantern strings over the main avenue: posts every 9 blocks, ropes across and along, paper lanterns hanging from them
    zs = list(range(MZ + 6, N - 6, 9))
    for z in zs:
        for x in (CX - 3, CX + 3): b.column(x, z, 1, 8, POST)
        for x in range(CX - 2, CX + 3): b.set(x, 8, z, fence("dark_oak"))
        for x in (CX - 2, CX, CX + 2): b.set(x, 7, z, "onepiece:paper_lantern[hanging=true]")
    for z in range(zs[0], zs[-1] + 1):
        if (z - zs[0]) % 9 == 0: continue
        for x in (CX - 3, CX + 3):
            b.set(x, 8, z, fence("dark_oak"))
            if (z - zs[0]) % 3 == 0: b.set(x, 7, z, "onepiece:paper_lantern[hanging=true]")
    OG.torii(b, CX, N - 4, w=4, h=9)
    for (x, z) in ((CX - 8, N - 6), (CX + 8, N - 6)): KH.stone_lantern(b, x, z)
    # ---------------- people and loot
    b.npc(CX + 4, 1, N - 10, "kinemon", False)
    b.chest(KX + 2, base + 1, KZ - 4, "wano", "west"); b.chest(KX + 2, ty[-1][2], KZ - 1, "treasure", "south")
    b.guards("samurai", ((CX - 4, MZ - 5), (CX + 4, MZ - 5), (CX, MZ + 20), (CX, MZ + 44), (30, MZ + 9)))
    return b, 0

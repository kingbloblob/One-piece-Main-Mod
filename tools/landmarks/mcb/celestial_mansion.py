"""A Celestial Dragon mansion v3 (2026-10-30 audit: the v1 house was one small box on a flat plate). Redone with the
Minecraft Builder skill: a noble's estate in the Holy Land on its own floating island of Red Line rock in the End,
a palace of excess. The main house is a white three-part palace round a court of honour: a 41-wide centre block of
two tall storeys with a six-column gold-capped portico and pediment, a gold dome on a drum over the ballroom, and
two side mansions (shared with Mary Geoise) facing each other across the court. In the court: a long pool with a
fountain and loungers under parasols, and the gold statue of the Saint. Inside: the ballroom (two storeys,
chandeliers), banquet hall and kitchens, the noble's bedchamber and bath, a trophy room, libraries, and under the
ballroom the vault of gold. Round it: rose gardens, hedges and clipped trees, the CP guards' lodge, and hidden at the
back behind an iron fence the slave quarters, a grim row of barred cells round a bare yard. 150 x 150.
Canvas y 0 = the island top, world y 62."""
import math

import numpy as np

from mcb.kit import BigBuild, P, AIR, st, lamp_post, cornice, tier, wing_floor, place_house, seed_of, set_if_air
from mcb.bridge import to_canvas
from mcb import nature as NT
from mcb import holy_kit as HK
from mcb import impel_kit as K
from mcb import mary_geoise as MG
from mcb.blazing_hell_furnace import block_house

SID = "celestial_mansion"
TITLE = "Celestial Dragon Mansion (Holy Land)"
CUTS = [3, 10, 18]
TILER = dict(terrain="none", sky_y=62)

N = 150
CX, CZ = 75, 77
Q, QB, QP, QST = MG.Q, MG.QB, MG.QP, MG.QST
GOLD, SLATE_ST, WIN = MG.GOLD, MG.SLATE_ST, MG.WIN
X1, X2, Z1, Z2 = 54, 96, 38, 62        # the centre block
FH = 7
LEAF = "minecraft:azalea_leaves[persistent=true,waterlogged=false]"
PAVE = [(Q, 0.55), (QB, 0.3), ("minecraft:quartz_block", 0.15)]
STONE = "minecraft:stone_bricks"


def centre_block(bb, tracker, audit):
    """The centre block: two storeys of 7, pilasters and gold bands, a hip roof, the portico and the domed ballroom."""
    top = tier(bb, X1, Z1, X2, Z2, 0, 2, FH, [Q, QB], WIN, QST, pilaster=QP, band=GOLD, plate=QB, top_plate=Q,
               weights=[0.7, 0.3], every=3, pil_every=4, win_h=3)
    bb.fill(X1 - 3, -2, Z1 - 3, X2 + 3, 0, Z2 + 3, QB)
    bb.fill(X1 - 3, 0, Z1 - 3, X2 + 3, 0, Z2 + 3, Q)
    cornice(bb, X1, Z1, X2, Z2, top, QST, parapet="minecraft:quartz_slab[type=bottom,waterlogged=false]")
    P.hip_roof(bb, X1 - 1, Z1 - 1, X2 + 1, Z2 + 1, top + 1, SLATE_ST)
    mx, mz = (X1 + X2) // 2, (Z1 + Z2) // 2
    # the ballroom: the middle third, both storeys, open
    hx1, hx2 = mx - 9, mx + 9
    bb.fill(hx1, 1, Z1 + 1, hx2, top - 1, Z2 - 1, AIR)
    bb.fill(hx1 - 1, 1, Z1 + 1, hx1 - 1, top - 1, Z2 - 1, QB)
    bb.fill(hx2 + 1, 1, Z1 + 1, hx2 + 1, top - 1, Z2 - 1, QB)
    bb.fill(hx1, 0, Z1 + 1, hx2, 0, Z2 - 1, "minecraft:polished_diorite")
    for x in range(hx1 + 1, hx2, 4):                       # checkered marble
        for z in range(Z1 + 1, Z2, 4):
            bb.fill(x, 0, z, x + 1, 0, z + 1, "minecraft:polished_blackstone")
    for z in range(Z1 + 4, Z2 - 1, 5):
        for x in (hx1 + 1, hx2 - 1):
            bb.fill(x, 1, z, x, top - 1, z, QP)
            bb.set(x, top - 1, z, GOLD)
    for (cx, cz) in ((mx, Z1 + 6), (mx, mz), (mx, Z2 - 6)):
        bb.fill(cx, top - 3, cz, cx, top - 1, cz, "minecraft:iron_chain[axis=y]")
        bb.set(cx, top - 4, cz, "onepiece:chandelier[facing=north]")
    bb.fill(mx - 4, 1, Z1 + 1, mx + 4, 1, Z1 + 3, "minecraft:quartz_bricks")      # the musicians' stage
    bb.set(mx - 2, 2, Z1 + 2, "minecraft:note_block"); bb.set(mx + 2, 2, Z1 + 2, "minecraft:jukebox")
    bb.fill(mx - 1, 1, Z1 + 4, mx + 1, 1, Z2 - 1, "minecraft:red_carpet")
    for x in (hx1 + 2, hx2 - 2):
        for z in range(Z1 + 6, Z2 - 2, 5):
            bb.set(x, 1, z, "onepiece:candelabra[facing=north]")
    # the drum and the gold dome over the ballroom
    bb.cylinder(mx, top + 1, mz, 8, top + 7, Q)
    bb.cylinder(mx, top + 1, mz, 7, top + 7, AIR)
    for a in range(0, 360, 30):
        t = math.radians(a)
        bb.fill(round(mx + 8 * math.cos(t)), top + 1, round(mz + 8 * math.sin(t)), round(mx + 8 * math.cos(t)), top + 7, round(mz + 8 * math.sin(t)), QP)
        bb.fill(round(mx + 8 * math.cos(t + 0.26)), top + 3, round(mz + 8 * math.sin(t + 0.26)), round(mx + 8 * math.cos(t + 0.26)), top + 5,
                round(mz + 8 * math.sin(t + 0.26)), WIN)
    bb.ring(mx, top + 8, mz, 7, 9, top + 8, GOLD)
    bb.dome(mx, top + 9, mz, 8, GOLD)
    bb.cylinder(mx, top + 17, mz, 1, top + 19, Q)
    bb.fill(mx, top + 20, mz, mx, top + 23, mz, GOLD)
    bb.fill(mx - 6, top, mz - 6, mx + 6, top, mz + 6, AIR)           # the ballroom looks up into the dome
    bb.fill(mx - 7, top + 1, mz - 7, mx + 7, top + 6, mz + 7, AIR)
    bb.cylinder(mx, top, mz, 7, top, "minecraft:quartz_slab[type=top,waterlogged=false]", hollow=True)
    # the side parts of the centre block: banquet hall + kitchen (west), trophy room + library (east), upstairs the
    # noble's bedchamber, bath and guest rooms
    for (a1, a2, kinds) in ((X1 + 1, hx1 - 2, ["dining", "kitchen", "storage", "library"]),
                            (hx2 + 2, X2 - 1, ["living", "library", "living", "storage"])):
        for k in range(2):
            fy = 1 + k * FH
            wing_floor(bb, a1, Z1 + 1, a2, Z2 - 1, fy, FH - 1, QB, seed_of("cm", a1, k), tracker,
                       kinds if k == 0 else ["bedroom", "living", "bedroom", "living"], corridor="z", cw=3,
                       carpet=(None, "minecraft:red_carpet"), wood="birch", audit=audit, max_room=10,
                       keep=[(a1, Z2 - 7, a1 + 5, Z2 - 1)] if a1 < mx else [(a2 - 5, Z2 - 7, a2, Z2 - 1)])
            dx = a2 + 1 if a1 < mx else a1 - 1
            bb.fill(dx, fy, mz - 1, dx, fy + 2, mz + 1, AIR)
        sx = a1 if a1 < mx else a2 - 5
        bb.fill(sx, 1, Z2 - 7, sx + 5, FH * 2 - 1, Z2 - 1, AIR)
        P.square_spiral_stair(bb, sx, 1, Z2 - 6, 5, FH, QST, core=QB, headroom=3)
    # the portico: six columns two storeys high, gold capitals, a pediment with the gold crest; steps down to the court
    pz = Z2 + 5
    bb.fill(mx - 13, 0, Z2 + 1, mx + 13, 0, pz + 1, QB)
    for x in (mx - 11, mx - 7, mx - 3, mx + 3, mx + 7, mx + 11):
        bb.fill(x, 1, pz, x, top - 2, pz, QP)
        bb.set(x, top - 1, pz, GOLD)
    bb.fill(mx - 13, top, Z2 + 1, mx + 13, top, pz + 1, Q)
    for k in range(7):
        bb.fill(mx - 13 + 2 * k, top + 1 + k, pz + 1, mx + 13 - 2 * k, top + 1 + k, pz + 1, QB)
        bb.fill(mx - 13 + 2 * k, top + 1 + k, Z2 + 1, mx + 13 - 2 * k, top + 1 + k, pz, QB)
    bb.fill(mx - 1, top + 3, pz + 2, mx + 1, top + 5, pz + 2, GOLD)
    for k in range(3):
        bb.fill(mx - 8 + k, -k, pz + 2 + k, mx + 8 - k, -k, pz + 2 + k, st(QST, "north"))
    bb.fill(mx - 2, 1, Z2, mx + 2, 5, Z2, AIR)
    bb.fill(mx - 3, 6, Z2 + 1, mx + 3, 6, Z2 + 1, GOLD)
    return top


def vault(bb):
    """Under the ballroom: the vault of gold, reached by a ladder behind the stage."""
    mx = (X1 + X2) // 2
    x1, x2, z1, z2 = mx - 8, mx + 8, Z1 + 3, Z1 + 15
    bb.fill(x1 - 1, -8, z1 - 1, x2 + 1, -1, z2 + 1, "minecraft:polished_blackstone_bricks")
    bb.fill(x1, -7, z1, x2, -2, z2, AIR)
    bb.fill(x1, -8, z1, x2, -8, z2, GOLD)
    rng = np.random.default_rng(4520)
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            h = int(rng.integers(0, 3)) if (x - x1) in (0, 1) or (x2 - x) in (0, 1) else 0
            for y in range(-7, -7 + h):
                bb.set(x, y, z, GOLD if rng.random() < 0.6 else "minecraft:raw_gold_block")
    for x in range(x1 + 3, x2 - 2, 3):
        bb.set(x, -2, (z1 + z2) // 2, "minecraft:lantern[hanging=true,waterlogged=false]")
    bb.set(mx, -7, z2, "minecraft:emerald_block")
    bb.set(mx, -6, z2, "minecraft:diamond_block")
    lx, lz = mx + 6, Z1 + 1
    bb.fill(lx, -7, lz, lx, 0, lz, "minecraft:ladder[facing=south,waterlogged=false]")
    bb.fill(lx, -7, lz + 1, lx, -2, lz + 1, AIR)
    bb.fill(lx, -7, lz + 2, lx, -2, z1, AIR)
    bb.set(lx, 1, lz, "minecraft:birch_trapdoor[facing=south,half=bottom,open=true,powered=false,waterlogged=false]")


def court(bb, rng):
    """The court of honour: paving, the long pool with a fountain, loungers and parasols, the gold statue."""
    z1, z2 = Z2 + 9, Z2 + 44
    NT.cover(bb, 52, z1, 98, z2, lambda X, Z: np.zeros(np.broadcast(X, Z).shape), PAVE, 4530)
    px1, px2, pz1, pz2 = 64, 86, z1 + 8, z1 + 24
    bb.fill(px1 - 1, -3, pz1 - 1, px2 + 1, 0, pz2 + 1, QB)
    bb.fill(px1, -2, pz1, px2, 0, pz2, "minecraft:water")
    bb.fill(px1 + 1, -3, pz1 + 1, px2 - 1, -3, pz2 - 1, "minecraft:prismarine_bricks")
    for x in range(px1 + 2, px2 - 1, 4):
        bb.set(x, -3, pz1, "minecraft:sea_lantern"); bb.set(x, -3, pz2, "minecraft:sea_lantern")
    MG.fountain(bb, CX, 1, (pz1 + pz2) // 2, 3)
    bb.fill(CX - 1, 0, (pz1 + pz2) // 2 - 1, CX + 1, 0, (pz1 + pz2) // 2 + 1, QB)
    # loungers (white beds) and parasols along both long sides
    for side, xx in ((-1, px1 - 3), (1, px2 + 3)):
        for z in range(pz1 + 1, pz2, 5):
            bb.set(xx, 1, z, "minecraft:white_bed[facing=north,occupied=false,part=foot]")
            bb.set(xx, 1, z - 1, "minecraft:white_bed[facing=north,occupied=false,part=head]")
            px = xx - side * 2 + side * 4
            bb.fill(px, 1, z, px, 3, z, "minecraft:birch_fence")
            bb.fill(px - 1, 4, z - 1, px + 1, 4, z + 1, "minecraft:white_carpet" if (z // 5) % 2 else "minecraft:yellow_carpet")
            bb.set(px, 4, z, "minecraft:birch_slab[type=bottom,waterlogged=false]")
    # the Saint's gold statue on a plinth, between the pool and the house
    sx, sz = CX, z1 + 3
    bb.fill(sx - 2, 1, sz - 2, sx + 2, 2, sz + 2, QB)
    bb.fill(sx - 1, 3, sz, sx + 1, 3, sz, GOLD)
    bb.fill(sx - 1, 4, sz, sx - 1, 5, sz, GOLD); bb.fill(sx + 1, 4, sz, sx + 1, 5, sz, GOLD)
    bb.fill(sx - 1, 6, sz, sx + 1, 9, sz, GOLD)
    bb.fill(sx - 2, 8, sz, sx - 2, 9, sz, GOLD); bb.fill(sx + 2, 8, sz, sx + 2, 10, sz, GOLD)
    bb.set(sx + 2, 11, sz, "minecraft:end_rod[facing=up]")
    bb.set(sx, 10, sz, GOLD)
    bb.set(sx, 11, sz, "minecraft:glass")                     # the bubble helmet
    for z in range(z1, z2 + 1, 6):
        for x in (54, 96):
            lamp_post(bb, x, 1, z, post="minecraft:quartz_pillar[axis=y]", h=3, light="minecraft:lantern[hanging=false,waterlogged=false]")
    return z2


def gardens(bb, shp, z0, rng):
    """South of the court: rose gardens in hedged rooms, clipped trees, a gate to the landing; groves elsewhere."""
    for i, (x1, x2) in enumerate(((30, 58), (61, 89), (92, 120))):
        z1, z2 = z0 + 3, z0 + 25
        HK.hedge(bb, x1, z1, x2, z1, 2, LEAF); HK.hedge(bb, x1, z2, x2, z2, 2, LEAF)
        HK.hedge(bb, x1, z1, x1, z2, 2, LEAF); HK.hedge(bb, x2, z1, x2, z2, 2, LEAF)
        mx, mz = (x1 + x2) // 2, (z1 + z2) // 2
        bb.fill(mx - 1, 1, z1, mx + 1, 2, z2, AIR)
        bb.fill(mx - 1, 0, z1, mx + 1, 0, z2, "minecraft:gravel")
        for bx in (x1 + 2, mx + 3):
            for bz in (z1 + 2, mz + 2):
                HK.rose_bed(bb, bx, bz, bx + 7, bz + 7, int(rng.integers(0, 999)), flowers=("minecraft:rose_bush",) if i != 1 else
                            ("minecraft:peony", "minecraft:lilac"))
        HK.topiary(bb, mx, mz, 5, LEAF)
    n = 0
    for _ in range(1500):
        x, z = int(rng.integers(4, N - 4)), int(rng.integers(4, N - 4))
        s = shp(np.array([[x]]), np.array([[z]]))[0, 0]
        if s < 5 or (24 <= x <= 126 and 14 <= z <= z0 + 30) or int(bb.get_region(x, 1, z, x, 1, z)[0, 0, 0]) > 1:
            continue
        P.tree(bb, x, 1, z, height=int(rng.integers(6, 10)), kind="cherry" if rng.random() < 0.5 else "birch", rng=rng)
        n += 1
        if n >= 26:
            break


def slave_quarters(bb, tracker):
    """Behind the house: the slave quarters, a row of barred stone cells round a bare yard behind an iron fence."""
    x1, x2, z1, z2 = 50, 100, 16, 32
    bb.fill(x1, 0, z1, x2, 0, z2, "minecraft:gravel")
    bb.mix(x1, 0, z1 + 8, x2, 0, z2, ["minecraft:gravel", "minecraft:coarse_dirt", "minecraft:cobblestone"], [0.5, 0.3, 0.2])
    for i, x in enumerate(range(x1 + 1, x2 - 6, 6)):
        K.cell(bb, x, z1, x + 6, z1 + 6, 1, 5, "south", "minecraft:cobblestone", "minecraft:iron_bars[east=true,north=false,south=false,west=true,waterlogged=false]",
               "spruce", 4540 + i, "cell")
        bb.set(x + 3, 4, z1 + 1, "minecraft:iron_chain[axis=y]")
    bb.fill(x1, 6, z1, x2, 6, z1 + 7, "minecraft:cobblestone_slab[type=bottom,waterlogged=false]")
    fence = "minecraft:iron_bars[east=true,north=true,south=true,west=true,waterlogged=false]"
    bb.fill(x1, 1, z2, x2, 3, z2, fence)
    bb.fill(x1, 1, z1 + 7, x1, 3, z2, fence); bb.fill(x2, 1, z1 + 7, x2, 3, z2, fence)
    bb.fill(CX - 1, 1, z2, CX + 1, 2, z2, AIR)
    bb.set(CX, 1, z2, "minecraft:iron_door[facing=south,half=lower,hinge=left,open=false,powered=false]")
    bb.set(CX, 2, z2, "minecraft:iron_door[facing=south,half=upper,hinge=left,open=false,powered=false]")
    bb.set(CX - 1, 1, z2, fence); bb.set(CX + 1, 1, z2, fence)
    for x in range(x1 + 6, x2 - 3, 12):                        # posts with chains, a water trough, a guard stand
        bb.fill(x, 1, z1 + 12, x, 3, z1 + 12, "minecraft:spruce_fence")
        bb.set(x, 4, z1 + 12, "minecraft:lantern[hanging=false,waterlogged=false]")
    bb.fill(x1 + 3, 1, z2 - 3, x1 + 7, 1, z2 - 3, "minecraft:cauldron")
    bb.set(x2 - 4, 1, z2 - 4, "minecraft:spruce_stairs[facing=north,half=bottom,shape=straight,waterlogged=false]")
    # a covered path to the house's back door
    bb.fill(CX - 1, 0, z2 + 1, CX + 1, 0, Z1 - 4, "minecraft:gravel")


def design():
    bb = BigBuild(seed=4500, y_min=-55, y_max=60)
    tracker = P.PropTracker(4500)
    audit = []
    rng = np.random.default_rng(4500)
    shp = HK.floating_island(bb, CX, CZ, 70, 4503, depth=42)
    top = centre_block(bb, tracker, audit)
    vault(bb)
    # the two side mansions, doors facing each other across the court
    for (x0, rot) in ((32, 3), (104, 1)):
        m = MG.mansion(seed_of("cm_wing", x0), 22, 16, tracker, audit)
        place_house(bb, m, 22, 16, x0, 0, Z2 - 2, rot)
    z_end = court(bb, rng)
    gardens(bb, shp, z_end, rng)
    slave_quarters(bb, tracker)
    block_house(bb, 104, 34, 116, 46, 2, STONE, "minecraft:spruce_planks", "minecraft:stone_brick_slab[type=bottom,waterlogged=false]",
                "minecraft:glass_pane", ("barracks", "armory"), "spruce", "south", 4550)
    NT.plants(bb, 0, 0, N - 1, N - 1, lambda X, Z: np.zeros(np.broadcast(X, Z).shape), 4560, density=0.22, kinds=NT.PLANTS_MEADOW,
              flowers=["minecraft:white_tulip", "minecraft:pink_tulip", "minecraft:allium"], mask=lambda X, Z: shp(X, Z) > 2)
    HK.balustrade(bb, shp, 0, 0, N - 1, N - 1, skip=lambda X, Z: (np.abs(X - CX) < 3) & (Z > CZ))
    # the landing: a white pier out of the south rim
    pz = int(max(z for z in range(CZ, N) if shp(np.array([[CX]]), np.array([[z]]))[0, 0] > 0))
    bb.fill(CX - 2, 0, z_end + 30, CX + 2, 0, pz + 5, QB)
    for z in range(z_end + 30, pz + 6, 4):
        lamp_post(bb, CX - 3, 1, z, post="minecraft:quartz_pillar[axis=y]", h=2, light="minecraft:lantern[hanging=false,waterlogged=false]")
        lamp_post(bb, CX + 3, 1, z, post="minecraft:quartz_pillar[axis=y]", h=2, light="minecraft:lantern[hanging=false,waterlogged=false]")
    return bb, audit


def build():
    bb, audit = design()
    print("audit fails:", len(audit))
    b = to_canvas(bb)
    mx = (X1 + X2) // 2
    b.chest(mx - 3, -7, Z1 + 10, "legendary", "east")
    b.chest(mx + 3, -7, Z1 + 10, "celestial", "west")
    b.chest(X1 + 3, 1 + FH, Z1 + 2, "celestial", "south")
    b.chest(114, 1, 36, "hard", "south")
    b.guards("cp0_agent", ((CX - 6, Z2 + 9), (CX + 6, Z2 + 9), (CX, 30)), y=1)
    b.guards("pacifista", ((CX, Z2 + 50),), y=1)
    return b, 0

"""Aokiji's Ice Fortress v3 (2026-10-30 audit: the v1 citadel was a small ice box with spikes). Redone with the
Minecraft Builder skill: a citadel frozen out of the sea by Kuzan's Ice Age. Silhouette first: six crystal towers
of packed and blue ice, tapering into spikes, round a hexagonal curtain of ice on frozen-stone footings, the snow
brick keep with a crown of ice spikes in the middle, and over the south gate a great frozen wave curling 26 high
as if the sea was stopped mid-crash. In front, the frozen bay: two Marine warships locked in the ice, frozen spray
and ice floes. Inside the keep: the frost soldiers' barracks and mess, the kitchen and cold store, the armory, a
library, and at the top Aokiji's lazy bedroom with his sleep mask on the pillow and his bicycle parked by the bed.
Snowfields, snowy spruces and ice spikes round it all. 150 x 150. Ground = y 0."""
import math

import numpy as np

from mcb.kit import BigBuild, P, AIR, seed_of, st, set_if_air, wing_floor, furnish, lamp_post, cornice
from mcb.bridge import to_canvas
from mcb import nature as NT
from mcb.shipstamp import stamp_ship
from mcb.blazing_hell_furnace import block_house

SID = "ice_fortress"
TITLE = "Aokiji's Ice Fortress"
CUTS = [3, 12, 24]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")
EDGE_REACH = 8

N = 150
CX, CZ = 75, 62
LAND = NT.outline(75, 75, 70, 4901, wobble=0.08)
PICE = "minecraft:packed_ice"
BICE = "minecraft:blue_ice"
SNOWB = "onepiece:snow_bricks"
FROZ = "onepiece:frozen_stone"
ICEW = [PICE, PICE, BICE, "minecraft:ice"]
SNOWY = [("minecraft:snow_block", 0.62), ("minecraft:packed_ice", 0.1), ("minecraft:snow_block", 0.12),
         ("onepiece:frozen_stone", 0.08), ("minecraft:gravel", 0.04), ("minecraft:ice", 0.04)]
R = 38                         # curtain "radius" (hexagon)
BAY = lambda X, Z: (((X - 75) / 60.0) ** 2 + ((Z - 128) / 17.0) ** 2 < 1 + 0.15 * (NT.noise(X, Z, 4902, 9) - 0.5)) & (LAND(X, Z) > 3)
FH = 7


def hexd(X, Z, r):
    """Hexagon (flat top/bottom faces north and south) signed distance, <0 inside."""
    dx, dz = np.abs(X - CX), np.abs(Z - CZ)
    return np.maximum(dz, dx * 0.866 + dz * 0.5) - r


def ground(bb):
    zero = lambda X, Z: np.zeros(np.broadcast(X, Z).shape)
    NT.cover(bb, 0, 0, N - 1, N - 1, zero, SNOWY, 4903, mask=lambda X, Z: (LAND(X, Z) > 0) & ~BAY(X, Z), core="minecraft:stone", base=-8)
    # the bay basin: stone floor and walls, still water, sea ice on top (left open round the ships)
    bb.fill_where(0, -9, 0, N - 1, -9, N - 1, lambda X, y, Z: BAY(X, Z), "minecraft:gravel")
    bb.fill_where(0, -10, 0, N - 1, -10, N - 1, lambda X, y, Z: BAY(X, Z), "minecraft:stone")
    for y in range(-9, 1):
        bb.fill_where(0, y, 0, N - 1, y, N - 1, lambda X, yy, Z: ~BAY(X, Z) & (LAND(X, Z) > 0) & (
            (np.abs(X - 75) < 66) & (np.abs(Z - 128) < 22)), "minecraft:stone", only_empty=True)
    rng = np.random.default_rng(4904)
    for (x, rot) in ((40, 0), (104, 2)):
        stamp_ship(bb, "marine_warship", x, 124 + (8 if rot else 0), water_y=0, rot=rot)
    bb.fill_where(0, -8, 0, N - 1, -1, N - 1, lambda X, y, Z: BAY(X, Z), "minecraft:water", only_empty=True)
    bb.fill_where(0, 0, 0, N - 1, 0, N - 1, lambda X, y, Z: BAY(X, Z), "minecraft:ice", only_empty=True)
    bb.fill_where(0, 0, 0, N - 1, 0, N - 1, lambda X, y, Z: BAY(X, Z) & (NT.noise(X, Z, 4905, 6) > 0.62), PICE)
    bb.fill_where(0, 0, 0, N - 1, 0, N - 1, lambda X, y, Z: BAY(X, Z) & (np.abs(NT.fbm(X, Z, 4906, 11) - 0.5) < 0.025), BICE)
    # frozen spray and ice floes round the ships
    for _ in range(22):
        x, z = int(rng.integers(20, 130)), int(rng.integers(114, 142))
        if not BAY(np.array([[x]]), np.array([[z]]))[0, 0]:
            continue
        h = int(rng.integers(2, 6))
        for y in range(1, h + 1):
            r = 1.6 * (1 - y / (h + 1)) + 0.4
            bb.fill_where(x - 2, y, z - 2, x + 2, y, z + 2, lambda X, yy, Z, r=r: ((X - x) ** 2 + (Z - z) ** 2 <= r * r + 0.3), PICE, only_empty=True)
    # snowy spruces and ice spikes on the snowfields
    n = 0
    for _ in range(1500):
        x, z = int(rng.integers(6, N - 6)), int(rng.integers(6, N - 6))
        if LAND(np.array([[x]]), np.array([[z]]))[0, 0] < 4 or BAY(np.array([[x]]), np.array([[z]]))[0, 0] or hexd(np.array([[x]]), np.array([[z]]), R + 6)[0, 0] < 0:
            continue
        if int(bb.get_region(x, 1, z, x, 1, z)[0, 0, 0]) > 1:
            continue
        if n % 3 == 0:
            spike(bb, x, z, int(rng.integers(6, 16)), float(rng.uniform(1.5, 2.6)))
        else:
            P.tree(bb, x, 1, z, height=int(rng.integers(7, 11)), kind="spruce", rng=rng)
        n += 1
        if n >= 36:
            break


def spike(bb, x, z, h, r):
    """An ice spike: a tapering cone of packed ice with a blue ice core."""
    for y in range(1, h + 1):
        rr = r * (1 - (y - 1) / h) ** 1.1 + 0.3
        ri = int(rr) + 1
        bb.fill_where(x - ri, y, z - ri, x + ri, y, z + ri, lambda X, yy, Z, rr=rr: (X - x) ** 2 + (Z - z) ** 2 <= rr * rr, PICE)
        if y < h * 0.6:
            bb.set(x, y, z, BICE)


def crystal_tower(bb, x, z, r, h):
    """A crystal tower: a hexagonal-ish ice shaft with blue-ice bands, two floors, a ladder, then a tall ice spike."""
    bb.cylinder(x, -3, z, r, h, PICE)
    bb.cylinder(x, 1, z, r - 2, h - 1, AIR)
    for y in range(0, h + 1, 6):
        bb.ring(x, y, z, r - 1, r + 1, y, BICE)
    for y in (0, 10, 20):
        if y < h:
            bb.cylinder(x, y, z, r - 2, y, "minecraft:spruce_planks" if y else SNOWB)
    bb.fill(x, 1, z - r + 2, x, h - 1, z - r + 2, "minecraft:ladder[facing=south,waterlogged=false]")
    for (dx, dz) in ((r, 0), (-r, 0), (0, r)):
        for y in (4, 14):
            bb.fill(x + dx, y, z + dz, x + dx, y + 2, z + dz, "minecraft:light_blue_stained_glass")
    for k in range(r * 4):
        rr = (r + 1) * (1 - k / (r * 4)) + 0.2
        ri = int(rr) + 1
        bb.fill_where(x - ri, h + 1 + k, z - ri, x + ri, h + 1 + k, z + ri, lambda X, y, Z, rr=rr: ((X - x) ** 2 + (Z - z) ** 2 <= rr * rr)
                      & ((X - x) ** 2 + (Z - z) ** 2 > (rr - 1.3) ** 2), "minecraft:light_blue_stained_glass" if k % 4 == 3 else PICE)
    bb.set(x, h + 1 + r * 4, z, BICE)
    for a in range(0, 360, 60):                                   # small spikes round the crown
        t = math.radians(a + 30)
        sx, sz = round(x + (r + 1) * math.cos(t)), round(z + (r + 1) * math.sin(t))
        bb.fill(sx, h + 1, sz, sx, h + 4, sz, PICE)
        bb.set(sx, h + 5, sz, BICE)


def curtain(bb):
    """The hexagonal curtain: ice walls 12 high on a frozen-stone footing, a snow-brick walk, crenels of blue ice;
    six crystal towers at the corners; the gate on the south under the frozen wave."""
    H = 12
    x1, x2, z1, z2 = CX - R - 4, CX + R + 4, CZ - R - 4, CZ + R + 4
    wall = lambda X, Z: (hexd(X, Z, R) <= 0) & (hexd(X, Z, R - 3) > 0)
    for y in range(-3, 4):
        bb.fill_where(x1, y, z1, x2, y, z2, lambda X, yy, Z: (hexd(X, Z, R + (1 if yy < 2 else 0)) <= 0) & (hexd(X, Z, R - 3) > 0), FROZ)
    for i, blk in enumerate(ICEW):
        bb.fill_where(x1, 4, z1, x2, H, z2, lambda X, y, Z, i=i: wall(X, Z) & (np.floor(NT.noise(X + y, Z - y, 4910, 5) * 4).astype(int) == i), blk)
    bb.fill_where(x1, H, z1, x2, H, z2, lambda X, y, Z: wall(X, Z), SNOWB)
    bb.fill_where(x1, H + 1, z1, x2, H + 1, z2, lambda X, y, Z: (hexd(X, Z, R) <= 0) & (hexd(X, Z, R - 1) > 0) & (((X + Z) % 3) != 0), BICE)
    corners = []
    for k in range(6):
        a = math.radians(k * 60)
        corners.append((round(CX + R / 0.866 * 0.99 * math.cos(a)), round(CZ + R / 0.866 * 0.99 * math.sin(a))))
    for k, (x, z) in enumerate(corners):
        crystal_tower(bb, x, z, 6, 26 if k % 3 else 32)
        sx, sz = int(np.sign(CX - x)), int(np.sign(CZ - z))
        bb.fill(x + sx * 4, 1, z + sz * 4 if sz else z - 1, x + sx * 6, 3, z + sz * 6 if sz else z + 1, AIR)
    # the south gate (the hexagon's flat south face), cut through the wall
    gz = CZ + R
    bb.fill(CX - 3, 1, gz - 4, CX + 3, 7, gz + 1, AIR)
    bb.fill(CX - 4, 8, gz - 4, CX + 4, 9, gz + 1, BICE)
    bb.fill(CX - 3, 0, gz - 4, CX + 3, 0, gz + 8, SNOWB)
    return corners


def frozen_wave(bb):
    """The frozen wave curling over the gate: a crest rising from the bay, arching over and breaking into icicles,
    in packed and blue ice with snow-white foam on its lip."""
    gz = CZ + R
    for x in range(CX - 22, CX + 23):
        wfac = 1 - (abs(x - CX) / 23.0) ** 2
        top = 6 + int(20 * wfac)
        lean = int(9 * wfac)
        for y in range(0, top + 1):
            t = y / max(top, 1)
            zc = gz + 14 - int(lean * t * t) - int(5 * t)               # the face leans in towards the wall as it rises
            th = max(2, int(5 * (1 - t)) + 2)
            for z in range(zc, zc + th):
                if abs(x - CX) <= 4 and y <= 9 and z <= gz + 9:
                    continue
                blk = BICE if (x + y * 2 + z) % 7 == 0 else ("minecraft:snow_block" if t > 0.9 else PICE)
                bb.set(x, y, z, blk)
        # the curl: the lip rolls over and hangs down towards the gate
        cy, cz = top, gz + 14 - lean - 5
        for i in range(1, 7):
            yy, zz = cy - (i * i) // 6, cz - i
            bb.set(x, yy, zz, PICE if i < 6 else "minecraft:snow_block")
            if i > 3 and (x + i) % 3 == 0:
                set_if_air(bb, x, yy - 1, zz, "minecraft:pointed_dripstone[thickness=tip,vertical_direction=down,waterlogged=false]")


def keep(bb, tracker, audit):
    """The keep: three storeys of snow bricks on a frozen-stone plinth, blue-ice corner piers, a crown of ice spikes,
    furnished floors and Aokiji's bedroom at the top."""
    x1, x2, z1, z2 = CX - 16, CX + 16, CZ - 14, CZ + 10
    bb.fill(x1 - 2, -3, z1 - 2, x2 + 2, 0, z2 + 2, FROZ)
    top = 3 * FH
    bb.fill(x1, 1, z1, x2, top, z2, SNOWB)
    bb.fill(x1 + 1, 1, z1 + 1, x2 - 1, top - 1, z2 - 1, AIR)
    for k in range(1, 3):
        bb.fill(x1 + 1, k * FH, z1 + 1, x2 - 1, k * FH, z2 - 1, "minecraft:spruce_planks")
        for (a, b, c, d) in ((x1, z1, x2, z1), (x1, z2, x2, z2), (x1, z1, x1, z2), (x2, z1, x2, z2)):
            bb.fill(a, k * FH, b, c, k * FH, d, BICE)
    for k in range(3):
        y = k * FH + 3
        for x in range(x1 + 3, x2 - 1, 4):
            bb.fill(x, y, z1, x, y + 1, z1, "minecraft:light_blue_stained_glass_pane"); bb.fill(x, y, z2, x, y + 1, z2, "minecraft:light_blue_stained_glass_pane")
        for z in range(z1 + 3, z2 - 1, 4):
            bb.fill(x1, y, z, x1, y + 1, z, "minecraft:light_blue_stained_glass_pane"); bb.fill(x2, y, z, x2, y + 1, z, "minecraft:light_blue_stained_glass_pane")
    for (x, z) in ((x1, z1), (x2, z1), (x1, z2), (x2, z2)):
        bb.fill(x - 1, 0, z - 1, x + 1, top + 4, z + 1, BICE)
        for k in range(8):
            rr = 1.8 * (1 - k / 8) + 0.2
            bb.fill_where(x - 2, top + 5 + k, z - 2, x + 2, top + 5 + k, z + 2, lambda X, y, Z, rr=rr: (X - x) ** 2 + (Z - z) ** 2 <= rr * rr, PICE)
    cornice(bb, x1, z1, x2, z2, top, "minecraft:stone_brick_stairs", parapet=PICE)
    # the crown of ice spikes on the roof
    bb.fill(x1, top, z1, x2, top, z2, SNOWB)
    for (dx, dz, h) in ((0, -2, 18), (-8, -2, 11), (8, -2, 11), (-4, 4, 8), (4, 4, 8), (-11, 5, 6), (11, 5, 6)):
        x, z = CX + dx, CZ - 2 + dz
        for k in range(h):
            rr = 2.6 * (1 - k / h) ** 1.1 + 0.3
            bb.fill_where(x - 3, top + 1 + k, z - 3, x + 3, top + 1 + k, z + 3, lambda X, y, Z, rr=rr: (X - x) ** 2 + (Z - z) ** 2 <= rr * rr,
                          BICE if k % 4 == 0 else PICE)
    # floors
    kinds = [["barracks", "mess", "kitchen", "storeroom"], ["armory", "library", "office", "barracks"]]
    for k in range(2):
        wing_floor(bb, x1 + 1, z1 + 1, x2 - 1, z2 - 1, k * FH + 1, FH - 2, SNOWB, seed_of("if", k), tracker, kinds[k], corridor="x", cw=3,
                   carpet=(None, "minecraft:light_blue_carpet"), keep=[(x1 + 1, z1 + 1, x1 + 3, z1 + 3)], wood="spruce", audit=audit,
                   lamp="minecraft:lantern[hanging=true]", kit=True)
    # Aokiji's bedroom: the whole top floor, a big bed with the sleep mask, the bicycle, a sofa and a desk
    fy = 2 * FH + 1
    bb.fill(CX - 1, fy, z1 + 2, CX + 1, fy, z1 + 3, "minecraft:light_blue_bed[facing=north,occupied=false,part=head]")
    for x in (CX - 1, CX, CX + 1):
        bb.set(x, fy, z1 + 2, "minecraft:light_blue_bed[facing=north,occupied=false,part=head]")
        bb.set(x, fy, z1 + 3, "minecraft:light_blue_bed[facing=north,occupied=false,part=foot]")
    bb.set(CX, fy + 1, z1 + 2, "minecraft:black_carpet")                       # the sleep mask on the pillow
    bb.fill(CX - 3, fy, z1 + 1, CX + 3, fy + 2, z1 + 1, "minecraft:spruce_planks")
    for x in (CX - 3, CX + 3):
        bb.set(x, fy + 3, z1 + 1, "minecraft:lantern[hanging=false,waterlogged=false]")
    # the bicycle, parked by the bed: two iron-bar wheels, a frame, a saddle, handlebars
    bx, bzz = CX + 5, z1 + 3
    for dz in (0, 3):
        bb.set(bx, fy, bzz + dz, "minecraft:iron_bars[east=false,north=true,south=true,west=false,waterlogged=false]")
        bb.set(bx, fy + 1, bzz + dz, "minecraft:iron_bars[east=false,north=true,south=true,west=false,waterlogged=false]")
    bb.fill(bx, fy + 1, bzz + 1, bx, fy + 1, bzz + 2, "minecraft:light_blue_concrete")
    bb.set(bx, fy + 2, bzz + 1, "minecraft:spruce_slab[type=bottom,waterlogged=false]")
    bb.set(bx, fy + 2, bzz + 3, "minecraft:lightning_rod[facing=up,powered=false,waterlogged=false]")
    furnish(bb, [(x1 + 4, z1 + 7, x2 - 4, z2 - 1)], fy, FH - 2, ["living", "library"], seed_of("aokiji"), tracker, doors=[(x1 + 2, z1 + 2)],
            wood="spruce", audit=audit)
    bb.fill(x1 + 2, 1, z1 + 2, x1 + 2, 2 * FH + 1, z1 + 2, "minecraft:ladder[facing=east,waterlogged=false]")
    bb.fill(x1 + 1, 1, z1 + 2, x1 + 1, 2 * FH + 1, z1 + 2, SNOWB)
    bb.fill(CX - 1, 1, z2, CX + 1, 3, z2, AIR)
    bb.fill(CX - 2, 0, z2 + 1, CX + 2, 0, z2 + 4, SNOWB)
    return top


def courtyard(bb):
    """Inside the curtain: snow, lantern posts, a training yard, a frozen fountain, the frost soldiers' guard posts."""
    zero = lambda X, Z: np.zeros(np.broadcast(X, Z).shape)
    NT.cover(bb, CX - R, CZ - R, CX + R, CZ + R, zero, [("minecraft:snow_block", 0.6), (SNOWB, 0.2), ("minecraft:packed_ice", 0.1),
                                                        (FROZ, 0.1)], 4920, mask=lambda X, Z: hexd(X, Z, R - 3) <= 0)
    for z in range(CZ + 14, CZ + R - 4, 5):
        for x in (CX - 5, CX + 5):
            lamp_post(bb, x, 1, z, post="minecraft:spruce_fence", h=3, light="minecraft:lantern[hanging=false,waterlogged=false]")
    fx, fz = CX + 24, CZ + 6                                     # the frozen fountain: water stopped mid-leap
    bb.cylinder(fx, 0, fz, 5, 1, FROZ)
    bb.cylinder(fx, 1, fz, 4, 1, "minecraft:ice")
    bb.fill(fx, 2, fz, fx, 7, fz, BICE)
    for a in range(0, 360, 45):
        t = math.radians(a)
        for i in range(1, 4):
            bb.set(round(fx + i * math.cos(t)), 7 - (i * i) // 3, round(fz + i * math.sin(t)), PICE)
    block_house(bb, CX - 30, CZ + 2, CX - 18, CZ + 14, 2, SNOWB, "minecraft:spruce_planks", "minecraft:packed_ice", "minecraft:light_blue_stained_glass_pane",
                ("kitchen", "storeroom"), "spruce", "east", 4921)
    for x in range(CX + 16, CX + 30, 4):
        for z in (CZ - 16, CZ - 10):
            bb.set(x, 1, z, "minecraft:spruce_fence"); bb.set(x, 2, z, "minecraft:snow_block"); bb.set(x, 3, z, "minecraft:carved_pumpkin[facing=south]")


def design():
    bb = BigBuild(seed=4900, y_min=-12, y_max=80)
    tracker = P.PropTracker(4900)
    audit = []
    ground(bb)
    curtain(bb)
    courtyard(bb)
    keep(bb, tracker, audit)
    frozen_wave(bb)
    return bb, audit


def build():
    bb, audit = design()
    print("audit fails:", len(audit))
    b = to_canvas(bb)
    b.npc(CX - 3, 2 * FH + 1, CZ - 6, "aokiji", True)
    b.chest(CX - 4, 2 * FH + 1, CZ - 13, "treasure", "south")
    b.chest(CX - 28, 1, CZ + 4, "marine", "east")
    b.guards("frost_soldier", ((CX - 4, CZ + 20), (CX + 4, CZ + 20), (CX - 14, CZ + 24), (CX + 14, CZ + 24)), y=1)
    b.guards("frost_soldier", ((CX, CZ + 52),), y=1)
    return b, 0

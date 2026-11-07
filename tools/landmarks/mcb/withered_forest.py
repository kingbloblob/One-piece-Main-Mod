"""Ryokugyu's Withered Forest v3 (2026-10-30 audit: the v1 tree was a short log pillar in a ring of dead bushes).
Redone with the Minecraft Builder skill: a Wano valley where Admiral Green Bull drank the life out of everything.
Silhouette first: one living giant in a dead grey land. Ryokugyu's tree rises 70 blocks from the middle, a twisted
trunk 15 across at the foot, buttress roots strangling the ground and great roots snaking out across the whole
valley, and a wide green crown; round it a forest of bare grey dead trees, dried grass and dust, a dry riverbed with
a broken bridge, and a withered Wano village whose houses sag, roofs holed, gardens dead. Inside the tree: a hollow
with a spiral stair round the heartwood, rooms on platforms (the Marine camp's store, Ryokugyu's study, a bedroom
with a hammock of vines), and up in the crown his throne of roots looking out over the dead land. The Marine camp
pitches its tents at the foot. 150 x 150. Ground = y 0."""
import math

import numpy as np

from mcb.kit import BigBuild, P, AIR, seed_of, st, set_if_air, is_air, place_house, lamp_post
from mcb.kit_interiors import furnish_kit
from mcb.bridge import to_canvas
from mcb import nature as NT
from mcb import flower_capital as FC

SID = "withered_forest"
TITLE = "Ryokugyu's Withered Forest (Wano)"
CUTS = [3, 22, 48]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")
EDGE_REACH = 8

N = 150
CX, CZ = 75, 75
LAND = NT.outline(75, 75, 66, 4701, wobble=0.1)
DRY = [("minecraft:coarse_dirt", 0.32), ("minecraft:podzol", 0.16), ("minecraft:dirt", 0.14), ("minecraft:packed_mud", 0.1),
       ("minecraft:gravel", 0.08), ("minecraft:pale_moss_block", 0.06), ("minecraft:rooted_dirt", 0.08), ("minecraft:grass_block", 0.06)]
BARK = "minecraft:oak_log"
WOOD = "minecraft:oak_wood"
LEAF = ("minecraft:oak_leaves[distance=7,persistent=true,waterlogged=false]", "minecraft:azalea_leaves[distance=7,persistent=true,waterlogged=false]",
        "minecraft:flowering_azalea_leaves[distance=7,persistent=true,waterlogged=false]", "minecraft:jungle_leaves[distance=7,persistent=true,waterlogged=false]")
TRUNK_H = 58
RIVER = lambda X, Z: np.abs(Z - (112 + 10 * np.sin(X / 17.0))) < 3 + 1.5 * NT.noise(X, Z, 4702, 7)


def land(X, Z):
    return LAND(X, Z) > 0


def ground(bb):
    zero = lambda X, Z: np.zeros(np.broadcast(X, Z).shape)
    NT.cover(bb, 0, 0, N - 1, N - 1, zero, DRY, 4703, mask=lambda X, Z: land(X, Z) & ~RIVER(X, Z), core="minecraft:stone", base=-4)
    bb.fill_where(0, -3, 0, N - 1, 0, N - 1, lambda X, y, Z: land(X, Z) & RIVER(X, Z) & (y >= -1), AIR)   # the dry riverbed
    bb.fill_where(0, -2, 0, N - 1, -2, N - 1, lambda X, y, Z: land(X, Z) & RIVER(X, Z),
                  "minecraft:gravel")
    bb.fill_where(0, -2, 0, N - 1, -2, N - 1, lambda X, y, Z: land(X, Z) & RIVER(X, Z) & (NT.noise(X, Z, 4704, 3) > 0.6), "minecraft:mud")
    bb.fill_where(0, -4, 0, N - 1, -3, N - 1, lambda X, y, Z: land(X, Z) & RIVER(X, Z), "minecraft:stone")
    # dried grass and dead bushes in drifts
    NT.plants(bb, 0, 0, N - 1, N - 1, zero, 4705, density=0.32, kinds=["minecraft:dead_bush", "minecraft:short_dry_grass",
              "minecraft:tall_dry_grass", "minecraft:dead_bush"], mask=lambda X, Z: land(X, Z) & (np.hypot(X - CX, Z - CZ) > 14),
              ground=("coarse_dirt", "podzol", "dirt", "packed_mud", "rooted_dirt", "grass_block", "pale_moss_block"))


def trunk_r(y):
    return 7.5 * (1 - y / (TRUNK_H * 1.25)) ** 1.1 + 1.5


def giant_tree(bb, rng):
    """Ryokugyu's tree: a twisted trunk (three lobes turning as it rises), buttress roots, roots across the valley,
    a hollow with a spiral stair and platform rooms, branches and a wide crown, the throne of roots on top."""
    for y in range(-3, TRUNK_H + 1):
        r = trunk_r(max(y, 0))
        tw = y / 14.0
        def m(X, Z, r=r, tw=tw):
            a = np.arctan2(Z - CZ, X - CX)
            return np.hypot(X - CX, Z - CZ) <= r * (1 + 0.16 * np.cos(3 * a + tw)) + 0.3
        ri = int(r * 1.2) + 2
        bb.fill_where(CX - ri, y, CZ - ri, CX + ri, y, CZ + ri, lambda X, yy, Z, m=m: m(X, Z), WOOD)
        bb.fill_where(CX - ri, y, CZ - ri, CX + ri, y, CZ + ri, lambda X, yy, Z, m=m: m(X, Z) & (NT.noise(X + yy, Z, 4710, 3) > 0.7),
                      "minecraft:jungle_wood")
    # the hollow: from 1 to 40, leaving a 2-thick shell and a 2x2 heartwood post
    HOL = 40
    for y in range(1, HOL):
        r = trunk_r(y) - 2.2
        bb.fill_where(CX - 9, y, CZ - 9, CX + 9, y, CZ + 9, lambda X, yy, Z, r=r: np.hypot(X - CX, Z - CZ) <= r, AIR)
    bb.fill(CX, 0, CZ, CX + 1, HOL, CZ + 1, "minecraft:stripped_oak_log[axis=y]")
    # the spiral stair: winding round the heartwood one block per step
    for i in range(HOL - 2):
        a = i * 0.42
        rr = 3.2
        x, z = round(CX + 0.5 + rr * math.cos(a)), round(CZ + 0.5 + rr * math.sin(a))
        bb.set(x, i + 1, z, "minecraft:spruce_slab[type=top,waterlogged=false]")
        bb.fill(x, i + 2, z, x, i + 4, z, AIR)
        if i % 6 == 0:
            set_if_air(bb, round(CX + 0.5 + 4.6 * math.cos(a)), i + 3, round(CZ + 0.5 + 4.6 * math.sin(a)),
                       "minecraft:lantern[hanging=false,waterlogged=false]")
    # platform rooms: ring floors at 12, 24, 34 (half rings so the stair still passes)
    for (fy, kind) in ((12, "storeroom"), (24, "library"), (34, "bedroom")):
        r = trunk_r(fy) - 2.2
        bb.fill_where(CX - 9, fy, CZ - 9, CX + 9, fy, CZ + 9,
                      lambda X, yy, Z, r=r: (np.hypot(X - CX, Z - CZ) <= r) & (np.hypot(X - CX - 0.5, Z - CZ - 0.5) > 4.6) & (X < CX), "minecraft:spruce_planks")
        furnish_kit(bb, (CX - int(r) + 1, CZ - 3, CX - 3, CZ + 3), fy + 1, 4, kind, wood="spruce", seed=4711 + fy)
    # the hammock of vines in the bedroom
    for x in range(CX - 4, CX - 1):
        bb.set(x, 37, CZ - 3, "minecraft:cave_vines[age=0,berries=false]")
    # door at the foot (south), windows (knot holes)
    bb.fill(CX - 1, 1, CZ + 5, CX + 1, 4, CZ + 10, AIR)
    for (fy, a) in ((14, 0.5), (26, 2.3), (36, 4.0), (8, 3.4)):
        r = trunk_r(fy)
        x, z = round(CX + r * math.cos(a)), round(CZ + r * math.sin(a))
        bb.fill(min(x, CX + round((r - 3) * math.cos(a))), fy + 1, min(z, CZ + round((r - 3) * math.sin(a))),
                max(x, CX + round((r - 3) * math.cos(a))), fy + 2, max(z, CZ + round((r - 3) * math.sin(a))), AIR)
    # buttress roots: 8 fins running out and down
    for k in range(8):
        a = k * math.pi / 4 + 0.2
        for d in range(5, 20):
            h = max(0, int((20 - d) * 0.8))
            x, z = round(CX + d * math.cos(a)), round(CZ + d * math.sin(a))
            if k == 2 and d < 12:                     # leave the door side open
                continue
            bb.fill(x, -1, z, x, h, z, WOOD)
            bb.fill(x + round(-math.sin(a)), -1, z + round(math.cos(a)), x + round(-math.sin(a)), max(0, h - 2), z + round(math.cos(a)), WOOD)
    # roots snaking across the valley: half-buried logs wandering outwards, some arching up
    for k in range(14):
        a = k * 2 * math.pi / 14 + rng.uniform(-0.2, 0.2)
        x, z = CX + 18 * math.cos(a), CZ + 18 * math.sin(a)
        for i in range(int(rng.integers(30, 60))):
            a += rng.uniform(-0.25, 0.25)
            x += math.cos(a); z += math.sin(a)
            xi, zi = round(x), round(z)
            if not LAND(np.array([[xi]]), np.array([[zi]]))[0, 0] > 2:
                break
            y = 0 if (i // 9) % 3 else 1
            ax = "x" if abs(math.cos(a)) > abs(math.sin(a)) else "z"
            bb.set(xi, y, zi, f"minecraft:oak_log[axis={ax}]")
            if y == 1:
                bb.set(xi, 0, zi, "minecraft:rooted_dirt")
            if i % 5 == 0:
                set_if_air(bb, xi, y + 1, zi, "minecraft:moss_carpet")
    # big branches and the crown
    tips = []
    for k in range(7):
        a = k * 2 * math.pi / 7 + 0.3
        y0 = TRUNK_H - 16 + (k % 3) * 5
        L = int(rng.integers(14, 20))
        for i in range(L):
            x, z = round(CX + (3 + i) * math.cos(a)), round(CZ + (3 + i) * math.sin(a))
            y = y0 + int(i * 0.55)
            ax = "x" if abs(math.cos(a)) > abs(math.sin(a)) else "z"
            bb.fill(x, y, z, x, y + (1 if i < L // 2 else 0), z, f"minecraft:oak_log[axis={ax}]")
        tips.append((round(CX + (3 + L) * math.cos(a)), y0 + int(L * 0.55), round(CZ + (3 + L) * math.sin(a))))
    tips.append((CX, TRUNK_H + 4, CZ))
    for (tx, ty, tz) in tips:
        r = 8 if (tx, tz) != (CX, CZ) else 11
        bb.fill_where(tx - r - 2, ty - 4, tz - r - 2, tx + r + 2, ty + 6, tz + r + 2,
                      lambda X, y, Z, tx=tx, ty=ty, tz=tz, r=r: (((X - tx) / r) ** 2 + ((y - ty) / 4.5) ** 2 + ((Z - tz) / r) ** 2
                                                               <= 1 - 0.35 * NT.noise(X + y, Z, 4712, 3)),
                      LEAF[0], only_empty=True)
        for i, lf in enumerate(LEAF[1:]):
            bb.fill_where(tx - r - 2, ty - 4, tz - r - 2, tx + r + 2, ty + 6, tz + r + 2,
                          lambda X, y, Z, tx=tx, ty=ty, tz=tz, r=r, i=i: (((X - tx) / r) ** 2 + ((y - ty) / 4.5) ** 2 + ((Z - tz) / r) ** 2 <= 1)
                          & (np.floor(NT.noise(X + 2 * y, Z, 4713, 4) * 5).astype(int) == i + 1), lf)
        for _ in range(r * 2):                                # vines hanging under the crown
            vx, vz = tx + int(rng.integers(-r + 2, r - 1)), tz + int(rng.integers(-r + 2, r - 1))
            for d in range(int(rng.integers(2, 7))):
                if not is_air(bb, vx, ty - 4 - d, vz):
                    break
                bb.set(vx, ty - 4 - d, vz, "minecraft:cave_vines_plant[berries=false]")
    # the throne of roots on top, reached by a ladder from the bedroom up the heartwood
    ty = TRUNK_H + 1
    bb.fill(CX - 4, ty, CZ - 4, CX + 4, ty, CZ + 4, WOOD)
    bb.fill(CX - 3, ty + 1, CZ - 3, CX + 3, ty + 6, CZ + 3, AIR)
    bb.fill(CX - 1, ty + 1, CZ - 3, CX + 1, ty + 1, CZ - 3, WOOD)
    bb.set(CX, ty + 1, CZ - 2, st("minecraft:oak_stairs", "south"))
    bb.fill(CX - 1, ty + 2, CZ - 3, CX + 1, ty + 4, CZ - 3, "minecraft:oak_log[axis=y]")
    bb.set(CX - 2, ty + 1, CZ - 2, "minecraft:oak_log[axis=y]"); bb.set(CX + 2, ty + 1, CZ - 2, "minecraft:oak_log[axis=y]")
    for (dx, dz) in ((-4, -4), (4, -4), (-4, 4), (4, 4), (0, 4)):
        bb.fill(CX + dx, ty + 1, CZ + dz, CX + dx, ty + 2, CZ + dz, "minecraft:oak_fence")
    bb.fill(CX + 2, 35, CZ - 1, CX + 2, ty - 1, CZ - 1, "minecraft:ladder[facing=east,waterlogged=false]")
    bb.fill(CX + 1, 35, CZ - 1, CX + 1, ty, CZ - 1, "minecraft:stripped_oak_log[axis=y]")
    bb.fill(CX + 2, 40, CZ - 1, CX + 2, ty, CZ - 1, "minecraft:ladder[facing=east,waterlogged=false]")
    bb.fill(CX + 3, 40, CZ - 1, CX + 3, ty, CZ - 1, AIR)
    bb.set(CX + 2, ty, CZ - 1, "minecraft:ladder[facing=east,waterlogged=false]")


def dead_tree(bb, x, z, h, rng):
    """A bare grey dead tree: a pale trunk, crooked branches, no leaves, some pale moss hanging."""
    for y in range(1, h + 1):
        bb.set(x, y, z, "minecraft:pale_oak_log[axis=y]")
    for k in range(int(rng.integers(3, 6))):
        a = rng.uniform(0, 2 * math.pi)
        y0 = int(rng.integers(h // 2, h))
        L = int(rng.integers(2, 6))
        for i in range(1, L + 1):
            bx, bz = round(x + i * math.cos(a)), round(z + i * math.sin(a))
            by = y0 + i // 2
            ax = "x" if abs(math.cos(a)) > abs(math.sin(a)) else "z"
            bb.set(bx, by, bz, f"minecraft:pale_oak_log[axis={ax}]")
            if i == L and rng.random() < 0.4:
                set_if_air(bb, bx, by - 1, bz, "minecraft:pale_hanging_moss[tip=true]")


def withered_house(bb, x0, z0, w, d, rot, k, tracker):
    """A Flower Capital town house, withered: roof holed, plaster cracked, dead garden at its door."""
    mod, _, au = FC.machiya(seed_of("wf", k), w, d, 2 if k % 3 else 1, tracker, FC.KINDS[k % len(FC.KINDS)])
    rng = np.random.default_rng(4720 + k)
    place_house(bb, mod, w, d, x0, 0, z0, rot)
    W, D = (w, d) if rot % 2 == 0 else (d, w)
    # holes in the roof and walls: knock out blobs high on the house
    for _ in range(3):
        hx, hz, hy = x0 + int(rng.integers(1, W - 1)), z0 + int(rng.integers(1, D - 1)), int(rng.integers(6, 12))
        bb.fill_where(hx - 2, hy - 1, hz - 2, hx + 2, hy + 3, hz + 2, lambda X, y, Z: (X - hx) ** 2 + (y - hy) ** 2 + (Z - hz) ** 2 <= 4.5, AIR)
    for _ in range(4):
        cx, cz = x0 + int(rng.integers(0, W)), z0 + int(rng.integers(0, D))
        set_if_air(bb, cx, 1, cz, "minecraft:cobweb")
    return au


def village(bb, tracker, rng):
    """The withered village: two rows of houses on a street west of the tree."""
    audit, taken = [], []
    k = 0
    for (zz, rot) in ((30, 0), (44, 2), (92, 0), (128, 2)):
        x = 14
        while x < 56:
            w = int(rng.integers(7, 10))
            d = 9
            ok = all(LAND(np.array([[xx]]), np.array([[z]]))[0, 0] > 3 for xx in (x, x + w) for z in (zz, zz + d))
            if ok and not RIVER(np.array([[x + w // 2]]), np.array([[zz + d // 2]]))[0, 0] and not any(
                    RIVER(np.array([[xx]]), np.array([[z]]))[0, 0] for xx in (x, x + w) for z in (zz, zz + d)):
                audit += withered_house(bb, x, zz, w, d, rot, k, tracker)
                taken.append((x - 1, zz - 1, x + w, zz + d))
                k += 1
            x += w + 2
    # the street between the two north rows, a dead well, a toppled stone lantern
    NT.cover(bb, 12, 40, 58, 43, lambda X, Z: np.zeros(np.broadcast(X, Z).shape), FC.PAVE, 4730)
    bb.fill(34, 1, 41, 36, 1, 43, "minecraft:cobblestone")
    bb.fill(35, 0, 42, 35, 1, 42, AIR)
    bb.set(35, -1, 42, "minecraft:gravel")
    bb.fill(34, 2, 41, 34, 4, 41, "minecraft:spruce_fence"); bb.fill(36, 2, 43, 36, 4, 43, "minecraft:spruce_fence")
    bb.fill(34, 5, 41, 36, 5, 43, "minecraft:spruce_slab[type=bottom,waterlogged=false]")
    bb.fill(50, 1, 40, 52, 1, 40, "minecraft:stone_brick_wall")
    bb.set(53, 1, 40, "minecraft:chiseled_stone_bricks")
    print("withered houses:", k)
    return taken, audit


def broken_bridge(bb):
    """A red arched bridge over the dry river, its middle fallen in."""
    x = 100
    zc = int(112 + 10 * math.sin(x / 17.0))
    for z in range(zc - 6, zc + 7):
        if abs(z - zc) < 2:
            continue
        y = 1 + (3 - abs(z - zc) // 2 if abs(z - zc) < 6 else 0)
        bb.fill(x - 1, y, z, x + 1, y, z, "minecraft:spruce_planks")
        bb.set(x - 2, y + 1, z, "minecraft:red_concrete" if z % 3 == 0 else "minecraft:spruce_fence")
        bb.set(x + 2, y + 1, z, "minecraft:red_concrete" if z % 3 == 0 else "minecraft:spruce_fence")
    bb.fill(x - 1, -2, zc - 1, x + 1, -2, zc + 1, "minecraft:spruce_planks")


def marine_camp(bb):
    """The Marines' tents at the tree's foot (south-east): white canvas, crates, a cooking fire, a flag."""
    for (tx, tz) in ((96, 92), (106, 90), (98, 102)):
        for i in range(4):
            bb.fill(tx - 3 + i, 1 + i, tz - 3, tx - 3 + i, 1 + i, tz + 3, "minecraft:white_wool")
            bb.fill(tx + 3 - i, 1 + i, tz - 3, tx + 3 - i, 1 + i, tz + 3, "minecraft:white_wool")
        bb.fill(tx - 2, 1, tz - 3, tx + 2, 3, tz - 3, "minecraft:white_wool")
        bb.fill(tx - 1, 1, tz + 3, tx + 1, 2, tz + 3, AIR)
        bb.set(tx, 1, tz, "minecraft:white_bed[facing=south,occupied=false,part=head]")
        bb.set(tx, 1, tz + 1, "minecraft:white_bed[facing=south,occupied=false,part=foot]")
    bb.set(102, 1, 97, "minecraft:campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
    for (x, z) in ((92, 99), (93, 99), (92, 100)):
        bb.set(x, 1, z, "minecraft:barrel[facing=up,open=false]")
    bb.fill(110, 1, 98, 110, 9, 98, "minecraft:white_concrete")
    bb.fill(111, 6, 98, 115, 9, 98, "minecraft:white_wool")
    bb.fill(112, 7, 98, 114, 8, 98, "minecraft:blue_wool")
    lamp_post(bb, 104, 1, 97, post="minecraft:spruce_fence", h=2)


def design():
    bb = BigBuild(seed=4700, y_min=-8, y_max=TRUNK_H + 20)
    tracker = P.PropTracker(4700)
    rng = np.random.default_rng(4700)
    ground(bb)
    giant_tree(bb, rng)
    taken, audit = village(bb, tracker, rng)
    broken_bridge(bb)
    marine_camp(bb)
    taken += [(CX - 24, CZ - 24, CX + 24, CZ + 24), (88, 84, 118, 106)]
    n = 0
    for _ in range(4000):
        x, z = int(rng.integers(6, N - 6)), int(rng.integers(6, N - 6))
        if LAND(np.array([[x]]), np.array([[z]]))[0, 0] < 3 or RIVER(np.array([[x]]), np.array([[z]]))[0, 0]:
            continue
        if any(t[0] - 2 <= x <= t[2] + 2 and t[1] - 2 <= z <= t[3] + 2 for t in taken):
            continue
        if int(bb.get_region(x, 1, z, x, 1, z)[0, 0, 0]) > 1 and "dry" not in bb.names[int(bb.get_region(x, 1, z, x, 1, z)[0, 0, 0])] \
                and "dead_bush" not in bb.names[int(bb.get_region(x, 1, z, x, 1, z)[0, 0, 0])]:
            continue
        dead_tree(bb, x, z, int(rng.integers(6, 15)), rng)
        taken.append((x - 2, z - 2, x + 2, z + 2))
        n += 1
        if n >= 90:
            break
    return bb, audit


def build():
    bb, audit = design()
    print("audit fails:", len(audit))
    b = to_canvas(bb)
    FC.steady(b)
    b.chest(CX - 5, 13, CZ + 1, "wano", "east")
    b.chest(CX - 4, TRUNK_H + 2, CZ + 2, "treasure", "north")
    b.chest(94, 1, 100, "marine", "east")
    b.npc(CX, TRUNK_H + 2, CZ, "ryokugyu", True)
    b.guards("marine", ((100, 96), (96, 86), (108, 96)), y=1)
    b.guards("war_beast", ((CX, CZ + 22),), y=1)
    return b, 0

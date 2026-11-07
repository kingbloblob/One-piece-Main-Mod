"""Ryokugyu's Withered Forest: a Wano valley where Admiral Green Bull drank the life out of everything. Grey dead
trees, dried grass and a village of withered Wano houses ring the one thing still alive: Ryokugyu's giant tree,
a 40 m trunk with buttress roots strangling the ground, a hollow inside with spiral stairs, rooms on platforms
(the Marine camp's store, a study, a bedroom with a hammock of vines) and the leafy crown where he sits on a
throne of roots. Vines and roots creep out across the whole valley. ~96 x 96. Ground = y 0."""
import math, random
from canvas import *
import interiors as I
import kamazo_hideout as KH

SID = "withered_forest"
TITLE = "Ryokugyu's Withered Forest"
CUTS = [3, 20]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")

N = 96
CX, CZ = 48, 46
TR = 8                    # trunk radius at the base
TH = 40                   # trunk height
BARK = "minecraft:jungle_wood[axis=y]"
GREEN = dict(wood="jungle", rug="green", rug2="lime", bed="green", light="minecraft:ochre_froglight[axis=y]", accent="minecraft:moss_block",
             banner="green", candle="lime")
MARINE = I.THEMES["marine"]


def dead_tree(b, x, z, h, rnd):
    for y in range(1, h): b.set(x, y, z, "minecraft:stripped_pale_oak_log[axis=y]" if y % 3 else "minecraft:pale_oak_log[axis=y]")
    for k in range(rnd.randint(2, 4)):
        ax, az = rnd.choice(((1, 0), (-1, 0), (0, 1), (0, -1)))
        y0 = rnd.randint(h // 2, h - 1)
        for j in range(1, rnd.randint(3, 5)): b.set(x + ax * j, y0 + j // 2, z + az * j, "minecraft:pale_oak_log[axis=x]" if ax else "minecraft:pale_oak_log[axis=z]")


def build():
    rnd = random.Random(113)
    b = B()
    # ---------------- drained valley
    for x in range(N):
        for z in range(N):
            for y in (-4, -3, -2, -1): b.set(x, y, z, "minecraft:dirt")
            d = math.hypot(x - CX, z - CZ)
            alive = d < 16
            b.set(x, 0, z, "minecraft:moss_block" if alive else rnd.choice(("minecraft:coarse_dirt", "minecraft:podzol", "minecraft:rooted_dirt", "minecraft:coarse_dirt", "minecraft:dirt_path" if False else "minecraft:packed_mud")))
            if alive and rnd.random() < 0.3: b.set(x, 1, z, rnd.choice(("minecraft:fern", "minecraft:short_grass", "minecraft:moss_carpet", "minecraft:azalea")))
            elif not alive and rnd.random() < 0.06: b.set(x, 1, z, rnd.choice(("minecraft:dead_bush", "minecraft:dead_bush", "minecraft:short_dry_grass" if False else "minecraft:dead_bush")))
    # dead forest all round
    for i in range(70):
        a = rnd.uniform(0, 2 * math.pi); rr = rnd.uniform(26, 46)
        x, z = round(CX + rr * math.cos(a)), round(CZ + rr * math.sin(a))
        if 3 < x < N - 4 and 3 < z < N - 4 and b.get(x, 1, z) is None: dead_tree(b, x, z, rnd.randint(7, 14), rnd)
    # ---------------- withered Wano village
    for (x0, z0, x1, z1, kind) in ((10, 12, 22, 22, "kitchen"), (72, 10, 84, 20, "bedroom"), (8, 70, 20, 80, "shrine"), (74, 72, 86, 84, "storage")):
        if any(b.get(x, 2, z) for x in range(x0, x1 + 1) for z in range(z0, z1 + 1)):
            for x in range(x0 - 1, x1 + 2):
                for z in range(z0 - 1, z1 + 2):
                    for y in range(1, 16): b.set(x, y, z, AIR) if (x, y, z) in b.blocks else None
        KH.wano_house(b, x0, z0, x1, z1, 5, 2)
        I.furnish(b, x0 + 1, 2, z0 + 1, x1 - 1, z1 - 1, 4, kind, "wano")
        for x in range(x0, x1 + 1):  # dried out: holes in the shoji, roof tiles slipped
            for z in (z0, z1):
                if rnd.random() < 0.3 and "shoji" in (b.get(x, 3, z) or ""): b.set(x, 3, z, AIR)
        for k in range(14): b.set(rnd.randint(x0 - 1, x1 + 1), rnd.randint(7, 9), rnd.randint(z0 - 1, z1 + 1), AIR)
    # ---------------- the Marine camp (east)
    for (tx, tz) in ((80, 40), (80, 50), (88, 45)):
        for dx in range(-2, 3):
            for dy in range(0, 3 - abs(dx)):
                for dz in range(0, 6): b.set(tx + dx, 1 + dy, tz + dz, "minecraft:white_wool" if dy < 2 else "minecraft:blue_wool")
        for dz in range(0, 6): b.set(tx, 1, tz + dz, AIR)
    for y in range(1, 10): b.set(76, y, 46, "minecraft:birch_fence")
    for y in range(7, 10):
        for k in range(1, 5): b.set(76, y, 46 + k, "minecraft:blue_wool" if y == 8 else "minecraft:white_wool")
    b.set(84, 1, 47, "minecraft:campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
    # ---------------- creeping roots across the valley
    for k in range(14):
        a = k / 14 * 2 * math.pi + rnd.uniform(-0.1, 0.1)
        L = rnd.uniform(22, 40)
        px, pz, py = CX + TR * math.cos(a), CZ + TR * math.sin(a), 4.0
        for s in range(int(L * 2)):
            a += rnd.uniform(-0.08, 0.08)
            px += 0.5 * math.cos(a); pz += 0.5 * math.sin(a); py = max(0.0, py - 0.12)
            rr = max(0.6, 2.4 * (1 - s / (L * 2)))
            for dx in range(-2, 3):
                for dz in range(-2, 3):
                    for dy in range(-1, 3):
                        if dx * dx + dz * dz + dy * dy <= rr * rr:
                            x, y, z = round(px + dx), round(py + dy), round(pz + dz)
                            if 0 <= x < N and 0 <= z < N and y >= 0: b.set(x, y, z, "minecraft:jungle_wood[axis=y]" if y > 0 else "minecraft:rooted_dirt")
    # ---------------- the giant living tree
    def trunk_r(y):
        return TR * (1 + 0.6 * math.exp(-y / 4)) * (1 - 0.35 * y / TH)
    for y in range(0, TH + 1):
        rr = trunk_r(y)
        b.cyl(CX, CZ, rr, y, y, BARK)
        b.cyl(CX, CZ, rr - 2.2, y, y, AIR) if y > 0 else b.cyl(CX, CZ, rr - 2.2, 0, 0, "minecraft:moss_block")
    for y in range(1, TH + 1, 9):  # knot holes as windows
        for a in range(0, 360, 90):
            t = math.radians(a + y * 7); rr = trunk_r(y)
            for k in range(-1, 3):
                for dy in (1, 2): b.set(round(CX + (rr - k) * math.cos(t)), y + dy, round(CZ + (rr - k) * math.sin(t)), AIR)
    for dz in range(-2, 3):  # entrance split in the trunk (south)
        for y in range(1, 6):
            for k in range(0, 5): b.set(CX + dz, y, CZ + round(trunk_r(y)) - k + 1, AIR)
    # platforms with rooms inside the hollow, a spiral stair round the wall
    PL = (12, 22, 32)
    for i, py in enumerate(PL):
        rin = trunk_r(py) - 2.3
        b.cyl(CX, CZ, rin, py - 1, py - 1, "minecraft:jungle_planks")
        hw = int(rin * 0.62)
        I.furnish(b, CX - hw, py, CZ - hw, CX + hw, CZ + hw, 7, ("storage", "study", "bedroom")[i], GREEN if i else MARINE, seed=500 + i)
    r0 = I.furnish(b, CX - 4, 1, CZ - 4, CX + 4, CZ + 4, 9, "hall", GREEN, seed=499)
    for s in range(PL[-1] + 1):
        a = s * 0.35
        rr = trunk_r(s) - 3.2
        x, z = round(CX + rr * math.cos(a)), round(CZ + rr * math.sin(a))
        for k in (0, 1):
            xx, zz = round(CX + (rr + k) * math.cos(a)), round(CZ + (rr + k) * math.sin(a))
            b.set(xx, s, zz, "minecraft:jungle_planks")
            for h in (1, 2, 3): b.set(xx, s + h, zz, AIR)
    # the crown: branches, leaf canopy and the root throne on top
    CY = TH + 1
    b.cyl(CX, CZ, trunk_r(TH) + 1, TH, TH, "minecraft:jungle_planks")
    for k in range(8):
        a = math.radians(k * 45 + 10)
        for s in range(18):
            x = round(CX + (4 + s) * math.cos(a)); z = round(CZ + (4 + s) * math.sin(a)); y = CY + s // 3
            b.set(x, y, z, "minecraft:jungle_log[axis=x]" if abs(math.cos(a)) > 0.7 else "minecraft:jungle_log[axis=z]")
        ex, ez = CX + 20 * math.cos(a), CZ + 20 * math.sin(a)
        b.sphere(round(ex), CY + 8, round(ez), 6, "minecraft:jungle_leaves[distance=7,persistent=true,waterlogged=false]", ry=3.5)
    b.sphere(CX, CY + 12, CZ, 12, "minecraft:jungle_leaves[distance=7,persistent=true,waterlogged=false]", ry=5)
    b.cyl(CX, CZ, 6, CY + 7, CY + 12, AIR)  # a hollow in the canopy for the throne
    b.cyl(CX, CZ, 6, CY + 6, CY + 6, "minecraft:moss_block")
    b.set(CX, CY + 7, CZ - 2, "minecraft:jungle_stairs[facing=south,half=bottom,shape=straight,waterlogged=false]")
    for (dx, dz) in ((-1, -2), (1, -2), (0, -3), (-1, -3), (1, -3)): b.set(CX + dx, CY + 7, CZ + dz, "minecraft:jungle_log[axis=y]")
    for dy in range(8, 11): b.set(CX, CY + dy, CZ - 3, "minecraft:jungle_log[axis=y]")
    for y in range(PL[-1], CY + 7): b.set(CX + 2, y, CZ + 2, "minecraft:ladder[facing=north,waterlogged=false]") if False else b.set(CX, y, CZ, "minecraft:jungle_log[axis=y]")
    for y in range(PL[-1], CY + 7): b.set(CX, y, CZ + 1, "minecraft:ladder[facing=south,waterlogged=false]")
    for (dx, dz) in ((0, 1), (0, 2)): b.set(CX + dx, PL[-1] - 1, CZ + dz, "minecraft:jungle_planks")
    for y in (TH, CY + 6): b.set(CX, y, CZ + 1, "minecraft:ladder[facing=south,waterlogged=false]")
    for i in range(60):  # hanging vines and glow berries round the crown
        a = rnd.uniform(0, 2 * math.pi); rr = rnd.uniform(8, 22)
        x, z = round(CX + rr * math.cos(a)), round(CZ + rr * math.sin(a))
        for y in range(CY + 4, CY - 6, -1):
            if b.get(x, y, z) is None:
                for k in range(rnd.randint(2, 6)):
                    if b.get(x, y - k, z) is None: b.set(x, y - k, z, "minecraft:cave_vines[age=0,berries=" + ("true" if k % 2 else "false") + "]" if k else "minecraft:cave_vines_plant[berries=false]")
                break
    # ---------------- people and loot
    b.npc(CX, CY + 7, CZ - 1, "ryokugyu", True)
    b.chest(CX + 3, PL[0], CZ - 3, "hard", "west"); b.chest(CX - 3, PL[2], CZ + 3, "hard", "east")
    b.guards("war_beast", ((CX, CZ + 20),))
    b.guards("marine", ((78, 44), (82, 56), (86, 40), (CX - 6, CZ + 14)))
    return b, 0

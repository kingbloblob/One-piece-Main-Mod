"""The skeleton of a colossal Sea King on the sea floor, life size: a serpent over 100 m long whose spine coils
across the sand in a great S, ribs arching up like the vaults of a cathedral, the huge horned skull with its
open jaws and rows of fangs, and fins of bone. Coral, kelp and sea pickles have grown over it, and a sunken
treasure lies inside the skull. Sea floor = y 0; everything inside is flooded."""
import math, random
from canvas import *

SID = "sea_king_bones"
TITLE = "Sea King Skeleton"
CUTS = [4, 10]
TILER = dict(heightmap="OCEAN_FLOOR_WG", terrain="none")

NX, NZ = 112, 80
BONE = "minecraft:bone_block[axis=y]"
BONEX = "minecraft:bone_block[axis=x]"


def spine(t):
    """Point and heading along the S-shaped spine, t in 0..1 (0 = tail, 1 = skull)."""
    x = 6 + t * 74
    z = 40 + 20 * math.sin(t * math.pi * 1.6)
    dz = 20 * math.pi * 1.6 * math.cos(t * math.pi * 1.6) / 74
    return x, z, math.atan2(dz, 1)


def build():
    rnd = random.Random(791)
    b = B()
    for x in range(NX):
        for z in range(NZ):
            for y in (-3, -2, -1): b.set(x, y, z, "minecraft:sandstone")
            b.set(x, 0, z, "minecraft:sand" if rnd.random() > 0.12 else "minecraft:gravel")
    # ---------------- the spine and ribs
    n = 200
    for i in range(n + 1):
        t = i / n
        x, z, h = spine(t)
        size = 1.5 + 5.0 * math.sin(math.pi * min(1, t * 1.1)) ** 0.7  # body thickness
        cy = 1 + size * 1.3
        b.sphere(x, cy, z, 1.3 if t < 0.9 else 1.7, BONE)
        if i % 9 == 0 and 0.08 < t < 0.92:  # a rib pair: arch over the body
            nx, nz = -math.sin(h), math.cos(h)
            R = size * 2.4
            for a in range(0, 181, 6):
                ar = math.radians(a)
                px = x + nx * R * math.cos(ar); pz = z + nz * R * math.cos(ar)
                py = cy + R * 0.8 * math.sin(ar) - R * 0.35
                if py >= 0.5: b.set(round(px), round(py), round(pz), BONE)
        if i % 12 == 0 and 0.15 < t < 0.85:  # spines of the dorsal fin
            for k in range(int(size * 2)): b.set(round(x), round(cy + 1 + k), round(z), BONE if k < size * 2 - 1 else "minecraft:bone_block[axis=y]")
    # ---------------- the skull, jaws open
    sx, sz, h = spine(1.0)
    ux, uz = math.cos(h), math.sin(h)
    for k in range(24):
        f = k / 23
        cx, cz = sx + ux * k, sz + uz * k
        rw = 8.5 * (1 - 0.55 * f)
        # upper jaw (raised) and lower jaw (dropped)
        for (yc, ry) in ((12 + 5 * f, 4.2 * (1 - 0.5 * f)), (2.5 - 0.6 * f, 1.6)):
            b.shape(lambda X, Y, Z, cx=cx, cz=cz, yc=yc, ry=ry, rw=rw: ((X - cx) / 1.2) ** 2 + ((Y - yc) / ry) ** 2 + ((Z - cz) / rw) ** 2 <= 1 and
                    ((X - cx) / 1.2) ** 2 + ((Y - yc) / (ry - 1)) ** 2 + ((Z - cz) / (rw - 1.2)) ** 2 > 1 if ry > 1.2 else True,
                    round(cx) - 2, max(1, round(yc - ry) - 1), round(cz - rw) - 1, round(cx) + 2, round(yc + ry) + 1, round(cz + rw) + 1, BONE, interior=None)
        if k % 2 == 0 and k > 2:  # fangs
            for side in (-1, 1):
                fz = cz + side * (rw - 1.3) * 0.9
                for d in range(3):
                    b.set(round(cx), round(12 + 5 * f - 4.2 * (1 - 0.5 * f)) - d, round(fz), "minecraft:white_concrete" if False else "minecraft:pointed_dripstone[thickness=tip,vertical_direction=down,waterlogged=true]" if d == 2 else "minecraft:calcite")
                    b.set(round(cx), 3 + d, round(fz), "minecraft:calcite" if d < 2 else "minecraft:pointed_dripstone[thickness=tip,vertical_direction=up,waterlogged=true]")
    for side in (-1, 1):  # horns and eye sockets
        for k in range(12):
            b.sphere(sx - ux * k * 0.6, 15 + k, sz + side * (5 + k * 0.5), 0.8, BONE)
        b.sphere(sx + ux * 5, 14, sz + side * 5.5, 1.6, "minecraft:black_concrete")
    # pectoral fins of bone
    for t in (0.75, 0.3):
        x, z, h = spine(t)
        for side in (-1, 1):
            for k in range(10):
                for s in range(-k // 3, k // 3 + 1):
                    b.set(round(x - math.cos(h) * k * 0.7 + s), 1, round(z + side * (5 + k)), BONEX if (k + s) % 2 else BONE)
    # ---------------- coral, kelp and the treasure inside the skull
    for i in range(160):
        x, z = rnd.randint(1, NX - 2), rnd.randint(1, NZ - 2)
        if b.get(x, 1, z) not in (None, AIR): continue
        b.set(x, 1, z, rnd.choice(("minecraft:tube_coral", "minecraft:brain_coral", "minecraft:fire_coral", "minecraft:horn_coral", "minecraft:bubble_coral",
                                   "minecraft:seagrass", "minecraft:sea_pickle[pickles=4,waterlogged=true]")))
    for i in range(36):
        x, z = rnd.randint(1, NX - 2), rnd.randint(1, NZ - 2)
        if b.get(x, 1, z) not in (None, AIR): continue
        h = rnd.randint(4, 14)
        for y in range(1, h): b.set(x, y, z, "minecraft:kelp_plant")
        b.set(x, h, z, "minecraft:kelp[age=20]")
    for k, v in list(b.blocks.items()):
        if v.startswith("minecraft:bone_block") and k[1] > 1 and rnd.random() < 0.05:
            b.blocks[k] = rnd.choice(("minecraft:brain_coral_block", "minecraft:tube_coral_block", "minecraft:dead_horn_coral_block"))
            up = (k[0], k[1] + 1, k[2])
            if up not in b.blocks: b.blocks[up] = "minecraft:sea_pickle[pickles=2,waterlogged=true]"
    for k, v in list(b.blocks.items()):
        if v == AIR: b.blocks[k] = WATER
    b.chest(round(sx + ux * 6), 1, round(sz + uz * 6), "easy", "south"); b.chest(round(sx + ux * 3), 1, round(sz + uz * 3) + 1, "easy", "north")
    return b, 0

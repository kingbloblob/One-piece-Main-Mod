"""Shared pieces for the underground builds: organic caverns made of overlapping domes with a rock shell, hanging
dripstone, tunnels that run out into the world's own caves, rubble and glowing patches."""
import math, random, sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'landmarks'))
from canvas import *  # noqa: F401,F403

DRIP_TIP = "minecraft:pointed_dripstone[thickness=tip,vertical_direction=down,waterlogged=false]"
DRIP_FRU = "minecraft:pointed_dripstone[thickness=frustum,vertical_direction=down,waterlogged=false]"
DRIP_BASE = "minecraft:pointed_dripstone[thickness=base,vertical_direction=down,waterlogged=false]"
DRIP_UP_TIP = "minecraft:pointed_dripstone[thickness=tip,vertical_direction=up,waterlogged=false]"
DRIP_UP_FRU = "minecraft:pointed_dripstone[thickness=frustum,vertical_direction=up,waterlogged=false]"


def cave(b, blobs, shell, floor, rnd, thick=3, below=3, rough=0.10):
    """blobs: (cx, cz, rx, rz, h) half-ellipsoid domes standing on y 0. The union is AIR from y 1 up, the floor
    (y <= 0 under the domes) is `floor`, and a shell `thick` deep of `shell` wraps it, so water and lava from the
    world's aquifers never pour in. shell/floor may be a block or a tuple to pick from. Returns inside(x, y, z)."""
    pick = lambda s: rnd.choice(s) if isinstance(s, tuple) else s

    def d(x, y, z, grow=0.0):
        best = 9.0
        for (cx, cz, rx, rz, h) in blobs:
            v = ((x - cx) / (rx + grow)) ** 2 + ((z - cz) / (rz + grow)) ** 2 + (max(0, y) / (h + grow)) ** 2
            best = min(best, v)
        n = 1 + rough * math.sin(x * 0.31 + z * 0.17 + y * 0.23) * math.cos(z * 0.27 - x * 0.11 + y * 0.19)
        return best / n
    x0 = int(min(c - r for (c, _, r, _, _) in blobs)) - thick - 2
    x1 = int(max(c + r for (c, _, r, _, _) in blobs)) + thick + 2
    z0 = int(min(c - r for (_, c, _, r, _) in blobs)) - thick - 2
    z1 = int(max(c + r for (_, c, _, r, _) in blobs)) + thick + 2
    top = int(max(h for (*_, h) in blobs)) + thick + 2
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            for y in range(-below, top + 1):
                if y <= 0:
                    if d(x, 0, z, thick) < 1: b.set(x, y, z, pick(floor) if y == 0 and d(x, 0, z) < 1 else pick(shell))
                elif d(x, y, z) < 1:
                    b.set(x, y, z, AIR)
                elif d(x, y, z, thick) < 1:
                    b.set(x, y, z, pick(shell))
    return lambda x, y, z: y >= 1 and d(x, y, z) < 1


# Vanilla water/lava springs (25 a chunk) only form in these blocks; a neighbouring chunk decorated after the build
# would put one in a notch of the cave wall and pour a waterfall in, so the rock that touches the air must not be one.
SPRING_ROCK = {"minecraft:stone": "minecraft:cobblestone", "minecraft:andesite": "minecraft:cobblestone",
               "minecraft:granite": "minecraft:packed_mud", "minecraft:diorite": "minecraft:cobblestone",
               "minecraft:deepslate": "minecraft:cobbled_deepslate", "minecraft:tuff": "minecraft:cobbled_deepslate",
               "minecraft:calcite": "minecraft:dripstone_block", "minecraft:dirt": "minecraft:coarse_dirt"}


def springproof(b, rnd=None):
    """Swap spring-friendly rock round every air cell for look-alikes that springs can't use (cells past the build's
    edge are left alone so the tunnels still open into the world's caves). Some stone becomes dripstone."""
    rnd = rnd or random.Random(7)
    near = set()
    for (x, y, z), v in list(b.blocks.items()):
        if v in (AIR, "minecraft:cave_air"):
            for (dx, dy, dz) in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
                near.add((x + dx, y + dy, z + dz))
    for p in near:
        cur = b.blocks.get(p)
        if cur is not None and cur.split("[")[0] in SPRING_ROCK:
            k = cur.split("[")[0]
            b.set(*p, "minecraft:dripstone_block" if k == "minecraft:stone" and rnd.random() < 0.35 else SPRING_ROCK[k])


def air(b, x, y, z):
    return b.get(x, y, z) in (AIR, "minecraft:cave_air")


def solid(b, x, y, z):
    s = b.get(x, y, z)
    return s is not None and s not in (AIR, "minecraft:cave_air") and "water" not in s and "dripstone" not in s


def dripstones(b, inside, area, rnd, chance=0.05, up_chance=0.02):
    """Hanging dripstone from the cave roof (and a few rising from the floor) over the free area."""
    (x0, z0, x1, z1) = area
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            ys = [y for y in range(1, 60) if (x, y, z) in b.blocks and air(b, x, y, z) and solid(b, x, y + 1, z)]
            for y in ys[-1:]:
                if rnd.random() < chance:
                    n = rnd.choice((1, 2, 2, 3))
                    if all(air(b, x, y - k, z) for k in range(n + 2)):
                        seq = [DRIP_BASE, DRIP_FRU][:max(0, n - 1)] + [DRIP_TIP]
                        for k, s in enumerate(seq): b.set(x, y - k, z, s)
            if rnd.random() < up_chance and air(b, x, 1, z) and air(b, x, 2, z) and air(b, x, 3, z) and solid(b, x, 0, z):
                b.set(x, 1, z, DRIP_UP_FRU); b.set(x, 2, z, DRIP_UP_TIP)


def tunnel(b, p0, p1, r=1.6, floor=None):
    """A rough tunnel of AIR (it carves through the world's rock too), flat-floored when floor is given."""
    (x0, y0, z0), (x1, y1, z1) = p0, p1
    n = int(max(abs(x1 - x0), abs(y1 - y0), abs(z1 - z0))) + 1
    for i in range(n + 1):
        t = i / n
        cx, cy, cz = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, z0 + (z1 - z0) * t
        R = r + 0.5 * math.sin(i * 0.7)
        for x in range(int(cx - R) - 1, int(cx + R) + 2):
            for y in range(int(cy - R) - 1, int(cy + R) + 2):
                for z in range(int(cz - R) - 1, int(cz + R) + 2):
                    if (x - cx) ** 2 + ((y - cy) * 1.2) ** 2 + (z - cz) ** 2 <= R * R and y >= int(cy) - 1:
                        cur = b.get(x, y, z)
                        if y == int(cy) - 1 and floor:
                            if cur is None or cur == AIR: b.set(x, y, z, floor)
                        elif cur is None or not cur.startswith("minecraft:") or cur.split("[")[0] in ROCKS:
                            b.set(x, y, z, AIR)


ROCKS = {"minecraft:stone", "minecraft:deepslate", "minecraft:tuff", "minecraft:andesite", "minecraft:cobbled_deepslate",
         "minecraft:calcite", "minecraft:dripstone_block", "minecraft:blackstone", "minecraft:basalt", "minecraft:smooth_basalt",
         "minecraft:granite", "minecraft:diorite", "minecraft:cobblestone", "minecraft:mossy_cobblestone", "minecraft:gravel"}


def scatter_floor(b, inside, area, blocks, n, rnd, need_air=2):
    """Drop props on free floor spots (solid below, air above)."""
    (x0, z0, x1, z1) = area
    placed = 0; tries = 0
    while placed < n and tries < n * 40:
        tries += 1
        x, z = rnd.randint(x0, x1), rnd.randint(z0, z1)
        for y in range(1, 40):
            if air(b, x, y, z) and solid(b, x, y - 1, z) and all(air(b, x, y + k, z) for k in range(1, need_air)):
                b.set(x, y, z, rnd.choice(blocks)); placed += 1
                break
            if not air(b, x, y, z): continue
    return placed


def ceiling_glow(b, area, rnd, block="minecraft:glow_lichen[down=false,east=false,north=false,south=false,up=true,waterlogged=false,west=false]", chance=0.04):
    """Glow lichen on the underside of the roof."""
    (x0, z0, x1, z1) = area
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            for y in range(50, 1, -1):
                if air(b, x, y, z) and solid(b, x, y + 1, z):
                    if rnd.random() < chance: b.set(x, y, z, block)
                    break


def skeleton(b, x, y, z, facing="east"):
    """Old pirate remains: a skull on a pile of bones."""
    b.set(x, y, z, "minecraft:bone_block[axis=x]" if facing in ("east", "west") else "minecraft:bone_block[axis=z]")
    rot = {"north": 8, "south": 0, "east": 12, "west": 4}[facing]
    b.set(x, y + 1, z, f"minecraft:skeleton_skull[powered=false,rotation={rot}]")

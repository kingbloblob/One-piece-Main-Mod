"""Shared pieces for the Sabaody Archipelago builds: the giant Yarukiman mangrove trees with their arching roots,
soap bubbles floating up from the ground, grove number signs and bubble lamps."""
import math, random
from canvas import *

YLOG = "onepiece:yarukiman_log[axis=y]"
YWOOD = "onepiece:yarukiman_wood"
YLEAF = "onepiece:yarukiman_leaves[distance=7,persistent=true,waterlogged=false]"
BUB = "onepiece:bubble_glass"


def ground_top(x, z, seed=4613):
    """The grove floor in soft patches, not a repeating grid: mostly grass, with moss and podzol drifts, coarse and
    rooted dirt where it is worn, and the dark mangrove roots only in a few wet hollows (with mud round them)."""
    import landkit as L
    m = L.noise2(x, z, seed, 13) * 0.6 + L.noise2(x, z, seed + 1, 5) * 0.4      # wet (low) .. mossy (high)
    q = L.noise2(x, z, seed + 2, 9) * 0.7 + L.noise2(x, z, seed + 3, 3) * 0.3   # second patch field
    fine = L.noise2(x, z, seed + 4, 2)                                          # ragged patch edges
    if m < 0.17 + 0.05 * fine:
        return "minecraft:muddy_mangrove_roots" if fine > 0.55 else "minecraft:mud"
    if m < 0.23 + 0.05 * fine:
        return "minecraft:rooted_dirt" if fine > 0.5 else "minecraft:podzol"
    if m > 0.72 + 0.06 * fine:
        return "minecraft:moss_block"
    if q > 0.76 + 0.06 * fine:
        return "minecraft:podzol" if fine > 0.35 else "minecraft:coarse_dirt"
    return "minecraft:grass_block"


def ground(b, nx, nz, rnd, seed=4613):
    for x in range(nx):
        for z in range(nz):
            for y in (-3, -2, -1): b.set(x, y, z, "minecraft:mud")
            top = ground_top(x, z, seed)
            b.set(x, 0, z, top)
            if rnd.random() < 0.06: rnd.choice((0, 1, 2))              # keeps the caller's random stream as before
            # plants grow in drifts: thick ferns and grass in some patches, bare in others, moss carpet on the moss
            import landkit as L
            d = L.noise2(x, z, seed + 7, 6) * 0.7 + L.noise2(x, z, seed + 8, 2) * 0.3
            r = L.noise2(x * 7 + 1, z * 7 + 3, seed + 9, 1)
            if top == "minecraft:moss_block":
                if r < 0.45: b.set(x, 1, z, "minecraft:moss_carpet")
            elif top == "minecraft:grass_block" and r < max(0.0, 1.6 * d - 0.55):
                b.set(x, 1, z, "minecraft:fern" if L.noise2(x, z, seed + 10, 7) > 0.6 else "minecraft:short_grass")


def yarukiman(b, x, z, rnd, r=4.0, h=30, crown=True):
    """A giant mangrove: a thick trunk standing on arching roots, crown of leaves high up."""
    for k in range(8):
        a = k * math.pi / 4 + rnd.uniform(-0.2, 0.2)
        L = r + rnd.uniform(4, 7)
        for i in range(24):
            t = i / 23
            rx, rz = x + (r + (L - r) * t) * math.cos(a), z + (r + (L - r) * t) * math.sin(a)
            ry = round(7 * math.sin((1 - t) * math.pi / 2) - 1)
            b.cyl(rx, rz, 1.1, max(0, ry - 1), ry, YWOOD)
    for y in range(6, h):
        b.cyl(x, z, r * (1 - 0.25 * y / h), y, y, YLOG)
    for y in range(0, 6):
        b.cyl(x, z, r * 0.6, y, y, YLOG)
    if crown:
        b.sphere(x, h + 3, z, r * 3.0, YLEAF, ry=r * 1.2)
        for k in range(5):
            a = k * 1.26
            b.line((x, h - 2, z), (x + r * 2.4 * math.cos(a), h + 2, z + r * 2.4 * math.sin(a)), YWOOD)


def grove_number(b, x, y, z, n, axis="x"):
    """The big painted grove number on a trunk."""
    b.text(x, y, z, str(n), "minecraft:white_concrete", axis=axis)


def bubbles(b, nx, nz, rnd, n=18, y0=4, y1=24, keep=lambda x, z: True):
    for i in range(n):
        x, z = rnd.randint(3, nx - 4), rnd.randint(3, nz - 4)
        if not keep(x, z): continue
        y = rnd.randint(y0, y1)
        if b.get(x, y, z) is None: b.sphere(x, y, z, rnd.uniform(1.0, 2.2), BUB, hollow=True)

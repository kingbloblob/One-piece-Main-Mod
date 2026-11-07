"""Demo of archkit.py: one of each house type and roof kind on flat ground, furnished through interiors.furnish, so the
helpers can be checked in renders and cuts. Row 1: house2 town houses (L gable, T hip, offset half-hip, U mansard,
saltbox cottage, gambrel). Row 2: curved roofs (bell, flare) and Alabasta desert houses. Row 3: Wano houses and a
row of Water 7 houses, plus a stone hall with a stair tower."""
import random
from canvas import *
import interiors as I
import townkit as T
import archkit as A

SID = "demo_archkit"
TITLE = "Architecture kit demo"
CUTS = [3, 7, 11]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")
SOFT_EDGES = False  # a test plate: keep the whole lawn so the gaps between houses don't read as holes
NX, NZ = 136, 100


INFOS = []  # the house dicts of the last build, for checks


def furnish(b, info, kinds, seed, theme="pirate"):
    """Furnish every room of a house dict, then put its ladder back (furniture may stand in the ladder column)."""
    INFOS.append(info)
    for f, (fy, rs) in enumerate(zip(info["floors"], info["rooms"])):
        for i, r in enumerate(rs):
            if r[2] - r[0] < 2 or r[3] - r[1] < 2: continue
            I.furnish(b, r[0], fy, r[1], r[2], r[3], A.FH - 1, kinds[(f + i) % len(kinds)], theme, seed=seed + f * 7 + i)
    for (lx, lz, ya, yb, blk) in info["ladder"]:
        for yy in range(ya, yb + 1): b.set(lx, yy, lz, blk)
        for yy in (yb + 1, yb + 2): b.set(lx, yy, lz, AIR) if b.get(lx, yy, lz) not in (None, AIR) and "ladder" not in b.get(lx, yy, lz) else None
    dx, dy, dz, side = info["door"]
    ox, oz = A.DIRV[side]
    for yy in (dy, dy + 1): b.set(dx - ox, yy, dz - oz, AIR)  # keep the way in clear


def build():
    rnd = random.Random(2610)
    b = B(); INFOS.clear()
    T.ground(b, NX, NZ, rnd, deco=0.03)
    homes = ("kitchen", "bedroom", "dining", "study")
    # row 1: town houses, one per roof kind
    row1 = ((4, 4, 13, 13, 2, "east_blue", "L", "gable", ["dormer", "bay", "porch"]),
            (24, 4, 15, 13, 2, "stone", "T", "hip", ["balcony", "tower", "dormer"]),
            (49, 4, 13, 13, 3, "brick", "offset", "half_hip", ["bay", "balcony", "dormer"]),
            (70, 4, 17, 13, 2, "plaster", "U", "mansard", ["bay", "balcony"]),
            (94, 6, 11, 9, 1, "cottage", "plain", "saltbox", ["porch", "dormer", "bay"]),
            (112, 4, 11, 11, 2, "orange", "plain", "gambrel", ["porch", "balcony"]))
    for i, (x, z, w, d, fl, st, pl, rk, ad) in enumerate(row1):
        info = A.house2(b, x, z, w, d, fl, st, random.Random(100 + i), plan=pl, roof_kind=rk, addons=ad)
        furnish(b, info, homes, 500 + i * 31)
    # row 2: curved roofs and the desert
    info = A.house2(b, 4, 34, 15, 11, 1, "east_blue", random.Random(7), plan="plain", roof_kind="gable", curve="bell", addons=["dormer", "porch"])
    furnish(b, info, ("tavern", "kitchen"), 71)
    info = A.house2(b, 24, 34, 13, 11, 2, "snow", random.Random(8), plan="L", roof_kind="gable", curve="flare", addons=["bay", "balcony"])
    furnish(b, info, homes, 81)
    for i, (x, z, w, d, fl, pl, dome) in enumerate(((44, 32, 15, 13, 2, "L", True), (66, 32, 15, 13, 3, "offset", False),
                                                     (88, 34, 9, 9, 1, "plain", None), (102, 32, 13, 11, 2, "T", True))):
        info = A.desert_house(b, x, z, w, d, fl, random.Random(300 + i), plan=pl, dome=dome)
        furnish(b, info, ("kitchen", "bedroom", "storage"), 900 + i, theme="desert" if False else "pirate")
    # row 3: Wano and Water 7
    info = A.japanese_house(b, 4, 62, 13, 11, 2, random.Random(41), plan="plain")
    furnish(b, info, ("dining", "bedroom"), 41)
    info = A.japanese_house(b, 24, 62, 15, 13, 1, random.Random(42), plan="L")
    furnish(b, info, ("dining", "study"), 42)
    x = 46
    for i, (w, fl, c) in enumerate(((7, 4, "minecraft:pink_terracotta"), (7, 3, "minecraft:yellow_terracotta"),
                                    (5, 4, "minecraft:light_blue_terracotta"), (7, 3, "minecraft:white_terracotta"))):
        info = A.venetian_house(b, x, 64, w, 11, fl, random.Random(60 + i), color=c)
        furnish(b, info, ("kitchen", "bedroom", "study", "bedroom"), 60 + i)
        x += w + 1
    info = A.house2(b, 84, 62, 17, 13, 2, "stone", random.Random(9), plan="L", roof_kind="hip", addons=["tower", "bay", "porch"])
    furnish(b, info, ("library", "dining", "bedroom"), 91)
    info = A.house2(b, 108, 64, 11, 13, 2, "brick", random.Random(10), plan="plain", roof_kind="hip_low", addons=["porch", "bay"],
                    door="east")
    furnish(b, info, homes, 101)
    return b, 0

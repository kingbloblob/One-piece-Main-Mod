"""Demo of landkit on a 64 x 64 land site: a rolling relief with a flat plaza and street, a cottage on a terraced
pad, a shed on a foundation down the slope, groves of every tree kind with understory, palms on a sandy corner,
boulders, a winding path and a trail, lived-in clutter and lamp posts. Ground = y 0 at the edges and under the
plaza; everything else reads its height with landkit.ground_y."""
import math, random
from canvas import *
import townkit as T
import landkit as L

SID = "demo_landkit"
TITLE = "Landkit demo"
CUTS = []
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")
NX, NZ = 64, 64
PLAZA = (33, 40)


def in_plaza(x, z):
    """A rounded plaza with one side cut off straight (not a square), plus the street running east from it."""
    cx, cz = PLAZA
    if math.hypot((x - cx) / 7.5, (z - cz) / 6.0) <= 1 and z <= cz + 4: return True
    zs = cz + 1 + (x - cx) * 0.18  # the street bends a little south as it goes east
    return x >= cx and abs(z - zs) <= 4.5


def build():
    rnd = random.Random(26_10_25)
    b = B()
    T.ground(b, NX, NZ, rnd, deco=0)
    for x in range(44, NX):  # a sandy corner for the palms
        for z in range(48, NZ):
            if (x - 44) + (z - 48) + 4 * L.noise2(x, z, 3, 5) > 9:
                b.set(x, 0, z, "minecraft:sand"); [b.set(x, y, z, "minecraft:sandstone") for y in (-3, -2, -1)]
    L.relief(b, 0, 0, NX - 1, NZ - 1, seed=11, amp=7, cell=16, keep_flat=in_plaza)

    # cottage on a terrace cut into the east flank of the hill, a stair down its south face to the path
    x0, z0, x1, z1 = 19, 8, 31, 20
    pad_y = round(sum(L.ground_y(b, x, z) for x in range(x0, x1 + 1) for z in range(z0, z1 + 1)) / ((x1 - x0 + 1) * (z1 - z0 + 1)))
    pad, foot = L.terrace(b, x0, z0, x1, z1, pad_y, "minecraft:cobblestone", rnd, stair="south")
    T.house(b, 21, 10, 7, 7, floors=2, style="cottage", rnd=rnd, y=pad_y, door="south")
    L.clutter(b, 22, 8, "north", "crates", rnd)
    L.clutter(b, 19, 12, "west", "woodpile", rnd)
    L.clutter(b, 21, 18, "south", "bench", rnd)
    L.clutter(b, 26, 18, "south", "pots", rnd)
    L.clutter(b, 29, 11, "west", "washing_line", rnd)

    # a shed down a slope east of the plaza: level floor, the foundation goes down to the ground on the low side
    def spot():
        best = None
        for sx in range(40, 56):
            for sz in range(14, 34):
                ys = [L.ground_y(b, x, z) for x in range(sx, sx + 4) for z in range(sz, sz + 5)]
                d = max(ys) - min(ys)
                if d <= 3 and (best is None or d > best[0]): best = (d, sx, sz, max(ys))
        return best[1:]
    sx, sz, sy = spot()
    sy += 1
    L.foundation(b, sx, sz, sx + 3, sz + 4, sy, "minecraft:cobblestone")
    b.box(sx, sy, sz, sx + 3, sy, sz + 4, "minecraft:spruce_planks")
    for yy in range(sy + 1, sy + 4):
        for x in range(sx, sx + 4):
            for z in range(sz, sz + 5):
                if x in (sx, sx + 3) or z in (sz, sz + 4):
                    b.set(x, yy, z, log("spruce") if x in (sx, sx + 3) and z in (sz, sz + 4) else "minecraft:spruce_planks")
                else: b.set(x, yy, z, AIR)
    b.set(sx + 1, sy + 1, sz + 4, door("minecraft:spruce_door", "south", "lower"))
    b.set(sx + 1, sy + 2, sz + 4, door("minecraft:spruce_door", "south", "upper"))
    b.set(sx + 3, sy + 2, sz + 2, pane_of("minecraft:glass_pane"))
    b.gable_roof(sx, sz, sx + 3, sz + 4, sy + 4, "minecraft:dark_oak_stairs", "minecraft:dark_oak_planks", gable_wall="minecraft:spruce_planks")
    shed = {(x, z) for x in range(sx - 1, sx + 5) for z in range(sz - 1, sz + 7)}

    # plaza and street (flat, paved with the stone mix), the well, a cart and a trough, lamps along the street
    paths = {}
    cx, cz = PLAZA
    sq = {(x, z) for x in range(cx - 8, cx + 9) for z in range(cz - 7, cz + 6)
          if math.hypot((x - cx) / 6.8, (z - cz) / 5.3) <= 1 and z <= cz + 3}
    paths.update(L.pave(b, sq, rnd))
    paths.update(L.organic_path(b, [(38, 41), (48, 43), (56, 44), (63, 46)], 4, rnd, street=True))
    T.well(b, PLAZA[0], PLAZA[1] - 1, y=L.ground_y(b, *PLAZA))
    L.clutter(b, 28, 44, "north", "cart", rnd)
    L.clutter(b, 38, 36, "south", "trough", rnd)
    for (x, z) in ((44, 39), (53, 47), (61, 42)):
        L.lamp_post(b, x, z, rnd, "street")

    # a path from the terrace stair down to the plaza, a shed lane, and a trail up into the spruces
    fx, fz = foot or (25, 22)
    paths.update(L.organic_path(b, [(fx, fz), (fx + 1, fz + 6), (27, 31), (29, 36)], 3, rnd))
    paths.update(L.organic_path(b, [(sx + 1, sz + 6), (sx - 1, sz + 12), (42, 40)], 2, rnd))
    paths.update(L.organic_path(b, [(40, 36), (42, 28), (44, 20), (50, 12), (56, 3)], 2, rnd))
    L.lamp_post(b, fx + 3, fz + 5, rnd, "hanging"); L.lamp_post(b, 45, 24, rnd, "wood"); L.lamp_post(b, 25, 33, rnd, "stone")
    taken = set(paths) | pad | shed

    def avoid(x, z):
        return (x, z) in taken or in_plaza(x, z)

    # groves: one dominant tree each, mixed where it makes sense
    L.grove(b, (0, 24, 22, 46), ("oak", "birch", "oak"), rnd, avoid=avoid)
    L.grove(b, (46, 0, 63, 20), ("spruce",), rnd, n=5, avoid=avoid)
    L.grove(b, (2, 48, 24, 63), ("cherry", "azalea", "cherry"), rnd, n=4, avoid=avoid)
    L.grove(b, (1, 2, 16, 21), ("dark_oak", "oak"), rnd, n=3, avoid=avoid)
    L.grove(b, [(36, 7), (58, 33)], ("jungle", "mangrove"), rnd, under=False, avoid=avoid)
    L.grove(b, (28, 48, 44, 63), ("acacia", "acacia"), rnd, n=3, avoid=avoid)
    L.grove(b, [(51, 57), (59, 52), (58, 61)], ("palm",), rnd, avoid=avoid)
    L.clutter(b, 37, 56, "north", "camp", rnd)
    L.clutter(b, 47, 51, "south", "fishing", rnd)
    for (x, z, r) in ((22, 46, 2.0), (34, 22, 1.6), (12, 30, 1.4), (60, 26, 2.2), (28, 58, 1.2)):
        if not avoid(x, z): L.boulder(b, x, z, r, rnd)
    L.meadow(b, 0, 0, NX - 1, NZ - 1, rnd, density=0.05, avoid=avoid)
    return b, 0

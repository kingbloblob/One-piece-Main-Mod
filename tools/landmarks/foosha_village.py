"""Foosha Village (Windmill Village): Luffy's home village in the Goa Kingdom. Tall windmills with big lattice sails on
the green knolls behind the village, Makino's Partys Bar with the PARTYS BAR board over its front and its long counter,
Mayor Woop Slap's house, a dozen furnished cottages, wheat fields, the well on the little square, and the harbour where
Shanks' ship once moored, with Luffy's little one-sail boat at the pier. ~84 x 80. Ground = y 0, the sea is to the south."""
import math, random
from canvas import *
import interiors as I
import townkit as T

SID = "foosha_village"
TITLE = "Foosha Village"
CUTS = [3]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")

NX, NZ = 84, 80
SEA = 62
# (x, z, size): the windmills the village is named after. Set far enough in from the north and east edges that the
# knolls and the sails stay inside the 84 x 80 tile (the third mill's sails reach cx + 9).
MILLS = ((14, 8, 1.0), (54, 8, 1.0), (73, 6, 0.75))


def knoll(x, z):
    """Height of the grassy knolls the windmills stand on. They ease down to the ground level over the last six
    blocks before the north edge, so the tile meets the world there without a dirt step."""
    h = 0
    fade = min(1.0, max(0.0, z / 6.0))
    for (mx, mz, k) in MILLS:
        d = math.hypot(x - mx, z - mz) / (9 * k)
        if d < 1: h = max(h, int(round(3 * k * (1 - d * d) * fade)))
    return h


def windmill(b, cx, cz, k=1.0):
    """A tower mill: a round whitewashed tower with timber bands on a stone footing, a dark timber cap, and four big
    lattice sails clothed in white canvas on the south face."""
    y0 = knoll(cx, cz)
    H = int(round(17 * k))
    r0, r1 = 4.2 * k, 3.0 * k
    for y in range(-1, y0 + H + 1):
        t = max(0.0, (y - y0) / H)
        r = r0 + (r1 - r0) * t
        if y <= y0 + 1: s = "minecraft:cobblestone" if y <= y0 else "minecraft:stone_bricks"
        elif (y - y0) % 6 == 0: s = "minecraft:stripped_spruce_log[axis=y]"  # timber band
        else: s = "minecraft:calcite" if (y * 7) % 3 else "minecraft:white_concrete_powder"
        b.cyl(cx, cz, r, y, y, s, hollow=y > y0)
    b.cyl(cx, cz, r0 - 0.8, y0, y0, "minecraft:spruce_planks")
    # small windows up the tower with a stair sill under each
    for yy in range(y0 + 5, y0 + H - 2, 5):
        rr = int(round(r0 + (r1 - r0) * (yy - y0) / H))
        for (dx, dz, f) in ((1, 0, "west"), (-1, 0, "east"), (0, -1, "south")):
            b.set(cx + dx * rr, yy, cz + dz * rr, pane_of("minecraft:glass_pane"))
            b.set(cx + dx * (rr + 1), yy - 1, cz + dz * (rr + 1), stairs("minecraft:spruce_stairs", f, "top"))
    # door on the south side
    rs = int(round(r0))
    b.set(cx, y0 + 1, cz + rs, door("minecraft:spruce_door", "south", "lower"))
    b.set(cx, y0 + 2, cz + rs, door("minecraft:spruce_door", "south", "upper"))
    b.set(cx, y0 + 3, cz + rs, "minecraft:stripped_spruce_log[axis=x]")
    b.set(cx, y0 + 4, cz + rs + 1, slab("minecraft:spruce_slab", "top")) if b.get(cx, y0 + 4, cz + rs + 1) in (None, AIR) else None
    # the cap: a dark timber cone with a little overhang and a finial
    top = y0 + H + 1
    rc = r1 + 1.2
    for i in range(int(rc) + 2):
        rr = rc - i
        if rr < 0.6:
            b.set(cx, top + i, cz, "minecraft:dark_oak_planks"); b.set(cx, top + i + 1, cz, fence("dark_oak")); break
        b.cyl(cx, cz, rr, top + i, top + i, "minecraft:dark_oak_planks" if i % 2 else "minecraft:spruce_planks")
    # windshaft out of the cap and the sails in the plane in front of the tower
    hy = top - 1
    zs = cz + int(round(r1)) + 2
    for z in range(cz, zs + 1): b.set(cx, hy, z, "minecraft:stripped_spruce_log[axis=z]")
    b.set(cx, hy, zs, "minecraft:spruce_log[axis=z]")
    R = int(round(12 * k))
    for (ux, uy) in ((1, 0), (0, 1), (-1, 0), (0, -1)):  # four arms in a cross, each with its canvas on the trailing side
        px, py = -uy, ux
        for a in range(1, R + 1):
            b.set(cx + ux * a, hy + uy * a, zs, f"minecraft:stripped_spruce_log[axis={'x' if ux else 'y'}]")  # the stock
            if a < 3: continue
            for p in (1, 2, 3):
                frame = p == 3 or a == R or (a - 3) % 4 == 0
                b.set(cx + ux * a + px * p, hy + uy * a + py * p, zs, "minecraft:spruce_planks" if frame else "minecraft:white_wool")
    n = max(1, int(r0) - 2)
    I.furnish(b, cx - n, y0 + 1, cz - n, cx + n, cz + n, 3, "storage", "pirate", seed=cx + cz)


def partys_bar(b, x0, z0, w, d, rnd):
    """Makino's Partys Bar: a two-storey timber house with a big board over the front reading PARTYS BAR."""
    T.house(b, x0, z0, w, d, 2, "east_blue", rnd, kinds=["tavern", "bedroom"], sign="minecraft:red_wool", chimney=True)
    # the long counter with stools in front and barrels and bottles behind it
    for x in range(x0 + 3, x0 + w - 3):
        b.set(x, 1, z0 + 3, "minecraft:spruce_planks")
        b.set(x, 2, z0 + 3, slab("minecraft:spruce_slab", "bottom") if x % 3 else AIR)
        b.set(x, 1, z0 + 4, stairs("minecraft:spruce_stairs", "south") if x % 2 == 0 else AIR)
        b.set(x, 2, z0 + 4, AIR)
    for x in range(x0 + 3, x0 + w - 3, 2):
        b.set(x, 1, z0 + 1, BARREL)
        if x % 4 == 0: b.set(x, 2, z0 + 1, "minecraft:brewing_stand[has_bottle_0=true,has_bottle_1=false,has_bottle_2=false]")
    # the name board: the whole south face of the jettied upper floor is a framed false front that rises to the roof
    # ridge, set in the plane of the upper wall (the upper room takes its light from the east, west and north walls),
    # with PARTYS BAR painted on it in big letters that read from the harbour (south)
    zf = z0 + d                           # the upper wall plane (the upper floor is jettied out by 1)
    bx0, bx1, by0, by1 = x0 - 1, x0 + w, 4, 14  # the jettied floor's full width, from the jetty beam up to the ridge
    for x in range(bx0 - 1, bx1 + 2):     # clear what the house put in front: eave, eave brackets, flower boxes, shutters
        for y in range(by0, by1 + 1): b.set(x, y, zf + 1, AIR)
    for x in range(bx0, bx1 + 1):
        for y in range(by0, by1 + 1):
            if y in (by0, by1): s = "minecraft:stripped_spruce_log[axis=x]"
            elif x in (bx0, bx1): s = "minecraft:stripped_spruce_log[axis=y]"
            else: s = "minecraft:dark_oak_planks"
            b.set(x, y, zf, s)
    b.text(bx0 + 1, 9, zf, "PARTYS", "minecraft:white_concrete", axis="x", step=1)
    b.text(bx0 + 7, 4, zf, "BAR", "minecraft:yellow_concrete", axis="x", step=1)
    for x in (bx0, bx1):  # brackets under the board ends
        b.set(x, by0 - 1, zf, stairs("minecraft:spruce_stairs", "north", "top"))
    # behind the board: plank panelling on the inside of the upper room (so the room never sees the letters from
    # behind), and framed boards on the back of the false front where it stands above the roof slope
    for x in range(bx0 + 1, bx1):
        post = (x - bx0) % 4 == 0
        for y in range(5, by1 + 1):
            if y <= 9 or b.get(x, y, zf - 1) in (None, AIR):
                b.set(x, y, zf - 1, "minecraft:stripped_spruce_log[axis=y]" if post else "minecraft:spruce_planks")
    # the upper room's light: a third window in each side wall, in the bay by the board (sill box, shutters)
    wz = z0 + d - 2
    for (wx, ox, f) in ((bx0, -1, "west"), (bx1, 1, "east")):
        for y in (6, 7): b.set(wx, y, wz, "minecraft:glass_pane")
        b.set(wx + ox, 5, wz, f"onepiece:flower_box[facing={f}]")
        for y in (6, 7):
            for s in (-1, 1): b.set(wx + ox, y, wz + s, trapdoor("minecraft:spruce_trapdoor", f, "bottom", "true"))


def build():
    rnd = random.Random(201)
    b = B()
    T.ground(b, NX, NZ, rnd)
    # the green knolls under the windmills
    for x in range(NX):
        for z in range(NZ):
            h = knoll(x, z)
            if h > 0:
                b.set(x, 0, z, "minecraft:dirt"); b.set(x, 1, z, AIR)
                for y in range(1, h + 1): b.set(x, y, z, "minecraft:grass_block" if y == h else "minecraft:dirt")
                if rnd.random() < 0.08: b.set(x, h + 1, z, "minecraft:short_grass")
    T.sea(b, NX, NZ, lambda x, z: z > SEA + 3 * math.sin(x * 0.11))
    for x in range(NX):  # sandy strip along the shore
        for z in range(SEA - 6, SEA + 6):
            if b.get(x, 0, z) == "minecraft:grass_block" and z > SEA - 4 + 3 * math.sin(x * 0.11):
                b.set(x, 0, z, "minecraft:sand")
                if b.get(x, 1, z) and "fence" not in b.get(x, 1, z): b.set(x, 1, z, AIR)
    # main street (east-west) and the lane to the harbour
    T.path(b, [(4, 36), (80, 36)], w=1, alt="minecraft:coarse_dirt")
    T.path(b, [(42, 36), (42, SEA)], w=1, alt="minecraft:coarse_dirt")
    # the square with the well
    for x in range(36, 49):
        for z in range(30, 43): b.set(x, 0, z, "minecraft:cobblestone" if (x + z) % 3 else "minecraft:mossy_cobblestone")
    T.well(b, 42, 36)
    for (x, z) in ((36, 30), (48, 30), (36, 42), (48, 42)): T.lamp_post(b, x, z)
    # Partys Bar (Makino), facing the harbour, with its big name board
    bx0, bz0, bw, bd = 49, 40, 24, 10
    partys_bar(b, bx0, bz0, bw, bd, rnd)
    # mayor's house (bigger, stone base)
    T.house(b, 20, 40, 12, 10, 2, "stone", rnd, kinds=["study", "bedroom"])
    # cottages along the street
    spots = [(6, 22), (18, 22), (30, 20), (52, 22), (64, 22), (74, 24), (6, 42), (8, 52), (77, 54), (30, 50)]
    for i, (x0, z0) in enumerate(spots):
        w, d = rnd.randint(7, 9), rnd.randint(6, 8)
        w = min(w, NX - 1 - x0)
        T.house(b, x0, z0, w, d, rnd.choice((1, 1, 2)), rnd.choice(("east_blue", "cottage", "east_blue")), rnd,
                door="south" if z0 < 36 else "north")
    # windmills on the knolls and the fields below them
    for (x, z, k) in MILLS: windmill(b, x, z, k)
    T.garden(b, 26, 4, 44, 14, crop="minecraft:wheat[age=7]")
    T.garden(b, 66, 12, 80, 18, crop="minecraft:carrots[age=7]")
    for (x, z) in ((4, 16), (34, 18), (78, 34), (2, 30), (46, 56), (28, 58)): T.tree(b, x, z, h=rnd.randint(4, 6))
    # the harbour: pier, fishing boats, crates, the ship's mooring posts
    T.pier(b, 40, SEA - 2, 16)
    T.pier(b, 20, SEA, 10, boat=True)
    for (x, z) in ((44, SEA - 3), (46, SEA - 3), (38, SEA - 3)): b.set(x, 1, z, "minecraft:barrel[facing=up,open=false]")
    # Luffy's little boat: the dinghy by the long pier gets a single mast and a white square sail
    mx, mz = 45, SEA - 2 + 16 - 4
    for y in range(1, 8): b.set(mx, y, mz, fence("spruce"))
    for x in range(mx - 2, mx + 3): b.set(x, 7, mz - 1, fence("spruce"))
    for x in range(mx - 2, mx + 3):
        for y in range(3, 7): b.set(x, y, mz - 1, "minecraft:white_wool")
    b.set(mx - 1, 1, mz + 1, BARREL)
    b.npc(46, 1, 38, "luffy", False)
    b.chest(bx0 + bw - 2, 1, bz0 + bd - 3, "easy", "west")
    return b, 0

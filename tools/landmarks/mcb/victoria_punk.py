"""Victoria Punk v2, redesigned with the Minecraft Builder skill: Eustass Kid's ship at anchor in a rocky cove, and
the Kid Pirates' scrap-metal harbour camp around it (Kid's heavy-metal style: iron, rust, spikes, red and black).

Silhouette first: the real Victoria Punk (the ship template, dinosaur-skull figurehead, red sails) floats in the
middle of a horseshoe cove between two dark rock arms; behind it a skyline of scrap: the forge hall with three smoking
stacks and a giant metal left arm (Kid's Punk Gibson) raised out of its roof, Kid's scrap keep flying his flaming-skull
flag, and Killer's lookout on the east crag.

On land: a pier of iron plates and chains to the ship, the forge hall (anvils, blast furnaces, the arm being built),
Kid's keep (crew bunks, Heat's and Wire's rooms, the mess, Kid's cabin on top), the bonfire pit with tents and log
benches where the crew drinks, heaps of scrap everywhere (iron, copper in every state of rust, chains, anvils,
cannons), a spiked scrap palisade with a gate on the land side. 168 x 136, y 0 = sea surface. (v2)"""
import math

import numpy as np

from mcb.kit import BigBuild, P, AIR, seed_of, st, set_if_air, tier, cornice, lamp_post, steady
from mcb.kit_interiors import furnish_kit, bench, wall_lights
from mcb.bridge import to_canvas
from mcb import nature as NT
from mcb.shipstamp import stamp_ship

SID = "victoria_punk"
TITLE = "Victoria Punk (Kid's ship)"
CUTS = [3, 10, 20]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")
EDGE_REACH = 6

NX, NZ = 168, 136
GY = 2
SHIP = (86, 104)                       # hull centre (bow east)
def _LAND(X, Z):
    """Wide oval of land (x 12..156, z 8..96) with a wobbly shore: blocks inside the shore."""
    e = np.sqrt(((X - 84) / 72.0) ** 2 + ((Z - 52) / 44.0) ** 2)
    return (1 - e) * 44 + (NT.noise(X, Z, 9108, 13) - 0.5) * 8
_COVE = NT.outline(86, 108, 34, 9102, wobble=0.08)
SCRAP = ["minecraft:iron_block", "minecraft:exposed_copper", "minecraft:weathered_copper", "minecraft:oxidized_copper",
         "minecraft:copper_block", "minecraft:waxed_weathered_cut_copper", "minecraft:anvil", "minecraft:chipped_anvil",
         "minecraft:damaged_anvil", "minecraft:blackstone", "minecraft:polished_blackstone_bricks", "minecraft:cracked_polished_blackstone_bricks",
         "minecraft:iron_trapdoor[facing=north,half=bottom,open=false]", "minecraft:heavy_core", "minecraft:hopper", "minecraft:cauldron"]
SCRAP_W = [0.17, 0.09, 0.09, 0.07, 0.05, 0.05, 0.04, 0.03, 0.03, 0.12, 0.08, 0.06, 0.04, 0.01, 0.04, 0.03]
WALLS = ["minecraft:weathered_copper", "minecraft:exposed_copper", "minecraft:oxidized_copper", "minecraft:iron_block",
         "minecraft:polished_blackstone_bricks"]
WALL_W = [0.3, 0.2, 0.15, 0.15, 0.2]
GROUND = [("minecraft:coarse_dirt", 0.3), ("minecraft:gravel", 0.0), ("minecraft:blackstone", 0.12), ("minecraft:tuff", 0.12),
          ("minecraft:rooted_dirt", 0.08), ("minecraft:grass_block", 0.2), ("minecraft:podzol", 0.12), ("minecraft:packed_mud", 0.06)]
ROCK = [("minecraft:blackstone", 0.25), ("minecraft:basalt[axis=y]", 0.2), ("minecraft:tuff", 0.2), ("minecraft:deepslate", 0.2),
        ("minecraft:stone", 0.15)]


def _height(X, Z):
    X = np.asarray(X, float); Z = np.asarray(Z, float)
    d = np.minimum(_LAND(X, Z), -_COVE(X, Z) + 2)                  # land, minus the cove bitten out of the south
    base = GY + NT.fbm(X, Z, 9103, 18) * 2
    arms = np.clip((np.abs(X - 86) - 30) / 14.0, 0, 1) * np.clip((Z - 60) / 20.0, 0, 1) * (16 + 10 * NT.fbm(X, Z, 9104, 9))
    back = np.clip((30 - Z) / 14.0, 0, 1) * np.clip(_LAND(X, Z) / 10.0, 0, 1) * 7
    h = base + arms + back
    h = np.where(d < 8, -6 + (h + 6) * np.clip(d / 8.0, 0, 1) ** 1.3, h)
    return np.round(h)


X_, Z_ = np.arange(NX)[:, None].astype(float), np.arange(NZ)[None, :].astype(float)
HMAP = _height(X_, Z_).astype(int)


def _ix(X, Z):
    return np.clip(np.asarray(X).astype(int), 0, NX - 1), np.clip(np.asarray(Z).astype(int), 0, NZ - 1)


def height(X, Z):
    return HMAP[_ix(X, Z)]


def land(X, Z):
    return HMAP[_ix(X, Z)] >= 1


def hy(x, z):
    return int(HMAP[min(max(int(x), 0), NX - 1), min(max(int(z), 0), NZ - 1)])


def terrain(bb):
    steep = lambda X, Z: height(X, Z) > GY + 4
    NT.cover(bb, 0, 0, NX - 1, NZ - 1, height, GROUND, 9105, mask=lambda X, Z: land(X, Z) & ~steep(X, Z), core="minecraft:stone", base=-8)
    NT.cover(bb, 0, 0, NX - 1, NZ - 1, height, ROCK, 9106, mask=lambda X, Z: land(X, Z) & steep(X, Z), under="minecraft:blackstone",
             core="minecraft:deepslate", base=-8)
    wet = lambda X, Z: ~land(X, Z)
    bed = lambda X, Z: np.minimum(height(X, Z), -2) - 3 * (_COVE(X, Z) > 6)
    bb.fill_where(0, -12, 0, NX - 1, 0, NZ - 1, lambda X, y, Z: wet(X, Z) & (y > bed(X, Z)), "minecraft:water")
    bb.fill_where(0, -12, 0, NX - 1, 0, NZ - 1, lambda X, y, Z: wet(X, Z) & (y == bed(X, Z)), "minecraft:gravel")
    bb.fill_where(0, -12, 0, NX - 1, 0, NZ - 1, lambda X, y, Z: wet(X, Z) & (y < bed(X, Z)) & (y >= bed(X, Z) - 3), "minecraft:blackstone")
    NT.plants(bb, 0, 0, NX - 1, NZ - 1, height, 9107, density=0.12, kinds=["minecraft:short_grass", "minecraft:fern", "minecraft:dead_bush"],
              mask=lambda X, Z: land(X, Z) & ~steep(X, Z), ground=("grass_block", "podzol", "coarse_dirt", "rooted_dirt"))


def heap(bb, x, z, r, h, rng):
    """A scrap heap: a lumpy mound of mixed metal junk with things sticking out."""
    y0 = hy(x, z)
    for dx in range(-r, r + 1):
        for dz in range(-r, r + 1):
            d = math.hypot(dx, dz) / r
            if d > 1:
                continue
            top = y0 + int(round(h * (1 - d ** 1.6) * (0.75 + 0.5 * rng.random())))
            for y in range(hy(x + dx, z + dz) + 1, top + 1):
                bb.set(x + dx, y, z + dz, str(rng.choice(SCRAP, p=SCRAP_W)))
    for _ in range(r):
        a = rng.random() * 6.28
        px, pz = x + int(round(math.cos(a) * r * 0.5)), z + int(round(math.sin(a) * r * 0.5))
        top = y0 + h
        bb.fill(px, top - 2, pz, px, top + int(rng.integers(1, 4)), pz, "minecraft:iron_bars" if rng.random() < 0.5 else "minecraft:iron_chain[axis=y]")


def palisade(bb, rng):
    """A spiked scrap wall on the land side: iron and copper panels on posts, spikes on top, a gate north."""
    pts = [(22, 66), (24, 28), (46, 16), (122, 16), (144, 28), (146, 66)]
    gate = 84
    for (x0, z0), (x1, z1) in zip(pts, pts[1:]):
        n = max(abs(x1 - x0), abs(z1 - z0))
        for i in range(n + 1):
            x = round(x0 + (x1 - x0) * i / n); z = round(z0 + (z1 - z0) * i / n)
            if abs(x - gate) <= 3 and z < 20:
                continue
            y = hy(x, z)
            post = i % 5 == 0
            bb.fill(x, y + 1, z, x, y + (8 if post else 6), z, "minecraft:polished_blackstone_bricks" if post else str(rng.choice(WALLS, p=WALL_W)))
            bb.set(x, y + (9 if post else 7), z, "minecraft:pointed_dripstone[vertical_direction=up,thickness=tip]" if False else
                   ("minecraft:iron_bars" if not post else "minecraft:lightning_rod"))
    # gate towers and a hanging skull sign
    for gx in (gate - 5, gate + 4):
        y = hy(gx, 16)
        bb.fill(gx, y - 2, 14, gx + 1, y + 12, 17, "minecraft:polished_blackstone_bricks")
        bb.fill(gx, y + 13, 14, gx + 1, y + 13, 17, "minecraft:iron_bars")
        bb.set(gx, y + 10, 13, "minecraft:lantern[hanging=false]") if False else bb.set(gx, y + 11, 18, "minecraft:soul_lantern[hanging=false]")
    y = hy(gate, 16)
    bb.fill(gate - 3, y + 10, 16, gate + 3, y + 11, 16, "minecraft:iron_block")
    bb.fill(gate - 1, y + 7, 16, gate + 1, y + 9, 16, "minecraft:bone_block[axis=y]")
    bb.set(gate - 1, y + 8, 16, "minecraft:black_concrete"); bb.set(gate + 1, y + 8, 16, "minecraft:black_concrete")


def forge(bb):
    """The forge hall: a long scrap-walled shed with three stacks; Kid's giant metal arm rises from its roof."""
    x1, z1, x2, z2 = 24, 30, 64, 58
    y = max(hy(x, z) for x in range(x1, x2 + 1, 4) for z in range(z1, z2 + 1, 4))
    bb.fill(x1, y - 6, z1, x2, y, z2, "minecraft:blackstone")
    bb.fill(x1 + 1, y, z1 + 1, x2 - 1, y, z2 - 1, "minecraft:polished_blackstone")
    bb.mix(x1, y + 1, z1, x2, y + 11, z2, WALLS, WALL_W)
    bb.fill(x1 + 1, y + 1, z1 + 1, x2 - 1, y + 11, z2 - 1, AIR)
    for x in range(x1, x2 + 1, 5):
        bb.fill(x, y + 1, z1 - 1, x, y + 11, z1 - 1, "minecraft:polished_blackstone_bricks")
        bb.fill(x, y + 1, z2 + 1, x, y + 11, z2 + 1, "minecraft:polished_blackstone_bricks")
        if x + 3 <= x2:
            bb.fill(x + 2, y + 6, z1, x + 3, y + 8, z1, "minecraft:iron_bars"); bb.fill(x + 2, y + 6, z2, x + 3, y + 8, z2, "minecraft:iron_bars")
    # saw-tooth roof of iron plates
    for z in range(z1 - 1, z2 + 2):
        k = (z - z1) % 7
        for x in range(x1 - 1, x2 + 2):
            bb.set(x, y + 12 + min(k, 4), z, "minecraft:iron_block" if k < 5 else AIR)
            if k == 4:
                bb.fill(x, y + 12, z, x, y + 15, z, "minecraft:glass")
    for (sx, sz) in ((x1 + 6, z1 + 4), (x1 + 20, z1 + 4), (x1 + 34, z1 + 4)):
        bb.cylinder(sx, y + 1, sz, 2, y + 28, "minecraft:bricks", hollow=True)
        bb.ring(sx, y + 22, sz, 1, 3, y + 22, "minecraft:iron_block")
        bb.set(sx, y + 28, sz, "minecraft:campfire[lit=true,signal_fire=true]")
    # inside: the forge line along the north wall, anvil rows, the arm on its cradle in the middle
    for x in range(x1 + 2, x2 - 1, 3):
        bb.set(x, y + 1, z1 + 2, "minecraft:blast_furnace[facing=south,lit=true]")
        bb.set(x + 1, y + 1, z1 + 2, "minecraft:anvil[facing=east]")
        bb.set(x, y + 1, z2 - 2, ["minecraft:smithing_table", "minecraft:grindstone[face=floor,facing=north]", "minecraft:barrel[facing=up]"][x % 3])
        bb.set(x, y + 5, z1 + 1, "minecraft:lantern[hanging=false]") if False else bb.set(x, y + 5, z1 + 1, "minecraft:wall_torch[facing=south]")
        bb.set(x, y + 5, z2 - 1, "minecraft:wall_torch[facing=north]")
    bb.fill(x1 + 10, y + 1, z1 + 10, x2 - 10, y + 1, z1 + 14, "minecraft:magma_block")
    bb.fill(x1 + 10, y + 1, z1 + 10, x2 - 10, y + 1, z1 + 10, "minecraft:iron_bars")
    bb.fill(x1 + 10, y + 1, z1 + 14, x2 - 10, y + 1, z1 + 14, "minecraft:iron_bars")
    for x in range(x1 + 6, x2 - 5, 8):
        bb.set(x, y + 10, (z1 + z2) // 2, "minecraft:lantern[hanging=true]")
        bb.fill(x, y + 11, (z1 + z2) // 2, x, y + 11, (z1 + z2) // 2, "minecraft:iron_chain[axis=y]")
    bb.fill(x2, y + 1, (z1 + z2) // 2 - 3, x2, y + 6, (z1 + z2) // 2 + 3, AIR)        # big doors east
    bb.fill((x1 + x2) // 2 - 2, y + 1, z2, (x1 + x2) // 2 + 2, y + 5, z2, AIR)         # and south
    # Kid's giant left arm: an iron forearm out of the roof, fist clenched, red-banded with copper plates
    ax, az = x1 + 28, z1 + 18
    for yy in range(y + 10, y + 34):
        t = (yy - y - 10) / 24.0
        r = 3.6 - 0.8 * t
        cx = ax + int(round(4 * t))
        for dx in range(-4, 5):
            for dz in range(-4, 5):
                if dx * dx + dz * dz <= r * r:
                    band = (yy - y) % 6 == 0
                    blk = "minecraft:red_concrete" if band else ("minecraft:iron_block" if (dx + dz + yy) % 3 else "minecraft:exposed_copper")
                    bb.set(cx + dx, yy, az + dz, blk)
    fx = ax + 4
    for dx in range(-5, 6):
        for dy in range(0, 9):
            for dz in range(-4, 5):
                if (dx / 5.2) ** 2 + ((dy - 4) / 4.6) ** 2 + (dz / 4.3) ** 2 <= 1:
                    bb.set(fx + dx, y + 34 + dy, az + dz, "minecraft:iron_block" if (dx + dy) % 4 else "minecraft:weathered_copper")
    for k in range(4):            # knuckles
        bb.fill(fx + 5, y + 36 + k * 2, az - 3 + k * 2, fx + 6, y + 37 + k * 2, az - 2 + k * 2, "minecraft:polished_blackstone_bricks")
    return y


def keep(bb):
    """Kid's keep: a three-storey scrap tower with crew rooms, the mess, and Kid's cabin under a spiked crown."""
    x1, z1, x2, z2 = 104, 30, 128, 52
    y = max(hy(x, z) for x in range(x1, x2 + 1, 3) for z in range(z1, z2 + 1, 3))
    bb.fill(x1, y - 8, z1, x2, y, z2, "minecraft:blackstone")
    top = tier(bb, x1, z1, x2, z2, y, 3, 6, WALLS, "minecraft:iron_bars", "minecraft:polished_blackstone_brick_stairs",
               pilaster="minecraft:polished_blackstone_bricks", band="minecraft:red_concrete", plate="minecraft:dark_oak_planks",
               top_plate="minecraft:polished_blackstone", weights=WALL_W, every=3, pil_every=4)
    kinds = (["mess", "kitchen"], ["barracks", "barracks"], ["captain", "armory"])
    for f, (ka, kb) in enumerate(kinds):
        fy = y + 1 + 6 * f
        mid = (x1 + x2) // 2
        bb.fill(mid, fy, z1 + 1, mid, fy + 4, z2 - 1, "minecraft:polished_blackstone_bricks")
        bb.fill(mid, fy, (z1 + z2) // 2, mid, fy + 1, (z1 + z2) // 2, AIR)
        furnish_kit(bb, (x1 + 1, z1 + 4, mid - 1, z2 - 1), fy, 5, ka, wood="dark_oak", seed=9110 + f, doors=[(mid, (z1 + z2) // 2)], accent="red")
        furnish_kit(bb, (mid + 1, z1 + 1, x2 - 1, z2 - 1), fy, 5, kb, wood="dark_oak", seed=9120 + f, doors=[(mid, (z1 + z2) // 2)], accent="red")
        bb.fill(x1 + 1, fy - 1, z1 + 1, x1 + 2, fy + 4, z1 + 2, AIR)
        bb.fill(x1 + 1, fy - 1, z1 + 1, x1 + 1, fy + 5, z1 + 1, "minecraft:ladder[facing=east]")
    bb.fill(x1 + 8, y + 1, z2, x1 + 10, y + 4, z2, AIR)
    cornice(bb, x1, z1, x2, z2, top, "minecraft:polished_blackstone_brick_stairs", merlons="minecraft:polished_blackstone_brick_wall")
    for x in range(x1, x2 + 1, 3):            # spikes round the crown
        for z in (z1, z2):
            bb.fill(x, top + 2, z, x, top + 3, z, "minecraft:iron_bars"); bb.set(x, top + 4, z, "minecraft:lightning_rod")
    # Kid's flag: black with a red flaming skull, on a tall iron mast
    mx, mz = x2 - 3, z1 + 3
    bb.fill(mx, top + 1, mz, mx, top + 22, mz, "minecraft:iron_bars")
    for u in range(11):
        for v in range(8):
            skull = (u - 5) ** 2 / 9.0 + (v - 4) ** 2 / 6.0 <= 1
            flame = v >= 5 and (u + v) % 3 == 0 and 2 <= u <= 8
            eye = (u in (4, 6) and v == 4)
            blk = "minecraft:black_wool" if eye else ("minecraft:white_wool" if skull else ("minecraft:red_wool" if flame else "minecraft:black_wool"))
            bb.set(mx - 1 - u, top + 21 - v, mz, blk)
    return top


def killer_lookout(bb):
    """Killer's lookout on the east crag: a thin scrap tower with a crow's nest and a searchlight."""
    x, z = 140, 66
    y = hy(x, z)
    bb.fill(x - 2, y - 6, z - 2, x + 2, y + 18, z + 2, "minecraft:polished_blackstone_bricks")
    bb.fill(x - 1, y + 1, z - 1, x + 1, y + 18, z + 1, AIR)
    bb.fill(x, y + 1, z - 1, x, y + 19, z - 1, "minecraft:ladder[facing=south]")
    bb.fill(x - 4, y + 19, z - 4, x + 4, y + 19, z + 4, "minecraft:iron_block")
    for (a, b) in ((x - 4, z - 4), (x + 4, z - 4), (x - 4, z + 4), (x + 4, z + 4)):
        bb.fill(a, y + 20, b, a, y + 23, b, "minecraft:iron_bars")
    for k in range(-4, 5):
        for (a, b) in ((x + k, z - 4), (x + k, z + 4), (x - 4, z + k), (x + 4, z + k)):
            bb.set(a, y + 20, b, "minecraft:iron_bars")
    bb.fill(x - 4, y + 24, z - 4, x + 4, y + 24, z + 4, "minecraft:polished_blackstone_slab[type=bottom]")
    bb.set(x, y + 20, z, AIR); bb.set(x + 2, y + 20, z + 2, "minecraft:redstone_lamp[lit=true]")
    bb.set(x - 2, y + 20, z + 2, "minecraft:barrel[facing=up]")


def camp(bb, rng):
    """The bonfire pit with log benches and tents between the forge and the keep."""
    cx, cz = 84, 62
    y = hy(cx, cz)
    bb.fill(cx - 9, y, cz - 9, cx + 9, y, cz + 9, "minecraft:coarse_dirt")
    bb.fill(cx - 9, y + 1, cz - 9, cx + 9, y + 6, cz + 9, AIR)
    bb.ring(cx, y, cz, 1, 2, y, "minecraft:cobblestone")
    bb.set(cx, y + 1, cz, "minecraft:campfire[lit=true]"); bb.set(cx, y, cz, "minecraft:netherrack")
    bb.set(cx, y + 1, cz, "minecraft:campfire[lit=true]")
    for a in range(0, 360, 45):
        t = math.radians(a)
        bx, bz = cx + int(round(6 * math.cos(t))), cz + int(round(6 * math.sin(t)))
        axis = "x" if abs(math.sin(t)) > 0.7 else "z"
        bb.set(bx, y + 1, bz, f"minecraft:stripped_dark_oak_log[axis={axis}]")
    for k in range(6):
        bb.set(cx + int(rng.integers(-7, 8)), y + 1, cz + int(rng.integers(-7, 8)), "minecraft:barrel[facing=up]") if k % 2 else None
    # tents: dark wool A-frames round the pit
    for (tx, tz, rot) in ((70, 70, 0), (98, 70, 0), (66, 54, 1), (102, 56, 1), (76, 76, 0)):
        ty = hy(tx, tz)
        for k in range(4):
            for L in range(7):
                ax, az = (tx + L, tz) if rot == 0 else (tx, tz + L)
                for s in (-1, 1):
                    px, pz = (ax, az + s * (3 - k)) if rot == 0 else (ax + s * (3 - k), az)
                    bb.set(px, ty + 1 + k, pz, "minecraft:red_wool" if (L + k) % 4 else "minecraft:black_wool")
        rx, rz = (tx + 3, tz) if rot == 0 else (tx, tz + 3)
        bb.set(rx, ty + 1, rz, "minecraft:red_bed[facing=north,part=foot]") if False else bb.set(rx, ty + 1, rz, "minecraft:brown_carpet")


def pier(bb):
    """An iron pier from the camp out to the ship's side: plates on piles, chain rails, lamps, bollards."""
    x0, x1 = 64, 110
    z = SHIP[1] - 12
    for x in range(x0, x1 + 1):
        bb.fill(x, 1, z - 2, x, 1, z + 2, "minecraft:iron_block" if x % 4 else "minecraft:polished_blackstone")
        if x % 4 == 0:
            for dz in (-2, 2):
                bb.fill(x, -8, z + dz, x, 0, z + dz, "minecraft:polished_blackstone_wall")
                bb.set(x, 2, z + dz, "minecraft:polished_blackstone_wall")
        if x % 8 == 0:
            lamp_post(bb, x, 2, z - 2, post="minecraft:iron_bars", h=3, light="minecraft:soul_lantern[hanging=false]")
    for zz in range(z - 2, 76, -1) if False else range(76, z - 1):
        bb.fill(84, 1, zz, 88, 1, zz, "minecraft:iron_block")
        bb.fill(84, 2, zz, 88, 6, zz, AIR)
    # a gangway from the pier to the ship's deck
    bb.fill(84, 2, z + 3, 86, 4, z + 4, "minecraft:dark_oak_slab[type=bottom]") if False else bb.fill(84, 2, z + 3, 86, 2, z + 4, "minecraft:dark_oak_planks")


def design():
    bb = BigBuild(seed=9100, y_min=-14, y_max=110)
    rng = np.random.default_rng(9100)
    terrain(bb)
    palisade(bb, rng)
    forge(bb)
    keep(bb)
    killer_lookout(bb)
    camp(bb, rng)
    pier(bb)
    for (x, z, r, h) in ((22, 70, 6, 6), (40, 70, 5, 5), (66, 28, 6, 5), (100, 26, 5, 6), (136, 38, 6, 6), (144, 50, 5, 4),
                         (56, 78, 4, 3), (118, 66, 5, 4), (34, 30, 5, 4), (110, 76, 4, 3), (62, 66, 4, 3)):
        if land(x, z):
            heap(bb, x, z, r, h, rng)
    stamp_ship(bb, "victoria_punk", SHIP[0], SHIP[1], water_y=0, rot=0)
    return bb, []


def build():
    bb, audit = design()
    b = to_canvas(bb)
    steady(b)
    y = max(hy(x, z) for x in range(104, 129, 3) for z in range(30, 53, 3))
    b.npc(116, y + 13, 46, "kid", True)
    b.chest(110, y + 13, 46, "hard", "east")
    b.chest(30, hy(30, 50) + 1, 50, "hard", "east")
    for (x, z) in ((80, 58), (90, 66), (70, 92), (100, 92), (84, 24)):
        b.guard(x, hy(x, z) + 1, z, "pirate")
    b.guard(140, hy(140, 66) + 20, 68, "pirate_gunner")
    return b, 0

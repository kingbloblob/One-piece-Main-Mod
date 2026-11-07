"""Victoria Punk: Eustass Kid's ship pulled up on a rocky shore, and the Kid Pirates' scrapyard camp around it.
A 70 m red-and-black hull patched with scrap metal, a horned skull figurehead, two masts with red sails and Kid's
flaming-skull flag, cannons along the rails, a stern castle with Kid's cabin and a furnished lower deck. On the
beach: heaps of scrap, Kid's workshop where he builds his metal arm, Killer's lookout, tents and a bonfire.
~100 x 84. Ground = y 0 (the sea half is cut into it)."""
import math, random
from canvas import *
import interiors as I

SID = "victoria_punk"
TITLE = "Victoria Punk (Kid's ship)"
CUTS = [3, 9]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")

NX, NZ = 100, 84
CZ = 40
SEA_X = 52            # water west of this x, beach east of it
HX, HL = 4, 72        # hull start and length (bow points +x, up the beach)
DECK = 6
KEEL = -6
RED = "minecraft:red_terracotta"
BLACK = "minecraft:black_terracotta"
PUNK = dict(wood="dark_oak", rug="red", rug2="black", bed="red", light="minecraft:lantern", accent="minecraft:iron_block",
            banner="red", candle="red")
SCRAP = ("minecraft:iron_block", "minecraft:exposed_copper", "minecraft:weathered_copper", "minecraft:oxidized_cut_copper",
         "minecraft:anvil[facing=north]", "minecraft:chipped_anvil[facing=east]", "minecraft:cauldron", "minecraft:iron_bars[east=false,north=false,south=false,west=false,waterlogged=false]",
         "minecraft:hopper[enabled=true,facing=down]", "minecraft:heavy_core[waterlogged=false]", "minecraft:iron_trapdoor[facing=north,half=bottom,open=false,powered=false,waterlogged=false]",
         "minecraft:raw_iron_block", "minecraft:copper_grate[waterlogged=false]", "minecraft:chain[axis=x,waterlogged=false]" if False else "minecraft:iron_block")


def scrap_heap(b, x, z, r, h, rnd):
    for dx in range(-r, r + 1):
        for dz in range(-r, r + 1):
            d = math.hypot(dx, dz)
            if d > r: continue
            top = int(h * (1 - d / (r + 0.5))) + rnd.randint(0, 1)
            for y in range(1, top + 1): b.set(x + dx, y, z + dz, rnd.choice(SCRAP))


def build():
    rnd = random.Random(61)
    b = B()
    # ---------------- shore: sea in the west, sand and stony shore, grass at the back
    for x in range(NX):
        for z in range(NZ):
            shore = SEA_X + 4 * math.sin(z * 0.15)
            if x < shore:
                depth = min(8, int((shore - x) / 3) + 1)
                for y in range(-depth, 1): b.set(x, y, z, WATER)
                b.set(x, -depth - 1, z, "minecraft:sand" if (x + z) % 3 else "minecraft:gravel")
                for y in range(-depth - 4, -depth - 1): b.set(x, y, z, "minecraft:stone")
            else:
                for y in range(-4, 0): b.set(x, y, z, "minecraft:sandstone" if y > -3 else "minecraft:stone")
                b.set(x, 0, z, "minecraft:sand" if x < shore + 10 else ("minecraft:gravel" if (x * z) % 5 == 0 else ("minecraft:stone" if x < shore + 18 else "minecraft:grass_block")))
                if x > shore + 20 and rnd.random() < 0.05: b.set(x, 1, z, "minecraft:short_grass")
    # ---------------- the hull
    def paint(x, y, z, zr):
        if y >= DECK - 1: return BLACK
        if y == DECK - 3: return "minecraft:gold_block" if x % 6 == 0 else BLACK  # wale stripe with rivets
        if (x * 7 + y * 13 + z * 3) % 23 == 0: return rnd.choice(("minecraft:iron_block", "minecraft:exposed_copper", "minecraft:weathered_cut_copper"))
        return RED
    hw = b.hull(HX, HL, CZ, 18, KEEL, DECK, RED, bottom="minecraft:dark_oak_planks", rail="minecraft:iron_bars[east=true,north=false,south=false,west=true,waterlogged=false]",
                bow_len=22, stern_len=8, rail_h=1, fill_deck="minecraft:spruce_planks", flare=0.15, waterline=-1, paint=paint)
    def half(x): return hw.get(x, 0)
    # lower deck floor
    for x in range(HX + 4, HX + HL - 12):
        zr = int(half(x)) - 2
        for z in range(CZ - zr, CZ + zr + 1): b.set(x, 0, z, "minecraft:dark_oak_planks")
    # lower deck rooms: two rows along a corridor
    I.subdivide(b, HX + 8, 1, CZ - 6, HX + HL - 18, CZ + 6, 4, "minecraft:dark_oak_planks",
                ("barracks", "kitchen", "dining", "armory", "storage", "workshop", "tavern", "barracks"), PUNK, cell=10, seed=3,
                keepout=((HX + 8, CZ - 1, HX + 10, CZ + 1),))
    for i in range(5):  # hatch and stairs from the deck down
        b.set(HX + 30 + i, DECK - i, CZ + 4, stairs("minecraft:dark_oak_stairs", "west")) if False else None
    for k in range(DECK):
        b.set(HX + 40, 1 + k, CZ + 1, "minecraft:ladder[facing=north,waterlogged=false]")
    b.set(HX + 40, DECK, CZ + 1, "minecraft:ladder[facing=north,waterlogged=false]")
    for y in range(1, DECK): b.set(HX + 40, y, CZ + 2, "minecraft:dark_oak_planks")
    # gun ports and cannons
    for x in range(HX + 12, HX + HL - 20, 6):
        for side in (-1, 1):
            z = CZ + side * int(round(half(x)))
            b.set(x, DECK - 2, z, "minecraft:black_concrete")
            b.set(x, DECK + 1, CZ + side * (int(round(half(x))) - 1), f"onepiece:cannon[facing={'south' if side > 0 else 'north'}]")
    # ---------------- stern castle: Kid's cabin and the helm
    S0, S1 = HX + 1, HX + 16
    for x in range(S0, S1 + 1):
        zr = int(round(half(x))) - 1
        for z in range(CZ - zr, CZ + zr + 1):
            for y in range(DECK + 1, DECK + 8):
                edge = x in (S0, S1) or abs(z - CZ) == zr
                b.set(x, y, z, BLACK if edge else AIR)
            b.set(x, DECK + 8, z, "minecraft:spruce_planks")
            if abs(z - CZ) == zr or x == S0: b.set(x, DECK + 9, z, "minecraft:iron_bars[east=true,north=true,south=true,west=true,waterlogged=false]")
    for z in range(CZ - 1, CZ + 2):
        for y in range(DECK + 1, DECK + 4): b.set(S1, y, z, AIR)
    for z in range(CZ - 6, CZ + 7, 3): b.set(S0, DECK + 4, z, "minecraft:red_stained_glass_pane")
    I.furnish(b, S0 + 1, DECK + 1, CZ - int(half(S0 + 4)) + 2, S1 - 1, CZ + int(half(S0 + 4)) - 2, 6, "captain", PUNK)
    b.set(S0 + 3, DECK + 9, CZ, "onepiece:ships_wheel[facing=east]")
    for i in range(7): b.set(S1 + 1 + i, DECK + 1 + i, CZ + int(half(S1)) - 3, stairs("minecraft:dark_oak_stairs", "west")) if i < 8 else None
    # ---------------- masts and the red sails with Kid's mark
    def kid_mark(u, v):
        if (u * 1.1) ** 2 + ((v - 0.15) * 1.3) ** 2 < 0.35:  # skull
            if (abs(u + 0.25) < 0.12 or abs(u - 0.25) < 0.12) and 0.05 < v < 0.35: return "minecraft:black_wool"
            return "minecraft:white_wool"
        if abs(abs(u) - abs(v + 0.5)) < 0.12 and v < -0.15: return "minecraft:white_wool"  # crossed bones
        if v > 0.55 and abs(u) < 0.6 and (int(u * 10) % 3 == 0): return "minecraft:orange_wool"  # flames
        return None
    for (mx, mh, nsl) in ((HX + 30, 44, 2), (HX + 50, 36, 2)):
        b.cyl(mx, CZ, 1, 0, DECK + mh, "minecraft:dark_oak_log[axis=y]")
        for y in range(DECK + mh + 1, DECK + mh + 4): b.set(mx, y, CZ, "minecraft:dark_oak_log[axis=y]")
        nest = DECK + mh - 4
        b.disk(mx, nest, CZ, 2, "minecraft:iron_block")
        for a in range(0, 360, 45):
            t = math.radians(a); b.set(round(mx + 2 * math.cos(t)), nest + 1, round(CZ + 2 * math.sin(t)), "minecraft:iron_bars[east=false,north=false,south=false,west=false,waterlogged=false]")
        span = (mh - 10) // nsl
        for s in range(nsl):
            y0 = DECK + 6 + s * span; y1 = y0 + span - 2
            hh = 12 - s * 3
            b.square_sail(mx + 2, CZ, y0, y1, hh, "minecraft:red_wool", belly=2, pattern=kid_mark if s == 0 else None)
            for z in range(CZ - hh - 2, CZ + hh + 3): b.set(mx + 1, y1 + 1, z, "minecraft:dark_oak_log[axis=z]")
        for side in (-1, 1):
            for k in range(3): b.line((mx - 2 + 2 * k, nest, CZ), (mx - 4 + 4 * k, DECK + 2, CZ + side * int(half(mx))), "minecraft:chain[axis=y,waterlogged=false]" if False else fence("dark_oak"))
    fx = HX + 30
    for y in range(DECK + 48, DECK + 54): b.set(fx, y, CZ, "minecraft:dark_oak_fence")
    b.jolly_roger(fx, DECK + 53, CZ + 1, 9, 6, bg="minecraft:black_wool", fg="minecraft:white_wool")
    # ---------------- horned skull figurehead on the bow
    bx = HX + HL - 1
    by = DECK + 2
    b.shape(lambda x, y, z: ((x - bx) / 4) ** 2 + ((y - by) / 4) ** 2 + ((z - CZ) / 4) ** 2 <= 1, bx - 4, by - 4, CZ - 4, bx + 4, by + 4, CZ + 4,
            "minecraft:bone_block[axis=y]", interior=None)
    for (dz,) in ((-2,), (2,)):
        b.set(bx + 4, by + 1, CZ + dz, "minecraft:black_concrete"); b.set(bx + 4, by + 1, CZ + dz + (1 if dz > 0 else -1), "minecraft:black_concrete")
    for dz in range(-2, 3): b.set(bx + 4, by - 2, CZ + dz, "minecraft:black_concrete" if dz % 2 else "minecraft:bone_block[axis=y]")
    for side in (-1, 1):  # horns curving forward
        for k in range(9):
            b.set(bx - 1 + k // 2, by + 3 + k, CZ + side * (3 + k // 3), "minecraft:bone_block[axis=y]" if k < 7 else "minecraft:black_concrete")
    b.line((bx - 4, DECK + 1, CZ), (bx + 8, DECK + 10, CZ), "minecraft:dark_oak_log[axis=x]")  # bowsprit
    # ---------------- beach camp: scrap heaps, workshop, tents, bonfire, Killer's lookout
    for (x, z, r, h) in ((64, 10, 4, 4), (90, 24, 4, 4), (66, 68, 6, 6), (86, 66, 4, 4), (92, 44, 3, 3)):
        scrap_heap(b, x, z, r, h, rnd)
    wx0, wz0 = 80, 6
    b.box(wx0, 0, wz0, wx0 + 13, 0, wz0 + 11, "minecraft:smooth_stone")
    b.walls(wx0, 1, wz0, wx0 + 13, 6, wz0 + 11, "minecraft:iron_block" if False else "minecraft:waxed_weathered_cut_copper")
    b.box(wx0 + 1, 1, wz0 + 1, wx0 + 12, 6, wz0 + 10, AIR)
    for x in range(wx0 - 1, wx0 + 15):
        for z in range(wz0 - 1, wz0 + 13): b.set(x, 7, z, "minecraft:waxed_exposed_cut_copper" if (x + z) % 3 else "minecraft:iron_block")
    for z in range(wz0 + 3, wz0 + 9):
        for y in range(1, 6): b.set(wx0, y, z, AIR)
    I.furnish(b, wx0 + 1, 1, wz0 + 1, wx0 + 12, wz0 + 10, 5, "workshop", PUNK)
    b.set(wx0 + 6, 1, wz0 + 9, "minecraft:smithing_table"); b.set(wx0 + 8, 1, wz0 + 9, "minecraft:blast_furnace[facing=north,lit=true]")
    b.set(wx0 + 10, 1, wz0 + 9, "minecraft:anvil[facing=north]")
    b.entities.append(("minecraft:armor_stand", wx0 + 6, 1, wz0 + 5, {"ShowArms": Byte(1), "Invulnerable": Byte(1),
                       "equipment": {"chest": {"id": "minecraft:iron_chestplate", "count": Int(1)}, "mainhand": {"id": "minecraft:iron_axe", "count": Int(1)}}}))
    for (tx, tz, col) in ((66, 48, "minecraft:red_wool"), (66, 56, "minecraft:black_wool"), (82, 54, "minecraft:red_wool")):
        for dx in range(-2, 3):
            for dy in range(0, 3 - abs(dx)):
                for dz in range(0, 5): b.set(tx + dx, 1 + dy, tz + dz, col)
        for dz in range(0, 5): b.set(tx, 1, tz + dz, AIR)
        b.set(tx, 1, tz + 2, "minecraft:red_bed[facing=south,occupied=false,part=foot]") if False else None
    b.cyl(74, 52, 2.5, 0, 0, "minecraft:cobblestone"); b.set(74, 1, 52, "minecraft:campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
    for (x, z) in ((71, 52), (77, 52), (74, 49), (74, 55)): b.set(x, 1, z, "minecraft:dark_oak_log[axis=x]")
    lx, lz = 92, 76
    for (dx, dz) in ((-1, -1), (1, -1), (-1, 1), (1, 1)): b.column(lx + dx, lz + dz, 1, 12, "minecraft:dark_oak_log[axis=y]")
    b.box(lx - 2, 13, lz - 2, lx + 2, 13, lz + 2, "minecraft:spruce_planks")
    for k in range(12): b.set(lx, 1 + k, lz - 2, "minecraft:ladder[facing=north,waterlogged=false]")
    for x in range(lx - 2, lx + 3):
        for z in (lz - 2, lz + 2): b.set(x, 14, z, fence("spruce"))
    b.set(lx, 14, lz, LANTERN) if False else b.set(lx + 1, 14, lz, lantern())
    # mooring posts and the gangway from the deck down to the beach
    gx = HX + 52
    for k in range(DECK):
        b.set(gx + k, DECK - k, CZ + int(half(gx)) + 1 + 0, "minecraft:spruce_slab[type=bottom,waterlogged=false]")
    for (x, z) in ((60, 30), (60, 52)): b.column(x, z, 1, 2, "minecraft:dark_oak_log[axis=y]")
    # ---------------- people and loot
    b.npc(S0 + 8, DECK + 1, CZ, "kid", True)
    b.chest(S0 + 2, DECK + 1, CZ + 3, "hard", "east"); b.chest(wx0 + 2, 1, wz0 + 2, "hard", "east")
    b.guards("pirate", ((HX + 25, CZ - 4), (HX + 35, CZ + 4), (HX + 45, CZ - 3)), y=DECK + 1)
    b.guards("pirate_gunner", ((lx, lz),), y=14)
    b.guards("pirate", ((72, 50), (80, 58), (70, 40)))
    return b, 0

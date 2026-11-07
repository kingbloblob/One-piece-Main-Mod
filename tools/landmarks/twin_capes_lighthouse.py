"""Twin Capes at the foot of Reverse Mountain: Crocus' striped lighthouse on the rocky cape, his house and clinic
beside it with the deck chair, the garden and the beach, and in the bay the head of Laboon the island whale
rising out of the water, scarred and with the Straw Hat jolly roger Luffy painted on his forehead. ~84 x 84.
Ground = y 0, the sea fills the south and east."""
import math, random
from canvas import *
import interiors as I
import townkit as T

SID = "twin_capes_lighthouse"
TITLE = "Twin Capes Lighthouse"
CUTS = [3]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")

N = 96
LX, LZ = 22, 22


def cape(x, z):
    d = math.hypot((x - 22) * 0.9, z - 22)
    return d < 24 + 3 * math.sin(math.atan2(z - 22, x - 22) * 3)


def build():
    rnd = random.Random(261)
    b = B()
    for x in range(N):
        for z in range(N):
            if cape(x, z):
                h = max(0, min(6, int((24 - math.hypot(x - 22, z - 22)) / 2)))
                for y in range(-4, h + 1): b.set(x, y, z, rnd.choice(("minecraft:stone", "minecraft:andesite", "minecraft:stone")) if y < h else ("minecraft:grass_block" if h > 1 else "minecraft:sand"))
                if h > 1 and rnd.random() < 0.06: b.set(x, h + 1, z, rnd.choice(("minecraft:short_grass", "minecraft:dandelion", "minecraft:poppy")))
            else:
                for y in range(-8, 1): b.set(x, y, z, WATER)
                b.set(x, -9, z, "minecraft:sandstone")
    TOP = 6
    # ---------------- the lighthouse: red and white bands, gallery and lamp room
    for y in range(TOP + 1, TOP + 31):
        r = 4.2 - (y - TOP) * 0.05
        b.cyl(LX, LZ, r, y, y, "minecraft:red_concrete" if ((y - TOP) // 5) % 2 else "minecraft:white_concrete", hollow=True)
    b.cyl(LX, LZ, 3, TOP, TOP, "minecraft:stone_bricks")
    for f in range(TOP + 8, TOP + 30, 8): b.cyl(LX, LZ, 2.4, f, f, "minecraft:spruce_planks")
    for y in range(TOP + 1, TOP + 31): b.set(LX, y, LZ - 2, "minecraft:ladder[facing=south,waterlogged=false]")
    for y in range(TOP + 4, TOP + 29, 6): b.set(LX + 4, y, LZ, "minecraft:glass_pane"); b.set(LX - 4, y, LZ, "minecraft:glass_pane")
    G = TOP + 31
    b.cyl(LX, LZ, 5, G, G, "minecraft:polished_andesite")
    for a in range(0, 360, 15):
        t = math.radians(a); b.set(round(LX + 5 * math.cos(t)), G + 1, round(LZ + 5 * math.sin(t)), "minecraft:iron_bars[east=false,north=false,south=false,west=false,waterlogged=false]")
    b.cyl(LX, LZ, 2.5, G + 1, G + 4, "minecraft:glass", hollow=True)
    b.set(LX, G + 2, LZ, "minecraft:sea_lantern"); b.set(LX, G + 3, LZ, "minecraft:glowstone"); b.set(LX, G + 1, LZ, "minecraft:redstone_lamp[lit=true]") if False else b.set(LX, G + 1, LZ, "minecraft:sea_lantern")
    for k in range(4): b.cyl(LX, LZ, 3.2 - k * 0.9, G + 5 + k, G + 5 + k, "minecraft:red_concrete")
    b.set(LX, G + 9, LZ, "minecraft:lightning_rod[facing=up,powered=false,waterlogged=false]")
    b.set(LX, G, LZ - 2, "minecraft:ladder[facing=south,waterlogged=false]")
    for y in (TOP + 1, TOP + 2): b.set(LX, y, LZ + 4, AIR); b.set(LX, y, LZ + 3, AIR)
    # Crocus' house and clinic
    T.house(b, 32, 16, 10, 8, 1, "plaster", rnd, kinds=["lab"], y=hgt(b, 36, 20), door="south")
    T.house(b, 30, 28, 8, 7, 1, "plaster", rnd, kinds=["bedroom"], y=hgt(b, 34, 31), door="north")
    for (x, z) in ((36, 26), (37, 26)): b.set(x, hgt(b, x, z) + 1, z, "minecraft:white_carpet")  # the deck chair
    b.set(38, hgt(b, 38, 26) + 1, z, "minecraft:white_bed[facing=east,occupied=false,part=foot]") if False else None
    b.set(38, hgt(b, 38, 26) + 1, 26, "minecraft:oak_fence"); b.set(38, hgt(b, 38, 26) + 2, 26, "minecraft:white_wool") if False else None
    T.garden(b, 10, 34, 20, 40, y=hgt(b, 15, 37), crop="minecraft:beetroots[age=3]")
    T.pier(b, 40, 36, 14, axis="x", y=1)
    # ---------------- Laboon's head rising from the bay
    WX, WZ = 66, 66
    def whale(x, y, z):
        dx, dy, dz = x - WX, y + 6, z - WZ
        return (dx / 27) ** 2 + (dy / 18) ** 2 + (dz / 17) ** 2 <= 1 and y >= -8
    def skin(x, y, z):
        if y < -2: return "minecraft:gray_concrete"
        if (x - WX + 24) ** 2 + (y - 3) ** 2 + (z - WZ) ** 2 < 6: return "minecraft:white_concrete"
        return "minecraft:light_blue_terracotta" if (x + y + z) % 13 else "minecraft:light_gray_concrete"
    b.shape(whale, WX - 28, -8, WZ - 18, WX + 28, 13, WZ + 18, skin, interior=None)
    for dz in (-7, 7):  # eyes on the sides
        ez = WZ + (12 if dz > 0 else -12); b.set(WX - 14, 2, ez, "minecraft:black_concrete"); b.set(WX - 14, 3, ez, "minecraft:white_concrete"); b.set(WX - 13, 2, ez, "minecraft:black_concrete")
    for x in range(WX - 27, WX - 8):  # mouth line
        z = WZ; y = -3 + (x - WX + 27) // 8
        for dz in range(-16, 17):
            if whale(x, y, WZ + dz) and not whale(x, y, WZ + dz + (1 if dz > 0 else -1)): b.set(x, y, WZ + dz, "minecraft:black_concrete")
    for i in range(12):  # scars
        x = WX - 6 + rnd.randint(-10, 14); z = WZ + rnd.randint(-10, 10)
        for y in range(13, -2, -1):
            if whale(x, y, z): b.set(x, y, z, "minecraft:pink_terracotta"); break
    # the Straw Hat jolly roger painted on top of his head
    def jr(u, v):
        if u * u + (v * 1.2) ** 2 < 16: return "minecraft:black_concrete" if (abs(u + 1.6) < 0.8 or abs(u - 1.6) < 0.8) and -1 < v < 1 else "minecraft:white_concrete"
        if 16 <= u * u + (v * 1.2) ** 2 < 30 and v > 0.5: return "minecraft:yellow_concrete"
        if abs(abs(u) - abs(v + 3)) < 0.9 and v < -2.5: return "minecraft:white_concrete"
        return None
    for x in range(WX - 8, WX + 9):
        for z in range(WZ - 8, WZ + 9):
            m = jr(x - WX, z - WZ)
            if m:
                for y in range(13, -3, -1):
                    if whale(x, y, z): b.set(x, y, z, m); break
    for y in range(-8, 1):  # sea water around the body (keep the bay full)
        pass
    # ---------------- people and loot
    b.chest(33, hgt(b, 36, 20) + 1, 17, "easy", "south")
    return b, 0


def hgt(b, x, z):
    for y in range(12, -1, -1):
        s = b.get(x, y, z)
        if s and s not in (AIR, WATER) and "grass" not in s.split(":")[1][:5] + "x" or (s and s == "minecraft:grass_block"):
            if s and s not in (AIR, WATER) and not s.startswith("minecraft:short_grass") and not s.startswith("minecraft:dandelion") and not s.startswith("minecraft:poppy"): return y
    return 0

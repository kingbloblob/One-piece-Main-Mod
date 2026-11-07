"""The Human Auctioning House in Grove 1 of Sabaody: a grand theatre-like hall with a domed roof and a blood-red
facade, built against a giant Yarukiman mangrove. Inside: the auditorium with tiered seats and the Celestial
Dragons' gilded box, the stage with its curtain and the display cage, the backstage cells and holding pens, the
auctioneer's office, the vault of bids and the lobby. Outside: the grove number and the Marine guards.
~84 x 80. Ground = y 0."""
import math, random
from canvas import *
import interiors as I
import townkit as T
import sabaody_kit as S

SID = "auction_house"
TITLE = "Human Auction House"
CUTS = [2, 8]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")

NX, NZ = 84, 80
RED = "minecraft:red_nether_bricks"
GILT = dict(wood="dark_oak", rug="red", rug2="yellow", bed="red", light="minecraft:lantern", accent="minecraft:gold_block",
            banner="red", candle="yellow")
X0, X1, Z0, Z1 = 14, 66, 18, 62
H = 16


def build():
    rnd = random.Random(471)
    b = B()
    S.ground(b, NX, NZ, rnd)
    S.yarukiman(b, 74, 10, rnd, r=4.5, h=32)
    S.grove_number(b, 71, 12, 15, 1)
    S.yarukiman(b, 8, 72, rnd, r=3.5, h=26)
    # ---------------- the hall shell
    b.box(X0, 0, Z0, X1, 0, Z1, "minecraft:polished_blackstone")
    b.walls(X0, 1, Z0, X1, H, Z1, RED)
    b.box(X0 + 1, 1, Z0 + 1, X1 - 1, H, Z1 - 1, AIR)
    for x in range(X0, X1 + 1, 6):
        for z in (Z0, Z1): b.column(x, z, 1, H, "minecraft:polished_blackstone_bricks")
    for z in range(Z0, Z1 + 1, 6):
        for x in (X0, X1): b.column(x, z, 1, H, "minecraft:polished_blackstone_bricks")
    for x in range(X0 + 3, X1 - 2, 6):
        for z in (Z0, Z1):
            for y in range(8, 13): b.set(x, y, z, "minecraft:red_stained_glass_pane")
    b.box(X0, H + 1, Z0, X1, H + 1, Z1, "minecraft:polished_blackstone_bricks")
    for x in range(X0, X1 + 1):  # gilded cornice and parapet
        for z in (Z0, Z1): b.set(x, H + 2, z, "minecraft:gold_block" if x % 6 == 2 else "minecraft:polished_blackstone_brick_wall")
    for z in range(Z0, Z1 + 1):
        for x in (X0, X1): b.set(x, H + 2, z, "minecraft:gold_block" if z % 6 == 2 else "minecraft:polished_blackstone_brick_wall")
    b.dome((X0 + X1) // 2, (Z0 + Z1) // 2, H + 2, 16, s="minecraft:red_terracotta", tip="minecraft:gold_block", hollow=True)
    b.cyl((X0 + X1) // 2, (Z0 + Z1) // 2, 16.5, H + 2, H + 2, "minecraft:gold_block", hollow=True)
    # ---------------- the grand facade (south) with columns and the entrance
    MX = (X0 + X1) // 2
    for x in range(MX - 12, MX + 13, 4):
        b.round_column(x, Z1 + 3, 1, 1, H - 2, "minecraft:quartz_pillar[axis=y]")
    b.box(MX - 13, H - 1, Z1 + 1, MX + 13, H, Z1 + 5, "minecraft:quartz_bricks")
    for k in range(6):
        b.box(MX - 12 + k * 2, H + 1 + k, Z1 + 1, MX + 12 - k * 2, H + 1 + k, Z1 + 1, "minecraft:quartz_bricks")
    b.box(MX - 13, 0, Z1 + 1, MX + 13, 0, Z1 + 6, "minecraft:red_carpet" if False else "minecraft:polished_blackstone")
    for x in range(MX - 2, MX + 3): b.set(x, 1, Z1 + 6, "minecraft:red_carpet")
    for z in range(Z1 + 1, Z1 + 7):
        for x in range(MX - 2, MX + 3): b.set(x, 1, z, "minecraft:red_carpet")
    for x in range(MX - 2, MX + 3):
        for y in range(1, 6): b.set(x, y, Z1, AIR)
    b.box(MX - 14, H + 1, Z1 + 5, MX + 14, H + 7, Z1 + 5, "minecraft:dark_oak_planks")
    b.text(MX - 13, H + 2, Z1 + 6, "AUCTION", "minecraft:gold_block")
    # ---------------- the lobby (south strip)
    LZ0 = Z1 - 9
    for x in range(X0 + 1, X1):
        for y in range(1, 7): b.set(x, y, LZ0, RED if not (MX - 2 <= x <= MX + 2 and y < 5) else AIR)
    b.box(X0 + 1, 6, LZ0 + 1, X1 - 1, 6, Z1 - 1, "minecraft:dark_oak_planks")
    I.furnish(b, X0 + 1, 1, LZ0 + 1, MX - 4, Z1 - 1, 4, "dining", GILT, seed=71)
    I.furnish(b, MX + 4, 1, LZ0 + 1, X1 - 1, Z1 - 1, 4, "study", GILT, seed=72)
    # ---------------- the auditorium: tiered seats rising toward the lobby
    SZ0, SZ1 = Z0 + 16, LZ0 - 1
    for z in range(SZ0, SZ1 + 1):
        tier = (z - SZ0) // 2
        for x in range(X0 + 2, X1 - 1):
            for y in range(1, tier + 1): b.set(x, y, z, "minecraft:dark_oak_planks")
            if (z - SZ0) % 2 == 0 and abs(x - MX) > 1:
                b.set(x, tier + 1, z, "minecraft:red_carpet" if (x % 3) else "minecraft:dark_oak_stairs[facing=south,half=bottom,shape=straight,waterlogged=false]")
            elif abs(x - MX) <= 1:
                b.set(x, tier + 1, z, "minecraft:red_carpet")
    for z in range(SZ0, SZ1, 4): b.set(X0 + 1, 6, z, lantern(True)); b.set(X1 - 1, 6, z, lantern(True))
    # the Celestial Dragons' box: a gilded balcony on the east wall
    for z in range(SZ0 + 4, SZ0 + 14):
        for x in range(X1 - 6, X1):
            b.set(x, 8, z, "minecraft:gold_block" if x == X1 - 6 else "minecraft:red_carpet" if False else "minecraft:dark_oak_planks")
            b.set(x, 9, z, "minecraft:red_carpet" if x > X1 - 6 else "minecraft:gold_block")
    for x in range(X1 - 5, X1, 2): b.set(x, 9, SZ0 + 8, "minecraft:quartz_stairs[facing=west,half=bottom,shape=straight,waterlogged=false]")
    b.set(X1 - 3, 11, SZ0 + 8, "minecraft:white_banner[rotation=4]") if False else b.set(X1 - 1, 11, SZ0 + 8, "minecraft:gold_block")
    for y in range(1, 9): b.set(X1 - 1, y, SZ0 + 3, "minecraft:ladder[facing=north,waterlogged=false]")
    # ---------------- the stage and curtain, with the display cage
    STZ0, STZ1 = Z0 + 6, Z0 + 14
    b.box(X0 + 6, 1, STZ0, X1 - 6, 2, STZ1, "minecraft:dark_oak_planks")
    for x in range(X0 + 6, X1 - 5): b.set(x, 3, STZ1, "minecraft:spruce_trapdoor[facing=south,half=bottom,open=false,powered=false,waterlogged=false]") if False else None
    for x in range(X0 + 4, X1 - 3):
        for y in range(3, H):
            if not (X0 + 10 <= x <= X1 - 10 and y < 12): b.set(x, y, STZ0 - 1, "minecraft:red_wool")
        b.set(x, H - 1, STZ1 + 1, "minecraft:red_wool"); b.set(x, H - 2, STZ1 + 1, "minecraft:red_wool" if x % 2 else AIR)
    b.box(MX - 2, 3, STZ0 + 2, MX + 2, 7, STZ0 + 6, "minecraft:iron_bars[east=true,north=true,south=true,west=true,waterlogged=false]")
    b.box(MX - 1, 3, STZ0 + 3, MX + 1, 6, STZ0 + 5, AIR)
    b.set(MX, 3, STZ1 - 1, "minecraft:lectern[facing=south,has_book=true,powered=false]")
    for x in (X0 + 8, X1 - 8): b.set(x, 3, STZ1, "minecraft:redstone_lamp[lit=true]")
    # ---------------- backstage: cells and holding pens, the auctioneer's office and the bid vault
    I.subdivide(b, X0 + 1, 1, Z0 + 1, X1 - 1, STZ0 - 2, 5, RED, ("cell", "cell", "study", "cell", "treasure", "cell"), GILT, cell=10, corridor=2, seed=73)
    for x in range(X0 + 2, X1 - 1, 10):
        b.set(x, 2, STZ0 - 2, AIR); b.set(x, 1, STZ0 - 2, AIR)
    # ---------------- the guards' post outside and the slave-trader's carriage
    T.house(b, 4, 26, 8, 8, 1, "marine", rnd, kinds=["barracks"], theme="marine", door="east")
    for x in range(MX - 16, MX + 17, 8): T.lamp_post(b, x, Z1 + 9)
    T.path(b, [(MX, Z1 + 7), (MX, NZ - 2)], w=2, s="minecraft:mangrove_planks")
    S.bubbles(b, NX, NZ, rnd, n=14, y0=6, y1=26, keep=lambda x, z: not (X0 - 2 <= x <= X1 + 2 and Z0 - 2 <= z <= Z1 + 7))
    # ---------------- loot and guards
    b.chest(X1 - 4, 1, Z0 + 2, "treasure", "west")
    b.chest(X1 - 3, 9, SZ0 + 6, "celestial", "west")
    b.guards("marine", ((MX - 6, Z1 + 4), (MX + 6, Z1 + 4), (MX, SZ0 + 6)))
    b.guards("cp_agent", ((MX, STZ0 + 7),), y=3)
    return b, 0

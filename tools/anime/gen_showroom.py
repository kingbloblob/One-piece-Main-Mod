"""Anime Look showroom: a flat test area that lines up vanilla and mod blocks, animated textures, biome-tinted grass
and leaves, and a few mobs, so the pack can be judged in one place (flip it on and off in Options > Resource Packs).
Usage: gen_showroom.py <mod resources folder> <output .mcfunction>
  e.g. gen_showroom.py src/main/resources src/main/resources/data/onepiece/function/anime_showroom.mcfunction
In game: stand where the north-west corner should be and run /function onepiece:anime_showroom (needs cheats/op).
It clears a 48 x 13 x 40 area east and south of you first.
"""
import sys, os, json

RES, OUT = sys.argv[1], sys.argv[2]
W, H, D = 48, 13, 40
cmds = []

def c(s):
    cmds.append(s)

def at(x, y, z):
    return f"~{x} ~{y} ~{z}"

def fill(x1, y1, z1, x2, y2, z2, block):
    c(f"fill {at(x1, y1, z1)} {at(x2, y2, z2)} {block}")

def setb(x, y, z, block):
    c(f"setblock {at(x, y, z)} {block}")

VANILLA = """grass_block dirt coarse_dirt podzol mud stone cobblestone mossy_cobblestone stone_bricks andesite granite diorite
deepslate tuff sand red_sand sandstone gravel clay bricks terracotta oak_planks spruce_planks birch_planks jungle_planks
acacia_planks dark_oak_planks cherry_planks oak_log spruce_log birch_log cherry_log coal_ore iron_ore gold_ore diamond_ore
emerald_ore copper_block oxidized_copper white_wool red_wool blue_wool yellow_wool white_concrete glass ice snow_block
obsidian netherrack end_stone prismarine bookshelf crafting_table furnace hay_block melon pumpkin""".split()

def mod_blocks():
    """Full-cube and log-style onepiece blocks, read from the mod's blockstates."""
    base = os.path.join(RES, "assets/onepiece")
    cubes = ("cube_all", "cube_column", "cube_bottom_top", "leaves", "cube")
    out = []
    for f in sorted(os.listdir(os.path.join(base, "blockstates"))):
        v = json.load(open(os.path.join(base, "blockstates", f))).get("variants") or {}
        keys = {k.split("=")[0] for k in v}
        if keys == {"axis"}:
            out.append(f[:-5])
        elif len(v) == 1:
            m = list(v.values())[0]
            m = (m[0] if isinstance(m, list) else m)["model"].split(":")[1]
            p = os.path.join(base, "models", m + ".json")
            if os.path.exists(p) and json.load(open(p)).get("parent", "").split("/")[-1] in cubes:
                out.append(f[:-5])
    return out

def leafy(b):
    return b + "[persistent=true]" if b.endswith("leaves") else b

def rows(blocks, z0, ns):
    """Two-high columns every 2 blocks, 23 per row, rows 3 apart. Returns the next free z."""
    per = (W - 2) // 2
    for i, b in enumerate(blocks):
        x, z = 1 + 2 * (i % per), z0 + 3 * (i // per)
        fill(x, 0, z, x, 1, z, leafy(f"{ns}:{b}"))
    return z0 + 3 * ((len(blocks) + per - 1) // per)

# clear the area, lay a floor, and remove mobs left from an earlier run
c(f"execute positioned ~ ~-1 ~ run kill @e[type=!player,dx={W},dy={H},dz={D}]")
fill(0, 0, 0, W - 1, H - 1, D - 1, "air")
fill(0, -1, 0, W - 1, -1, D - 1, "smooth_stone")

z = rows(VANILLA, 1, "minecraft")
fill(0, -1, z, W - 1, -1, z, "polished_andesite")           # divider between vanilla and mod blocks
z = rows(mod_blocks(), z + 2, "onepiece")
fill(0, -1, z, W - 1, -1, z, "polished_andesite")
z += 2

# animated textures: fires, campfires, lava and water pools, a nether portal, glowing blocks
setb(1, 0, z, "campfire")
setb(3, 0, z, "soul_campfire")
setb(5, -1, z, "netherrack"); setb(5, 0, z, "fire")
setb(7, -1, z, "soul_sand"); setb(7, 0, z, "soul_fire")
for x0, liquid in ((9, "lava"), (14, "water")):
    fill(x0, -1, z, x0 + 3, 0, z + 3, "stone_bricks")
    fill(x0 + 1, 0, z + 1, x0 + 2, 0, z + 2, liquid)
fill(19, 0, z, 22, 4, z, "obsidian")
fill(20, 1, z, 21, 3, z, "nether_portal[axis=x]")
for i, b in enumerate(("magma_block", "sea_lantern", "prismarine", "glowstone", "lantern", "torch")):
    setb(24 + 2 * i, 0, z, b)
z += 5

# biome strips: the same grass, leaves and water in different biomes, to judge the colormaps
for i, biome in enumerate(("plains", "forest", "jungle", "swamp", "savanna", "badlands", "dark_forest", "taiga")):
    x0 = 1 + 6 * i
    if x0 + 4 >= W:
        break
    fill(x0, -1, z, x0 + 4, -1, z + 4, "grass_block")
    fill(x0, 0, z, x0 + 4, 0, z + 1, "short_grass")
    fill(x0 + 1, 0, z + 3, x0 + 3, 2, z + 3, "oak_leaves[persistent=true]")
    setb(x0 + 2, -1, z + 2, "water")
    c(f"fillbiome {at(x0, -1, z)} {at(x0 + 4, H - 2, z + 4)} minecraft:{biome}")
z += 6

# mobs on plinths, frozen in place
for i, mob in enumerate(("pig", "cow", "sheep", "chicken", "villager", "wolf", "zombie", "skeleton", "creeper", "horse")):
    x = 2 + 4 * i
    if x >= W - 1:
        break
    setb(x, 0, z, "polished_andesite")
    c(f"summon {mob} {at(x, 1, z)} {{NoAI:1b,Silent:1b,PersistenceRequired:1b,Invulnerable:1b}}")

assert z + 1 < D, f"showroom is {z + 2} deep but the cleared area is only {D}"
c('tellraw @s {"text":"Anime Look showroom built. Toggle One Piece Anime Look in Options > Resource Packs to compare.","color":"gold"}')
os.makedirs(os.path.dirname(OUT), exist_ok=True)
open(OUT, "w").write("# Made by tools/anime/gen_showroom.py, do not edit by hand.\n" + "\n".join(cmds) + "\n")
print(f"{len(cmds)} commands, {z + 2} blocks deep, written to {OUT}")

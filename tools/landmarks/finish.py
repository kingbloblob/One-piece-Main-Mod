"""Finishing pass run on every landmark build before it is rendered and tiled (make.py calls finish()).

It fixes what structure placement can't: the game places blocks exactly as saved and never updates them, so
  1. block ids that don't exist in 26.3 (minecraft:chain is now iron_chain) are renamed,
  2. glass panes, bars, fences and walls get their connections (unconnected panes show as thin posts = "holes"),
  3. anything that has to hang on or stand on something is checked: hanging lanterns get a chain up to the
     ceiling (or stand on the floor), wall torches/lamps need a wall, candles/lanterns/carpets need a floor,
     plants need soil (a flower on a table becomes a potted flower), crops get farmland,
  4. small groups of blocks touching nothing (floating stairs, slabs, furniture) are given a post or removed,
  5. every indoor floor gets enough light: chandeliers in tall halls, hanging lanterns, wall lamps and flush
     ceiling lamps are added until no indoor floor cell is darker than light level MIN_LIGHT.
finish(b, mode, sid) changes b.blocks in place and returns a short report dict.
mode: "land" (ground at y 0), "sea" (water at y 0), "seafloor" (everything under water), "cave" (no sky:
Nether/underground) or "sky" (floating build, lowest blocks are its base).
"""
import collections, re

MIN_LIGHT = 7
AIRS = ("minecraft:air", "minecraft:cave_air", "minecraft:void_air")
RENAME = {"minecraft:chain": "minecraft:iron_chain", "minecraft:prismarine_brick_wall": "minecraft:prismarine_wall",
          "minecraft:crimson_log": "minecraft:crimson_stem", "minecraft:stripped_crimson_log": "minecraft:stripped_crimson_stem",
          "minecraft:grass": "minecraft:short_grass"}
H4 = ((1, 0, 0, "east"), (-1, 0, 0, "west"), (0, 0, 1, "south"), (0, 0, -1, "north"))
DIRV = {"east": (1, 0), "west": (-1, 0), "south": (0, 1), "north": (0, -1)}
OPP = {"north": "south", "south": "north", "east": "west", "west": "east"}
N26 = [(dx, dy, dz) for dx in (-1, 0, 1) for dy in (-1, 0, 1) for dz in (-1, 0, 1) if (dx, dy, dz) != (0, 0, 0)]

# ---------------------------------------------------------------- block classes
FLOWERS = {"dandelion", "poppy", "blue_orchid", "allium", "azure_bluet", "red_tulip", "orange_tulip", "white_tulip", "pink_tulip",
           "oxeye_daisy", "cornflower", "lily_of_the_valley", "wither_rose", "torchflower", "open_eyeblossom", "closed_eyeblossom",
           "short_grass", "fern", "dead_bush", "brown_mushroom", "red_mushroom", "azalea", "flowering_azalea", "sweet_berry_bush",
           "crimson_fungus", "warped_fungus", "crimson_roots", "warped_roots", "nether_sprouts", "bush", "firefly_bush",
           "short_dry_grass", "tall_dry_grass", "cactus_flower", "wildflowers", "leaf_litter", "pink_petals",
           "cloud_puff", "sky_lotus", "fire_lily", "frost_bloom", "snow_lily", "ghost_mushroom", "desert_bloom", "candy_cane_sprout",
           "lollipop_flower", "sakura_petals"}
TALL = {"tall_grass", "large_fern", "sunflower", "lilac", "rose_bush", "peony", "pitcher_plant", "amazon_flower", "giant_fern"}
CROPS = {"wheat", "carrots", "potatoes", "beetroots", "melon_stem", "pumpkin_stem", "torchflower_crop"}
SOIL = {"grass_block", "dirt", "coarse_dirt", "podzol", "rooted_dirt", "moss_block", "pale_moss_block", "mud", "muddy_mangrove_roots",
        "farmland", "mycelium", "crimson_nylium", "warped_nylium", "soul_soil", "soul_sand", "clay", "sand", "red_sand",
        "island_cloud", "snow_block", "frosting_block", "chocolate_block", "packed_mud",
        "jungle_loam", "sugar_sand", "black_sand", "volcanic_ash", "grave_soil", "permafrost"}
LIGHTS = {"lantern": 15, "paper_lantern": 15, "bubble_lamp": 15, "soul_lantern": 10, "torch": 14, "wall_torch": 14, "soul_torch": 10,
          "soul_wall_torch": 10, "redstone_torch": 7, "redstone_wall_torch": 7, "glowstone": 15, "sea_lantern": 15, "shroomlight": 15,
          "ochre_froglight": 15, "verdant_froglight": 15, "pearlescent_froglight": 15, "lab_light": 15, "jack_o_lantern": 15,
          "campfire": 15, "soul_campfire": 10, "fire": 15, "soul_fire": 10, "lava": 15, "magma_block": 3, "end_rod": 14,
          "glow_lichen": 7, "beacon": 15, "crying_obsidian": 10, "conduit": 15, "lava_cauldron": 15, "copper_lantern": 15,
          "wall_lamp": 15, "candle_sconce": 12, "chandelier": 15, "iron_chandelier": 15, "ceiling_lamp": 15, "candelabra": 13,
          "den_den_relay": 0, "amethyst_cluster": 5, "light": 15, "sea_pickle": 6, "copper_torch": 14, "copper_wall_torch": 14}
NONFULL_KEYS = ("stairs", "slab", "fence", "_wall", "pane", "bars", "door", "carpet", "candle", "lantern", "torch", "button",
                "pressure_plate", "sign", "banner", "rail", "ladder", "chain", "_rod", "sapling", "potted_", "flower_pot", "skull", "head",
                "_bed", "chest", "lectern", "anvil", "cauldron", "campfire", "bell", "grindstone", "cake", "scaffolding", "vine",
                "lichen", "cobweb", "sea_pickle", "coral", "kelp", "seagrass", "bamboo", "sugar_cane", "cactus", "brewing_stand",
                "enchanting_table", "stonecutter", "hopper", "decorated_pot", "fire", "shelf", "dripstone", "lily_pad", "cocoa",
                "sweet_berry", "petals", "screen", "lamp", "sconce", "chandelier", "candelabra", "flower_box", "cannon", "anchor",
                "ships_wheel", "rope_coil", "den_den", "recruitment_board", "navigators_desk", "feast_table", "shipwright_bench",
                "ships_galley", "swordsmith_forge", "training_post", "treasure_vault", "shipyard_crane", "heavy_core", "conduit",
                "end_rod", "lightning_rod", "snow", "frame", "_roots", "fungus", "sprouts", "composter", "daylight", "mushroom",
                "turtle_egg", "pickle", "porthole", "_fan", "leaf_litter")
FULL_EXCEPT = ("snow_block", "mushroom_block", "mushroom_stem", "coral_block", "dried_kelp_block", "bamboo_block", "bamboo_planks",
               "bamboo_mosaic", "stripped_bamboo_block", "lab_light", "sea_lantern", "redstone_lamp", "honeycomb_block", "packed_mud",
               "bubble_glass", "chiseled_bookshelf", "bookshelf", "coral_bricks")
FULL_EXACT = {"snow_bricks", "permafrost"}  # full blocks whose names hold a non-full key ("snow")
TRANSPARENT_FULL = ("glass", "leaves", "ice", "slime_block", "honey_block", "beacon", "spawner", "barrier", "island_cloud", "cloud_puff")

# furniture from the furniture thread (com.onepiecemod.furniture): none are full cubes; some have a solid top,
# some hang on a wall (need the block behind them) or under a ceiling
def _load_furniture():
    import json, os
    f = "/mnt/project-files/one-piece-mod/furniture/furniture-blocks.json"
    top, other = set(), set()
    try:
        d = json.load(open(f))
        top = {n.split(":", 1)[1] for n in d.get("solid_top", [])}
        other = {n.split(":", 1)[1] for n in d.get("other", [])}
    except (OSError, ValueError):
        pass
    return top, other
FURN_TOP, FURN_OTHER = _load_furniture()
FURN = FURN_TOP | FURN_OTHER
FURN_WALL = {"life_ring", "rope_ladder", "weapon_rack", "tool_rack", "notice_board", "fishing_net"} | {n for n in FURN if n.endswith("_wall_shelf")}
FURN_CEIL = {"hanging_rope"}
FURN_WALK = {"rope_ladder", "hanging_rope", "fishing_net", "straw_mat"} | {n for n in FURN if n.endswith("_rug") or n.endswith("_curtain")}
LIGHTS.update({"iron_stove": 10, "hearth": 13})

_cache = {}


def nm(s):
    return s.split("[", 1)[0]


def short(s):
    return nm(s).split(":", 1)[1]


def props(s):
    if "[" not in s: return {}
    out = {}
    for kv in s[s.index("[") + 1:-1].split(","):
        if "=" in kv:
            k, v = kv.split("=", 1); out[k] = v
    return out


def withp(s, **kw):
    p = props(s); p.update({k: str(v).lower() if isinstance(v, bool) else str(v) for k, v in kw.items()})
    return nm(s) + ("[" + ",".join(f"{k}={v}" for k, v in sorted(p.items())) + "]" if p else "")


def kind(s):
    """'air' 'water' 'full' 'glass' (full but lets light through) or 'part' (anything smaller than a block)."""
    n = nm(s)
    k = _cache.get(n)
    if k: return k
    sh = n.split(":", 1)[1]
    if n in AIRS: k = "air"
    elif sh in ("water", "bubble_column"): k = "water"
    elif sh == "lava": k = "part"
    elif any(t in sh for t in FULL_EXCEPT) or sh in FULL_EXACT: k = "full"
    elif sh in FURN and n.startswith("onepiece:"): k = "part"
    elif sh in FLOWERS or sh in TALL or sh in CROPS: k = "part"
    elif any(t in sh for t in NONFULL_KEYS): k = "part"
    elif any(sh == t or sh.endswith("_" + t) or sh.startswith(t) for t in TRANSPARENT_FULL) or "stained_glass" in sh or sh.endswith("glass"): k = "glass"
    else: k = "full"
    if k == "full" and n.startswith("onepiece:"):
        # our plants, mosses and flags have no "part" key in their names (cloud_moss, jaya_hibiscus, jolly_roger): read
        # the block's model like tiler.op_full does, so panes don't join them, eaves and floors don't count them as wall
        from tiler import op_full
        if not op_full(n): k = "part"
    _cache[n] = k
    return k


def is_pane(sh):
    return sh.endswith("_pane") or sh in ("glass_pane", "iron_bars", "prison_bars", "shoji_screen")


def is_fence(sh):
    return sh.endswith("_fence")


def is_wall(sh):
    return sh.endswith("_wall") and not any(t in sh for t in ("wall_banner", "wall_sign", "wall_torch", "wall_head", "wall_skull", "wall_fan", "hanging"))


def top_sturdy(s):
    """Can a carpet-free thing (a block, a bed, a table leg) stand on top of s?"""
    if s is None: return False
    k = kind(s)
    if k in ("full", "glass"): return True
    sh = short(s); p = props(s)
    if sh.endswith("_slab"): return p.get("type") in ("top", "double")
    if sh.endswith("_stairs"): return p.get("half") == "top"
    if sh.endswith("trapdoor"): return p.get("half") == "top" and p.get("open") == "false"
    if sh == "snow": return p.get("layers") == "8"
    if sh in ("dirt_path", "farmland", "scaffolding", "composter", "barrel", "lectern", "enchanting_table", "stonecutter", "anvil",
              "chipped_anvil", "damaged_anvil", "cauldron", "water_cauldron", "lava_cauldron", "hopper", "chest", "trapped_chest",
              "ender_chest", "feast_table", "navigators_desk", "shipwright_bench", "ships_galley", "swordsmith_forge", "treasure_vault",
              "cake", "decorated_pot") or sh.endswith("_shelf") or sh.endswith("_bed") or sh in FURN_TOP:
        return True
    return False


def center_top(s):
    """Can a candle, lantern or flower pot stand on s (it only needs the middle)?"""
    if top_sturdy(s): return True
    if s is None: return False
    sh = short(s)
    return is_fence(sh) or is_wall(sh) or is_pane(sh) or (sh in ("iron_chain", "end_rod", "lightning_rod") and props(s).get("axis", "y") == "y") \
        or sh.endswith("_stairs") or sh.endswith("_slab") or sh.endswith("_bed")


def bottom_sturdy(s):
    """Can a lantern or chandelier hang under s?"""
    if s is None: return False
    k = kind(s)
    if k in ("full", "glass"): return True
    sh = short(s); p = props(s)
    if sh.endswith("_slab"): return p.get("type") in ("bottom", "double")
    if sh.endswith("_stairs"): return p.get("half") == "bottom"
    if sh.endswith("trapdoor"): return p.get("half") == "bottom" and p.get("open") == "false"
    return is_fence(sh) or is_wall(sh) or is_pane(sh) or sh in ("iron_chain", "end_rod", "lightning_rod", "hopper", "scaffolding")


def side_sturdy(s):
    return s is not None and kind(s) in ("full", "glass") and "leaves" not in s


def passable(s):
    return s is None or kind(s) in ("air", "water") or short(s) in ("short_grass", "snow", "vine", "glow_lichen") or "carpet" in s \
        or "pressure_plate" in s or (short(s) == "snow" and props(s).get("layers", "1") in ("1", "2")) \
        or (short(s) in FURN_WALK and s.startswith("onepiece:"))


def walk(s):
    """Can a person pass through this cell (air, water, an open doorway, a ladder, a rug...)?"""
    if s is None or passable(s): return True
    sh = short(s)
    if sh.endswith("_door") or sh.endswith("door") and "trap" not in sh: return True
    if sh.endswith("trapdoor"): return props(s).get("open") == "true"
    return any(t in sh for t in ("ladder", "vine", "torch", "sign", "banner", "button", "rail", "sapling", "lever", "candle", "scaffolding",
                                 "cobweb", "iron_chain", "fire", "lichen", "_roots", "petals", "flower_box", "wall_lamp", "sconce")) \
        or sh in FLOWERS or sh in TALL or sh in CROPS


def light_of(s):
    sh = short(s)
    if "candle" in sh and "cake" not in sh:
        p = props(s)
        return 3 * int(p.get("candles", "1")) if p.get("lit") == "true" else 0
    if sh in ("redstone_lamp", "copper_bulb", "furnace", "smoker", "blast_furnace") or sh.endswith("copper_bulb"):
        return 15 if props(s).get("lit") == "true" else 0
    if sh in ("campfire", "soul_campfire") and props(s).get("lit") == "false": return 0
    if sh == "sea_pickle":
        p = props(s)
        return 3 + 3 * int(p.get("pickles", "1")) if p.get("waterlogged") == "true" else 0
    if sh == "cave_vines" or sh == "cave_vines_plant":
        return 14 if props(s).get("berries") == "true" else 0
    return LIGHTS.get(sh, 0)


def blocks_light(s):
    """True if light doesn't pass (full opaque blocks, and to be safe stairs and slabs)."""
    if s is None: return False
    k = kind(s)
    if k == "full": return True
    if k in ("air", "water", "glass"): return False
    sh = short(s)
    return sh.endswith("_stairs") or (sh.endswith("_slab") and props(s).get("type") == "double")


# ---------------------------------------------------------------- the pass
class Finisher:
    def __init__(self, b, mode, sid, style):
        self.b = b; self.B = b.blocks; self.mode = mode; self.sid = sid; self.style = style
        self.rep = collections.Counter()

    def get(self, x, y, z):
        s = self.B.get((x, y, z))
        if s is None or nm(s) in AIRS: return None
        return s

    def put(self, p, s):
        self.B[p] = s

    def vacant(self, p):
        """What a removed block leaves behind: sea water where it touches the sea under a seafloor build, otherwise air
        (a prop taken out of an air bubble or a dry room under the sea must not flood it)."""
        if self.mode == "seafloor":
            x, y, z = p
            for d in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
                s = self.B.get((x + d[0], y + d[1], z + d[2]))
                if s is None or kind(s) == "water": return "minecraft:water[level=0]"
        return "minecraft:air"

    def kill(self, p, why):
        if self.mode == "seafloor" or p in self.B: self.B[p] = self.vacant(p)
        self.rep["removed " + why] += 1

    # 1 ---------------------------------------------------------
    def rename(self):
        for p, s in list(self.B.items()):
            n = nm(s)
            if n in RENAME:
                self.B[p] = RENAME[n] + s[len(n):]; self.rep["renamed " + n] += 1
            if n.endswith("_chain") or n == "minecraft:chain" or n == "minecraft:iron_chain":
                if "axis" not in props(self.B[p]): self.B[p] = withp(self.B[p], axis="y", waterlogged="false")

    def clouds(self):
        """onepiece:cloud_puff is a flower (a cross sprite with no collision). A lone puff on firm ground stays a flower, but
        puffs used as cloud (spheres, rims, soft beaches) become solid island_cloud, or players see X shapes and fall through."""
        B, PUFF, ISLE = self.B, "onepiece:cloud_puff", "onepiece:island_cloud"
        hard = []
        for (x, y, z), s in B.items():
            if nm(s) != PUFF: continue
            below = B.get((x, y - 1, z))
            firm = below is not None and nm(below) != PUFF and kind(below) in ("full", "glass")
            near = [B.get(q) for q in ((x + 1, y, z), (x - 1, y, z), (x, y, z + 1), (x, y, z - 1), (x, y + 1, z))]
            if not firm or any(n is not None and nm(n) in (PUFF, ISLE) for n in near): hard.append((x, y, z))
        for p in hard: B[p] = ISLE
        if hard: self.rep["cloud puffs made solid cloud"] += len(hard)

    # 3 ---------------------------------------------------------
    def supports(self):
        B = self.B
        # several rounds: removing a table can leave its candle floating
        for _ in range(3):
            changed = 0
            for p in sorted(B):
                s = B[p]
                if s is None or nm(s) in AIRS: continue
                x, y, z = p
                sh = short(s); pr = props(s)
                below = self.get(x, y - 1, z); above = self.get(x, y + 1, z)
                if sh in ("lantern", "soul_lantern", "paper_lantern", "bubble_lamp", "copper_lantern") or sh.endswith("_lantern") and "sea" not in sh and "jack" not in sh:
                    if pr.get("hanging") == "true":
                        if not self.hang(p, s): changed += 1
                    elif not center_top(below):
                        if bottom_sturdy(above): B[p] = withp(s, hanging="true"); self.rep["lantern flipped to hang"] += 1
                        elif not self.hang(p, withp(s, hanging="true"), quiet=True): self.kill(p, "floating lantern"); changed += 1
                elif sh in ("chandelier", "iron_chandelier", "ceiling_lamp"):
                    if not self.hang(p, s): changed += 1
                elif sh in ("iron_chain",) and pr.get("axis", "y") == "y":
                    pass
                elif ("candle" in sh and "cake" not in sh) or sh in ("torch", "soul_torch", "redstone_torch", "copper_torch", "flower_pot", "candelabra") \
                        or sh.startswith("potted_") or (sh.endswith("_skull") or sh.endswith("_head")) and "wall" not in sh:
                    if not center_top(below):
                        if self.drop_to_floor(p, s, center_top): self.rep["dropped to floor " + sh] += 1
                        else: self.kill(p, "floating " + sh); changed += 1
                elif "carpet" in sh or "pressure_plate" in sh or sh in ("rail", "powered_rail", "detector_rail", "activator_rail", "snow",
                                                                         "pink_petals", "sakura_petals", "leaf_litter", "wildflowers"):
                    if below is None or kind(below) in ("water",):
                        self.kill(p, "floating " + sh); changed += 1
                elif sh == "cloud_puff":
                    continue  # puffs of cloud are used as cloud, in the air on purpose
                elif sh in FLOWERS or sh in TALL and pr.get("half", "lower") == "lower":
                    if below is not None and short(below) in SOIL:
                        continue
                    if sh in TALL:
                        up = (x, y + 1, z)
                        if top_sturdy(below):  # a big plant on a floor: put it in a pot instead
                            pot = f"minecraft:potted_{'fern' if 'fern' in sh else 'azalea_bush'}"
                            B[p] = pot
                            if up in B and short(B[up]) == sh: B[up] = "minecraft:air"
                            self.rep["potted " + sh] += 1
                        else:
                            self.kill(p, "floating " + sh); changed += 1
                            if up in B and short(B[up]) == sh: self.kill(up, "floating " + sh)
                        continue
                    pot = "minecraft:potted_" + ("azalea_bush" if sh == "azalea" else "flowering_azalea_bush" if sh == "flowering_azalea" else sh)
                    if top_sturdy(below) and sh not in ("short_grass", "pink_petals", "sakura_petals", "leaf_litter", "wildflowers", "sweet_berry_bush",
                                                        "bush", "firefly_bush", "short_dry_grass", "tall_dry_grass", "nether_sprouts") \
                            and (pot in VALID or not VALID):
                        B[p] = pot; self.rep["potted " + sh] += 1
                    elif below is not None and kind(below) == "full" and short(below) in ("stone", "andesite", "cobblestone", "gravel") and self.mode == "land" and y <= 1:
                        B[(x, y - 1, z)] = "minecraft:grass_block[snowy=false]"; self.rep["soil under " + sh] += 1
                    else:
                        self.kill(p, "plant without soil " + sh); changed += 1
                elif sh in TALL and pr.get("half") == "upper":
                    if below is None or short(below) != sh: self.kill(p, "half plant"); changed += 1
                elif sh in CROPS:
                    if below is None or short(below) != "farmland":
                        if below is not None and short(below) in SOIL:
                            B[(x, y - 1, z)] = "minecraft:farmland[moisture=7]"; self.rep["farmland under crops"] += 1
                        else:
                            self.kill(p, "crop without soil"); changed += 1
                elif sh in FURN_CEIL and nm(s).startswith("onepiece:"):
                    if not (bottom_sturdy(above) or (above is not None and short(above) in FURN_CEIL)):
                        self.kill(p, "floating " + sh); changed += 1
                elif sh in ("wall_torch", "soul_wall_torch", "redstone_wall_torch", "copper_wall_torch", "ladder", "wall_lamp", "candle_sconce",
                            "flower_box") or (sh in FURN_WALL and nm(s).startswith("onepiece:")) or sh.endswith("_wall_banner") or sh.endswith("_wall_sign") or sh.endswith("wall_fan") \
                        or sh.endswith("_wall_head") or sh.endswith("_wall_skull"):
                    f = pr.get("facing", "north")
                    dx, dz = DIRV.get(f, (0, -1))
                    behind = self.get(x - dx, y, z - dz)
                    if side_sturdy(behind): continue
                    loose = sh == "ladder" or "banner" in sh or "sign" in sh
                    if loose and behind is not None and kind(behind) != "water": continue
                    if sh == "ladder" and any(self.get(x, y + k, z) and short(self.get(x, y + k, z)) == "ladder" for k in (-1, 1)) \
                            and not any(side_sturdy(self.get(x - ex, y, z - ez)) for ex, ez in DIRV.values()):
                        continue  # part of a ladder column; it hangs with the rest
                    for f2, (ex, ez) in DIRV.items():
                        if side_sturdy(self.get(x - ex, y, z - ez)):
                            B[p] = withp(s, facing=f2); self.rep["turned to wall " + sh] += 1; break
                    else:
                        if sh.endswith("wall_torch") and center_top(below):
                            B[p] = "minecraft:" + sh.replace("wall_torch", "torch"); self.rep["torch stood up"] += 1
                        elif sh.endswith("_wall_banner") and above is not None:
                            pass  # a banner hung from a beam is fine
                        else:
                            self.kill(p, "floating " + sh); changed += 1
            if not changed: break

    def hang(self, p, s, quiet=False):
        """Make a hanging lantern/chandelier really hang: chain it up to a ceiling within 12 blocks,
        else stand it on the floor, else remove it. Returns True if it stays."""
        x, y, z = p
        above = self.get(x, y + 1, z)
        if bottom_sturdy(above) and short(above) != "iron_chain":
            self.B[p] = s; return True
        yy = y + 1
        while yy <= y + 12:
            a = self.get(x, yy, z)
            if a is not None and short(a) == "iron_chain":
                yy += 1; continue
            if a is None:
                yy += 1; continue
            break
        a = self.get(x, yy, z)
        if a is not None and bottom_sturdy(a) and yy <= y + 12:
            for k in range(y + 1, yy):
                self.B[(x, k, z)] = "minecraft:iron_chain[axis=y,waterlogged=false]"
            self.B[p] = s
            if yy > y + 1 and not quiet: self.rep["chain added"] += 1
            return True
        below = self.get(x, y - 1, z)
        sh = short(s)
        if "lantern" in sh or sh == "bubble_lamp":
            if center_top(below):
                self.B[p] = withp(s, hanging="false"); self.rep["lantern set on floor"] += 1; return True
            if self.drop_to_floor(p, withp(s, hanging="false"), center_top):
                self.rep["lantern dropped to floor"] += 1; return True
        if not quiet: self.kill(p, "floating " + sh)
        return False

    def drop_to_floor(self, p, s, ok, depth=3):
        x, y, z = p
        for k in range(1, depth + 1):
            q = (x, y - k, z)
            if self.get(*q) is not None: return False
            if ok(self.get(x, y - k - 1, z)):
                self.B[q] = s; self.B[p] = self.vacant(p)
                return True
        return False

    def farms(self):
        """Farmland needs water within 4 blocks or it dries to dirt: turn the odd farmland cell into a water hole.
        In snowy builds the hole gets a slab lid so it doesn't freeze."""
        B = self.B
        farm = sorted(p for p, s in B.items() if s and short(s) == "farmland")
        if not farm: return
        water = {p for p, s in B.items() if s and kind(s) == "water"}
        snowy = sum(1 for s in B.values() if s and "snow" in s) > 200
        for (x, y, z) in farm:
            wet = any((x + dx, yy, z + dz) in water for dx in range(-4, 5) for dz in range(-4, 5) for yy in (y, y + 1))
            if wet: continue
            B[(x, y, z)] = "minecraft:water[level=0]"; water.add((x, y, z))
            B[(x, y + 1, z)] = "minecraft:spruce_slab[type=bottom,waterlogged=false]" if snowy else "minecraft:air"
            self.rep["water added to farm"] += 1

    # 4 ---------------------------------------------------------
    def floating(self):
        B = self.B
        solid = {p for p, s in B.items() if s is not None and kind(s) not in ("air", "water")}
        if not solid: return
        ymin = min(p[1] for p in solid)
        if self.mode in ("land", "sea"): base = 0
        elif self.mode == "seafloor": base = ymin + 2
        else: base = ymin + 1
        seen = set(); comps = []
        for p in solid:
            if p in seen: continue
            comp = [p]; seen.add(p); i = 0
            while i < len(comp):
                x, y, z = comp[i]; i += 1
                for d in N26:  # diagonal neighbours count: domes and curved walls are only joined at their corners
                    q = (x + d[0], y + d[1], z + d[2])
                    if q in solid and q not in seen:
                        seen.add(q); comp.append(q)
            comps.append(comp)
        for comp in comps:
            if any(q[1] <= base for q in comp): continue
            if self.mode in ("sea", "seafloor") and any(kind(B.get((q[0] + dx, q[1] + dy, q[2] + dz), "minecraft:air")) == "water"
                                                         for q in comp for dx, dy, dz in ((1, 0, 0), (-1, 0, 0), (0, 0, 1), (0, 0, -1), (0, -1, 0))):
                continue
            if len(comp) > 60:
                self.rep["big floating part kept"] += 1
                continue
            if all("bubble_glass" in B[q] for q in comp):    # Sabaody's soap bubbles are meant to float
                self.rep["floating bubble kept"] += 1
                continue
            # small and touching nothing: if it is close above something, give it a post; else remove it
            hangs = any(any(t in B[q] for t in ("lantern", "chain", "chandelier", "lamp", "bubble_lamp")) for q in comp)
            if hangs and self.hang_up(comp): self.rep["hung floating part from ceiling"] += 1; continue
            fixed = self.prop_up(comp)
            if fixed: self.rep["propped up floating part"] += 1
            else:
                for q in comp: self.kill(q, "floating bit")

    def hang_up(self, comp):
        """A floating chandelier or lamp: run a chain from its top block up to a ceiling within 16 blocks."""
        cs = set(comp)
        topy = max(q[1] for q in comp)
        tops = sorted(q for q in comp if q[1] == topy)
        for (x, y, z) in tops:
            for k in range(1, 17):
                a = self.get(x, y + k, z)
                if a is None: continue
                if (x, y + k, z) in cs: break
                if bottom_sturdy(a):
                    for j in range(1, k): self.B[(x, y + j, z)] = "minecraft:iron_chain[axis=y,waterlogged=false]"
                    return True
                break
        return False

    def prop_up(self, comp):
        B = self.B; cs = set(comp)
        lows = {}
        for (x, y, z) in comp:
            if (x, z) not in lows or y < lows[(x, z)]: lows[(x, z)] = y
        posts = []
        for (x, z), y in lows.items():
            for k in range(1, 5):
                q = (x, y - k, z)
                if q in cs: break
                s = self.get(*q)
                if s is not None:
                    if top_sturdy(s) or center_top(s): posts.append(((x, z), y, k)); break
                    else: break
        if not posts: return False
        wood = "spruce"
        for q in comp:
            m = re.search(r"minecraft:([a-z_]+?)_(planks|stairs|slab|log|fence|trapdoor)", B[q])
            if m and m.group(1) in ("oak", "spruce", "birch", "jungle", "acacia", "dark_oak", "mangrove", "cherry", "crimson", "warped", "pale_oak"):
                wood = m.group(1); break
        fence = f"minecraft:{wood}_fence[east=false,north=false,south=false,waterlogged=false,west=false]"
        posts.sort(key=lambda t: t[2])
        for (x, z), y, k in posts[:max(1, len(posts) // 3)]:
            for j in range(1, k): B[(x, y - j, z)] = fence
        return True

    # 2 ---------------------------------------------------------
    def seal_hull(self):
        """Sea builds float with the top water block at y 0, so the world's sea fills every unset cell at y <= 0. A hull
        drawn with only diagonal joins, or an open stern, lets that sea into the dry hold below the waterline. Close the
        gap cells (air at y <= 0 touching the sea and at least two solid blocks) with the hull material around them."""
        B = self.B
        sea = lambda q: B.get(q) is None
        cover = collections.defaultdict(lambda: -999)  # highest solid block in each column: air under it is inside the hull
        for (x, y, z), s in B.items():
            if s is not None and kind(s) in ("full", "part") and y > cover[(x, z)]: cover[(x, z)] = y
        for _ in range(24):
            fills = {}
            for p, s in B.items():
                if s is None or p[1] > 0 or kind(s) != "air": continue
                x, y, z = p
                nb = ((x + 1, y, z), (x - 1, y, z), (x, y, z + 1), (x, y, z - 1), (x, y - 1, z), (x, y + 1, z))
                if not any(sea(q) for q in nb[:5]): continue
                solid = [B[q] for q in nb if B.get(q) is not None and kind(B[q]) in ("full", "part")]
                if not solid or len(solid) < 2 and cover[(x, z)] <= y: continue
                full = [t for t in solid if kind(t) == "full"]
                pick = collections.Counter(nm(t) for t in (full or solid)).most_common(1)[0][0]
                if kind(pick) != "full": pick = "minecraft:dark_oak_planks"
                fills[p] = pick
            if not fills: break
            B.update(fills); self.rep["sealed hull gap"] += len(fills)

    def waterlog(self):
        """Blocks sitting under the build's own water (a fence post in a pool, the hull of a ship below the waterline) get
        waterlogged, so they don't show dry pockets. Land builds are placed with the world's waterlogging switched off
        (tiler: liquid_settings), so a lamp or wall standing at sea level stays dry and can't leak sea water onto a plaza."""
        B = self.B
        wet = {p for p, s in B.items() if s is not None and kind(s) == "water"}
        deep = {p for p in wet if (p[0], p[1] + 1, p[2]) in wet}
        # sea builds float with the top water block at y 0, seafloor builds sit wholly under the sea: unset cells there are sea
        sea_top = 0 if self.mode == "sea" else 10 ** 6 if self.mode == "seafloor" else None
        for p, s in list(B.items()):
            if s is None or "waterlogged=false" not in s: continue
            x, y, z = p
            side = ((x + 1, y, z), (x - 1, y, z), (x, y, z + 1), (x, y, z - 1))
            if any(B.get(q) is not None and kind(B[q]) == "air" for q in side + ((x, y - 1, z),)): continue  # would leak into a dry room
            if (x, y + 1, z) in wet or any(q in deep for q in side) or (sea_top is not None and y <= sea_top and any(B.get(q) is None for q in side + ((x, y - 1, z), (x, y + 1, z)))):
                B[p] = s.replace("waterlogged=false", "waterlogged=true"); self.rep["waterlogged under water"] += 1

    def connections(self):
        B = self.B
        for p, s in B.items():
            if s is None: continue
            sh = short(s)
            pane, fen, wal = is_pane(sh), is_fence(sh), is_wall(sh)
            if not (pane or fen or wal): continue
            x, y, z = p
            con = {}
            for dx, dy, dz, f in H4:
                n = B.get((x + dx, y, z + dz))
                c = False
                if n is not None and nm(n) not in AIRS:
                    nsh = short(n)
                    # the game joins a pane or fence to any face that is sturdy toward it: full blocks, but also the
                    # tall back of a stair and a double slab (a window next to a stair moulding showed a gap, ryan 11-01)
                    np_ = props(n)
                    back = (nsh.endswith("_stairs") and np_.get("facing") == OPP[f]) or (nsh.endswith("_slab") and np_.get("type") == "double")
                    if pane: c = is_pane(nsh) or (kind(n) in ("full", "glass") and "leaves" not in nsh) or is_wall(nsh) or back
                    elif fen: c = (is_fence(nsh) and (("nether" in nsh) == ("nether" in sh))) or "fence_gate" in nsh or (kind(n) in ("full",) and "leaves" not in nsh) or back
                    else: c = is_wall(nsh) or is_pane(nsh) or "fence_gate" in nsh or kind(n) in ("full", "glass")
                con[f] = c
            if pane and "glass" in sh and not any(con.values()) and \
                    not any(B.get((x, y + d, z)) and is_pane(short(B.get((x, y + d, z)))) for d in (-1, 1)):
                B[p] = self.vacant(p); self.rep["floating glass panes removed"] += 1; continue
            if pane or fen:
                s2 = withp(s, **{f: ("true" if c else "false") for f, c in con.items()})
            else:
                above = B.get((x, y + 1, z))
                tall = above is not None and kind(above) == "full"
                vals = {f: (("tall" if tall else "low") if c else "none") for f, c in con.items()}
                straight = (con["north"] and con["south"] and not con["east"] and not con["west"]) or \
                           (con["east"] and con["west"] and not con["north"] and not con["south"])
                up = not straight or (above is not None and nm(above) not in AIRS and not tall)
                s2 = withp(s, up=("true" if up else "false"), **vals)
            if s2 != s:
                B[p] = s2; self.rep["connected " + ("panes" if pane else "fences" if fen else "walls")] += 1

    # 6 --------------------------------------------------------- ryan's 2026-11-01 review
    WOOD_MAP = (("dark_oak", "dark_oak"), ("pale_oak", "birch"), ("oak", "oak"), ("spruce", "spruce"), ("birch", "birch"),
                ("sakura", "sakura"), ("cherry", "sakura"), ("palm", "palm"), ("jungle", "palm"), ("bamboo", "palm"),
                ("acacia", "oak"), ("mangrove", "dark_oak"), ("crimson", "dark_oak"), ("warped", "dark_oak"), ("adam", "oak"))

    def wood_near(self, p, first=None):
        """The furniture wood (oak/spruce/birch/dark_oak/sakura/palm) that fits a spot: the block's own wood, else the floor's
        or the nearest wooden wall's, else spruce."""
        x, y, z = p
        cands = [first] if first else []
        cands += [self.B.get((x, y - 1, z))] + [self.B.get((x + dx, y, z + dz)) for dx, dy, dz, _ in H4] + \
                 [self.B.get((x + dx, y + 1, z + dz)) for dx, dy, dz, _ in H4]
        for s in cands:
            if not s: continue
            sh = short(s)
            if not any(t in sh for t in ("planks", "log", "wood", "stairs", "slab", "trapdoor", "fence", "door")): continue
            for k, w in self.WOOD_MAP:
                if k in sh: return w
        return "spruce"

    def furniture(self):
        """Trapdoor 'stools' floating a block off the floor become real stools, chests used as tables (a candle, pot or
        lantern on top) become tables, and chests or barrels beside a bed's pillow become nightstands (ryan: "chests with
        candles and flower pots look bad"; "floating trap doors as stools is horrible")."""
        B = self.B
        TOP = ("candle", "flower_pot", "potted_", "lantern", "skull", "head", "book_stack", "fruit_bowl", "bread_basket", "sake_set",
               "beer_mugs", "tea_set", "meat_platter", "candelabra", "decorated_pot")
        for p, s in list(B.items()):
            if s is None: continue
            sh = short(s); x, y, z = p
            if sh.endswith("trapdoor") and "iron" not in sh:
                pr = props(s)
                floor_round = sum(1 for dx, dy, dz, _ in H4 if self.get(x + dx, y, z + dz) is None and top_sturdy(B.get((x + dx, y - 1, z + dz))))
                if pr.get("half") == "top" and pr.get("open") == "false" and top_sturdy(B.get((x, y - 1, z))) \
                        and self.get(x, y + 1, z) is None and floor_round >= 2:
                    B[p] = f"onepiece:{self.wood_near(p, s)}_stool[facing={pr.get('facing', 'north')}]"
                    self.rep["trapdoor stools made real stools"] += 1
                continue
            chest = sh in ("chest", "trapped_chest")
            if not (chest or sh == "barrel"): continue
            above = self.get(x, y + 1, z)
            topped = above is not None and any(t in short(above) for t in TOP)
            bed = None
            for dx, dy, dz, f in H4:
                n = B.get((x + dx, y, z + dz))
                if n and short(n).endswith("_bed") and props(n).get("part") == "head": bed = n; break
            if bed is not None:
                face = OPP[props(bed).get("facing", "north")]  # the drawers face the room, like the bed's foot
                B[p] = f"onepiece:{self.wood_near(p)}_nightstand[facing={face}]"
                self.rep["nightstands instead of chests/barrels"] += 1
            elif chest and topped:
                B[p] = f"onepiece:{self.wood_near(p)}_table[facing=north]"
                self.rep["tables instead of chests"] += 1

    def beds(self):
        """Every bed: two halves that agree (the foot behind the head), the pillow end against a wall (ryan: "beds are placed
        backwards, the pillow always needs to be up against the wall") and a floor under both halves."""
        B = self.B
        seen = set()
        heads = [(p, s) for p, s in B.items() if s and short(s).endswith("_bed") and props(s).get("part") == "head"]
        feet = {p: s for p, s in B.items() if s and short(s).endswith("_bed") and props(s).get("part") == "foot"}
        def wallish(q):
            s = B.get(q)
            return s is not None and (kind(s) in ("full", "glass") or is_pane(short(s)) or is_wall(short(s)) or
                                      short(s).endswith(("_nightstand", "_table", "_counter", "bookshelf")))
        for hp, hs in heads:
            if hp in seen: continue
            name = nm(hs); f = props(hs).get("facing", "north")
            x, y, z = hp
            dx, dz = DIRV[f]
            fp = (x - dx, y, z - dz)
            if not (fp in feet and nm(feet[fp]) == name):
                # the halves disagree: find this head's foot beside it and turn the bed to match it
                fp = None
                for ddx, ddy, ddz, d in H4:
                    q = (x + ddx, y, z + ddz)
                    if q in feet and nm(feet[q]) == name and q not in seen:
                        fp, f = q, OPP[d]; dx, dz = DIRV[f]; break
                if fp is None:
                    # a lone pillow half (a window or prop was drawn over its foot): give it its foot back when that
                    # cell is only air or a stray pane, otherwise take the half bed away
                    fp = (x - dx, y, z - dz); fs = B.get(fp)
                    if fs is None or nm(fs) in AIRS or is_pane(short(fs)) or passable(fs):
                        B[fp] = f"{name}[facing={f},occupied=false,part=foot]"; feet[fp] = B[fp]
                        self.rep["lone bed halves given their foot"] += 1
                    else:
                        self.kill(hp, "half beds"); continue
                else:
                    self.rep["beds with mismatched halves joined"] += 1
            seen.update((hp, fp))
            beyond_head, beyond_foot = (x + dx, y, z + dz), (fp[0] - dx, y, fp[2] - dz)
            if not wallish(beyond_head) and wallish(beyond_foot):
                hp, fp, f = fp, hp, OPP[f]
                self.rep["beds turned so the pillow is against the wall"] += 1
            B[hp] = f"{name}[facing={f},occupied=false,part=head]"
            B[fp] = f"{name}[facing={f},occupied=false,part=foot]"
            for q in (hp, fp):
                below = (q[0], q[1] - 1, q[2])
                bs = B.get(below)
                if not top_sturdy(bs) or kind(bs) == "glass":  # glass under a bed reads as a hole (ryan's screenshot)
                    fl = None
                    for ddx, ddy, ddz, d in H4 + ((2, 0, 0, ""), (-2, 0, 0, ""), (0, 0, 2, ""), (0, 0, -2, "")):
                        n = B.get((below[0] + ddx, below[1], below[2] + ddz))
                        if n and kind(n) == "full" and not short(n).endswith("_bed"): fl = n; break
                    B[below] = fl or "minecraft:spruce_planks"
                    self.rep["floor filled under beds"] += 1

    def eaves(self):
        """Close the slot between a wall's top and a roof that starts higher up (ryan: "gaps in the eaves on houses and
        buildings"). A bottom roof stair with 1-3 air cells under it, then the top of a wall whose outer side is open air
        under the overhang: the air is filled with the wall's block."""
        B = self.B
        fill = {}
        for p, s in B.items():
            if not s or not short(s).endswith("_stairs"): continue
            pr = props(s)
            if pr.get("half") != "bottom": continue
            f = pr.get("facing", "north")
            ox, oz = DIRV[OPP[f]]  # down the slope, outwards
            x, y, z = p
            k = 0
            while k < 4 and self.get(x, y - 1 - k, z) is None and (x, y - 1 - k, z) not in fill: k += 1
            if not 1 <= k <= 3: continue
            yw = y - 1 - k
            w = B.get((x, yw, z))
            if not w or kind(w) != "full" or "leaves" in w or short(w).endswith(("_slab", "_stairs")): continue
            if self.get(x + ox, yw, z + oz) is not None: continue        # the wall's outer face is open
            if any(self.get(x + ox, yy, z + oz) is not None for yy in range(yw, y - 1)): continue  # open under the overhang
            # the wall runs on either side (a real wall top, not a lone post or a chimney)
            sx, sz = abs(oz), abs(ox)
            if not (B.get((x + sx, yw, z + sz)) and kind(B.get((x + sx, yw, z + sz))) == "full" or
                    B.get((x - sx, yw, z - sz)) and kind(B.get((x - sx, yw, z - sz))) == "full"):
                continue
            blk = w
            if any(t in short(w) for t in ("log", "_wood", "stem", "hyphae", "pillar")):
                under = B.get((x, yw - 1, z))
                blk = under if under and kind(under) == "full" and not any(t in short(under) for t in ("log", "_wood", "stem")) else w
            for j in range(1, k + 1): fill[(x, yw + j, z)] = blk
        for q, b in fill.items():
            B[q] = b
        if fill: self.rep["eave gaps closed"] += len(fill)

    PATHS = ("dirt_path", "gravel", "cobblestone", "stone_bricks", "andesite", "polished_", "bricks", "packed_mud", "mud_bricks",
             "cut_sandstone", "smooth_sandstone", "smooth_stone", "tuff", "deepslate_tiles", "stone_tile", "terracotta", "planks")
    SOILS = ("grass_block", "dirt", "coarse_dirt", "podzol", "rooted_dirt", "moss_block", "mycelium")

    def doors(self):
        """Every door can be walked up to (ryan: "houses have no easy access to the doors, such as paths and stairways"):
        a door that opens over a drop gets stairs down to the ground below it, and a door at ground level on bare ground
        gets a dirt path to the nearest street or paved block."""
        if self.mode == "sea": self.blind_doors()
        if self.mode not in ("land", "sky"): return
        B = self.B
        def free(q):  # air, or (land) untouched sky above the ground
            s = B.get(q)
            return (s is None and q[1] >= 0) or (s is not None and nm(s) in AIRS) or (s is not None and passable(s) and kind(s) != "water")
        def floor(s):
            return s is not None and (top_sturdy(s) or short(s).endswith(("_stairs", "_slab")) or short(s) in ("dirt_path", "farmland"))
        doors = [(p, s) for p, s in B.items() if s and short(s).endswith("_door") and "trap" not in short(s) and props(s).get("half") == "lower"]
        for (x, y, z), s in doors:
            f = props(s).get("facing", "north")
            for side in (f, OPP[f]):
                dx, dz = DIRV[side]
                c = (x + dx, y, z + dz)
                fs = B.get(c)
                if fs and not free(c) and free((c[0], y + 1, c[2])) and \
                        any(short(fs).startswith(t) for t in self.SOILS + ("sand", "red_sand", "snow_block", "island_cloud", "gravel")):
                    # the ground outside is a block higher than the door: dig a step down to it
                    B[c] = "minecraft:air"
                    if any(short(B.get((c[0], y - 1, c[2])) or "").startswith(t) for t in self.SOILS):
                        B[(c[0], y - 1, c[2])] = "minecraft:dirt_path"
                    self.rep["ground dug away in front of doors"] += 1
                c_up = (c[0], y + 1, c[2])
                if not (free(c) and free(c_up)): self.open_doorway(x, y, z, dx, dz, free, floor)
                if not (free(c) and free((c[0], y + 1, c[2]))): continue
                if floor(B.get((c[0], y - 1, c[2]))):
                    self.path_from(c)
                    continue
                # a drop: how far down is the ground?
                g = None
                for k in range(1, 13):
                    q = (c[0], y - 1 - k, c[2])
                    if not free(q):
                        g = q[1]; break
                if g is not None and kind(B.get((c[0], g, c[2])) or "minecraft:air") == "water":
                    self.landing(x, y, z, dx, dz, g, free)
                    continue
                if g is None or not floor(B.get((c[0], g, c[2]))) and B.get((c[0], g, c[2])) is not None: continue
                base = B.get((x, y - 1, z))
                base = base if base and kind(base) == "full" else "minecraft:cobblestone"
                stair = "minecraft:stone_brick_stairs" if "stone" in short(base) or "cobble" in short(base) else \
                        "minecraft:" + self.wood_near((x, y - 1, z)) + "_stairs" if self.wood_near((x, y - 1, z)) in ("oak", "spruce", "birch", "dark_oak") else "minecraft:stone_brick_stairs"
                plan, top, k = [], y - 1, 1
                ok = True
                while top > g + 0 and k <= 12:
                    q = (x + dx * k, top, z + dz * k)
                    gq = None
                    for kk in range(0, 14):
                        r = (q[0], top - kk, q[2])
                        if not free(r): gq = r[1]; break
                    if gq is not None and gq >= top: break   # the ground came up to meet the stairs
                    if not all(free((q[0], top + h, q[2])) for h in range(0, 3)): ok = False; break
                    plan.append((q, gq if gq is not None else top - 13))
                    top -= 1; k += 1
                if not ok or not plan or len(plan) > 10: continue
                for (q, gq) in plan:
                    for yy in range(gq + 1, q[1]): B[(q[0], yy, q[2])] = base
                    B[q] = f"{stair}[facing={OPP[side]},half=bottom]"
                self.rep["doors given steps down to the ground"] += 1
                last = plan[-1][0]
                self.path_from((last[0] + dx, last[1], last[2] + dz))

    NATURAL = SOILS + ("sand", "red_sand", "snow_block", "snow", "gravel", "island_cloud", "clay", "mud")

    def open_doorway(self, x, y, z, dx, dz, free, floor):
        """A door with no standing room on one side (ryan: no easy access to the doors). Ground heaped 2 high in front
        (a dune or a hill) gets a notch dug out to open ground or a one-block step, at most 6 cells; a building wall one block thick right
        behind the door, with open floor beyond it, gets a doorway cut through. True when something was opened."""
        B = self.B
        c, cu = (x + dx, y, z + dz), (x + dx, y + 1, z + dz)
        natural = lambda q: B.get(q) is not None and short(B.get(q)).startswith(self.NATURAL)
        if natural(c) or natural(cu):
            dig = []
            for k in range(1, 7):
                q, qu = (x + dx * k, y, z + dz * k), (x + dx * k, y + 1, z + dz * k)
                # open ground, or ground one block up (a step the player can walk up)
                if free(qu) and (free(q) or natural(q)) and free((q[0], y + 2, q[2])):
                    if not dig: return False
                    for r in dig: B[r] = "minecraft:air"
                    for r in dig:
                        bl = (r[0], y - 1, r[2])
                        if r[1] == y and short(B.get(bl) or "").startswith(self.SOILS): B[bl] = "minecraft:dirt_path"
                    self.rep["ground dug away in front of doors"] += 1
                    return True
                if not all(free(r) or natural(r) for r in (q, qu)) or not floor(B.get((q[0], y - 1, q[2]))) and not natural((q[0], y - 1, q[2])):
                    return False
                dig += [r for r in (q, qu) if not free(r)]
            return False
        sc, su = B.get(c), B.get(cu)
        b2, b2u = (x + 2 * dx, y, z + 2 * dz), (x + 2 * dx, y + 1, z + 2 * dz)
        if sc and kind(sc) == "full" and free(cu) and free(b2) and free(b2u) and floor(B.get((b2[0], y - 1, b2[2])))                 and top_sturdy(B.get((c[0], y - 1, c[2]))) and not any(t in short(sc) for t in ("chest", "furnace", "crafting", "table")):
            B[c] = "minecraft:air"  # a one-block kerb or rail right across the doorway
            self.rep["kerbs opened in front of doors"] += 1
            return True
        if not (sc and su and kind(sc) == "full" and kind(su) == "full"): return False
        if any(t in short(sc) for t in ("door", "chest", "furnace", "crafting", "table", "spawner")): return False  # a bookshelf or barrel in a doorway goes
        if free(b2) and free(b2u) and floor(B.get((b2[0], y - 1, b2[2]))):
            B[c] = B[cu] = "minecraft:air"
            self.rep["doorways cut through a wall behind a door"] += 1
            return True
        return False

    def blind_doors(self):
        """Ships and sea builds: a door whose outer side is a solid block with only the ship's edge beyond it leads
        nowhere (the Baratie's kitchen doors opened into its quartz rail): wall it up with the blocks beside it."""
        B = self.B
        def solid(q): return B.get(q) is not None and kind(B[q]) == "full"
        def stand(q): return not solid(q) and not solid((q[0], q[1] + 1, q[2])) and top_sturdy(B.get((q[0], q[1] - 1, q[2])))
        for (x, y, z), s in [(p, s) for p, s in B.items() if s and short(s).endswith("_door") and "trap" not in short(s)
                             and props(s).get("half") == "lower"]:
            f = props(s).get("facing", "north")
            for side in (f, OPP[f]):
                dx, dz = DIRV[side]
                c = (x + dx, y, z + dz)
                if not solid(c): continue
                if not solid((c[0], y + 1, c[2])) and top_sturdy(B.get((c[0], y - 1, c[2]))) and stand((x + 2 * dx, y, z + 2 * dz)):
                    B[c] = "minecraft:air"  # a one-block rail or kerb across the doorway, with deck beyond: open it
                    self.rep["rail opened in front of doors"] += 1
                    break
                if stand((x + 2 * dx, y, z + 2 * dz)) or stand((x + 2 * dx, y + 1, z + 2 * dz)): continue
                sx, sz = abs(dz), abs(dx)
                lo = [B.get((x + sx * w, y, z + sz * w)) for w in (1, -1)]; hi = [B.get((x + sx * w, y + 1, z + sz * w)) for w in (1, -1)]
                lo = next((b for b in lo if b and kind(b) == "full"), None); hi = next((b for b in hi if b and kind(b) == "full"), lo)
                if not lo: continue
                B[(x, y, z)] = lo; B[(x, y + 1, z)] = hi
                self.rep["doors to nowhere walled up"] += 1
                break

    def landing(self, x, y, z, dx, dz, water_y, free):
        """A door that opens over water: a small plank landing (3 wide, 2 out) on fence posts, like a jetty step."""
        B = self.B
        wood = self.wood_near((x, y - 1, z))
        wood = wood if wood in ("oak", "spruce", "birch", "dark_oak", "jungle", "acacia", "mangrove", "cherry") else "spruce"
        sx, sz = abs(dz), abs(dx)
        cells = [(x + dx * k + sx * w, y - 1, z + dz * k + sz * w) for k in (1, 2) for w in (-1, 0, 1)]
        if not all(free(q) and free((q[0], y, q[2])) and free((q[0], y + 1, q[2])) for q in cells): return
        for q in cells: B[q] = f"minecraft:{wood}_planks"
        for w in (-1, 1):
            px, pz = x + dx * 2 + sx * w, z + dz * 2 + sz * w
            for yy in range(water_y, y - 1):
                wet = kind(B.get((px, yy, pz)) or "minecraft:air") == "water"
                if free((px, yy, pz)) or wet:
                    B[(px, yy, pz)] = f"minecraft:{wood}_fence" + ("[waterlogged=true]" if wet else "")
        self.rep["landings built where a door opens over water"] += 1

    def path_from(self, c):
        """A dirt path over bare soil from c (a cell someone stands in) to the nearest paved block, at most 16 steps."""
        B = self.B
        def top(xz, y0):  # the soil/paving under a standing cell near height y0
            for yy in (y0 - 1, y0, y0 - 2):
                s = B.get((xz[0], yy, xz[1]))
                if s and kind(s) == "full" and (B.get((xz[0], yy + 1, xz[1])) is None or passable(B.get((xz[0], yy + 1, xz[1])))):
                    return yy, s
            return None, None
        y0 = c[1]
        gy, gs = top((c[0], c[2]), y0)
        if gy is None or not any(short(gs).startswith(t) or short(gs) == t for t in self.SOILS): return
        prev = {(c[0], c[2]): None}; hgt = {(c[0], c[2]): gy}
        q = collections.deque([(c[0], c[2])]); goal = None
        while q:
            p = q.popleft()
            n0 = 0; pp = p
            while prev[pp] is not None: pp = prev[pp]; n0 += 1
            if n0 > 16: continue
            for dx, dy, dz, _ in H4:
                n = (p[0] + dx, p[1] + dz)
                if n in prev: continue
                ny, ns = top(n, hgt[p] + 1)
                if ny is None or abs(ny - hgt[p]) > 1: continue
                prev[n] = p; hgt[n] = ny
                sh = short(ns)
                if any(t in sh for t in self.PATHS) and not any(sh.startswith(t) for t in self.SOILS):
                    goal = n; q.clear(); break
                if any(sh.startswith(t) for t in self.SOILS): q.append(n)
        if goal is None: return
        p = prev[goal]; n = 0
        while p is not None:
            yy = hgt[p]
            if any(short(B.get((p[0], yy, p[1])) or "").startswith(t) for t in self.SOILS):
                B[(p[0], yy, p[1])] = "minecraft:dirt_path"
                ab = B.get((p[0], yy + 1, p[1]))
                if ab is not None and passable(ab) and nm(ab) not in AIRS: B[(p[0], yy + 1, p[1])] = "minecraft:air"
                n += 1
            p = prev[p]
        if n: self.rep["path blocks laid to doors"] += n

    # 5 ---------------------------------------------------------
    def lighting(self):
        B = self.B
        if self.mode == "seafloor": return
        cols = collections.defaultdict(list)  # (x,z) -> sorted ys of light blocking blocks
        for (x, y, z), s in B.items():
            if s is not None and blocks_light(s): cols[(x, z)].append(y)
        top = {k: max(v) for k, v in cols.items()}
        sky = self.mode in ("land", "sea", "sky")

        def covered(x, y, z):
            return top.get((x, z), -10**9) > y

        def opn(x, y, z):  # does light go through this cell?
            return not blocks_light(B.get((x, y, z)))

        # sky light reaching under roofs (only how far it gets matters: up to 7 blocks in)
        skylit = {}
        if sky:
            front = collections.deque()
            for (x, z), t in top.items():
                for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nt = top.get((x + dx, z + dz), -10**9)
                    for y in range(max(nt + 1, -2), t):
                        if opn(x, y, z) and (x, y, z) not in skylit:
                            skylit[(x, y, z)] = 14; front.append((x, y, z))
            sources = list(front)
            while front:
                x, y, z = front.popleft(); l = skylit[(x, y, z)]
                if l <= 8: continue
                for d in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
                    q = (x + d[0], y + d[1], z + d[2])
                    if q in skylit or not covered(*q) or not opn(*q): continue
                    skylit[q] = l - 1; front.append(q)
        else:  # caves: people come in through the edges of the build
            xs = [p[0] for p in B]; ys = [p[1] for p in B]; zs = [p[2] for p in B]
            x0, x1, z0, z1, y0 = min(xs), max(xs), min(zs), max(zs), min(ys)
            sources = [p for p, s in B.items() if (p[0] in (x0, x1) or p[2] in (z0, z1)) and p[1] > y0 and walk(s)]
        # rooms people can walk into from outside (sealed voids inside walls and shapes don't need lights)
        reach = set(sources)
        dq = collections.deque(sources)
        while dq and len(reach) < 3_000_000:
            x, y, z = dq.popleft()
            for d in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
                q = (x + d[0], y + d[1], z + d[2])
                if q in reach: continue
                if sky and not covered(*q): continue
                if q not in B and not sky: continue
                if not walk(B.get(q)): continue
                reach.add(q); dq.append(q)
        if not sources: reach = None
        light = {}

        def spread(src, l0):
            if l0 <= 1: return
            dq = collections.deque()
            x, y, z = src
            if light.get(src, 0) < l0: light[src] = l0
            dq.append((src, l0))
            while dq:
                (x, y, z), l = dq.popleft()
                if l <= 1: continue
                for d in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
                    q = (x + d[0], y + d[1], z + d[2])
                    if light.get(q, 0) >= l - 1 or not opn(*q): continue
                    light[q] = l - 1; dq.append((q, l - 1))

        for p, s in list(B.items()):
            if s is None: continue
            l = light_of(s)
            if l: spread(p, l)
        # indoor floor cells
        dark = set()
        for (x, y, z), s in B.items():
            if s is None or not top_sturdy(s): continue
            c = (x, y + 1, z)
            if not passable(B.get(c)) or not passable(B.get((x, y + 2, z))): continue
            cs = B.get(c)
            if cs is not None and kind(cs) == "water": continue
            if not covered(*c): continue
            if sky and skylit.get(c, 0) >= 8: continue
            if reach is not None and c not in reach: continue
            if self.mode in ("land", "sea") and y + 1 < 0 and self.sid not in UNDERGROUND: continue
            if light.get(c, 0) < MIN_LIGHT: dark.add(c)
        self.rep["dark floor cells before"] = len(dark)
        failed = set()
        placed = 0
        while dark:
            p0 = min(dark)
            # the dark patch around p0 (within 6 blocks), light its middle
            patch = [p0]; seen = {p0}; i = 0
            while i < len(patch):
                x, y, z = patch[i]; i += 1
                for dx in (-1, 0, 1):
                    for dz in (-1, 0, 1):
                        for dy in (-1, 0, 1):
                            q = (x + dx, y + dy, z + dz)
                            if q in dark and q not in seen and max(abs(q[0] - p0[0]), abs(q[2] - p0[2])) <= 6 and abs(q[1] - p0[1]) <= 2:
                                seen.add(q); patch.append(q)
            cx = sum(q[0] for q in patch) / len(patch); cz = sum(q[2] for q in patch) / len(patch)
            patch.sort(key=lambda q: (q[0] - cx) ** 2 + (q[2] - cz) ** 2 + (q[1] - p0[1]) ** 2 * 4)
            done = None
            for c in patch[:12]:
                done = self.place_light(c)
                if done: break
            if not done:
                done = self.wall_light(patch)
            if done:
                for q, l in done: spread(q, l)
                placed += 1
                dark = {q for q in dark if light.get(q, 0) < MIN_LIGHT}
            else:
                for q in patch: dark.discard(q); failed.add(q)
            if placed > 4000: break
        self.rep["lights added"] = placed
        self.rep["dark floor cells left"] = len(failed)

    def place_light(self, c):
        """Put a light above floor cell c: chandelier in tall rooms, hanging lantern in mid rooms, ceiling lamp in low ones."""
        B = self.B; x, y, z = c
        h = 1
        while h < 30 and self.get(x, y + h, z) is None:
            h += 1
        ceil = self.get(x, y + h, z)
        if ceil is None or h >= 30: return self.lamp_post(c)
        if not bottom_sturdy(ceil):
            sh = short(ceil)
            if sh.endswith("_slab") and props(ceil).get("type") == "top":
                B[(x, y + h, z)] = withp(ceil, type="double")
            elif sh.endswith("_stairs") and props(ceil).get("half") == "top":
                return None
            else:
                return None
        st = self.style
        if h >= 6:  # hang it low (3 blocks over heads): light spreads 1 level per block, so low lights reach further
            ly = y + 4
            for k in range(ly + 1, y + h): B[(x, k, z)] = "minecraft:iron_chain[axis=y,waterlogged=false]"
            B[(x, ly, z)] = st["grand"]
            return [((x, ly, z), light_of(st["grand"]))]
        if h >= 4:
            B[(x, y + h - 1, z)] = st["hang"]
            return [((x, y + h - 1, z), light_of(st["hang"]))]
        if h >= 2:
            B[(x, y + h - 1, z)] = st["flush"]
            return [((x, y + h - 1, z), light_of(st["flush"]))]
        return None

    def lamp_post(self, c):
        """No ceiling to hang from (a huge cavern or hall): a lamp post on the floor."""
        x, y, z = c
        if any(self.get(x, y + k, z) is not None for k in range(0, 5)): return None
        fen = "minecraft:dark_oak_fence[east=false,north=false,south=false,waterlogged=false,west=false]"
        for k in range(0, 3): self.B[(x, y + k, z)] = fen
        lan = self.style["hang"].replace("hanging=true", "hanging=false") if "lantern" in self.style["hang"] else "minecraft:lantern[hanging=false,waterlogged=false]"
        self.B[(x, y + 3, z)] = lan
        return [((x, y + 3, z), light_of(lan))]

    def wall_light(self, patch):
        B = self.B
        for (x, y, z) in patch:
            for f, (dx, dz) in DIRV.items():
                w = self.get(x - dx, y + 1, z - dz)
                if side_sturdy(w) and self.get(x, y + 1, z) is None:
                    s = withp(self.style["wall"], facing=f)
                    B[(x, y + 1, z)] = s
                    return [((x, y + 1, z), light_of(s))]
        return None


UNDERGROUND = {"impel_down"}
VALID = set()
try:
    VALID = set(open("/mnt/project-files/one-piece-mod/tools/landmarks/furnish/valid_blocks.txt").read().split())
except OSError:
    pass

STYLE_DEFAULT = dict(hang="minecraft:lantern[hanging=true,waterlogged=false]", grand="onepiece:chandelier[facing=north]",
                     flush="onepiece:ceiling_lamp[facing=north]", wall="onepiece:wall_lamp[facing=north]")
STYLE_DARK = dict(hang="minecraft:lantern[hanging=true,waterlogged=false]", grand="onepiece:iron_chandelier[facing=north]",
                  flush="onepiece:ceiling_lamp[facing=north]", wall="onepiece:wall_lamp[facing=north]")
STYLE_SOUL = dict(hang="minecraft:soul_lantern[hanging=true,waterlogged=false]", grand="onepiece:iron_chandelier[facing=north]",
                  flush="onepiece:ceiling_lamp[facing=north]", wall="onepiece:wall_lamp[facing=north]")
STYLE_GRAND = dict(hang="onepiece:chandelier[facing=north]", grand="onepiece:chandelier[facing=north]",
                   flush="onepiece:ceiling_lamp[facing=north]", wall="onepiece:candle_sconce[facing=north]")
STYLES = {**{k: STYLE_DARK for k in ("thriller_bark", "kuraigana_castle", "withered_forest", "impel_down", "freezing_hell_cells",
                                      "eternal_hell_vault", "baltigo", "udon_prison", "hachinosu", "navarone", "marine_base", "g5_base",
                                      "punk_hazard_lab", "god_valley", "banaro_island", "void_century_ruins", "tequila_wolf", "sunken_galleon")},
          **{k: STYLE_SOUL for k in ("blazing_hell_furnace",)},
          **{k: STYLE_GRAND for k in ("alubarna_palace", "whole_cake_chateau", "dressrosa_palace", "mary_geoise", "pangaea_castle",
                                       "celestial_mansion", "ryugu_palace", "mirror_hall", "corrida_colosseum", "drum_castle", "ohara_library",
                                       "tower_of_justice", "marineford", "shandora", "newkama_land", "flower_capital", "amazon_lily",
                                       "auction_house", "mokomo_dukedom", "toy_house")}}


def finish(b, mode="land", sid="", light=True):
    f = Finisher(b, mode, sid, STYLES.get(sid, STYLE_DEFAULT))
    f.rename()
    f.clouds()
    f.supports()
    f.floating()
    f.supports()
    f.furniture()
    f.beds()
    f.eaves()
    f.doors()
    f.farms()
    if light: f.lighting()
    f.connections()
    # lights, steps and joined fences can open a new eave slot or a wall at a pillow end: check those two again last
    f.beds()
    f.eaves()
    if mode == "sea": f.seal_hull()
    f.waterlog()
    return dict(f.rep)

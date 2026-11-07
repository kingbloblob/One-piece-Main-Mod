"""Underground cave zones and blocks (package com.onepiecemod.underground).

Run:  python3 gen_underground.py <path to a source/ copy>
Writes only files owned by the underground feature: block textures/models/blockstates/items, block loot,
lang (assets/onepiece_underground), the cave-zone features and placed features, processor lists, the Sea King
fossil templates, the biome tag has_underground_caves. Appends its ids to the shared minecraft mineable tag.
Structures are made by make_structures.py.
"""
import json, math, os, random, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'deco'))
sys.path.insert(0, os.path.join(HERE, '..', 'worldgen'))
import textures as T  # noqa: E402
from kit import B  # noqa: E402

SRC = sys.argv[1] if len(sys.argv) > 1 else '/mnt/project-files/one-piece-mod/source'
RES = os.path.join(SRC, 'src/main/resources')
A = os.path.join(RES, 'assets/onepiece')
D = os.path.join(RES, 'data/onepiece')

NAMES = {
    'sea_prism_stone': 'Sea Prism Stone',
    'sea_prism_crystal': 'Sea Prism Crystal',
    'sulfur_vent': 'Sulfur Vent',
    'fossil_rock': 'Fossil Rock',
    'ancient_glyph_stone': 'Ancient Glyph Stone',
}


def wjson(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)
        f.write('\n')


def save(img, name):
    p = os.path.join(A, 'textures/block', name + '.png')
    os.makedirs(os.path.dirname(p), exist_ok=True)
    img.save(p)


# ---------------------------------------------------------------- textures

def sea_prism_stone():
    r = T.rng('sea_prism_stone'); img = T.new()
    for y in range(16):
        for x in range(16):
            v = 0.5 + 0.5 * math.sin(x * 0.9 + y * 0.4) * math.cos(y * 0.7 - x * 0.2)
            img.putpixel((x, y), T.mix('#8fb8c8', '#c9e6ee', v * 0.7 + r.uniform(-0.12, 0.12)))
    for _ in range(9):  # little glinting crystal grains
        x, y = r.randrange(16), r.randrange(16)
        img.putpixel((x, y), T.shade('#e9fbff', 1))
    for _ in range(6):
        x, y = r.randrange(16), r.randrange(16)
        img.putpixel((x, y), T.shade('#5f8fa3', 1))
    return img


def sea_prism_crystal():
    img = T.new()
    shards = [(7, 1, 2, '#bff4ff'), (3, 6, 1, '#7fd9f0'), (11, 5, 1, '#9fe6f7'), (5, 9, 1, '#6cc9e6'), (10, 9, 1, '#8fe1f5')]
    for (cx, top, half, col) in shards:
        for y in range(top, 16):
            w = half if y > top + 1 else max(0, half - 1)
            for x in range(cx - w, cx + w + 1):
                if 0 <= x < 16:
                    f = 1.15 if x == cx - w else 0.85 if x == cx + w else 1.0
                    img.putpixel((x, y), T.shade(col, f))
        img.putpixel((cx, top), T.shade('#ffffff', 1))
    return img


def sulfur_vent_side():
    r = T.rng('sulfur_vent_side'); img = T.new()
    T.noise(img, r, '#3d3a36', 0.14)
    for x in range(16):  # streaks of yellow sulfur crust running down
        if r.random() < 0.35:
            y0 = r.randrange(0, 4)
            for y in range(y0, y0 + r.randrange(2, 7)):
                img.putpixel((x, y), T.shade('#d9c234', r.uniform(0.8, 1.1)))
    for x in range(16):
        img.putpixel((x, 0), T.shade('#e8d23a', r.uniform(0.9, 1.1)))
    return img


def sulfur_vent_top():
    r = T.rng('sulfur_vent_top'); img = T.new()
    T.noise(img, r, '#4a4640', 0.14)
    for y in range(16):
        for x in range(16):
            d = math.hypot(x - 7.5, y - 7.5)
            if d < 7:
                img.putpixel((x, y), T.mix('#e8d23a', '#7a6a20', d / 7 + r.uniform(-0.1, 0.1)))
            if d < 3.2:
                img.putpixel((x, y), T.mix('#ff8a20', '#ffe070', d / 3.2))
            if d < 1.5:
                img.putpixel((x, y), T.shade('#2a1a0a', 1))
    return img


def fossil_rock():
    r = T.rng('fossil_rock'); img = T.new()
    T.noise(img, r, '#8a8780', 0.12)
    bone = '#e8e0c8'
    # a curved rib and a vertebra pressed into the stone
    for t in range(14):
        x = 2 + t; y = int(11 - 6 * math.sin(t / 13 * math.pi))
        img.putpixel((x, y), T.shade(bone, r.uniform(0.9, 1.05)))
        if t % 4 == 0 and y + 1 < 16: img.putpixel((x, y + 1), T.shade(bone, 0.85))
    for (x, y) in ((3, 2), (4, 2), (3, 3), (4, 3), (5, 3), (12, 12), (13, 12), (12, 13)):
        img.putpixel((x, y), T.shade(bone, 0.95))
    return img


def ancient_glyph_stone():
    r = T.rng('ancient_glyph_stone'); img = T.new()
    T.noise(img, r, '#2e3236', 0.1)
    for x in range(16):
        img.putpixel((x, 0), T.shade('#202326', 1)); img.putpixel((x, 15), T.shade('#202326', 1))
    for y in range(16):
        img.putpixel((0, y), T.shade('#202326', 1)); img.putpixel((15, y), T.shade('#202326', 1))
    glyph = '#5fa0a8'  # carved script, faintly glowing teal like the Poneglyph letters
    for row in (2, 6, 10):
        x = 2
        while x < 13:
            kind = r.randrange(4)
            if kind == 0:
                for d in range(3): img.putpixel((x, row + d), T.shade(glyph, 1))
                img.putpixel((x + 1, row), T.shade(glyph, 1))
            elif kind == 1:
                img.putpixel((x, row + 1), T.shade(glyph, 1)); img.putpixel((x + 1, row), T.shade(glyph, 1)); img.putpixel((x + 1, row + 2), T.shade(glyph, 1))
            elif kind == 2:
                for d in range(2): img.putpixel((x + d, row + 2), T.shade(glyph, 1))
                img.putpixel((x, row), T.shade(glyph, 1))
            else:
                img.putpixel((x, row), T.shade(glyph, 1)); img.putpixel((x + 1, row + 1), T.shade(glyph, 1)); img.putpixel((x, row + 2), T.shade(glyph, 1))
            x += 3
    return img


# ---------------------------------------------------------------- blocks

def cube_all(i):
    wjson(f'{A}/blockstates/{i}.json', {"variants": {"": {"model": f"onepiece:block/{i}"}}})
    wjson(f'{A}/models/block/{i}.json', {"parent": "minecraft:block/cube_all", "textures": {"all": f"onepiece:block/{i}"}})
    item_block(i)


def item_block(i, model=None):
    wjson(f'{A}/items/{i}.json', {"model": {"type": "minecraft:model", "model": model or f"onepiece:block/{i}"}})


def drop_self(i):
    return {"type": "minecraft:block", "pools": [{"rolls": 1, "entries": [{"type": "minecraft:item", "name": f"onepiece:{i}"}],
                                                 "condition": {"type": "minecraft:survives_explosion"}}],
            "random_sequence": f"onepiece:blocks/{i}"}


def silk_or(i, entries):
    return {"type": "minecraft:block", "pools": [{"rolls": 1, "entries": [{"type": "minecraft:alternatives", "children": [
        {"type": "minecraft:item", "condition": "minecraft:tool/can_silk_touch", "name": f"onepiece:{i}"}] + entries}]}],
            "random_sequence": f"onepiece:blocks/{i}"}


def count(lo, hi, fortune=True):
    m = [{"type": "minecraft:set_count", "count": {"type": "minecraft:uniform", "min": lo, "max": hi}}]
    if fortune: m.append({"type": "minecraft:apply_bonus", "enchantment": "minecraft:fortune", "formula": "minecraft:ore_drops"})
    m.append({"type": "minecraft:explosion_decay"})
    return m


def blocks():
    save(sea_prism_stone(), 'sea_prism_stone'); cube_all('sea_prism_stone')
    save(fossil_rock(), 'fossil_rock'); cube_all('fossil_rock')
    save(ancient_glyph_stone(), 'ancient_glyph_stone'); cube_all('ancient_glyph_stone')
    save(sulfur_vent_side(), 'sulfur_vent_side'); save(sulfur_vent_top(), 'sulfur_vent_top')
    wjson(f'{A}/blockstates/sulfur_vent.json', {"variants": {"": {"model": "onepiece:block/sulfur_vent"}}})
    wjson(f'{A}/models/block/sulfur_vent.json', {"parent": "minecraft:block/cube_bottom_top", "textures": {
        "top": "onepiece:block/sulfur_vent_top", "bottom": "onepiece:block/sulfur_vent_side", "side": "onepiece:block/sulfur_vent_side"}})
    item_block('sulfur_vent')
    save(sea_prism_crystal(), 'sea_prism_crystal')
    rot = {"down": (180, 0), "east": (90, 90), "north": (90, 0), "south": (90, 180), "up": (0, 0), "west": (90, 270)}
    wjson(f'{A}/blockstates/sea_prism_crystal.json', {"variants": {
        f"facing={f}": dict({"model": "onepiece:block/sea_prism_crystal"}, **({"x": x} if x else {}), **({"y": y} if y else {}))
        for f, (x, y) in rot.items()}})
    wjson(f'{A}/models/block/sea_prism_crystal.json', {"parent": "minecraft:block/cross", "textures": {"cross": "onepiece:block/sea_prism_crystal"}})
    wjson(f'{A}/models/item/sea_prism_crystal.json', {"parent": "minecraft:item/generated", "textures": {"layer0": "onepiece:block/sea_prism_crystal"}})
    item_block('sea_prism_crystal', "onepiece:item/sea_prism_crystal")

    L = os.path.join(D, 'loot_table/blocks')
    wjson(f'{L}/sea_prism_stone.json', drop_self('sea_prism_stone'))
    wjson(f'{L}/ancient_glyph_stone.json', drop_self('ancient_glyph_stone'))
    wjson(f'{L}/sea_prism_crystal.json', silk_or('sea_prism_crystal', [
        {"type": "minecraft:item", "name": "onepiece:raw_seastone", "condition": {"type": "minecraft:match_tool", "predicate": {"items": "#minecraft:cluster_max_harvestables"}},
         "modifier": count(1, 2)},
        {"type": "minecraft:item", "name": "onepiece:raw_seastone", "modifier": [
            {"type": "minecraft:set_count", "count": {"type": "minecraft:uniform", "min": 0, "max": 1}}, {"type": "minecraft:explosion_decay"}]}]))
    wjson(f'{L}/sulfur_vent.json', silk_or('sulfur_vent', [{"type": "minecraft:item", "name": "onepiece:sulfur", "modifier": count(2, 4)}]))
    fossil = silk_or('fossil_rock', [{"type": "minecraft:item", "name": "minecraft:bone", "modifier": count(1, 3)}])
    fossil["pools"].append({"rolls": 1, "condition": {"type": "minecraft:all_of", "terms": [
        {"type": "minecraft:inverted", "term": "minecraft:tool/can_silk_touch"},
        {"type": "minecraft:random_chance", "chance": 0.06}]},
        "entries": [{"type": "minecraft:item", "name": "onepiece:sea_king_scale"}]})
    wjson(f'{L}/fossil_rock.json', fossil)

    # names in their own namespace so the shared en_us.json is never touched
    wjson(os.path.join(RES, 'assets/onepiece_underground/lang/en_us.json'),
          dict({f'block.onepiece.{k}': v for k, v in NAMES.items()}, **{"itemGroup.onepiece.underground": "One Piece: Underground"}))

    # pickaxe tag is shared with other features: add our ids, keep theirs
    p = os.path.join(RES, 'data/minecraft/tags/block/mineable/pickaxe.json')
    tag = json.load(open(p)) if os.path.exists(p) else {"replace": False, "values": []}
    for i in NAMES:
        if f'onepiece:{i}' not in tag["values"]: tag["values"].append(f'onepiece:{i}')
    wjson(p, tag)


# ---------------------------------------------------------------- cave zones

def state(i, **props):
    return {"id": i, "properties": {k: str(v).lower() for k, v in props.items()}} if props else {"id": i}


def weighted(*entries):
    return {"type": "minecraft:weighted", "entries": [{"data": d, "weight": w} for d, w in entries]}


def inline(feature):
    return {"feature": feature, "placement": []}


def patch(surface, ground, veg, chance, rmin, rmax, vrange=5, depth=1, edge=0.3, replaceable="#onepiece:underground_patch_replaceable", kind="vegetation_patch"):
    f = {"type": f"minecraft:{kind}", "depth": depth, "extra_bottom_block_chance": 0.0, "extra_edge_column_chance": edge,
         "ground_state": ground, "replaceable": replaceable, "surface": surface, "vegetation_chance": chance,
         "vegetation_feature": inline(veg), "vertical_range": vrange,
         "xz_radius": {"type": "minecraft:uniform", "min_inclusive": rmin, "max_inclusive": rmax}}
    if kind == "waterlogged_vegetation_patch": f["extra_bottom_block_chance"] = 0.6
    return f


def zone_placement(count, lo, hi, direction, noise=None):
    """noise: (threshold, above) -> count where the 2D biome-info noise is above (True) or below the threshold,
    so each zone covers patches of the map ~150-300 blocks across instead of being sprinkled everywhere."""
    first = {"type": "minecraft:count", "count": count}
    if noise:
        lvl, above = noise
        first = {"type": "minecraft:noise_threshold_count", "noise_level": lvl,
                 "above_noise": count if above else 0, "below_noise": 0 if above else count}
    return [first, {"type": "minecraft:in_square"},
            {"type": "minecraft:height_range", "height": {"type": "minecraft:uniform", "min_inclusive": {"absolute": lo}, "max_inclusive": {"absolute": hi}}},
            {"type": "minecraft:environment_scan", "allowed_search_condition": {"type": "minecraft:matching_block_tag", "tag": "minecraft:air"},
             "direction_of_search": direction, "max_steps": 12, "target_condition": {"type": "minecraft:solid"}},
            {"type": "minecraft:offset", "x": 0, "y": 1 if direction == "down" else -1, "z": 0},
            {"type": "minecraft:biome"}]


GROTTO_NOISE = (0.35, True)   # Seastone Grottos where the noise is high
SULFUR_NOISE = (-0.35, False)  # Sulfur Vents where it is low


def features():
    F = os.path.join(D, 'worldgen/feature'); P = os.path.join(D, 'worldgen/placed_feature')
    crystal_up = {"type": "minecraft:simple_block", "to_place": weighted((state("onepiece:sea_prism_crystal", facing="up", waterlogged=False), 3),
                                                                         ("minecraft:cave_air", 2))}
    crystal_down = {"type": "minecraft:simple_block", "to_place": state("onepiece:sea_prism_crystal", facing="down", waterlogged=False)}
    prism_ground = weighted(("onepiece:sea_prism_stone", 10), ("minecraft:calcite", 2), ("onepiece:seastone_ore", 1))
    wjson(f'{F}/underground_grotto_floor.json', patch("floor", prism_ground, crystal_up, 0.45, 3, 7))
    wjson(f'{P}/underground_grotto_floor.json', {"feature": "onepiece:underground_grotto_floor", "placement": zone_placement(110, 0, 50, "down", GROTTO_NOISE)})
    wjson(f'{F}/underground_grotto_ceiling.json', patch("ceiling", weighted(("onepiece:sea_prism_stone", 6), ("minecraft:calcite", 1)), crystal_down, 0.45, 2, 6, edge=0.4))
    wjson(f'{P}/underground_grotto_ceiling.json', {"feature": "onepiece:underground_grotto_ceiling", "placement": zone_placement(80, 0, 50, "up", GROTTO_NOISE)})
    wjson(f'{F}/underground_grotto_pool.json', patch("floor", state("onepiece:sea_prism_stone"), crystal_up, 0.08, 3, 6, depth=2, edge=0.6,
                                                    kind="waterlogged_vegetation_patch"))
    wjson(f'{P}/underground_grotto_pool.json', {"feature": "onepiece:underground_grotto_pool", "placement": zone_placement(8, 0, 40, "down", GROTTO_NOISE)})

    sulfur_ground = weighted(("minecraft:basalt", 6), ("minecraft:smooth_basalt", 3), ("minecraft:magma_block", 2), ("onepiece:sulfur_vent", 3),
                             ("onepiece:sulfur_ore", 1), ("minecraft:blackstone", 2))
    nothing = {"type": "minecraft:simple_block", "to_place": state("minecraft:cave_air")}
    wjson(f'{F}/underground_sulfur_floor.json', patch("floor", sulfur_ground, nothing, 0.0, 3, 7, depth=2, edge=0.4))
    wjson(f'{P}/underground_sulfur_floor.json', {"feature": "onepiece:underground_sulfur_floor", "placement": zone_placement(70, -58, -8, "down", SULFUR_NOISE)})
    wjson(f'{F}/underground_sulfur_ceiling.json', patch("ceiling", weighted(("minecraft:basalt", 4), ("minecraft:smooth_basalt", 2), ("onepiece:sulfur_ore", 1)),
                                                       nothing, 0.0, 2, 5, edge=0.3))
    wjson(f'{P}/underground_sulfur_ceiling.json', {"feature": "onepiece:underground_sulfur_ceiling", "placement": zone_placement(40, -58, -8, "up", SULFUR_NOISE)})

    wjson(f'{D}/tags/block/underground_patch_replaceable.json', {"replace": False, "values": [
        "#minecraft:base_stone_overworld", "minecraft:dirt", "minecraft:gravel", "minecraft:sand", "minecraft:clay", "minecraft:cobblestone",
        "minecraft:mossy_cobblestone", "minecraft:dripstone_block", "minecraft:coarse_dirt"]})

    # Sea King fossils: whole skeletons buried in the rock (like vanilla fossils, but huge and fishy)
    names = fossils()
    wjson(f'{D}/worldgen/processor_list/underground_fossil_rot.json', {"processors": [
        {"processor_type": "minecraft:block_rot", "integrity": 0.92},
        {"processor_type": "minecraft:protected_blocks", "value": "#minecraft:features_cannot_replace"}]})
    wjson(f'{D}/worldgen/processor_list/underground_fossil_overlay.json', {"processors": [
        {"processor_type": "minecraft:block_rot", "integrity": 0.35},
        {"processor_type": "minecraft:protected_blocks", "value": "#minecraft:features_cannot_replace"}]})
    wjson(f'{F}/underground_sea_king_fossil.json', {
        "type": "minecraft:fossil", "fossil_processors": "onepiece:underground_fossil_rot",
        "fossil_structures": [f"onepiece:underground/fossil/{n}" for n in names],
        "max_empty_corners_allowed": 6, "overlay_processors": "onepiece:underground_fossil_overlay",
        "overlay_structures": [f"onepiece:underground/fossil/{n}_rock" for n in names]})
    wjson(f'{P}/underground_sea_king_fossil.json', {"feature": "onepiece:underground_sea_king_fossil", "placement": [
        {"type": "minecraft:rarity_filter", "chance": 40}, {"type": "minecraft:in_square"},
        {"type": "minecraft:height_range", "height": {"type": "minecraft:uniform", "min_inclusive": {"absolute": -40}, "max_inclusive": {"absolute": 30}}},
        {"type": "minecraft:biome"}]})
    wjson(f'{F}/underground_fossil_rock.json', {"type": "minecraft:ore", "discard_chance_on_air_exposure": 0.0, "size": 14, "targets": [
        {"state": "onepiece:fossil_rock", "target": {"predicate_type": "minecraft:tag_match", "tag": "minecraft:stone_ore_replaceables"}}]})
    wjson(f'{P}/underground_fossil_rock.json', {"feature": "onepiece:underground_fossil_rock", "placement": [
        {"type": "minecraft:count", "count": 2}, {"type": "minecraft:in_square"},
        {"type": "minecraft:height_range", "height": {"type": "minecraft:uniform", "min_inclusive": {"absolute": 0}, "max_inclusive": {"absolute": 48}}},
        {"type": "minecraft:biome"}]})

    wjson(f'{D}/tags/worldgen/biome/has_underground_caves.json', {"replace": False, "values": ["#minecraft:is_overworld"]})


def fossils():
    """Sea King skeletons in pieces: a skull with open jaws, a ribcage, a curling tail. Saved twice: the bones, and a
    matching 'rock' overlay that turns some bones into Fossil Rock."""
    BONE_X, BONE_Y, BONE_Z = "minecraft:bone_block[axis=x]", "minecraft:bone_block[axis=y]", "minecraft:bone_block[axis=z]"
    out = []

    def skull():
        b = B()
        # long snout along x, top of the head and lower jaw hanging open
        for x in range(0, 12):
            w = 2 if x < 5 else 3
            for z in range(-w, w + 1):
                b.set(x, 5, z, BONE_X)            # upper skull
                if x > 2 and abs(z) == w: b.set(x, 1 + (x - 3) // 4, z, BONE_X)  # lower jaw rim
            b.set(x, 4, -w, BONE_X); b.set(x, 4, w, BONE_X)
        for x in range(1, 11, 2):  # teeth
            b.set(x, 4, -2, "minecraft:bone_block[axis=y]"); b.set(x, 3, -2, BONE_Y)
            b.set(x, 4, 2, BONE_Y); b.set(x, 3, 2, BONE_Y)
        for x in range(3, 12):
            for z in range(-3, 4):
                if abs(z) == 3 or x == 11: b.set(x, 1, z, BONE_X)
        for (y, z) in ((6, -2), (6, 2), (7, -2), (7, 2), (6, 0)):  # brow ridges
            b.set(9, y, z, BONE_Y)
        return b

    def ribs(n):
        b = B()
        for x in range(0, n):
            b.set(x, 7, 0, BONE_X)  # spine
            if x % 2 == 0:
                for a in range(0, 13):
                    t = a / 12 * math.pi
                    y = int(round(7 - 6 * math.sin(t / 2) ** 1.2))
                    z = int(round(-6 * math.cos(t)))
                    b.set(x, max(0, y), z, BONE_Y if abs(z) > 4 else BONE_Z)
        return b

    def tail():
        b = B()
        for i in range(0, 22):
            ang = i / 21 * math.pi * 0.9
            x = int(round(9 * math.sin(ang))); z = int(round(9 - 9 * math.cos(ang)))
            y = 1 + (i % 7 == 0)
            b.set(x, y, z, BONE_X if abs(math.cos(ang)) > 0.5 else BONE_Z)
            if i % 3 == 0: b.set(x, y + 1, z, BONE_Y); b.set(x, y - 1, z, BONE_Y)
        return b

    for name, b in (("sea_king_skull", skull()), ("sea_king_ribs", ribs(13)), ("sea_king_ribs_short", ribs(7)), ("sea_king_tail", tail())):
        b.save(os.path.join(D, 'structure/underground/fossil', name + '.nbt'))
        o = B()
        for p, s in b.blocks.items():
            if 'bone' in s: o.set(*p, "onepiece:fossil_rock")
        o.save(os.path.join(D, 'structure/underground/fossil', name + '_rock.nbt'))
        out.append(name)
    return out


if __name__ == '__main__':
    blocks()
    features()
    print('underground blocks + cave zones written to', SRC)

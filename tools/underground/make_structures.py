"""Build the underground structures and write everything the game needs into a source copy.

  python3 make_structures.py <source dir> [id ...] [--no-render]

For each build: runs the landmarks finishing pass ("cave" mode: supports, floating props, lighting), checks every
onepiece: block state against its blockstate file, renders previews to previews/underground/, and writes the
jigsaw tiles with tools/landmarks/tiler.py. Then writes the structure jsons, the structure set
underground_locations, has_structure biome tags, chest loot tables and the treasure-map structure tags.
"""
import json, os, re, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', 'landmarks'))
import importlib
import finish, render, tiler  # noqa: E402
from ugkit import springproof, AIR  # noqa: E402


def cull_deep(b, keep=4):
    """The tiler drops every buried block, trusting the world's ground to fill in. Underground the world there may be
    cave air or aquifer water, and a neighbouring chunk's clay pool can then dig through the thin rock left over and
    pour a waterfall into the build. So keep all rock within `keep` blocks of the build's air and drop only the rest."""
    near = set()
    for (x, y, z), v in b.blocks.items():
        if v in (AIR, "minecraft:cave_air"):
            for dx in range(-keep, keep + 1):
                for dy in range(-keep, keep + 1):
                    for dz in range(-keep, keep + 1):
                        near.add((x + dx, y + dy, z + dz))
    hidden = tiler_cull(b)
    return {p: s for p, s in b.blocks.items() if p in hidden or p in near}


tiler_cull = tiler.cull_hidden
tiler.cull_hidden = cull_deep

SRC = sys.argv[1]
RES = os.path.join(SRC, 'src/main/resources/data/onepiece')
ASSETS = os.path.join(SRC, 'src/main/resources/assets/onepiece')
PREVIEW = '/mnt/project-files/one-piece-mod/previews/underground'
IDS = ['treasure_grotto', 'ancient_ruins', 'marine_bunker', 'smile_factory']
DEEP = ['seastone_deep_mine']  # its own, rarer structure set (deep_mine_locations)
args = [a for a in sys.argv[2:] if not a.startswith('--')] or IDS + DEEP


def wjson(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)
        f.write('\n')


_props = {}


def check_states(b, sid):
    """Every onepiece: block must use property names its blockstate file knows (else the game drops the state)."""
    bad = set()
    for s in set(b.blocks.values()):
        if not s.startswith('onepiece:'): continue
        name = s.split('[')[0].split(':')[1]
        if name not in _props:
            p = os.path.join(ASSETS, 'blockstates', name + '.json')
            if not os.path.exists(p): _props[name] = None
            else:
                d = json.load(open(p)); keys = set()
                for v in (d.get('variants') or {}):
                    keys |= {kv.split('=')[0] for kv in v.split(',') if '=' in kv}
                for part in d.get('multipart', []):
                    w = part.get('when', {})
                    for c in (w.get('OR') or [w]): keys |= set(c.keys())
                _props[name] = keys
        if _props[name] is None: bad.add(f'{s} (no such block)'); continue
        if '[' in s:
            for kv in s.split('[')[1].rstrip(']').split(','):
                if kv.split('=')[0] not in _props[name] and _props[name] and not kv.startswith('waterlogged'): bad.add(f'{s} (unknown property {kv})')
                if not _props[name] and not kv.startswith('waterlogged'): bad.add(f'{s} (block has no properties)')
    if bad:
        raise SystemExit(f'{sid}: bad block states:\n  ' + '\n  '.join(sorted(bad)))


def structure_json(sid, y):
    return {"type": "minecraft:jigsaw", "biomes": f"#onepiece:has_structure/{sid}", "step": "top_layer_modification",
            "spawn_overrides": {"monster": {"bounding_box": "piece", "spawns": []}, "ambient": {"bounding_box": "piece", "spawns": []}},
            "start_pool": f"onepiece:{sid}", "size": 1, "max_distance_from_center": {"horizontal": 80, "vertical": 40},
            "use_expansion_hack": False, "start_height": {"absolute": y}, "terrain_adaptation": "none"}


def build_one(sid):
    t = time.time()
    m = importlib.import_module(sid)
    b, ground = m.build()
    springproof(b)
    rep = finish.finish(b, "cave", sid, light=getattr(m, "AUTO_LIGHT", False))
    check_states(b, sid)
    print(sid, ' '.join(f'{k}={v}' for k, v in sorted(rep.items())))
    if '--no-render' not in sys.argv:
        os.makedirs(PREVIEW, exist_ok=True)
        render.render(b.blocks, f'{PREVIEW}/{sid}_se.png', 'se', title=m.TITLE + ' (from the south-east)')
        for cut in m.CUTS:
            render.render(b.blocks, f'{PREVIEW}/{sid}_cut{cut}.png', 'se', cut=cut, title=f'{m.TITLE}: cut at height {cut}')
    sp = os.path.join(RES, 'worldgen/structure', sid + '.json')
    if not os.path.exists(sp): wjson(sp, structure_json(sid, m.TILER['sky_y']))
    if sid in DEEP:  # three levels: taller than the other cave builds
        sj = json.load(open(sp)); sj["max_distance_from_center"] = {"horizontal": 80, "vertical": 64}; wjson(sp, sj)
    info = tiler.write(sid, b, ground, res=RES, **m.TILER)
    sj = json.load(open(sp)); sj["step"] = "top_layer_modification"
    # place lanterns, dripstone, fences as drawn: with the default the cave's aquifer water waterlogs them and they leak
    sj["liquid_settings"] = "ignore_waterlogging"; wjson(sp, sj)
    wjson(os.path.join(RES, 'tags/worldgen/biome/has_structure', sid + '.json'), {"replace": False, "values": ["#onepiece:has_underground_caves"]})
    print(sid, len(b.blocks), 'blocks', info, f'{time.time() - t:.1f}s')


def data():
    wjson(os.path.join(RES, 'worldgen/structure_set/underground_locations.json'), {
        "structures": [{"structure": f"onepiece:{s}", "weight": 1} for s in IDS],
        "placement": {"type": "minecraft:random_spread", "spacing": 22, "separation": 9, "salt": 2510251}})
    wjson(os.path.join(RES, 'worldgen/structure_set/deep_mine_locations.json'), {
        "structures": [{"structure": f"onepiece:{s}", "weight": 1} for s in DEEP],
        "placement": {"type": "minecraft:random_spread", "spacing": 40, "separation": 16, "salt": 5110526}})
    wjson(os.path.join(RES, 'tags/worldgen/structure/on_deep_mine_maps.json'), {"replace": False, "values": ["onepiece:seastone_deep_mine"]})
    wjson(os.path.join(RES, 'tags/worldgen/structure/on_treasure_grotto_maps.json'), {"replace": False, "values": ["onepiece:treasure_grotto"]})
    wjson(os.path.join(RES, 'tags/worldgen/structure/on_smile_factory_maps.json'), {"replace": False, "values": ["onepiece:smile_factory"]})
    wjson(os.path.join(RES, 'tags/worldgen/structure/on_ancient_ruins_maps.json'), {"replace": False, "values": ["onepiece:ancient_ruins"]})
    wjson(os.path.join(RES, 'tags/worldgen/structure/on_marine_bunker_maps.json'), {"replace": False, "values": ["onepiece:marine_bunker"]})
    import loot
    loot.write(RES)


if __name__ == '__main__':
    for sid in args: build_one(sid)
    data()

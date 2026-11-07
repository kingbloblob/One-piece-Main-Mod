"""Build the dungeons and write everything the game needs into a source copy.

  python3 make_dungeons.py <source dir> [id ...] [--no-render]

Each dungeon is a LAND structure (heightmap WORLD_SURFACE_WG, terrain "none"; world.TerrainCut clears the hill
over it): a themed entrance on the surface and the dungeon dug into the rock below. Runs the landmark finishing
pass (lighting reaches underground for these ids), soft edges, checks block ids and states, renders one contact
sheet per dungeon to previews/dungeons/, and writes the jigsaw tiles. Then writes the structure set
dungeon_locations, the has_structure biome tags, the treasure-map structure tags and the chest loot tables.

Buried rock is kept within 4 blocks of the dungeon's air (like the underground builds): the tiler normally drops
every hidden block and trusts the world's ground, but caves or aquifers there would open holes into the rooms.
"""
import importlib, json, os, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "landmarks"))
sys.path.insert(0, os.path.join(HERE, "..", "underground"))
import finish, pipeline, render, tiler  # noqa: E402
from make_structures_helpers import check_states, cull_deep_factory, steady  # noqa: E402

SRC = sys.argv[1]
RES = os.path.join(SRC, "src/main/resources/data/onepiece")
PREVIEW = "/mnt/project-files/one-piece-mod/previews/dungeons"
IDS = ["sand_king_tomb", "ryuma_crypt", "kitetsu_forge", "oden_shrine", "roger_vault"]
args = [a for a in sys.argv[2:] if not a.startswith("--")] or IDS

finish.UNDERGROUND.update(IDS)        # light the rooms below ground too
tiler.cull_hidden = cull_deep_factory(tiler.cull_hidden)


def contact_sheet(paths, dest, width=1000):
    """All views on one small image (look at this one, not the separate renders)."""
    from PIL import Image
    ims = [Image.open(p).convert("RGB") for p in paths if os.path.exists(p)]
    cw = width // 2
    ims = [im.resize((cw, max(1, im.height * cw // im.width))) for im in ims]
    rows = [ims[i:i + 2] for i in range(0, len(ims), 2)]
    hs = [max(im.height for im in r) for r in rows]
    s = Image.new("RGB", (width, sum(hs)), (255, 255, 255))
    y = 0
    for r, h in zip(rows, hs):
        for i, im in enumerate(r):
            s.paste(im, (i * cw, y))
        y += h
    s.save(dest)
    return dest


def wjson(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def structure_json(sid):
    return {"type": "minecraft:jigsaw", "biomes": f"#onepiece:has_structure/{sid}", "step": "surface_structures",
            "spawn_overrides": {"monster": {"bounding_box": "piece", "spawns": []}, "ambient": {"bounding_box": "piece", "spawns": []}},
            "terrain_adaptation": "none", "start_pool": f"onepiece:{sid}", "size": 1,
            "max_distance_from_center": {"horizontal": 80, "vertical": 48}, "use_expansion_hack": False,
            "project_start_to_heightmap": "WORLD_SURFACE_WG", "start_height": {"absolute": -20},
            "liquid_settings": "ignore_waterlogging"}


def build_one(sid):
    t = time.time()
    m = importlib.import_module(sid)
    b = m.build()
    steady(b)
    rep = finish.finish(b, "land", sid)
    rep["edge columns left out"] = pipeline.soften_edges(b, sid, skirt=8, cut=6, reach=10)
    rep["air above"] = pipeline.clear_above(b)
    from mcb.bridge import check_ids
    bad = check_ids(b)
    if bad:
        raise SystemExit(f"{sid}: UNKNOWN BLOCK IDS {bad}")
    check_states(b, sid, os.path.join(SRC, "src/main/resources/assets/onepiece"))
    print(sid, " ".join(f"{k}={v}" for k, v in sorted(rep.items())))
    if "--no-render" not in sys.argv:
        os.makedirs(PREVIEW, exist_ok=True)
        shots = [f"{PREVIEW}/{sid}_se.png"]
        render.render(b.blocks, shots[0], "se", title=m.TITLE + " (from the south-east)")
        for cut in m.CUTS:
            shots.append(f"{PREVIEW}/{sid}_cut{cut}.png")
            render.render(b.blocks, shots[-1], "se", cut=cut, title=f"{m.TITLE}: cut at height {cut}")
        print(sid, "sheet:", contact_sheet(shots, f"{PREVIEW}/{sid}_sheet.png"))
    sp = os.path.join(RES, "worldgen/structure", sid + ".json")
    if not os.path.exists(sp):
        wjson(sp, structure_json(sid))
    info = tiler.write(sid, b, 0, res=RES, heightmap="WORLD_SURFACE_WG", terrain="none", liquid="ignore_waterlogging")
    wjson(os.path.join(RES, "tags/worldgen/biome/has_structure", sid + ".json"), {"replace": False, "values": m.BIOMES})
    print(sid, len(b.blocks), "blocks", len(b.entities), "entities", info, f"{time.time() - t:.1f}s")


def data():
    # Wano's islands are small and crowded with landmarks, so its two dungeons get their own, denser grid
    wano = ["kitetsu_forge", "oden_shrine"]
    wjson(os.path.join(RES, "worldgen/structure_set/dungeon_locations.json"), {
        "structures": [{"structure": f"onepiece:{s}", "weight": 1} for s in IDS if s not in wano],
        "placement": {"type": "onepiece:ring_spread", "spacing": 18, "separation": 7, "salt": 3111202601, "min_distance": 600}})
    wjson(os.path.join(RES, "worldgen/structure_set/dungeon_wano_locations.json"), {
        "structures": [{"structure": f"onepiece:{s}", "weight": 1} for s in wano],
        "placement": {"type": "onepiece:ring_spread", "spacing": 10, "separation": 4, "salt": 3111202602, "min_distance": 1200}})
    for s in IDS:
        wjson(os.path.join(RES, f"tags/worldgen/structure/on_{s}_maps.json"), {"replace": False, "values": [f"onepiece:{s}"]})
    wjson(os.path.join(RES, "tags/worldgen/structure/dungeons.json"), {"replace": False, "values": [f"onepiece:{s}" for s in IDS]})
    import dgloot
    dgloot.write(RES)


if __name__ == "__main__":
    for sid in args:
        build_one(sid)
    data()

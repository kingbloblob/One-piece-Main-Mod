"""Writes the models, blockstates, item models, loot, recipes and names of the furnish blocks (com.onepiecemod.furnish).
python3 gen_assets.py <src/main/resources dir>. Uses vanilla textures only. Models face north; wall fixtures touch z = 16."""
import json, os, sys

R = sys.argv[1]
LAN = "minecraft:block/lantern"


def box(f, t, tex, uv=None, side_uv=None, top_uv=None, rot=None):
    faces = {}
    for d in ("north", "south", "east", "west", "up", "down"):
        u = (top_uv if d in ("up", "down") else side_uv) or uv
        faces[d] = {"texture": tex} if u is None else {"texture": tex, "uv": u}
    e = {"from": f, "to": t, "faces": faces}
    if rot: e["rotation"] = rot
    return e


def cross(cx, y0, cz, w, h, tex):
    """Two crossed quads like a plant."""
    out = []
    for ang in (45, -45):
        out.append({"from": [cx - w / 2, y0, cz], "to": [cx + w / 2, y0 + h, cz],
                    "rotation": {"origin": [cx, y0, cz], "axis": "y", "angle": ang},
                    "faces": {"north": {"texture": tex, "uv": [0, 0, 16, 16]}, "south": {"texture": tex, "uv": [0, 0, 16, 16]}}})
    return out


def lantern_body(x0, y0, z0):
    """Vanilla lantern body (6x7x6 plus cap) with its corner at x0,y0,z0."""
    return [box([x0, y0, z0], [x0 + 6, y0 + 7, z0 + 6], "#lantern", side_uv=[0, 2, 6, 9], top_uv=[0, 9, 6, 15]),
            box([x0 + 1, y0 + 7, z0 + 1], [x0 + 5, y0 + 9, z0 + 5], "#lantern", side_uv=[1, 0, 5, 2], top_uv=[1, 10, 5, 14])]


def candle(x, y, z, tex="#candle"):
    """A 2x6 candle with a wick, x,z = its corner."""
    return [box([x, y, z], [x + 2, y + 6, z + 2], tex, side_uv=[0, 8, 2, 14], top_uv=[0, 6, 2, 8]),
            {"from": [x + 0.5, y + 6, z + 1], "to": [x + 1.5, y + 7, z + 1], "rotation": {"origin": [x + 1, y + 6, z + 1], "axis": "y", "angle": 45},
             "faces": {"north": {"texture": tex, "uv": [0, 5, 1, 6]}, "south": {"texture": tex, "uv": [0, 5, 1, 6]}}},
            {"from": [x + 0.5, y + 6, z + 1], "to": [x + 1.5, y + 7, z + 1], "rotation": {"origin": [x + 1, y + 6, z + 1], "axis": "y", "angle": -45},
             "faces": {"north": {"texture": tex, "uv": [0, 5, 1, 6]}, "south": {"texture": tex, "uv": [0, 5, 1, 6]}}}]


METAL_UV = dict(side_uv=[0, 9, 6, 15], top_uv=[0, 9, 6, 15])
M = {}
# wall lamp: a lantern hanging from an iron arm fixed to the wall
M["wall_lamp"] = ({"lantern": LAN, "particle": LAN},
                  lantern_body(5, 1, 5) + [box([7.5, 10, 7.5], [8.5, 11, 16], "#lantern", **METAL_UV),
                                          box([7, 9, 7], [9, 10, 9], "#lantern", **METAL_UV),
                                          box([6, 5, 15], [10, 12, 16], "#lantern", **METAL_UV),
                                          box([7.5, 6, 14], [8.5, 10, 15], "#lantern", **METAL_UV)])
# candle sconce: a back plate, an arm, a cup and a lit candle
M["candle_sconce"] = ({"metal": "minecraft:block/gold_block", "candle": "minecraft:block/white_candle_lit", "particle": "minecraft:block/gold_block"},
                      [box([6, 2, 15], [10, 10, 16], "#metal"), box([7.5, 4, 10], [8.5, 5, 15], "#metal"),
                       box([6, 5, 8.5], [10, 6, 12.5], "#metal")] + candle(7, 6, 9.5))


def chandelier(metal, cand):
    els = [box([7.5, 11, 7.5], [8.5, 16, 8.5], "#metal"), box([6, 5, 6], [10, 8, 10], "#metal"),
           box([1, 6, 7.5], [15, 7, 8.5], "#metal"), box([7.5, 6, 1], [8.5, 7, 15], "#metal"),
           box([6.5, 8, 6.5], [9.5, 11, 9.5], "#metal"), box([6.5, 15, 6.5], [9.5, 16, 9.5], "#metal")]
    for (x, z) in ((1, 7), (13, 7), (7, 1), (7, 13)):
        els += [box([x - 0.5, 7, z - 0.5], [x + 2.5, 8, z + 2.5], "#metal")] + candle(x, 8, z)
    for (x, z) in ((3.5, 3.5), (10.5, 3.5), (3.5, 10.5), (10.5, 10.5)):  # little drops of crystal between the arms
        els.append(box([x, 4, z], [x + 2, 6, z + 2], "#glass"))
        els.append(box([x + 0.5, 6, z + 0.5], [x + 1.5, 7, z + 1.5], "#metal"))
    return ({"metal": metal, "candle": cand, "glass": "minecraft:block/glass", "particle": metal}, els)


M["chandelier"] = chandelier("minecraft:block/gold_block", "minecraft:block/white_candle_lit")
M["iron_chandelier"] = chandelier("minecraft:block/polished_blackstone", "minecraft:block/candle_lit")
# ceiling lamp: a framed glowing panel set against the ceiling
M["ceiling_lamp"] = ({"frame": "minecraft:block/dark_oak_planks", "glow": "minecraft:block/ochre_froglight_top", "particle": "minecraft:block/ochre_froglight_top"},
                     [box([2, 15, 2], [14, 16, 14], "#frame"), box([3.5, 13.5, 3.5], [12.5, 15, 12.5], "#glow"),
                      box([2, 14, 2], [3.5, 15, 14], "#frame"), box([12.5, 14, 2], [14, 15, 14], "#frame"),
                      box([3.5, 14, 2], [12.5, 15, 3.5], "#frame"), box([3.5, 14, 12.5], [12.5, 15, 14], "#frame")])
# candelabra: a stand with five candles
els = [box([5, 0, 5], [11, 1, 11], "#metal"), box([6.5, 1, 6.5], [9.5, 2, 9.5], "#metal"), box([7.5, 2, 7.5], [8.5, 8, 8.5], "#metal"),
       box([2.5, 7, 7.5], [13.5, 8, 8.5], "#metal"), box([7.5, 7, 2.5], [8.5, 8, 13.5], "#metal")]
for (x, z, y) in ((2, 7, 8), (12, 7, 8), (7, 2, 8), (7, 12, 8), (7, 7, 8)):
    els += [box([x - 0.5, y - 0.5, z - 0.5], [x + 2.5, y, z + 2.5], "#metal")] + candle(x, y if (x, z) != (7, 7) else y + 0, z)
M["candelabra"] = ({"metal": "minecraft:block/gold_block", "candle": "minecraft:block/white_candle_lit", "particle": "minecraft:block/gold_block"}, els)
# flower box: a planter on the wall under a window, full of flowers
els = [box([0, 0, 10], [16, 6, 16], "#wood"), box([0.5, 5, 10.5], [15.5, 5.5, 15.5], "#soil"),
       box([0, 5, 9.5], [16, 6, 10], "#wood"), box([0, -1, 12], [1, 0, 15], "#wood"), box([15, -1, 12], [16, 0, 15], "#wood")]
els[3]["from"][1] = 0; els[3]["to"][1] = 1; els[4]["from"][1] = 0; els[4]["to"][1] = 1
for i, (x, t) in enumerate(((2.5, "#f1"), (6, "#f2"), (9.5, "#f3"), (13, "#f4"))):
    els += cross(x, 5.5, 13, 5, 5.5, t)
M["flower_box"] = ({"wood": "minecraft:block/spruce_planks", "soil": "minecraft:block/rooted_dirt", "particle": "minecraft:block/spruce_planks",
                    "f1": "minecraft:block/poppy", "f2": "minecraft:block/azure_bluet", "f3": "minecraft:block/dandelion", "f4": "minecraft:block/cornflower"}, els)

NAMES = {"wall_lamp": "Wall Lamp", "candle_sconce": "Candle Sconce", "chandelier": "Chandelier", "iron_chandelier": "Iron Chandelier",
         "ceiling_lamp": "Ceiling Lamp", "candelabra": "Candelabra", "flower_box": "Flower Box"}
RECIPES = {
    "wall_lamp": (["I ", "IL"], {"I": "minecraft:iron_nugget", "L": "minecraft:lantern"}, 1),
    "candle_sconce": (["GC", "G "], {"G": "minecraft:gold_nugget", "C": "#minecraft:candles"}, 1),
    "chandelier": ([" N ", "CGC", " C "], {"N": "minecraft:iron_chain", "G": "minecraft:gold_ingot", "C": "#minecraft:candles"}, 1),
    "iron_chandelier": ([" N ", "CIC", " C "], {"N": "minecraft:iron_chain", "I": "minecraft:iron_ingot", "C": "#minecraft:candles"}, 1),
    "ceiling_lamp": (["PFP"], {"P": "minecraft:dark_oak_slab", "F": "minecraft:glowstone"}, 2),
    "candelabra": (["CCC", " G ", " G "], {"G": "minecraft:gold_nugget", "C": "#minecraft:candles"}, 1),
    "flower_box": (["FFF", "PDP"], {"F": "#minecraft:small_flowers", "P": "minecraft:spruce_planks", "D": "minecraft:dirt"}, 2),
}


def w(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f: json.dump(obj, f, indent=2)


for name, (tex, elements) in M.items():
    w(f"{R}/assets/onepiece/models/block/{name}.json", {"parent": "minecraft:block/block", "ambientocclusion": False, "textures": tex, "elements": elements,
                                                       "display": {"gui": {"rotation": [30, 225, 0], "translation": [0, 0, 0], "scale": [0.8, 0.8, 0.8]}}})
    w(f"{R}/assets/onepiece/blockstates/{name}.json", {"variants": {
        f"facing={d}": ({"model": f"onepiece:block/{name}", "y": y} if y else {"model": f"onepiece:block/{name}"})
        for d, y in (("north", 0), ("east", 90), ("south", 180), ("west", 270))}})
    w(f"{R}/assets/onepiece/items/{name}.json", {"model": {"type": "minecraft:model", "model": f"onepiece:block/{name}"}})
    w(f"{R}/data/onepiece/loot_table/blocks/{name}.json", {"type": "minecraft:block", "pools": [{"condition": {"type": "minecraft:survives_explosion"},
        "entries": [{"type": "minecraft:item", "name": f"onepiece:{name}"}], "rolls": 1}], "random_sequence": f"onepiece:blocks/{name}"})
    pat, key, n = RECIPES[name]
    w(f"{R}/data/onepiece/recipe/{name}.json", {"type": "minecraft:crafting_shaped", "category": "building", "pattern": pat, "key": key,
                                                "result": {"count": n, "id": f"onepiece:{name}"}})
w(f"{R}/assets/onepiece_furnish/lang/en_us.json", {f"block.onepiece.{k}": v for k, v in NAMES.items()})
print("wrote", len(M), "fixtures")

"""Signs, hanging signs, boats and chest boats for the island woods (Java side: com.onepiecemod.deco.WoodExtras).

Run:  python3 gen_signs_boats.py <unzipped 26.3 client.jar + server data> <source dir>
      (the first folder needs assets/minecraft/... and data/minecraft/... for the oak sign and boat files)

The oak sign, hanging sign and boat files are used as templates: models and blockstates are copied with our
names, and the oak textures are repainted in each wood's own colours (taken from its planks, or for hanging
signs its stripped log), keeping grey metal parts like chains and hinges as they are.
Writes blockstates, block/item models, item definitions, textures, loot tables, recipes, tags and lang
(assets/onepiece_woodextras/lang/en_us.json). Shared minecraft tag files are union-merged.
"""
import colorsys
import json
import os
import sys

from PIL import Image

VAN, SRC = sys.argv[1], sys.argv[2]
RES = os.path.join(SRC, "src", "main", "resources")
A = os.path.join(RES, "assets", "onepiece")
D = os.path.join(RES, "data")

# name, display name, planks texture, hanging-sign wood (stripped log, or the log for Adam)
WOODS = [
    ("sakura", "Sakura", "sakura_planks", "stripped_sakura_log"),
    ("yarukiman", "Yarukiman Mangrove", "yarukiman_planks", "stripped_yarukiman_log"),
    ("palm", "Palm", "palm_planks", "stripped_palm_log"),
    ("gloom", "Gloom", "gloom_planks", "stripped_gloom_log"),
    ("adam", "Adam", "adam_planks", "adam_log"),
]


def wjson(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def rjson(path):
    with open(path) as f:
        return json.load(f)


def lum(c):
    return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]


def is_wood(c):
    """Brown oak pixels get repainted; grey or black ones (chains, iron, outlines) stay."""
    h, l, s = colorsys.rgb_to_hls(c[0] / 255, c[1] / 255, c[2] / 255)
    return s > 0.18 and 0.04 < h < 0.17


def repaint(template, palette_png, out):
    """Histogram-match the oak wood pixels of `template` onto the colours of `palette_png`."""
    src = Image.open(template).convert("RGBA")
    pal = sorted((p for p in Image.open(palette_png).convert("RGBA").getdata() if p[3] > 0), key=lum)
    wood = sorted({p[:3] for p in src.getdata() if p[3] > 0 and is_wood(p)}, key=lum)
    mapping = {}
    for i, c in enumerate(wood):
        t = i / max(1, len(wood) - 1)
        mapping[c] = pal[round(t * (len(pal) - 1))][:3]
    img = Image.new("RGBA", src.size)
    img.putdata([(mapping[p[:3]] + (p[3],)) if p[3] > 0 and p[:3] in mapping else p for p in src.getdata()])
    os.makedirs(os.path.dirname(out), exist_ok=True)
    img.save(out)


def swap(obj, w, planks, hang):
    """Copy an oak JSON file with our names in it."""
    s = json.dumps(obj)
    s = s.replace("minecraft:block/stripped_oak_log", "onepiece:block/" + hang)
    s = s.replace("minecraft:block/oak_planks", "onepiece:block/" + planks)
    s = s.replace("minecraft:block/oak_", "onepiece:block/%s_" % w).replace("minecraft:item/oak_", "onepiece:item/%s_" % w)
    s = s.replace("minecraft:oak_", "onepiece:%s_" % w).replace("minecraft:stripped_oak_log", "onepiece:" + hang)
    s = s.replace("minecraft:blocks/oak_", "onepiece:blocks/%s_" % w)
    return json.loads(s)


def merge_tag(path, values):
    data = rjson(path) if os.path.exists(path) else {"replace": False, "values": []}
    for v in values:
        if v not in data["values"]:
            data["values"].append(v)
    wjson(path, data)


def main():
    va = os.path.join(VAN, "assets", "minecraft")
    vd = os.path.join(VAN, "data", "minecraft")
    lang = {}
    tags = {k: [] for k in ("block/standing_signs", "block/wall_signs", "block/ceiling_hanging_signs",
                            "block/wall_hanging_signs", "block/mineable/axe", "item/signs", "item/hanging_signs",
                            "item/boats", "item/chest_boats")}
    for w, title, planks, hang in WOODS:
        tex_planks = os.path.join(A, "textures", "block", planks + ".png")
        tex_hang = os.path.join(A, "textures", "block", hang + ".png")
        # Textures
        for rel, pal in [("block/oak_sign", tex_planks), ("item/oak_sign", tex_planks), ("item/oak_boat", tex_planks),
                         ("item/oak_chest_boat", tex_planks), ("block/oak_hanging_sign", tex_hang),
                         ("item/oak_hanging_sign", tex_hang)]:
            repaint(os.path.join(va, "textures", rel + ".png"), pal,
                    os.path.join(A, "textures", rel.replace("oak_", w + "_") + ".png"))
        for rel, pal in [("entity/boat/oak", tex_planks), ("entity/chest_boat/oak", tex_planks),
                         ("gui/signs/oak", tex_planks), ("gui/hanging_signs/oak", tex_hang)]:
            repaint(os.path.join(va, "textures", rel + ".png"), pal,
                    os.path.join(A, "textures", rel.replace("/oak", "/" + w) + ".png"))
        # Blockstates and block models
        for kind in ("sign", "wall_sign", "hanging_sign", "wall_hanging_sign"):
            wjson(os.path.join(A, "blockstates", "%s_%s.json" % (w, kind)),
                  swap(rjson(os.path.join(va, "blockstates", "oak_%s.json" % kind)), w, planks, hang))
        for f in sorted(os.listdir(os.path.join(va, "models", "block"))):
            if f.startswith("oak_") and "sign" in f:
                wjson(os.path.join(A, "models", "block", f.replace("oak_", w + "_", 1)),
                      swap(rjson(os.path.join(va, "models", "block", f)), w, planks, hang))
        # Items
        for kind in ("sign", "hanging_sign", "boat", "chest_boat"):
            wjson(os.path.join(A, "items", "%s_%s.json" % (w, kind)),
                  swap(rjson(os.path.join(va, "items", "oak_%s.json" % kind)), w, planks, hang))
            wjson(os.path.join(A, "models", "item", "%s_%s.json" % (w, kind)),
                  swap(rjson(os.path.join(va, "models", "item", "oak_%s.json" % kind)), w, planks, hang))
        # Loot (wall signs drop their standing sign) and recipes
        for kind in ("sign", "hanging_sign"):
            wjson(os.path.join(D, "onepiece", "loot_table", "blocks", "%s_%s.json" % (w, kind)),
                  swap(rjson(os.path.join(vd, "loot_table", "blocks", "oak_%s.json" % kind)), w, planks, hang))
        for kind in ("sign", "hanging_sign", "boat", "chest_boat"):
            r = swap(rjson(os.path.join(vd, "recipe", "oak_%s.json" % kind)), w, planks, hang)
            r = json.loads(json.dumps(r).replace("onepiece:%s_planks" % w, "onepiece:" + planks))
            wjson(os.path.join(D, "onepiece", "recipe", "%s_%s.json" % (w, kind)), r)
        # Tags and names
        p = "onepiece:%s_" % w
        tags["block/standing_signs"].append(p + "sign")
        tags["block/wall_signs"].append(p + "wall_sign")
        tags["block/ceiling_hanging_signs"].append(p + "hanging_sign")
        tags["block/wall_hanging_signs"].append(p + "wall_hanging_sign")
        tags["block/mineable/axe"] += [p + k for k in ("sign", "wall_sign", "hanging_sign", "wall_hanging_sign")]
        tags["item/signs"].append(p + "sign")
        tags["item/hanging_signs"].append(p + "hanging_sign")
        tags["item/boats"].append(p + "boat")
        tags["item/chest_boats"].append(p + "chest_boat")
        lang["block.onepiece.%s_sign" % w] = title + " Sign"
        lang["block.onepiece.%s_hanging_sign" % w] = title + " Hanging Sign"
        lang["item.onepiece.%s_boat" % w] = title + " Boat"
        lang["item.onepiece.%s_chest_boat" % w] = title + " Boat with Chest"
        lang["entity.onepiece.%s_boat" % w] = title + " Boat"
        lang["entity.onepiece.%s_chest_boat" % w] = title + " Boat with Chest"
    for tag, values in tags.items():
        merge_tag(os.path.join(D, "minecraft", "tags", tag + ".json"), values)
    wjson(os.path.join(RES, "assets", "onepiece_woodextras", "lang", "en_us.json"), lang)
    print(len(WOODS), "woods: signs, hanging signs, boats and chest boats written")


if __name__ == "__main__":
    main()

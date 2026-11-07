#!/usr/bin/env python3
"""Makes every furniture block (com.onepiecemod.furniture.FurnitureBlocks) and its blockstate, model,
item model, loot table, recipe, lang name, tags and drawn textures. The blocks are listed in props.py.

    python3 gen_furniture.py <source dir> [vanilla recipe dir to check for clashes]

FurnitureBlock.java, StorageFurnitureBlock.java, FurnitureStorageBlockEntity.java, SeatEntity.java, Furniture.java and client/FurnitureClient.java are hand-written.
Shared minecraft tag files (mineable/axe, mineable/pickaxe, climbable) are union-merged, never replaced.
Also writes descriptions.json here (read by tools/descriptions/gen_descriptions.py) and
/mnt/project-files/one-piece-mod/furniture/furniture-blocks.json (block ids by kind, for the structure builders)."""
import json, os, sys, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import props, textures

HERE = os.path.dirname(os.path.abspath(__file__))
COPY = {"wood": "Blocks.OAK_PLANKS", "wool": "Blocks.WOOL.white()", "stone": "Blocks.STONE_BRICKS", "metal": "Blocks.LANTERN"}
TOOL = {"wood": "axe", "stone": "pickaxe", "metal": "pickaxe"}
FACES = ["north", "south", "east", "west", "up", "down"]


def dump(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def element(box):
    x1, y1, z1, x2, y2, z2, tex = box[:7]
    extra = box[7] if len(box) > 7 else {}
    if isinstance(tex, str):
        faces = {f: tex for f in FACES}
    else:
        faces = {f: tex.get(f, tex.get("*")) for f in FACES}
    el = {"from": [x1, y1, z1], "to": [x2, y2, z2],
          "faces": {f: {"texture": "#" + t} for f, t in faces.items() if t}}
    if "rot" in extra:
        axis, angle, origin = extra["rot"]
        el["rotation"] = {"origin": list(origin), "axis": axis, "angle": angle}
    return el


def java_box(box):
    c = [min(16, max(0, v)) for v in box[:6]]
    return "b(" + ", ".join(f"{v:g}" for v in c) + ")"


def const(pid):
    return pid.upper()


def recipe_json(p):
    result = {"count": p["recipe"][2] if "recipe" in p else p["shapeless"][1], "id": "onepiece:" + p["id"]}
    if "recipe" in p:
        pattern, key, _ = p["recipe"]
        return {"type": "minecraft:crafting_shaped", "category": "building", "pattern": pattern, "key": key, "result": result}
    return {"type": "minecraft:crafting_shapeless", "category": "building", "ingredients": p["shapeless"][0], "result": result}


def signature(r):
    """A comparable form of a crafting recipe, to spot two recipes with the same inputs."""
    def ing(v):
        if isinstance(v, list):
            v = v[0] if v else ""
        if isinstance(v, dict):
            v = v.get("item") or ("#" + v.get("tag", ""))
        return v if ":" in v.lstrip("#") else "minecraft:" + v.lstrip("#")
    t = r.get("type", "")
    if t.endswith("crafting_shaped"):
        rows = [row for row in r["pattern"]]
        while rows and not rows[0].strip(): rows.pop(0)
        while rows and not rows[-1].strip(): rows.pop()
        left = min(len(row) - len(row.lstrip()) for row in rows)
        right = max(len(row.rstrip()) for row in rows)
        grid = tuple(tuple(ing(r["key"][ch]) if ch != " " else "" for ch in row.ljust(right)[left:right]) for row in rows)
        return ("shaped", grid)
    if t.endswith("crafting_shapeless"):
        return ("shapeless", tuple(sorted(ing(i) for i in r["ingredients"])))
    return None


def check_clashes(recipes, dirs):
    mine = {}
    for pid, r in recipes.items():
        s = signature(r)
        if s in mine:
            print("CLASH between our recipes:", pid, mine[s])
        mine[s] = pid
    for d in dirs:
        for f in glob.glob(d + "/**/*.json", recursive=True):
            name = os.path.basename(f)[:-5]
            if name in recipes:
                continue
            try:
                s = signature(json.load(open(f)))
            except Exception:
                continue
            if s and s in mine:
                print("CLASH:", mine[s], "has the same recipe as", f)


def main(source, vanilla=None):
    res = source + "/src/main/resources"
    allp = props.all_props()
    lang = {"itemGroup.onepiece.furniture": "One Piece: Furniture", "entity.onepiece.seat": "Seat"}
    tags = {"mineable/axe": [], "mineable/pickaxe": [], "climbable": []}
    fields, flam, recipes, descs, storage = [], [], {}, {}, []
    kinds = {"full_cubes": [], "solid_top": [], "other": []}

    for name, fn in textures.ALL.items():
        path = f"{res}/assets/onepiece/textures/block/furniture/{name}.png"
        os.makedirs(os.path.dirname(path), exist_ok=True)
        fn().save(path)

    for p in allp:
        pid = p["id"]
        model = {"parent": "minecraft:block/block", "textures": dict(p["tex"], particle=list(p["tex"].values())[0]),
                 "elements": [element(b) for b in p["boxes"]]}
        dump(f"{res}/assets/onepiece/models/block/{pid}.json", model)
        m = "onepiece:block/" + pid
        dump(f"{res}/assets/onepiece/blockstates/{pid}.json", {"variants": {
            "facing=north": {"model": m}, "facing=east": {"model": m, "y": 90},
            "facing=south": {"model": m, "y": 180}, "facing=west": {"model": m, "y": 270}}})
        dump(f"{res}/assets/onepiece/items/{pid}.json", {"model": {"type": "minecraft:model", "model": m}})
        dump(f"{res}/data/onepiece/loot_table/blocks/{pid}.json", {
            "type": "minecraft:block", "random_sequence": "onepiece:blocks/" + pid,
            "pools": [{"rolls": 1, "condition": {"type": "minecraft:survives_explosion"},
                       "entries": [{"type": "minecraft:item", "name": "onepiece:" + pid}]}]})
        recipes[pid] = recipe_json(p)
        dump(f"{res}/data/onepiece/recipe/{pid}.json", recipes[pid])
        lang["block.onepiece." + pid] = p["name"]
        descs["onepiece:" + pid] = p["desc"]
        tool = TOOL.get(p["mat"])
        if tool:
            tags["mineable/" + tool].append("onepiece:" + pid)
        if p.get("climbable"):
            tags["climbable"].append("onepiece:" + pid)
        kinds["solid_top" if p["cat"] == "top" else "other"].append("onepiece:" + pid)
        boxes = ", ".join(java_box(b) for b in p["boxes"])
        maker = f'storage("{pid}", {p["storage"]}, ' if p.get("storage") else f'furniture("{pid}", '
        if p.get("storage"):
            storage.append(const(pid))
        fields.append(f'\tpublic static final Block {const(pid)} = {maker}{COPY[p["mat"]]}, {p.get("light", 0)}, '
                      f'Mount.{p.get("mount", "FLOOR")}, {p.get("seat", 0)}, {str(p.get("solid", True)).lower()},\n\t\t\t{boxes});')
        if p["mat"] in ("wood", "wool"):
            burn = (30, 60) if p["mat"] == "wool" else (5, 20)
            flam.append(f"\t\tflammable.add({const(pid)}, {burn[0]}, {burn[1]});")

    java = open(HERE + "/FurnitureBlocks.java.in").read()
    java = java.replace("%%BLOCKS%%", "\n".join(fields)).replace("%%FLAMMABLE%%", "\n".join(flam))
    java = java.replace("%%ALL%%", ",\n\t\t\t".join(const(p["id"]) for p in allp))
    java = java.replace("%%STORAGE%%", ",\n\t\t\t".join(storage))
    path = source + "/src/main/java/com/onepiecemod/furniture/FurnitureBlocks.java"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w").write(java)

    dump(f"{res}/assets/onepiece_furniture/lang/en_us.json", lang)
    for tag, ids in tags.items():
        path = f"{res}/data/minecraft/tags/block/{tag}.json"
        old = json.load(open(path)) if os.path.exists(path) else {"replace": False, "values": []}
        values = old.get("values", [])
        values += [i for i in ids if i not in values]
        old["values"] = values
        dump(path, old)
    dump(HERE + "/descriptions.json", descs)
    dump(os.environ.get("FURNITURE_KINDS_OUT", "/mnt/project-files/one-piece-mod/furniture/furniture-blocks.json"), kinds)
    check_clashes(recipes, [res + "/data/onepiece/recipe"] + ([vanilla] if vanilla else []))
    print(len(allp), "furniture blocks written to", source)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)

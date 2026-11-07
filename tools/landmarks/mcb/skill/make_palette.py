"""Generate a palette.json from a mod's resource assets.

Usage:
    python make_palette.py <path-to-assets-or-mod-root> [-o palette.json]

Finds every assets/<namespace>/blockstates/*.json, reads block property values
(facing, half, type...) from the variants/multipart, picks up display names from
lang/en_us.json when present, and guesses a shape "kind" (stairs, slab, wall...)
and a "family" (e.g. copper_bricks groups copper_bricks, copper_bricks_stairs...).

Edit the result by hand to add notes ("rough texture", "glowing", "roof only").
"""
import argparse
import json
import os
import re

KINDS = ["stairs", "slab", "wall", "fence_gate", "fence", "door", "trapdoor", "pane",
         "button", "pressure_plate", "log", "wood", "planks", "lamp", "lantern",
         "glass", "carpet", "leaves", "ore", "bricks", "block"]


def guess_kind(name):
    for k in KINDS:
        if name.endswith("_" + k) or name == k or ("_" + k + "_") in name:
            return k
    return "block"


def family(name):
    base = re.sub(r"_(stairs|slab|wall|fence_gate|fence|button|pressure_plate)$", "", name)
    return base


def props_from_blockstate(data):
    props = {}

    def add(k, v):
        props.setdefault(k, set()).add(str(v))

    for key in (data.get("variants") or {}):
        if key:
            for pair in key.split(","):
                if "=" in pair:
                    k, v = pair.split("=", 1)
                    add(k, v)
    for part in data.get("multipart", []) or []:
        when = part.get("when") or {}
        conds = when.get("OR") or when.get("AND") or [when]
        for cond in conds:
            for k, v in cond.items():
                for vv in str(v).split("|"):
                    add(k, vv)
    return {k: sorted(v) for k, v in props.items()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root")
    ap.add_argument("-o", "--out", default="palette.json")
    args = ap.parse_args()

    blocks, mod_ns = {}, set()
    for dirpath, _, files in os.walk(args.root):
        parts = dirpath.replace("\\", "/").split("/")
        if "blockstates" not in parts:
            continue
        i = parts.index("blockstates")
        if i == 0 or parts[i - 2:i - 1] != ["assets"]:
            continue
        ns = parts[i - 1]
        mod_ns.add(ns)
        lang = {}
        lang_path = os.path.join(os.path.dirname(dirpath), "lang", "en_us.json")
        if os.path.exists(lang_path):
            with open(lang_path, encoding="utf-8") as f:
                lang = json.load(f)
        for fn in sorted(files):
            if not fn.endswith(".json"):
                continue
            name = fn[:-5]
            with open(os.path.join(dirpath, fn), encoding="utf-8") as f:
                data = json.load(f)
            entry = {"kind": guess_kind(name), "family": family(name)}
            props = props_from_blockstate(data)
            if props:
                entry["states"] = props
            display = lang.get(f"block.{ns}.{name}")
            if display:
                entry["display"] = display
            entry["notes"] = ""
            blocks[f"{ns}:{name}"] = entry

    out = {"mod": sorted(mod_ns), "blocks": blocks}
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    print(f"Wrote {len(blocks)} blocks from namespaces {sorted(mod_ns)} to {args.out}")


if __name__ == "__main__":
    main()

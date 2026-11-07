#!/usr/bin/env python3
"""Adds the furniture tooltips (descriptions.json, written by gen_furniture.py) to
src/main/resources/onepiece/item_descriptions.json without touching other threads' hand-added lines."""
import json, os, sys
here = os.path.dirname(os.path.abspath(__file__))
source = sys.argv[1] if len(sys.argv) > 1 else "/mnt/project-files/one-piece-mod/source"
path = source + "/src/main/resources/onepiece/item_descriptions.json"
data = json.load(open(path))
data.update(json.load(open(here + "/descriptions.json")))
with open(path, "w") as f:
    json.dump(dict(sorted(data.items())), f, indent="\t", ensure_ascii=False)
    f.write("\n")
print(len(data), "descriptions ->", path)

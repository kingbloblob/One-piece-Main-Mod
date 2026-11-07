"""Keeps vanilla monsters (zombies, creepers, skeletons...) and bats from spawning inside the mod's structures.

Run:  python3 structure_spawns.py [path to source/]
Sets "spawn_overrides" in every data/onepiece/worldgen/structure/*.json so the "monster" and "ambient" groups have
no spawns inside the structure's pieces. Pirates and Marines there are the structure's own guards (com.onepiecemod.npc).
Animals ("creature") are left alone. A structure that already lists its own monster spawns is left alone too.
Safe to rerun; run it again after (re)generating structure files.
"""
import json
import os
import sys

SRC = sys.argv[1] if len(sys.argv) > 1 else '/mnt/project-files/one-piece-mod/source'
DIR = os.path.join(SRC, 'src/main/resources/data/onepiece/worldgen/structure')
EMPTY = {"bounding_box": "piece", "spawns": []}

changed = 0
for name in sorted(os.listdir(DIR)):
    if not name.endswith('.json'):
        continue
    path = os.path.join(DIR, name)
    with open(path) as f:
        data = json.load(f)
    overrides = data.get('spawn_overrides') or {}
    if overrides.get('monster', {}).get('spawns'):
        continue  # this structure picked its own monsters on purpose
    new = dict(overrides)
    new['monster'] = EMPTY
    new['ambient'] = EMPTY
    if new != overrides:
        data['spawn_overrides'] = new
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
            f.write('\n')
        changed += 1
print('no-monster spawn overrides set on %d structures' % changed)

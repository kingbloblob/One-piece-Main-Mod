"""Merge this thread's world files into the newest shared zip without touching other threads' work."""
import os, shutil, json, sys
SRC = '/tmp/claude-0/sync/one-piece-mod'
DST = sys.argv[1]
R = 'src/main/resources'
OWNED_DIRS = [f'{R}/data/onepiece/structure', f'{R}/data/onepiece/worldgen', f'{R}/data/onepiece/tags/worldgen',
              f'{R}/data/onepiece/loot_table/chests', f'{R}/assets/onepiece_world', 'src/main/java/com/onepiecemod/world']
OWNED_FILES = [f'{R}/onepiece/guards.json']
MY_BLOCKS = ['seastone_ore', 'deepslate_seastone_ore', 'seastone_block', 'adam_log', 'adam_planks', 'island_cloud', 'sea_cloud']
MY_ITEMS = MY_BLOCKS + ['raw_seastone', 'seastone_ingot', 'seastone_jitte', 'seastone_cuffs']
for n in MY_BLOCKS:
    OWNED_FILES += [f'{R}/data/onepiece/loot_table/blocks/{n}.json', f'{R}/assets/onepiece/blockstates/{n}.json',
                    f'{R}/assets/onepiece/models/block/{n}.json', f'{R}/assets/onepiece/textures/block/{n}.png']
OWNED_FILES += [f'{R}/assets/onepiece/models/block/adam_log_horizontal.json', f'{R}/assets/onepiece/textures/block/adam_log_top.png']
for n in MY_ITEMS:
    OWNED_FILES += [f'{R}/assets/onepiece/items/{n}.json']
for n in ['raw_seastone', 'seastone_ingot', 'seastone_jitte', 'seastone_cuffs']:
    OWNED_FILES += [f'{R}/assets/onepiece/models/item/{n}.json', f'{R}/assets/onepiece/textures/item/{n}.png']
for f in os.listdir(f'{SRC}/{R}/data/onepiece/recipe'):
    if ('seastone' in f or 'adam' in f) and f not in ('seastone_jitte.json', 'seastone_cuffs.json'):  # those two are made at the Seastone Workbench
        OWNED_FILES.append(f'{R}/data/onepiece/recipe/{f}')
for d in OWNED_DIRS:
    shutil.rmtree(f'{DST}/{d}', ignore_errors=True)
    shutil.copytree(f'{SRC}/{d}', f'{DST}/{d}')
for f in OWNED_FILES:
    os.makedirs(os.path.dirname(f'{DST}/{f}'), exist_ok=True); shutil.copy(f'{SRC}/{f}', f'{DST}/{f}')
# vanilla tag files are shared: union of values
TAGS = f'{R}/data/minecraft/tags'
for root, _, fs in os.walk(f'{SRC}/{TAGS}'):
    for fn in fs:
        rel = os.path.relpath(os.path.join(root, fn), SRC)
        mine = json.load(open(f'{SRC}/{rel}'))
        if os.path.exists(f'{DST}/{rel}'):
            theirs = json.load(open(f'{DST}/{rel}'))
            vals = theirs.get('values', [])
            for v in mine['values']:
                if v not in vals: vals.append(v)
            theirs['values'] = vals; mine = theirs
        os.makedirs(os.path.dirname(f'{DST}/{rel}'), exist_ok=True)
        json.dump(mine, open(f'{DST}/{rel}', 'w'), indent=2)
# README: replace this thread's section
rd = open(f'{DST}/README.md').read()
new = open('/tmp/claude-0/gen/readme_world.md').read().strip('\n') + '\n'
start = rd.find('## The world:')
if start >= 0:
    nxt = rd.find('\n## ', start + 5)
    rd = rd[:start] + new + (rd[nxt + 1:] if nxt >= 0 else '')
else:
    rd = rd.rstrip('\n') + '\n\n' + new
open(f'{DST}/README.md', 'w').write(rd)
# main entry point must call WorldFeature
p = f'{DST}/src/main/java/com/onepiecemod/OnePieceMod.java'
assert 'WorldFeature.initialize()' in open(p).read()
print('merged')

"""Gives each island biome its own look and sound: fog colour, haze, ambient particles and (once the songs exist) island music.

Safe to rerun. The worldgen generators (tools/worldgen/gen_biomes.py, gen_boss_islands.py, tools/dimensions/gen_dimensions.py)
rewrite biome files from scratch, so they call this script at the end to put the island look back.

Usage: python3 island_look.py [source dir]   (default: $ONEPIECE_SOURCE or the shared source)
"""
import json, os, sys

SRC = sys.argv[1] if len(sys.argv) > 1 else os.environ.get('ONEPIECE_SOURCE', '/mnt/project-files/one-piece-mod/source')
BIOMES = f'{SRC}/src/main/resources/data/onepiece/worldgen/biome'
SOUNDS = f'{SRC}/src/main/resources/assets/onepiece_sounds/sounds.json'

# biome: fog colour (only set when the biome has none), fog distance multiplier, particles [(type, chance)]
LOOK = {
    'amazon_lily':    {'fog': '#d4f0cc'},
    'conomi_islands': {'fog': '#c4ecff'},
    'dressrosa':      {'fog': '#ffe0c4', 'particles': [('minecraft:cherry_leaves', 0.0015)]},
    'elbaph':         {'fog': '#dfe6ff', 'haze': 0.75, 'particles': [('minecraft:snowflake', 0.004)]},
    'enies_lobby':    {'fog': '#fff3cf'},
    'god_valley':     {'fog': '#fff4d6'},
    'green_bit':      {'fog': '#c8ecd0'},
    'jaya':           {'fog': '#f2ecc6'},
    'marineford':     {'fog': '#e0f0ff'},
    'orange_town':    {'fog': '#ffe4c0'},
    'zou':            {'fog': '#d8ecff', 'particles': [('minecraft:falling_spore_blossom', 0.0008)]},
    'drum_island':    {'haze': 0.6, 'particles': [('minecraft:snowflake', 0.008)]},
    'punk_hazard_frozen': {'haze': 0.6, 'particles': [('minecraft:snowflake', 0.006)]},
    'alabasta':       {'haze': 0.7, 'particles': [('minecraft:white_ash', 0.003)]},
    'wano':           {'particles': [('minecraft:cherry_leaves', 0.004)]},
    'withered_forest': {'particles': [('minecraft:orange_poplar_leaves', 0.003)]},
    'little_garden':  {'haze': 0.8},
}

# Island songs from the music thread (onepiece_sounds). Only used once that sound id exists in sounds.json.
MUSIC = {
    'winter':     ['drum_island'],
    'desert':     ['alabasta', 'kuri'],
    'wano':       ['wano'],
    'sky':        ['skypiea'],
    'spooky':     ['thriller_bark', 'withered_forest'],
    'marine':     ['marineford'],
    'tropical':   ['conomi_islands'],
    'east_blue':  ['east_blue', 'orange_town'],
    'fishman':    ['fishman_reef'],
    'sabaody':    ['sabaody'],
    'dressrosa':  ['dressrosa', 'green_bit'],
    'whole_cake': ['whole_cake', 'cacao_island'],
    'egghead':    ['egghead'],
    'giants':     ['elbaph'],
    'jungle':     [],
    'prison':     ['impel_down_blazing_hell', 'impel_down_freezing_hell'],
    'holy':       ['red_line', 'red_line_heights'],
    'ancient':    ['void_century_ruins', 'god_valley'],
    'newkama':    ['newkama_land'],
    # 2026-11-05 (tools/sounds/music_isles.py): islands that used to share a theme got their own.
    'punk_hazard':   ['punk_hazard_burning', 'punk_hazard_frozen'],
    'loguetown':     ['loguetown'],
    'enies_lobby':   ['enies_lobby'],
    'onigashima':    ['onigashima'],
    'zou':           ['zou'],
    'amazon_lily':   ['amazon_lily'],
    'jaya':          ['jaya'],
    'little_garden': ['little_garden'],
    'kuraigana':     ['kuraigana'],
    'hachinosu':     ['hachinosu'],
}

sounds = json.load(open(SOUNDS)) if os.path.exists(SOUNDS) else {}
changed = 0
for name in sorted(set(LOOK) | {b for bs in MUSIC.values() for b in bs}):
    path = f'{BIOMES}/{name}.json'
    if not os.path.exists(path):
        print('missing biome', name); continue
    biome = json.load(open(path))
    before = json.dumps(biome, sort_keys=True)
    a = biome.setdefault('attributes', {})
    look = LOOK.get(name, {})
    if 'fog' in look:
        a.setdefault('minecraft:visual/fog_color', look['fog'])
    if 'haze' in look:
        a['minecraft:visual/fog_end_distance'] = {'argument': look['haze'], 'modifier': 'multiply'}
    for kind, chance in look.get('particles', []):
        p = a.setdefault('minecraft:visual/ambient_particles', {'argument': [], 'modifier': 'append'})
        if not any(e['particle']['type'] == kind for e in p['argument']):
            p['argument'].append({'particle': {'type': kind}, 'probability': chance})
    for song, biomes in MUSIC.items():
        if name in biomes and f'music.island.{song}' in sounds:
            a['minecraft:audio/background_music'] = {'default': {
                'sound': f'onepiece_sounds:music.island.{song}', 'min_delay': 600, 'max_delay': 2400, 'replace_current_music': True}}
    if json.dumps(biome, sort_keys=True) != before:
        with open(path, 'w') as f:
            json.dump(biome, f, indent=2); f.write('\n')
        changed += 1
print('island look: changed', changed, 'biomes; island songs found:', sorted(k for k in sounds if k.startswith('music.island.')))

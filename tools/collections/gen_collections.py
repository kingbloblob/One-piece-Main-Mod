#!/usr/bin/env python3
"""Writes src/main/resources/onepiece/collections.json for the Collector's Log (com.onepiecemod.collection).

Islands come from locations.json (every named One Piece place) grouped into seas by hand below.
The locals of a place (who lives there) come from locations.json "homes" and characters.json roles:
  boss   -> "Defeat <name>"
  quest  -> "Finish <name>'s first quest"
  trader -> "Meet <name>"
Swords come from the SWORDS list below; their "where to find" hint comes from item_sources.json or the HINTS here.

Usage: python3 tools/collections/gen_collections.py [source dir, default: the shared source]
Safe to rerun. Add a new place to a REGION list, or it lands in "paradise" with a warning.
"""
import json
import os
import sys

SRC = sys.argv[1] if len(sys.argv) > 1 else '/mnt/project-files/one-piece-mod/source'
RES = os.path.join(SRC, 'src/main/resources/onepiece')

REGIONS = [
    # id, title, base berries for finishing one island there, rewards for finishing every island there
    ('east_blue', 'The East Blue', 60, {'berries': 1500, 'xp': 400, 'items': ['onepiece:eternal_pose']}, [
        'foosha_village', 'dadan_hideout', 'gray_terminal', 'shells_town', 'buggy_big_top', 'syrup_village',
        'baratie', 'arlong_park', 'cocoyasi_village', 'loguetown']),
    ('paradise', 'Paradise', 150,
     {'berries': 4000, 'xp': 900, 'items': ['onepiece:shandora_gold_ingot*8', 'onepiece:grand_line_wall_map']}, [
        'twin_capes_lighthouse', 'whisky_peak', 'little_garden_camp', 'drum_castle', 'nanohana_port', 'yuba_oasis',
        'rain_dinners', 'alubarna_palace', 'banaro_island', 'mock_town', 'cricket_house', 'giant_jack', 'angel_beach',
        'shandora', 'weatheria', 'davy_back_stage', 'galley_la_dock', 'franky_house', 'sea_train_station',
        'tequila_wolf', 'tower_of_justice', 'going_merry_farewell', 'thriller_bark', 'sabaody_park', 'shakky_bar',
        'auction_house', 'straw_shrine', 'kamazo_hideout', 'navarone', 'amazon_lily', 'rusukaina', 'boin_archipelago',
        'momoiro_island', 'kuraigana_castle', 'ohara_library', 'baltigo', 'marineford', 'fishman_district',
        'ryugu_palace']),
    ('new_world', 'The New World', 300,
     {'berries': 9000, 'xp': 2000, 'items': ['onepiece:supreme_whetstone*2', 'minecraft:netherite_ingot*2']}, [
        'punk_hazard_lab', 'ice_fortress', 'g5_base', 'dressrosa_palace', 'toy_house', 'corrida_colosseum',
        'mokomo_dukedom', 'whole_cake_chateau', 'chocolate_town', 'mirror_hall', 'wano_house', 'flower_capital',
        'ebisu_town', 'udon_prison', 'onigashima', 'flame_fortress', 'egghead_lab', 'elbaph_tree', 'victoria_punk',
        'withered_forest', 'hachinosu', 'moby_dick', 'god_valley', 'laugh_tale']),
    ('impel_down', 'Impel Down', 250,
     {'berries': 5000, 'xp': 1200, 'items': ['minecraft:enchanted_golden_apple*2']}, [
        'impel_down', 'blazing_hell_furnace', 'freezing_hell_cells', 'newkama_land', 'eternal_hell_vault']),
    ('red_line', 'The Holy Land', 500,
     {'berries': 8000, 'xp': 2000, 'items': ['minecraft:nether_star']}, [
        'mary_geoise', 'pangaea_castle', 'celestial_mansion', 'void_century_ruins']),
]

# Generic builds that appear many times (outposts, camps, wrecks, caves) are not islands to finish.
SKIP = {'den_den_outpost', 'pirate_camp', 'sea_king_bones', 'sunken_galleon', 'treasure_grotto', 'ancient_ruins',
        'marine_bunker', 'smile_factory', 'marine_base', 'marine_battleship'}

SWORDS = [
    # Meito and famous blades
    'wado_ichimonji', 'sandai_kitetsu', 'shusui', 'enma', 'ame_no_habakiri', 'shodai_kitetsu', 'yoru', 'ace',
    'kikoku', 'gryphon', 'shigure', 'soul_solid', 'kiribachi', 'tamahagane_katana', 'kokuto_blade',
    # Legendary weapons of the great pirates and Marines
    'seastone_jitte', 'neko_no_te', 'golden_hook', 'nonosama_bo', 'punisher', 'mogura', 'homie_umbrella',
    'murakumogiri', 'hassaikai', 'sorcery_clima_tact',
]

HINTS = {
    'wado_ichimonji': 'Zoro hands it over when he teaches you Santoryu.',
    'ame_no_habakiri': "Kozuki Oden's second sword. A prize of the Beasts Pirates raid.",
    'ace': "Gol D. Roger's sword. The prize of the Roger Pirates raid, the last sword in the game.",
    'shodai_kitetsu': 'Forged from a Sandai Kitetsu: the late-game reforge.',
    'tamahagane_katana': 'Forged from Wano tamahagane steel.',
    'kokuto_blade': 'Forged from kokuto, the black steel of the deep.',
}

SHIP_HINTS = {
    'going_merry': "Kaya's gift at Syrup Village. Sail her to fill in the page.",
    'thousand_sunny': "Franky's masterpiece after Enies Lobby.",
    'polar_tang': "The Heart Pirates' submarine. Seen in Paradise and the New World.",
    'miss_love_duck': "Alvida's ship. Sails the East Blue.",
    'big_top': "Buggy's circus ship. East Blue and early Paradise.",
    'bezan_black': "Captain Kuro's ship, the Black Cat Pirates. Early Paradise waters.",
    'marine_warship': 'Marine patrols from the East Blue to Paradise.',
    'marine_battleship': 'Marine battleships guard the New World.',
    'victoria_punk': "Eustass Kid's scrap ship. New World waters.",
    'red_force': "Shanks's flagship. Only the strongest seas.",
}


def main():
    locations = json.load(open(os.path.join(RES, 'locations.json')))
    characters = {c['id']: c for c in json.load(open(os.path.join(RES, 'characters.json')))}
    sources = {s['item']: s for s in json.load(open(os.path.join(RES, 'item_sources.json')))}
    descriptions = json.load(open(os.path.join(RES, 'item_descriptions.json')))

    placed = {}
    for region, *_rest in REGIONS:
        for place in _rest[-1]:
            placed[place] = region
    for place in locations['locations']:
        if place not in placed and place not in SKIP:
            print('WARNING: no sea for', place, '- putting it in paradise')
            placed[place] = 'paradise'
            REGIONS[1][4].append(place)

    homes = {}
    for character, place in locations['homes'].items():
        homes.setdefault(place, []).append(character)

    islands = []
    regions = []
    for region, title, berries, reward, places in REGIONS:
        regions.append({'id': region, 'title': title, 'reward': reward})
        for place in places:
            if place not in locations['locations']:
                print('WARNING: unknown place', place)
                continue
            goals = [{'type': 'visit', 'text': 'Set foot there'},
                     {'type': 'explore', 'text': 'Explore it for a minute', 'seconds': 60}]
            for who in sorted(homes.get(place, []), key=lambda c: (characters.get(c, {}).get('role') != 'boss', c)):
                c = characters.get(who)
                if c is None:
                    continue
                if c['role'] == 'boss':
                    goals.append({'type': 'boss', 'character': who, 'text': 'Defeat ' + c['name']})
                elif c['role'] == 'quest' and c.get('quests'):
                    goals.append({'type': 'quest', 'character': who, 'text': 'Finish ' + c['name'] + "'s first quest"})
                else:
                    goals.append({'type': 'meet', 'character': who, 'text': 'Meet ' + c['name']})
            people = len(goals) - 2
            islands.append({
                'id': place,
                'name': locations['locations'][place],
                'region': region,
                'goals': goals,
                'reward': {'berries': int(berries * (1 + 0.5 * people)), 'xp': int(berries / 2 * (1 + 0.5 * people))},
            })

    stations = {}
    for recipe in json.load(open(os.path.join(RES, 'station_recipes.json'))):
        stations.setdefault(recipe['result'], recipe['station'])
    data_dir = os.path.join(SRC, 'src/main/resources/data')
    recipe_text = loot_text = ''
    for root, _dirs, files in os.walk(data_dir):
        for name in files:
            if name.endswith('.json') and ('/recipe' in root or '/loot_table' in root):
                text = open(os.path.join(root, name)).read()
                if '/recipe' in root:
                    recipe_text += text
                else:
                    loot_text += text
    drops = json.dumps([{k: v for k, v in c.items() if k != 'heldItem'} for c in characters.values()])

    swords = []
    for sword in SWORDS:
        item = 'onepiece:' + sword
        hint = HINTS.get(sword)
        if sword in HINTS:
            pass
        elif item in sources:
            s = sources[item]
            hint = hint or s['title'] + ('. ' + s['notes'][0] if s.get('notes') else '')
        elif item in stations:
            hint = hint or 'Made at the ' + stations[item].replace('_', ' ').title() + '.'
        elif '"' + item + '"' in recipe_text:
            hint = hint or 'Crafted.'
        elif '"' + item + '"' in loot_text or '"' + item + '"' in drops:
            hint = hint or descriptions.get(item, 'Found out on the Grand Line.')
        else:
            print('skipping', item, '- no way to get it in survival')
            continue
        swords.append({'item': item, 'hint': hint})

    ships = []
    ship_dir = os.path.join(SRC, 'src/main/resources/data/onepiece/ships')
    ship_items = {'going_merry', 'thousand_sunny', 'polar_tang'}
    for name in sorted(os.listdir(ship_dir)):
        spec = json.load(open(os.path.join(ship_dir, name)))
        ship = name[:-5]
        icon = 'onepiece:' + ship if ship in ship_items else (
            'minecraft:birch_boat' if spec.get('faction') == 'marine' else 'minecraft:dark_oak_boat')
        ships.append({'id': ship, 'name': spec['name'], 'crew': spec.get('crew') or '', 'faction': spec.get('faction', 'pirate'),
                      'length': spec.get('length', 0), 'icon': icon, 'hint': SHIP_HINTS.get(ship, 'Out on the open sea.')})
    order = list(SHIP_HINTS)
    ships.sort(key=lambda s: order.index(s['id']) if s['id'] in order else 99)

    out = {
        '_help': 'Generated by tools/collections/gen_collections.py. Edit the script, not this file.',
        'tabs': {
            # Rewards when this many entries of a tab are collected. "all" = every entry.
            'fish': {'milestones': {'6': 150, '12': 400, 'all': 1500}, 'items': ['onepiece:all_blue_full_course*3'], 'xp': 600},
            'food': {'milestones': {'10': 150, '25': 400, 'half': 800, 'all': 2500}, 'items': ['minecraft:enchanted_golden_apple'], 'xp': 800},
            'ships': {'milestones': {'3': 200, '6': 600, 'all': 2500}, 'items': ['onepiece:grand_line_wall_map'], 'xp': 800},
            'swords': {'milestones': {'5': 300, '12': 1000, '18': 2500, 'all': 6000}, 'items': ['onepiece:supreme_whetstone*3'], 'xp': 1500},
            'islands': {'milestones': {'5': 300, '20': 1200, '40': 3000, 'all': 15000}, 'items': ['minecraft:nether_star*2'], 'xp': 3000},
        },
        'ships': ships,
        'swords': swords,
        'regions': regions,
        'islands': islands,
    }
    path = os.path.join(RES, 'collections.json')
    with open(path, 'w') as f:
        json.dump(out, f, indent=1, ensure_ascii=False)
        f.write('\n')
    print('wrote', path, len(islands), 'islands', len(swords), 'swords', len(ships), 'ships')


if __name__ == '__main__':
    main()

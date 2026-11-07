"""Paints the skins for the townsfolk (package com.onepiecemod.town).

Run:  PYTHONDONTWRITEBYTECODE=1 python3 gen_town_skins.py [path to source/] [--preview out.png]
Writes assets/onepiece/textures/entity/townsfolk/<group>_<n>.png and the generated TownSkins.java.

Same idea as tools/npcs/gen_npc_skins.py: every group is a recipe that returns an outfit spec for
tools/skins/outfits.py, and each skin rolls its own skin tone, hair, face and colours.
Groups are named in src/main/resources/onepiece/towns.json (cultures and jobs).
"""
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'skins'))
from PIL import Image
from outfits import build
from skinkit import preview

SRC = next((a for a in sys.argv[1:] if not a.startswith('--') and not a.endswith('.png')),
           '/mnt/project-files/one-piece-mod/source')
TEX = os.path.join(SRC, 'src/main/resources/assets/onepiece/textures/entity/townsfolk')
JAVA = os.path.join(SRC, 'src/main/java/com/onepiecemod/town/TownSkins.java')

SKINS = ['#f6d6b8', '#f2c9a0', '#e8b890', '#dca478', '#c8905e', '#b07a50', '#8f603e', '#7a5238', '#5e3e28']
DESERT_SKINS = ['#dca478', '#c8905e', '#b07a50', '#8f603e', '#7a5238', '#e8b890']
FISH_SKINS = ['#5a8ac8', '#4aa0a8', '#6a6ad0', '#3a8a6a', '#c86a6a', '#8a5ab0', '#e08a5a', '#e0a0b0']
HAIR = ['#141414', '#2a1a10', '#3a2a1a', '#5a3a1a', '#8a5a2a', '#c09040', '#e8d070', '#a03020', '#e06020', '#5a5a5a']
GREY = ['#d0d0d0', '#e8e8e8', '#b0b0b0', '#a0a0a0', '#f0f0f0']
CANDY_HAIR = ['#f080b0', '#a0d0f0', '#f0d060', '#c090f0', '#80e0b0', '#f0a060']
MEN_STYLES = ['short', 'spiky', 'slick', 'buzz', 'curly', 'side', 'bald', 'pomp', 'wavy']
WOMEN_STYLES = ['long', 'bangs', 'pony', 'wavy', 'long', 'curly']
MEN_FACES = ['beard', 'stubble', 'mustache', 'goatee', 'freckles', 'glasses', 'grin', 'scar_eye_l', 'cigarette']
WOMEN_FACES = ['freckles', 'earring_l', 'glasses', 'grin']
BRIGHT = ['#c02020', '#e06020', '#e8c040', '#30a050', '#2a6ac0', '#7a3ab0', '#e04080', '#20a0a0', '#f0f0f0', '#8a1a3a']
EARTHY = ['#8a6a4a', '#6a5a3a', '#a08060', '#5a6a4a', '#7a4a3a', '#c0a070', '#4a5a6a', '#9a7a5a', '#e0d0b0']
PASTEL = ['#f0b0c8', '#b0d8f0', '#f0e0a0', '#c8b0f0', '#b0f0d0', '#f8c8a0', '#f0f0f0']
WANO = ['#a02030', '#2a3a6a', '#3a5a3a', '#6a2a5a', '#c08030', '#2a2a2a', '#e8e0d0', '#4a6a8a', '#8a3a2a']


def apron(color, top=4):
    return lambda s: [s.front('body', x, y, color) for x in range(1, 7) for y in range(top, 12)]


def person(r, skins=SKINS, hair=HAIR, woman=None):
    woman = r.random() < 0.45 if woman is None else woman
    d = dict(skin=r.choice(skins), hair=r.choice(hair),
             hair_style=r.choice(WOMEN_STYLES if woman else MEN_STYLES), hair_len=r.randint(4, 8) if woman else r.randint(3, 5),
             face=r.sample(WOMEN_FACES if woman else MEN_FACES, r.choice([0, 1, 1, 2])))
    return d, woman


def villager(r):  # East Blue villages: Foosha, Syrup, Cocoyasi
    d, woman = person(r)
    if woman and r.random() < 0.6:
        d['top'] = dict(kind='dress', color=r.choice(BRIGHT + EARTHY + PASTEL), sleeves=r.choice(['short', 'elbow']),
                        pattern=r.choice([None, None, 'flowers', 'dots']), patcol='#f0f0f0')
    else:
        d['top'] = dict(kind=r.choice(['shirt', 'v', 'vest', 'shirt']), color=r.choice(BRIGHT + EARTHY), sleeves=r.choice(['short', 'elbow', 'long']),
                        pattern=r.choice([None, None, 'checker', 'stripes']), patcol=r.choice(EARTHY))
    d['pants'] = dict(color=r.choice(EARTHY), length=r.choice(['long', 'knee', 'capri']))
    d['shoes'] = dict(kind=r.choice(['sandal', 'shoe', 'boot']), color=r.choice(['#5a3a20', '#3a2a1a', '#6a4a2a']))
    if r.random() < 0.25:
        d['hat'] = dict(kind='straw', color='#e8c860', color2=r.choice(BRIGHT))
    if r.random() < 0.25:
        d['post'] = [apron(r.choice(['#f0f0e8', '#e0d8c0', '#c0d0e0']))]
    return d


def fisher(r):
    d, _ = person(r, woman=r.random() < 0.2)
    d['top'] = dict(kind=r.choice(['shirt', 'vest', 'v']), color=r.choice(['#f0f0f0', '#2a4a8a', '#c02020', '#e8e0c8']),
                    sleeves=r.choice(['short', 'none', 'elbow']), pattern=r.choice([None, 'hstripes', 'stripes']), patcol=r.choice(['#2a4a8a', '#f0f0f0']))
    d['pants'] = dict(color=r.choice(['#3a4a6a', '#6a5a3a', '#4a4a3a']), length=r.choice(['capri', 'knee']))
    d['shoes'] = dict(kind='boot', color=r.choice(['#e8c020', '#2a2a2a', '#3a5a3a']), **{'from': 6})
    if r.random() < 0.7:
        d['hat'] = dict(kind=r.choice(['cap', 'bandana', 'straw']), color=r.choice(['#e8c860', '#2a4a8a', '#c02020', '#f0f0f0']))
    return d


def sailor(r):  # dock hands and bar regulars: the ones who start the brawls
    d, _ = person(r, woman=r.random() < 0.15)
    d['face'] = list(set(d['face'] + [r.choice(['stubble', 'beard', 'scar_across', 'grin', 'earring_l'])]))
    d['top'] = dict(kind=r.choice(['shirt', 'vest', 'open', 'none']), color=r.choice(['#f0f0f0', '#2a3a6a', '#6a3a2a', '#3a3a3a']),
                    sleeves=r.choice(['short', 'none']), pattern=r.choice(['hstripes', None, 'hstripes']), patcol=r.choice(['#2a3a8a', '#c02020']))
    d['pants'] = dict(color=r.choice(['#2a3a5a', '#4a3a2a', '#3a3a3a']), length=r.choice(['long', 'capri']))
    d['shoes'] = dict(kind=r.choice(['boot', 'sandal', 'bare']), color='#2a1a10')
    if r.random() < 0.6:
        d['hat'] = dict(kind='bandana', color=r.choice(BRIGHT))
    if r.random() < 0.4:
        d['sash'] = (r.choice(BRIGHT), 9, 1)
    return d


def merchant(r):
    d, woman = person(r)
    d['top'] = dict(kind=r.choice(['vest', 'shirt', 'robe']), color=r.choice(BRIGHT + EARTHY), color2='#f0f0f0',
                    sleeves=r.choice(['long', 'elbow']), pattern=r.choice([None, 'dots', 'checker']), patcol=r.choice(BRIGHT))
    d['pants'] = dict(color=r.choice(EARTHY))
    d['shoes'] = dict(kind=r.choice(['shoe', 'sandal']), color='#4a2a1a')
    d['sash'] = (r.choice(BRIGHT), 8, 2)
    roll = r.random()
    if roll < 0.35:
        d['hat'] = dict(kind='bandana', color=r.choice(BRIGHT + ['#f0f0f0']), low=True)
    elif roll < 0.55:
        d['hat'] = dict(kind='top', color=r.choice(['#4a2a1a', '#2a2a2a']), color2=r.choice(BRIGHT))
    if r.random() < 0.5:
        d['post'] = [apron(r.choice(['#e8e0c8', '#5a3a2a', '#2a5a3a']), 5)]
    return d


def bartender(r):
    d, woman = person(r)
    if not woman:
        d['face'] = list(set(d['face'] + [r.choice(['mustache', 'goatee', 'cigarette'])]))
    d['top'] = dict(kind='suit', color=r.choice(['#2a2a2a', '#4a2a2a', '#3a3a4a', '#5a3a2a']), color2='#f4f4f4',
                    color3=r.choice(['#c02020', '#202020', '#e8c040']), sleeves='long')
    d['pants'] = dict(color='#2a2a2a')
    d['shoes'] = dict(kind='shoe', color='#141414')
    d['post'] = [apron('#f0f0e8', 7)]
    return d


def cook(r):
    d, _ = person(r)
    d['top'] = dict(kind='shirt', color='#f4f4f0', sleeves=r.choice(['long', 'elbow']))
    d['pants'] = dict(color=r.choice(['#2a2a2a', '#4a4a4a', '#f0f0f0', '#3a3a5a']))
    d['shoes'] = dict(kind='shoe', color='#2a2a2a')
    d['hat'] = dict(kind='top', color='#f8f8f8', color2='#f0f0f0')
    d['post'] = [apron(r.choice(['#f0f0f0', '#e8e0d0', '#c02020']), 6)]
    return d


def shipwright(r):  # Galley-La
    d, _ = person(r, woman=r.random() < 0.15)
    d['top'] = dict(kind=r.choice(['open', 'shirt', 'vest']), color=r.choice(['#e8e0c8', '#2a4a8a', '#f0f0f0', '#6a8ab0']),
                    sleeves=r.choice(['short', 'none', 'elbow']))
    d['pants'] = dict(color=r.choice(['#3a4a6a', '#5a4a3a']), length='long')
    d['shoes'] = dict(kind='boot', color='#3a2a1a')
    d['hat'] = dict(kind='cap', color=r.choice(['#e8e0c8', '#2a4a8a', '#c02020']), color2='#f0f0f0')
    d['sash'] = ('#6a4a2a', 9, 1)   # tool belt
    return d


def wano_folk(r):
    d, woman = person(r, hair=['#141414', '#1a1a1a', '#2a1a10', '#3a2a1a', '#5a5a5a'])
    d['hair_style'] = r.choice(['pony', 'long', 'bangs'] if woman else ['pony', 'buzz', 'bald', 'pony', 'short'])
    d['top'] = dict(kind='kimono', color=r.choice(WANO), color2=r.choice(['#f0f0f0', '#e8e0d0']), color3=r.choice(WANO),
                    sleeves='wide', pattern=r.choice([None, None, 'flowers', 'dots']), patcol=r.choice(['#f0f0f0', '#e8c040', '#f0a0b0']))
    d['pants'] = dict(color=r.choice(WANO))
    d['shoes'] = dict(kind=r.choice(['geta', 'sandal']), color='#6a4a2a')
    d['sash'] = (r.choice(WANO), 8, 2)
    if not woman and r.random() < 0.3:
        d['hat'] = dict(kind='bandana', color=r.choice(['#f0f0f0', '#2a3a6a']))
    return d


def alabasta_folk(r):
    d, woman = person(r, skins=DESERT_SKINS)
    d['top'] = dict(kind=r.choice(['robe', 'robe', 'shirt']), color=r.choice(['#f0e8d0', '#e8d8b0', '#c0a070', '#f0f0f0', '#a07050', '#4a6a9a']),
                    sleeves='long', pattern=r.choice([None, 'hstripes']), patcol=r.choice(['#c02020', '#2a4a8a', '#c09040']))
    d['pants'] = dict(color=r.choice(['#f0e8d0', '#c0a070', '#8a6a4a']))
    d['shoes'] = dict(kind='sandal', color='#8a6a4a')
    d['hat'] = dict(kind='bandana', color=r.choice(['#f0f0f0', '#e8d8b0', '#c02020', '#2a4a8a']), low=True)
    d['sash'] = (r.choice(['#c02020', '#2a4a8a', '#c09040', '#3a6a3a']), 8, 1)
    return d


def fishfolk(r):  # Fish-Man Island's townsfolk and merfolk visitors
    d, woman = person(r, skins=FISH_SKINS, hair=HAIR + ['#3a6ae0', '#e040a0', '#30c0c0'])
    d['top'] = dict(kind=r.choice(['shirt', 'vest', 'open', 'bikini' if woman else 'none']),
                    color=r.choice(['#f0a040', '#40c0a0', '#f06080', '#f0f0f0', '#e8c040']), sleeves=r.choice(['short', 'none']),
                    pattern=r.choice([None, 'flowers', 'dots']), patcol='#f0f0f0')
    d['pants'] = dict(color=r.choice(['#2a6a8a', '#e8e0c8', '#4a4a6a']), length=r.choice(['knee', 'short', 'long']))
    d['shoes'] = dict(kind=r.choice(['sandal', 'bare']), color='#6a4a2a')
    return d


def sabaody_folk(r):
    d, woman = person(r)
    if woman and r.random() < 0.6:
        d['top'] = dict(kind='dress', color=r.choice(PASTEL + BRIGHT), sleeves='short', pattern=r.choice([None, 'dots', 'stars']), patcol='#f0f0f0')
    else:
        d['top'] = dict(kind=r.choice(['suit', 'shirt', 'hoodie']), color=r.choice(BRIGHT + PASTEL), color2='#f0f0f0', color3=r.choice(BRIGHT),
                        sleeves=r.choice(['short', 'long']), pattern=r.choice([None, 'flowers']), patcol='#f0f0f0')
    d['pants'] = dict(color=r.choice(['#f0f0f0', '#3a3a5a', '#e8d8b0', '#2a2a2a']), length=r.choice(['long', 'knee', 'short']))
    d['shoes'] = dict(kind=r.choice(['shoe', 'sandal']), color=r.choice(['#f0f0f0', '#2a2a2a', '#c02020']))
    if r.random() < 0.35:
        d['face'] = list(set(d['face'] + ['sunglasses']))
    if r.random() < 0.3:
        d['hat'] = dict(kind=r.choice(['cowboy', 'cap', 'straw']), color=r.choice(PASTEL + BRIGHT), color2=r.choice(BRIGHT))
    return d


def totto_folk(r):  # Totto Land: candy-coloured everything
    d, woman = person(r, hair=HAIR + CANDY_HAIR)
    d['top'] = dict(kind='dress' if woman and r.random() < 0.6 else r.choice(['shirt', 'vest', 'suit']), color=r.choice(PASTEL),
                    color2='#f8f8f8', color3=r.choice(CANDY_HAIR), sleeves=r.choice(['short', 'elbow']),
                    pattern=r.choice(['dots', 'stars', 'hstripes', None]), patcol=r.choice(CANDY_HAIR + ['#f8f8f8']))
    d['pants'] = dict(color=r.choice(PASTEL), pattern=r.choice([None, 'dots']), patcol='#f8f8f8')
    d['shoes'] = dict(kind='shoe', color=r.choice(CANDY_HAIR))
    if r.random() < 0.4:
        d['hat'] = dict(kind='top', color=r.choice(PASTEL), color2=r.choice(CANDY_HAIR))
    return d


def kuja_folk(r):  # Amazon Lily: only women live here
    d, _ = person(r, woman=True, hair=['#141414', '#2a1a10', '#5a3a1a', '#e8d070', '#a03020'])
    d['hair_style'] = r.choice(['long', 'pony', 'bangs'])
    d['top'] = dict(kind=r.choice(['dress', 'bikini', 'kimono']), color=r.choice(['#c02060', '#e8c040', '#7a3ab0', '#20a0a0', '#f0f0f0']),
                    color2='#f0f0f0', color3='#e8c040', sleeves='none', pattern=r.choice([None, 'flowers']), patcol='#e8c040')
    d['pants'] = dict(color=r.choice(['#c02060', '#7a3ab0', '#2a2a2a']), length=r.choice(['long', 'short']))
    d['shoes'] = dict(kind='sandal', color='#e8c040')
    d['face'] = list(set(d['face'] + ['earring_l']))
    return d


def child(r):
    d, woman = person(r)
    d['face'] = r.sample(['freckles', 'grin'], r.choice([0, 1]))
    d['top'] = dict(kind=r.choice(['shirt', 'shirt', 'v', 'dress' if woman else 'vest']), color=r.choice(BRIGHT + PASTEL), sleeves='short',
                    pattern=r.choice([None, 'stripes', 'hstripes', 'stars']), patcol=r.choice(BRIGHT + ['#f0f0f0']))
    d['pants'] = dict(color=r.choice(EARTHY + BRIGHT[:5]), length=r.choice(['short', 'knee']))
    d['shoes'] = dict(kind=r.choice(['sandal', 'shoe', 'bare']), color='#5a3a20')
    if r.random() < 0.3:
        d['hat'] = dict(kind=r.choice(['straw', 'cap']), color=r.choice(['#e8c860'] + BRIGHT), color2=r.choice(BRIGHT))
    return d


def elder(r):
    d, woman = person(r, hair=GREY)
    d['hair_style'] = r.choice(['bald', 'short', 'side', 'slick'] if not woman else ['pony', 'curly', 'short'])
    d['face'] = list(set(r.sample(['glasses', 'mustache', 'beard'] if not woman else ['glasses'], 1)))
    d['top'] = dict(kind=r.choice(['robe', 'vest', 'shirt', 'kimono']), color=r.choice(EARTHY + ['#6a2a2a', '#2a3a5a']), color2='#f0f0f0',
                    sleeves='long')
    d['pants'] = dict(color=r.choice(EARTHY))
    d['shoes'] = dict(kind=r.choice(['sandal', 'shoe']), color='#3a2a1a')
    return d


def festival_dancer(r):  # Wano fire festival performers and Totto Land party hosts
    d, woman = person(r, hair=['#141414', '#2a1a10', '#a03020'])
    d['hair_style'] = r.choice(['pony', 'long', 'buzz'])
    d['top'] = dict(kind='kimono', color=r.choice(['#e02020', '#f08020', '#e8c040', '#f0f0f0']), color2='#f0f0f0', color3='#141414',
                    sleeves='wide', pattern='flowers', patcol=r.choice(['#f0f0f0', '#e8c040']))
    d['pants'] = dict(color='#c02020')
    d['shoes'] = dict(kind='geta', color='#6a4a2a')
    d['sash'] = ('#141414', 8, 2)
    d['hat'] = dict(kind='bandana', color=r.choice(['#f0f0f0', '#e02020']))
    return d


GROUPS = {
    'villager': (villager, 16),
    'fisher': (fisher, 10),
    'sailor': (sailor, 12),
    'merchant': (merchant, 14),
    'bartender': (bartender, 6),
    'cook': (cook, 6),
    'shipwright': (shipwright, 8),
    'wano_folk': (wano_folk, 14),
    'alabasta_folk': (alabasta_folk, 12),
    'fishfolk': (fishfolk, 10),
    'sabaody_folk': (sabaody_folk, 10),
    'totto_folk': (totto_folk, 10),
    'kuja_folk': (kuja_folk, 8),
    'child': (child, 12),
    'elder': (elder, 8),
    'festival_dancer': (festival_dancer, 6),
}


def write_java(counts):
    lines = ',\n'.join('\t\t\tMap.entry("%s", %d)' % kv for kv in counts.items())
    src = '''package com.onepiecemod.town;

import java.util.Map;

/**
 * GENERATED by tools/towns/gen_town_skins.py, do not edit by hand.
 * How many skins each townsfolk skin group has: textures/entity/townsfolk/<group>_<0..count-1>.png
 */
public final class TownSkins {
	public static final Map<String, Integer> COUNT = Map.ofEntries(
%s);

	private TownSkins() {
	}
}
''' % lines
    os.makedirs(os.path.dirname(JAVA), exist_ok=True)
    with open(JAVA, 'w') as f:
        f.write(src)


def main():
    os.makedirs(TEX, exist_ok=True)
    previews, counts = [], {}
    for gi, (group, (recipe, n)) in enumerate(GROUPS.items()):
        for i in range(n):
            r = random.Random(f'town-{group}-{i}')
            spec = {k: v for k, v in recipe(r).items() if v is not None}
            spec['post'] = [f for f in spec.get('post', []) if f]
            img = build(spec, seed=17000 + gi * 101 + i).finish(os.path.join(TEX, f'{group}_{i}.png'))
            previews.append(preview(img, 3))
        counts[group] = n
    write_java(counts)
    if '--preview' in sys.argv:
        out = sys.argv[sys.argv.index('--preview') + 1]
        cols = 16
        w, h = previews[0].size
        rows = (len(previews) + cols - 1) // cols
        sheet = Image.new('RGBA', (cols * w, rows * h), (40, 40, 48, 255))
        for k, p in enumerate(previews):
            sheet.alpha_composite(p, ((k % cols) * w, (k // cols) * h))
        sheet.save(out)
    print('painted %d townsfolk skins in %d groups' % (len(previews), len(counts)))


if __name__ == '__main__':
    main()

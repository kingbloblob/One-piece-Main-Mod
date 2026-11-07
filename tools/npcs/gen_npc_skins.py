"""Paints the skins for the pirate and Marine NPCs (package com.onepiecemod.npc).

Run:  PYTHONDONTWRITEBYTECODE=1 python3 gen_npc_skins.py [path to source/] [--preview out.png]
Writes assets/onepiece/textures/entity/npc/<group>_<n>.png and the generated NpcSkins.java (how many skins each group has).

Every group is a recipe: a function that takes a random generator and returns an outfit spec for
tools/skins/outfits.py. Each skin in a group rolls its own skin tone, hair, face and colours, so no two look alike.
To add a group: write a recipe, add it to GROUPS with how many skins it should have, rerun, then use the group name
in src/main/resources/onepiece/npc_kits.json.
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
TEX = os.path.join(SRC, 'src/main/resources/assets/onepiece/textures/entity/npc')
JAVA = os.path.join(SRC, 'src/main/java/com/onepiecemod/npc/NpcSkins.java')

SKINS = ['#f6d6b8', '#f2c9a0', '#e8b890', '#dca478', '#c8905e', '#b07a50', '#8f603e', '#7a5238', '#5e3e28']
FISH_SKINS = ['#5a8ac8', '#4aa0a8', '#6a6ad0', '#3a8a6a', '#c86a6a', '#8a5ab0', '#4a7ab8', '#e08a5a']
HAIR = ['#141414', '#1a1a1a', '#2a1a10', '#3a2a1a', '#5a3a1a', '#8a5a2a', '#c09040', '#e8d070', '#d0d0d0',
        '#a03020', '#e06020', '#5a5a5a']
WILD_HAIR = ['#e03030', '#3a6ae0', '#30b060', '#e040a0', '#a040e0', '#30c0c0', '#f0f0f0', '#f0a020']
STYLES = ['short', 'spiky', 'long', 'bangs', 'slick', 'buzz', 'afro', 'pomp', 'wavy', 'pony', 'curly', 'bald', 'side']
NEAT = ['short', 'slick', 'buzz', 'side', 'bald', 'curly', 'pony']
FACES = ['beard', 'goatee', 'stubble', 'mustache', 'scar_eye_l', 'scar_eye_r', 'scar_across', 'x_scar', 'freckles',
         'sunglasses', 'glasses', 'cigarette', 'cigar', 'grin', 'earring_l', 'earrings3', 'tattoo_left', 'dark_circles']
ROUGH = ['beard', 'stubble', 'scar_eye_l', 'scar_eye_r', 'scar_across', 'x_scar', 'grin', 'earring_l', 'earrings3',
         'tattoo_left', 'cigar', 'goatee', 'burn_left', 'tusks']
NEAT_FACES = ['mustache', 'glasses', 'stubble', 'goatee', 'cigarette', 'sunglasses', 'freckles', 'scar_eye_l']
BRIGHT = ['#c02020', '#e06020', '#e8c040', '#30a050', '#2a6ac0', '#7a3ab0', '#e04080', '#20a0a0', '#f0f0f0',
          '#202020', '#6a4a2a', '#8a1a3a', '#3a5a2a']
DULL = ['#5a4a3a', '#4a4a3a', '#3a3a4a', '#6a5a4a', '#4a3a2a', '#2a2a2a', '#5a3a2a', '#3a4a3a', '#7a6a50', '#4a2a2a']
MARINE_BLUE = '#2a4a9a'


def faces(r, pool, most=2):
    return r.sample(pool, r.choice([0, 1, 1, 2][:most + 2]))


def head(r, hair_pool=HAIR, styles=STYLES, face_pool=FACES, skins=SKINS, most=2):
    return dict(skin=r.choice(skins), hair=r.choice(hair_pool), hair_style=r.choice(styles),
                hair_len=r.randint(3, 7), face=faces(r, face_pool, most))


def collar(color):
    return [lambda s: s.band('body', 0, 2, color, cols=range(16, 24)),
            lambda s: [s.front('body', x, y, color) for (x, y) in ((2, 1), (5, 1), (3, 2), (4, 2))]]


def gull(color=MARINE_BLUE):
    """The Marines' seagull on the back of the uniform."""
    return lambda s: [s.back('body', x, y, color) for (x, y) in
                      ((0, 3), (1, 2), (2, 3), (3, 4), (4, 4), (5, 3), (6, 2), (7, 3), (3, 5), (4, 5), (3, 6))]


def wings(color='#141414'):
    """Black Lunarian wings folded on the back (Seraphim)."""
    return lambda s: [s.back('body', x, y, color) for x in (0, 1, 6, 7) for y in range(0, 9)] + \
                     [s.back('body', x, y, color) for x in (2, 5) for y in range(0, 4)]


def bandolier(color):
    return lambda s: [s.front('body', i, i + 1, color) for i in range(8)]


# ---------------- Marines ----------------

def marine_grunt(r):
    d = head(r, styles=NEAT, face_pool=NEAT_FACES, most=1)
    d.update(top=dict(kind='shirt', color='#f4f4f4', sleeves=r.choice(['long', 'long', 'elbow']), cuff=MARINE_BLUE),
             pants=dict(color=r.choice([MARINE_BLUE, '#2a3a6a', '#1e2a5a'])), shoes=dict(kind='shoe', color='#1a1a1a'),
             hat=dict(kind='marine', color='#f4f4f4', color2=MARINE_BLUE), post=collar(MARINE_BLUE) + [gull()])
    if r.random() < 0.3:
        d['sash'] = ('#2a2a2a', 9, 1)
    return d


def marine_rifle(r):
    d = marine_grunt(r)
    d['post'] = d['post'] + [bandolier(r.choice(['#5a3a20', '#3a2a1a', '#4a4a3a']))]
    d['shoes'] = dict(kind='boot', color=r.choice(['#1a1a1a', '#3a2a1a']))
    if r.random() < 0.4:
        d['hat'] = dict(kind='cap', color='#f4f4f4', color2=MARINE_BLUE)
    return d


def marine_officer(r):
    d = head(r, styles=NEAT, face_pool=NEAT_FACES)
    suit = r.choice(['#2a3a6a', '#3a3a4a', '#4a4a5a', '#f0f0f0', '#2a2a2a', '#5a4a3a'])
    d.update(top=dict(kind='suit', color=suit, color2='#f4f4f4', color3=r.choice(['#c02020', MARINE_BLUE, '#202020', '#e8c040'])),
             pants=dict(color=suit), shoes=dict(kind='shoe', color='#1a1a1a'))
    if r.random() < 0.6:
        d['hat'] = dict(kind='marine', color=r.choice(['#f4f4f4', suit]), color2=r.choice([MARINE_BLUE, '#1a2a4a']))
    if r.random() < 0.5:
        d['coat'] = dict(kind='jacket', color='#f2f2f0', kanji=True)
    else:
        d['post'] = [gull()]
    return d


def marine_captain(r):
    d = marine_officer(r)
    d['coat'] = dict(kind='cape', color='#f2f2f0', kanji=True, length=r.choice([8, 9, 10]),
                     epaulettes=r.choice(['#e8c040', None]))
    return d


def vice_admiral(r):
    d = head(r, hair_pool=HAIR + ['#e8e8e8', '#c8c8c8'], face_pool=FACES)
    suit = r.choice(BRIGHT + DULL)
    d.update(top=dict(kind=r.choice(['suit', 'suit', 'shirt', 'kimono']), color=suit, color2=r.choice(['#f4f4f4', '#202020']),
                      color3=r.choice(BRIGHT)), pants=dict(color=r.choice([suit] + DULL)),
             shoes=dict(kind=r.choice(['shoe', 'boot']), color='#141414'),
             coat=dict(kind='cape', color='#f2f2f0', kanji=True, length=r.choice([9, 10, 11]), epaulettes='#e8c040'))
    if r.random() < 0.4:
        d['hat'] = dict(kind='marine', color=r.choice(['#2a2a3a', '#f4f4f4']), color2='#e8c040')
    return d


def cp_agent(r):
    d = head(r, styles=NEAT + ['long', 'spiky'], face_pool=['sunglasses', 'glasses', 'stubble', 'goatee', 'scar_eye_l', 'mustache'])
    suit = r.choice(['#141414', '#1a1a22', '#2a2a2a', '#222230'])
    d.update(top=dict(kind='suit', color=suit, color2='#f4f4f4', color3=r.choice(['#141414', '#8a1a1a', '#2a2a2a'])),
             pants=dict(color=suit), shoes=dict(kind='shoe', color='#0a0a0a'))
    if r.random() < 0.5:
        d['hat'] = dict(kind='top', color='#141414', color2=r.choice(['#141414', '#8a1a1a']))
    if r.random() < 0.3:
        d['gloves'] = '#f0f0f0'
    return d


def cp0_agent(r):
    d = cp_agent(r)
    d['top'] = dict(kind='suit', color='#f2f2f0', color2='#202020', color3='#202020')
    d['pants'] = dict(color='#f2f2f0')
    d['shoes'] = dict(kind='shoe', color='#f2f2f0')
    d['face'] = ['mask_cp0'] if r.random() < 0.7 else r.sample(['sunglasses', 'stubble', 'goatee'], 1)
    d['hat'] = dict(kind='top', color='#f2f2f0', color2='#202020') if r.random() < 0.7 else None
    d['gloves'] = '#f2f2f0'
    return d


# Bartholomew Kuma's look, shared by the Pacifista (his copies) and S-Bear: white bear-eared cap with brown spots,
# pale mirrored rimless glasses, a black coat with a big white crosshair on the front and white paw prints on the hem,
# dark navy trousers with brown spots, brown gloves.
KUMA_SKINS = ['#a8744e', '#b07c54', '#9c6a44']
KUMA_RING = [(2, 2), (3, 2), (4, 2), (5, 2), (1, 3), (6, 3), (1, 4), (6, 4), (1, 5), (6, 5), (1, 6), (6, 6),
             (2, 7), (3, 7), (4, 7), (5, 7), (3, 4), (4, 4), (3, 5), (4, 5), (3, 0), (4, 0), (3, 9), (4, 9),
             (0, 4), (0, 5), (7, 4), (7, 5)]


def kuma_style(skin, hair='#141414', cap='#ece6d6', spots='#8a5a34', eyes='#2a2a2a'):
    def target(s):
        for (x, y) in KUMA_RING:
            s.front('body', x, y, '#f4f4f0')

    def paws(s):
        for (x, y) in ((1, 9), (2, 9), (1, 10), (2, 10), (0, 8), (1, 7), (2, 7), (3, 8)):
            s.front('leg', x, y, '#f4f4f0')

    def cap_spots(s):
        s.cap('hat', 'top', None, fn=lambda x, y: spots if (x * 3 + y * 5) % 7 == 0 and 1 < x < 6 else None)
        for col in range(1, 32, 5):
            s.w('hat', col, 0, spots, 0)

    def lenses(s):
        for x in (1, 2, 5, 6):
            s.front('head', x, 4, '#c8dcea')

    return dict(skin=skin, hair=hair, hair_style='short', hair_len=3, eyes=eyes,
                face=[('glasses', '#e4ecf2'), ('bear_ears', cap)],
                top=dict(kind='shirt', color='#1a1a1e', sleeves='long'),
                pants=dict(color='#262a40', pattern='spots', patcol=spots),
                shoes=dict(kind='shoe', color='#141414'), gloves='#6a4a2a',
                coat=dict(kind='long', color='#18181c', length=10),
                hat=dict(kind='cap', color=cap),
                post=[target, paws, cap_spots, lenses])


def pacifista(r):
    return kuma_style(r.choice(KUMA_SKINS))


# Seraphim are Lunarian: warm tan-brown skin, white hair, red eyes, black wings and a flame on the back.
SERAPHIM_SKINS = ['#b5845c', '#a87650', '#bc8c62']


def seraphim(r):
    d = head(r, hair_pool=['#f0f0f0', '#f4f4f4', '#e8e8e8'], styles=['long', 'spiky', 'side', 'wavy', 'bangs'],
             face_pool=['grin', 'closed_eyes'], skins=SERAPHIM_SKINS, most=1)
    d['eyes'] = '#c82828'
    d.update(top=dict(kind=r.choice(['v', 'shirt', 'bikini']), color=r.choice(['#f2f2f0', '#141414', '#e8c040']),
                      sleeves='short'),
             pants=dict(color=r.choice(['#202020', '#2a3a6a']), length=r.choice(['short', 'knee'])), shoes=dict(kind='boot', color='#202020'),
             post=[wings(), lambda s: [s.back('body', x, y, '#ff7a20' if y % 2 else '#ff4010') for x in (3, 4) for y in range(0, 3)]])
    return d


# The four named Seraphim hunt units (com.onepiecemod.vegapunk.HuntUnit), one skin each in this order:
# 0 S-Hawk (Mihawk), 1 S-Snake (Hancock), 2 S-Bear (Kuma), 3 S-Shark (Jinbe). All Lunarian: dark skin, white hair, black wings.
def seraphim_s(r, i):
    skin = r.choice(SERAPHIM_SKINS)
    flame = lambda s: [s.back('body', x, y, '#ff7a20' if y % 2 else '#ff4010') for x in (3, 4) for y in range(0, 3)]
    if i == 2:
        # S-Bear: a young Kuma with white hair and white bear ears, in Kuma's coat.
        d = kuma_style(skin, hair='#f2f2f2', cap='#f4f4f4', spots='#c8c8c8', eyes='#c82828')
        d['post'] = d['post'] + [wings(), flame]
        return d
    d = dict(skin=skin, hair='#f2f2f2', shoes=dict(kind='boot', color='#202020'), eyes='#c82828')
    if i == 0:
        # S-Hawk: Mihawk's plumed black hat, open shirt, long black coat, gold hawk eyes, a cross on the chest.
        d.update(hair_style='slick', hair_len=3, face=['goatee'], eyes='#e8c020',
                 top=dict(kind='open', color='#5a1a24', color2=skin, sleeves='long'),
                 coat=dict(kind='long', color='#141414', length=10), pants=dict(color='#2a2a30'),
                 hat=dict(kind='cowboy', color='#141414', color2='#c03030'))
        cross = lambda s: [s.front('body', x, y, '#3a8a5a') for (x, y) in ((3, 3), (4, 3), (3, 4), (4, 4), (2, 4), (5, 4), (3, 5), (4, 5), (3, 6), (4, 6))]
        d['post'] = [wings(), flame, cross]
    elif i == 1:
        # S-Snake: Hancock's long hair (Lunarian white), red top, long white skirt, snake earrings.
        d.update(hair_style='long', hair_len=7, face=['lips', 'earrings3'],
                 top=dict(kind='v', color='#c02040', sleeves='short'), pants=dict(color='#f0ece0', pattern='dots', patcol='#c02040'))
        d['post'] = [wings(), flame]
    else:
        # S-Shark: Jinbe's dark kimono with an orange sash, fish-man fangs, hair tied up.
        d.update(hair_style='pony', hair_len=4, face=['tusks'],
                 top=dict(kind='kimono', color='#1e2a4a', color2='#e06020', sleeves='long'), pants=dict(color='#1e2a4a'),
                 sash=('#e06020', 8, 2))
        d['post'] = [wings(), flame]
    return d

def jailer(r):
    d = head(r, styles=['buzz', 'bald', 'short'], face_pool=ROUGH, most=1)
    c = r.choice(['#1e2a5a', '#243470', '#1a2448'])
    d.update(top=dict(kind='suit', color=c, color2='#f0f0f0', color3='#e8c040', sleeves='long', cuff='#e8c040'),
             pants=dict(color=shade_ok(c)),
             shoes=dict(kind='boot', color='#1a1a1a', **{'from': 8}), gloves='#f0f0f0',
             hat=dict(kind='cap', color=r.choice(['#1a1a2a', c]), color2='#e8c040'),
             sash=('#1a1a1a', 8, 1))
    if r.random() < 0.4:
        d['face'] = list(set(d['face'] + ['sunglasses']))
    return d


def shade_ok(c):
    return c


# ---------------- Pirates ----------------

def deckhand(r):
    d = head(r, hair_pool=HAIR + WILD_HAIR[:3], face_pool=ROUGH + FACES)
    top = r.choice(['shirt', 'v', 'vest', 'none', 'open', 'shirt'])
    d.update(top=dict(kind=top, color=r.choice(BRIGHT + DULL), sleeves=r.choice(['short', 'none', 'long', 'elbow']),
                      pattern=r.choice([None, None, 'stripes', 'hstripes', 'checker']), patcol=r.choice(BRIGHT)),
             pants=dict(color=r.choice(DULL + BRIGHT[-4:]), length=r.choice(['long', 'capri', 'knee', 'short'])),
             shoes=dict(kind=r.choice(['boot', 'sandal', 'shoe', 'bare']), color=r.choice(DULL)))
    hat = r.random()
    if hat < 0.45:
        d['hat'] = dict(kind='bandana', color=r.choice(BRIGHT), color2=r.choice([None, '#f0f0f0']))
    elif hat < 0.6:
        d['hat'] = dict(kind='cap', color=r.choice(BRIGHT + DULL))
    if r.random() < 0.35:
        d['sash'] = (r.choice(BRIGHT), r.choice([8, 9]), r.choice([1, 2]))
    return d


def rookie(r):
    d = deckhand(r)
    d['hair'] = r.choice(HAIR + WILD_HAIR)
    if r.random() < 0.3:
        d['hat'] = dict(kind='straw', color='#e8c860', color2=r.choice(BRIGHT))
    return d


def pirate_captain(r):
    d = head(r, hair_pool=HAIR + WILD_HAIR, face_pool=ROUGH + FACES)
    c = r.choice(BRIGHT + DULL)
    d.update(top=dict(kind=r.choice(['shirt', 'open', 'suit', 'v']), color=r.choice(BRIGHT + DULL), color2='#f0f0f0',
                      color3=r.choice(BRIGHT), sleeves='long'),
             pants=dict(color=r.choice(DULL)), shoes=dict(kind='boot', color=r.choice(['#1a1a1a', '#3a2a1a', '#5a3a1a'])),
             coat=dict(kind=r.choice(['long', 'cape', 'long']), color=c, trim=r.choice([None, '#e8c040', '#f0f0f0']),
                       length=r.choice([8, 9, 10]), collar=r.choice([None, None, '#f0f0f0', '#8a6a4a'])),
             hat=dict(kind=r.choice(['tricorn', 'tricorn', 'cowboy', 'top']), color=r.choice(['#1a1a1a', '#2a1a1a', c]),
                      color2=r.choice(['#e8c040', None]), skull=r.random() < 0.6),
             sash=(r.choice(BRIGHT), 8, 2))
    return d


def buggy(r):
    d = deckhand(r)
    d['face'] = ['big_nose_red'] + faces(r, ['grin', 'eyeshadow', 'freckles', 'stubble'], 1)
    d['hair'] = r.choice(WILD_HAIR + ['#3a6ae0'])
    d['top'] = dict(kind=r.choice(['shirt', 'v', 'vest']), color=r.choice(['#c02020', '#e8c040', '#3a6ae0', '#e06020', '#f0f0f0']),
                    sleeves=r.choice(['short', 'long']), pattern=r.choice(['stripes', 'hstripes', 'dots', 'checker', 'stars']),
                    patcol=r.choice(['#f0f0f0', '#c02020', '#e8c040']))
    d['pants'] = dict(color=r.choice(['#e8c040', '#c02020', '#3a6ae0', '#7a3ab0']), pattern=r.choice([None, 'stripes', 'dots']),
                      patcol='#f0f0f0', length=r.choice(['long', 'capri']))
    if r.random() < 0.5:
        d['hat'] = dict(kind='top', color=r.choice(['#c02020', '#3a6ae0', '#141414']), color2=r.choice(['#e8c040', '#f0f0f0']))
    return d


def fishman(r):
    d = head(r, skins=FISH_SKINS, hair_pool=HAIR[:6] + WILD_HAIR[:2], face_pool=ROUGH + ['grin', 'tusks'])
    d['eyes'] = r.choice(['#e0c040', '#e03030', '#141414', '#f0f0f0'])
    d.update(top=dict(kind=r.choice(['none', 'open', 'shirt', 'vest', 'kimono']), color=r.choice(BRIGHT + DULL),
                      color2=d['skin'], sleeves=r.choice(['short', 'none']),
                      pattern=r.choice([None, 'flowers', 'stripes']), patcol=r.choice(BRIGHT)),
             pants=dict(color=r.choice(DULL + BRIGHT), length=r.choice(['knee', 'capri', 'short'])),
             shoes=dict(kind=r.choice(['sandal', 'geta', 'bare']), color=r.choice(DULL)))
    # gills and fins on the arms
    gill = '#2a3a5a'
    d['post'] = [lambda s: [s.side('head', w, x, 5, gill) for w in ('r', 'l') for x in (2, 4)]]
    return d


def baroque(r):
    d = head(r, hair_pool=HAIR + WILD_HAIR, face_pool=FACES)
    look = r.random()
    if look < 0.5:
        suit = r.choice(['#2a2a2a', '#5a2a2a', '#3a3a5a', '#e8e0d0'])
        d.update(top=dict(kind='suit', color=suit, color2='#f0f0f0', color3=r.choice(BRIGHT)), pants=dict(color=suit),
                 shoes=dict(kind='shoe', color='#1a1a1a'))
    else:
        d.update(top=dict(kind=r.choice(['robe', 'shirt', 'hoodie']), color=r.choice(['#e8d8b0', '#c8b890', '#f0f0f0', '#e0a040']),
                          sleeves='long'), pants=dict(color=r.choice(['#c8b890', '#8a7a5a'])),
                 shoes=dict(kind='sandal', color='#6a4a2a'), sash=(r.choice(BRIGHT), 8, 2))
    if r.random() < 0.5:
        d['hat'] = dict(kind=r.choice(['cowboy', 'top', 'bandana']), color=r.choice(DULL + BRIGHT), color2=r.choice(BRIGHT))
    if r.random() < 0.5:
        d['face'] = list(set(d['face'] + ['sunglasses']))
    return d


def bandit(r):
    d = head(r, styles=STYLES, face_pool=ROUGH, most=2)
    d.update(top=dict(kind=r.choice(['vest', 'open', 'shirt', 'none']), color=r.choice(DULL), sleeves=r.choice(['short', 'none'])),
             pants=dict(color=r.choice(DULL), length=r.choice(['long', 'capri'])),
             shoes=dict(kind=r.choice(['boot', 'sandal']), color=r.choice(DULL)),
             hat=dict(kind='bandana', color=r.choice(['#5a3a2a', '#3a3a3a', '#8a2a2a', '#4a4a2a']), low=r.random() < 0.4),
             sash=(r.choice(DULL), 9, 1))
    return d


def bounty_hunter(r):
    d = head(r, face_pool=ROUGH + ['sunglasses', 'cigarette'])
    d.update(top=dict(kind=r.choice(['shirt', 'v', 'suit']), color=r.choice(DULL), color2='#d0d0d0', color3='#2a2a2a', sleeves='long'),
             pants=dict(color=r.choice(DULL)), shoes=dict(kind='boot', color='#2a1a1a'),
             coat=dict(kind='long', color=r.choice(['#5a4a3a', '#3a3a3a', '#6a5a3a', '#2a2a2a']), length=r.choice([9, 10, 11])),
             post=[bandolier('#3a2a1a')])
    if r.random() < 0.6:
        d['hat'] = dict(kind='cowboy', color=r.choice(['#5a4a2a', '#2a2a2a', '#6a3a1a']), color2='#2a1a1a')
    return d


def donquixote(r):
    d = head(r, hair_pool=HAIR + ['#e8d070', '#e040a0'], face_pool=['sunglasses', 'sunglasses', 'grin', 'tattoo_left', 'goatee'])
    d.update(top=dict(kind=r.choice(['open', 'shirt', 'suit']), color=r.choice(['#f0f0f0', '#e04080', '#c02020', '#e8c040', '#2a2a2a']),
                      color2='#f0f0f0', color3='#e04080', sleeves='long', pattern=r.choice([None, 'stripes', 'stars']), patcol='#e04080'),
             pants=dict(color=r.choice(['#e8a0c0', '#3a3a5a', '#f0f0f0', '#c02020'])),
             shoes=dict(kind='shoe', color=r.choice(['#c02020', '#1a1a1a'])))
    if r.random() < 0.4:
        d['coat'] = dict(kind='cape', color='#e04080', collar='#f070a0', length=9)
    return d


def gifter(r):
    d = head(r, hair_pool=HAIR + WILD_HAIR, face_pool=ROUGH + ['horns', 'tusks', 'horns'])
    d.update(top=dict(kind=r.choice(['open', 'vest', 'kimono', 'none']), color=r.choice(['#3a2a4a', '#2a2a2a', '#5a3a2a', '#7a3ab0']),
                      color2=d['skin'], sleeves=r.choice(['short', 'none'])),
             pants=dict(color=r.choice(['#2a2a2a', '#4a3a2a', '#3a2a4a'])),
             shoes=dict(kind=r.choice(['boot', 'geta', 'hoof']), color=r.choice(DULL)),
             sash=(r.choice(['#c02020', '#7a3ab0', '#e8c040']), 8, 2))
    if r.random() < 0.4:
        d['coat'] = dict(kind='cape', color='#2a1a2a', collar='#e8e0d0', length=8)
    return d


def headliner(r):
    d = gifter(r)
    d['face'] = list(set(d['face'] + ['horns']))
    d['coat'] = dict(kind='long', color=r.choice(['#2a1a2a', '#3a2a2a']), collar='#f0f0f0', length=10, trim='#e8c040')
    return d


def whitebeard(r):
    d = deckhand(r)
    d['top'] = dict(kind=r.choice(['open', 'shirt', 'kimono', 'vest']), color=r.choice(['#e8e0d0', '#5a8ac8', '#e8c040', '#f0f0f0', '#c02020']),
                    color2=d['skin'], sleeves=r.choice(['short', 'long']))
    d['post'] = [lambda s: [s.back('body', x, y, '#5a2a8a') for (x, y) in
                            ((3, 2), (4, 2), (2, 3), (3, 3), (4, 3), (5, 3), (3, 4), (4, 4), (2, 5), (5, 5), (1, 3), (6, 3), (3, 6), (4, 6))]]
    return d


def blackbeard(r):
    d = head(r, hair_pool=['#141414', '#1a1a1a', '#3a2a1a', '#5a5a5a'], face_pool=ROUGH, most=2)
    d.update(top=dict(kind=r.choice(['open', 'shirt', 'vest']), color=r.choice(['#2a2a2a', '#4a2a2a', '#1a1a1a', '#3a3a2a']),
                      sleeves='long'), pants=dict(color=r.choice(['#2a2a2a', '#3a2a1a'])),
             shoes=dict(kind='boot', color='#1a1a1a'), sash=('#c02020', 8, 2))
    if r.random() < 0.5:
        d['coat'] = dict(kind='long', color='#1a1a1a', length=10)
    if r.random() < 0.5:
        d['hat'] = dict(kind='tricorn', color='#1a1a1a', skull=True)
    return d


# ---- Dungeon guards (added 2026-11-03, tools/dungeons) ----
UNDEAD_SKINS = ['#8a9a8a', '#7a8a7e', '#9aa294', '#6e7e74', '#a0a898']


def tomb_guard(r):
    """Alabasta tomb raiders: desert robes, head wraps, a gold sash."""
    d = head(r, hair_pool=['#141414', '#2a1a10', '#3a2a1a'], styles=['bald', 'buzz'], face_pool=ROUGH, skins=SKINS[3:])
    d.update(top=dict(kind='robe', color=r.choice(['#e8d8b0', '#d8c090', '#c8a870', '#e0d0b8']), sleeves='long'),
             pants=dict(color=r.choice(['#a08860', '#8a7050', '#e8d8b0'])), shoes=dict(kind='sandal', color='#6a4a2a'),
             sash=(r.choice(['#e8c040', '#2a6ac0', '#c02020']), 8, 2),
             hat=dict(kind='bandana', color=r.choice(['#f0e8d0', '#e8d8b0', '#2a6ac0'])))
    return d


def undead(r):
    """Thriller Bark's restless dead: grey-green skin, rotting pirate rags, scars."""
    d = head(r, hair_pool=['#d0d0d0', '#5a5a5a', '#2a2a2a', '#8a8a7a'], styles=['long', 'bald', 'wavy', 'spiky'],
             face_pool=['scar_across', 'x_scar', 'scar_eye_l', 'scar_eye_r', 'dark_circles', 'grin', 'closed_eyes'], skins=UNDEAD_SKINS)
    d.update(top=dict(kind=r.choice(['open', 'vest', 'kimono']), color=r.choice(['#3a3a4a', '#4a3a2a', '#2a2a2a', '#5a4a5a']),
                      color2=d['skin'], sleeves=r.choice(['short', 'none'])),
             pants=dict(color=r.choice(['#2a2a2a', '#3a2a3a', '#4a3a2a'])), shoes=dict(kind=r.choice(['bare', 'boot']), color='#2a2a2a'),
             sash=('#5a2a8a', 8, 2))
    if r.random() < 0.4:
        d['hat'] = dict(kind='tricorn', color='#2a2a2a', skull=True)
    return d


def ronin(r):
    """Wano ronin: plain kimono and hakama, a topknot, straw sandals."""
    d = head(r, hair_pool=['#141414', '#1a1a1a', '#3a2a1a', '#5a5a5a'], styles=['pony', 'long', 'slick'], face_pool=ROUGH + ['stubble'])
    d.update(top=dict(kind='kimono', color=r.choice(['#2a3a5a', '#4a3a2a', '#2a2a2a', '#5a2a2a', '#3a4a3a']), sleeves='long',
                      color2=r.choice(['#e8e0d0', '#2a2a2a'])),
             pants=dict(color=r.choice(['#2a2a2a', '#3a3a4a', '#5a4a3a'])), shoes=dict(kind='geta', color='#5a3a1a'),
             sash=(r.choice(['#e8e0d0', '#c02020', '#2a2a2a']), 8, 2))
    if r.random() < 0.4:
        d['coat'] = dict(kind='cape', color=r.choice(['#2a2a2a', '#4a3a2a']), length=8)
    return d


def smith(r):
    """Wano swordsmiths of the cursed forge: soot, a leather apron over bare arms."""
    d = head(r, hair_pool=HAIR, styles=['bald', 'buzz', 'short', 'pony'], face_pool=['beard', 'stubble', 'burn_left', 'scar_eye_l', 'goggles'])
    d.update(top=dict(kind='vest', color='#5a3a1a', color2=d['skin'], sleeves='none'),
             pants=dict(color=r.choice(['#2a2a2a', '#3a2a1a'])), shoes=dict(kind='boot', color='#1a1a1a'),
             sash=('#c02020', 8, 2), hat=dict(kind='bandana', color=r.choice(['#2a2a2a', '#e8e0d0'])))
    return d


def rocks(r):
    """Old Rocks Pirates: grizzled veterans in dark long coats with gold trim."""
    d = head(r, hair_pool=['#d0d0d0', '#8a8a8a', '#5a5a5a', '#141414'], styles=['long', 'slick', 'bald', 'wavy'],
             face_pool=['beard', 'scar_across', 'x_scar', 'scar_eye_l', 'mustache', 'cigar', 'earring_l'], most=2)
    d.update(top=dict(kind=r.choice(['shirt', 'open', 'vest']), color=r.choice(['#e8e0d0', '#4a2a2a', '#2a2a2a']), color2=d['skin'], sleeves='long'),
             pants=dict(color=r.choice(['#2a2a2a', '#3a2a1a'])), shoes=dict(kind='boot', color='#1a1a1a'),
             coat=dict(kind='long', color=r.choice(['#1a1a1a', '#2a1a2a', '#3a1a1a']), length=10, trim='#e8c040'))
    if r.random() < 0.5:
        d['hat'] = dict(kind='tricorn', color='#1a1a1a', skull=r.random() < 0.5)
    return d


def big_mom(r):
    """Big Mom Pirates: candy-coloured coats and chef whites for the Tea Party crowd, some with a pirate hat."""
    d = head(r, hair_pool=HAIR + ['#e8a0c0', '#f0f0f0', '#e8c040'], face_pool=['grin', 'mustache', 'goatee', 'freckles', 'scar_eye_l', 'earring_l'])
    d.update(top=dict(kind=r.choice(['shirt', 'suit', 'open']), color=r.choice(['#f0a0c0', '#f4e8d0', '#a0d8f0', '#f0d070', '#e86080', '#fafafa']),
                      color2='#fafafa', color3='#c02060', sleeves='long', pattern=r.choice([None, 'stripes', 'dots']), patcol=r.choice(['#c02060', '#f0f0f0', '#e8c040'])),
             pants=dict(color=r.choice(['#f4e8d0', '#6a3a2a', '#e8a0c0', '#2a2a3a'])),
             shoes=dict(kind=r.choice(['boot', 'shoe']), color=r.choice(['#6a3a2a', '#1a1a1a', '#c02060'])))
    if r.random() < 0.45:
        d['coat'] = dict(kind=r.choice(['cape', 'long']), color=r.choice(['#c02060', '#f0a0c0', '#7a3a2a']), collar='#fafafa', length=9)
    if r.random() < 0.3:
        d['hat'] = dict(kind='tricorn', color='#c02060', skull=r.random() < 0.5)
    return d


def holy_knight(r):
    """Holy Knights of Mary Geoise: white uniforms with gold trim and long capes, some masked, some with a plumed helmet."""
    d = head(r, hair_pool=HAIR + ['#f0f0f0', '#e8c040'], face_pool=['stubble', 'scar_eye_l', 'mustache', 'goatee', 'sunglasses'])
    d.update(top=dict(kind='suit', color=r.choice(['#f2f0ea', '#f4f4f4', '#e8e4d8']), color2='#d8b040',
                      color3=r.choice(['#1a1a1c', '#2a2a48']), sleeves='long'),
             pants=dict(color=r.choice(['#f2f0ea', '#e8e4d8', '#1a1a1c'])),
             shoes=dict(kind='boot', color=r.choice(['#1a1a1c', '#d8b040'])),
             coat=dict(kind='cape', color=r.choice(['#1a1a28', '#f2f0ea', '#6a1a1a']), collar='#d8b040', length=10))
    d['gloves'] = '#f2f0ea'
    if r.random() < 0.3:
        d['face'] = ['mask_cp0']
    return d


GROUPS = {
    # Marines and the World Government
    'marine_grunt': (marine_grunt, 14),
    'marine_rifle': (marine_rifle, 10),
    'marine_officer': (marine_officer, 10),
    'marine_captain': (marine_captain, 8),
    'vice_admiral': (vice_admiral, 8),
    'cp_agent': (cp_agent, 8),
    'cp0_agent': (cp0_agent, 6),
    'pacifista': (pacifista, 3),
    'seraphim': (seraphim, 4),
    'jailer': (jailer, 8),
    # Pirates and outlaws
    'deckhand': (deckhand, 20),
    'rookie': (rookie, 14),
    'pirate_captain': (pirate_captain, 12),
    'buggy': (buggy, 10),
    'fishman': (fishman, 12),
    'baroque': (baroque, 8),
    'bandit': (bandit, 8),
    'bounty_hunter': (bounty_hunter, 8),
    'donquixote': (donquixote, 8),
    'gifter': (gifter, 10),
    'headliner': (headliner, 5),
    'whitebeard': (whitebeard, 10),
    'blackbeard': (blackbeard, 6),
    # Appended last on purpose: a group's place in this list seeds its skins, so new groups go at the end.
    'seraphim_s': (seraphim_s, 4),
    'tomb_guard': (tomb_guard, 6),
    'undead': (undead, 8),
    'ronin': (ronin, 8),
    'smith': (smith, 4),
    'rocks': (rocks, 6),
    'big_mom': (big_mom, 8),
    'holy_knight': (holy_knight, 6),
}


def write_java(counts):
    lines = ',\n'.join('\t\t\tMap.entry("%s", %d)' % kv for kv in counts.items())
    src = '''package com.onepiecemod.npc;

import java.util.Map;

/**
 * GENERATED by tools/npcs/gen_npc_skins.py, do not edit by hand.
 * How many skins each NPC skin group has: textures/entity/npc/<group>_<0..count-1>.png
 */
public final class NpcSkins {
	public static final Map<String, Integer> COUNT = Map.ofEntries(
%s);

	private NpcSkins() {
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
            r = random.Random(f'{group}-{i}')
            made = recipe(r, i) if recipe.__code__.co_argcount == 2 else recipe(r)
            spec = {k: v for k, v in made.items() if v is not None}
            spec['post'] = [f for f in spec.get('post', []) if f]
            img = build(spec, seed=9000 + gi * 101 + i).finish(os.path.join(TEX, f'{group}_{i}.png'))
            previews.append(preview(img, 3))
        counts[group] = n
    write_java(counts)
    if '--preview' in sys.argv:
        out = sys.argv[sys.argv.index('--preview') + 1]
        cols = 14
        w, h = previews[0].size
        rows = (len(previews) + cols - 1) // cols
        sheet = Image.new('RGBA', (cols * w, rows * h), (40, 40, 48, 255))
        for k, p in enumerate(previews):
            sheet.alpha_composite(p, ((k % cols) * w, (k // cols) * h))
        sheet.save(out)
    print('painted %d NPC skins in %d groups' % (len(previews), len(counts)))


if __name__ == '__main__':
    main()

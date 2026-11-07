"""Cave creatures (third batch, added by the underground thread 2026-10-25): shapes, names, eggs, spawn biomes, drops.
gen_creatures.py calls add(S, D). Their Java entries in CreatureSpecies.ALL use .underground(minY, maxY), which
keeps them below the surface: they only spawn in caves between those heights, where the sky can't be seen.
"""
from gen_creatures import box, part
from creatures_more import quadruped, biped

OVERWORLD = ['#minecraft:is_overworld']


def add(S, D):
    # Prism Crab: a crab whose shell has grown Sea Prism crystals. Lives in the Seastone Grottos.
    SH, SH2, CRY = '#4f8fa8', '#6fb3c8', '#bff4ff'
    side = []
    for i, z in enumerate((-2, 1, 4)):
        side.append(part('sideleg%d' % (2 * i), (-5, 19, z), [box(-6, -0.5, -0.5, 6, 1, 1, SH)], rot=(0, 0, -0.6)))
        side.append(part('sideleg%d' % (2 * i + 1), (5, 19, z), [box(0, -0.5, -0.5, 6, 1, 1, SH)], rot=(0, 0, 0.6)))
    S['prism_crab'] = [
        part('body', (0, 0, 0), [box(-5, 15, -5, 10, 5, 10, SH, pattern='shell'),
                                 box(-2, 12, -2, 1, 3, 1, CRY), box(1, 11, 0, 1, 4, 1, CRY), box(-3, 13, 2, 1, 2, 1, CRY),
                                 box(2, 13, -3, 1, 2, 1, CRY)]),
        part('head', (0, 17, -5), [box(-3, -2, -2, 6, 2, 2, SH2, eyes='#111111'),
                                   box(-2.5, -5, -1, 1, 3, 1, SH2), box(1.5, -5, -1, 1, 3, 1, SH2)]),
        part('arm0', (-5, 17, -4), [box(-4, -1, -5, 3, 3, 5, SH2), box(-5, -2, -8, 4, 4, 3, CRY)]),
        part('arm1', (5, 17, -4), [box(1, -1, -5, 3, 3, 5, SH2), box(1, -2, -8, 4, 4, 3, CRY)]),
        *side,
    ]
    D['prism_crab'] = ('Prism Crab', SH, CRY, OVERWORLD,
                       [('onepiece:raw_seastone', 0, 1), ('minecraft:prismarine_crystals', 0, 2), ('minecraft:cod', 1, 1, 'smelt')])

    # Mogura: the giant moles of the underground. Wano's miners ride them through their tunnels.
    MO, MO2, CLAW = '#4a3d36', '#5d4f47', '#e6d7c0'
    S['cave_mole'] = quadruped(MO, 12, 9, 16, 5, 4, 8, 7, 7, c2=MO2, tail_len=3, tail_w=2, body_pat='fluff', leg_c=MO,
                               head_extra=[box(-1.5, -1, -10, 3, 3, 3, '#e88a9a'),
                                           box(-5, 3, -6, 2, 1, 3, CLAW), box(3, 3, -6, 2, 1, 3, CLAW)],
                               eyes='#1a1a1a')
    D['cave_mole'] = ('Mogura', MO, '#e88a9a', OVERWORLD,
                      [('minecraft:leather', 1, 2), ('minecraft:coal', 0, 2), ('minecraft:raw_iron', 0, 1, 'rare')])

    # Gloom Centipede: a long armoured centipede with a poison bite, from the dark deep tunnels.
    CE, CE2 = '#5a2a3a', '#a03a3a'
    body = [box(-3, 18, -9, 6, 3, 18, CE, pattern='stripes')]
    legs = []
    for i, z in enumerate((-7, -3, 1, 5)):
        legs.append(part('sideleg%d' % (2 * i), (-3, 20, z), [box(-5, -0.5, -0.5, 5, 1, 1, CE2)], rot=(0, 0, -0.7)))
        legs.append(part('sideleg%d' % (2 * i + 1), (3, 20, z), [box(0, -0.5, -0.5, 5, 1, 1, CE2)], rot=(0, 0, 0.7)))
    S['cave_centipede'] = [
        part('body', (0, 0, 0), body),
        part('head', (0, 19, -9), [box(-3, -2, -4, 6, 3, 4, CE2, eyes='#ffd040'),
                                   box(-3, 0, -6, 1, 1, 2, '#e6d7c0'), box(2, 0, -6, 1, 1, 2, '#e6d7c0'),
                                   box(-2, -5, -3, 1, 3, 1, CE2), box(1, -5, -3, 1, 3, 1, CE2)]),
        *legs,
        part('tail', (0, 19, 9), [box(-2.5, -1, 0, 5, 3, 8, CE, pattern='stripes'), box(-1, -1, 7, 2, 2, 4, CE2)]),
    ]
    D['cave_centipede'] = ('Gloom Centipede', CE, '#ffd040', OVERWORLD,
                           [('minecraft:string', 0, 2), ('minecraft:spider_eye', 0, 1), ('onepiece:berry', 2, 8, 'player')])

    # Sulfur Salamander: lives by the deep sulfur vents. Its bite burns.
    SA, SA2 = '#d9a02a', '#7a3a1a'
    S['sulfur_salamander'] = quadruped(SA, 7, 4, 16, 3, 3, 7, 4, 7, c2='#e8b83a', tail_len=12, tail_w=3, tail_rot=0.1,
                                       body_pat='spots', leg_c=SA2, head_pat='spots', eyes='#ff3010',
                                       body_extra=[box(-1, 15, -6, 2, 2, 12, '#ff6a20', pattern='band')])
    D['sulfur_salamander'] = ('Sulfur Salamander', SA, SA2, OVERWORLD,
                              [('onepiece:sulfur', 1, 3), ('minecraft:magma_cream', 0, 1), ('minecraft:blaze_powder', 0, 1, 'rare')])

    # Ancient Sentinel: a stone warrior left behind by the Void Century kingdom to guard its ruins.
    ST, ST2, GL = '#5a5f63', '#3e4347', '#5fe0e8'
    S['ancient_sentinel'] = biped(ST, 12, 13, 7, 11, 5, 14, 5, 9, 9, 8, c2=ST2, eyes=GL, arm_c=ST2, leg_c=ST2,
                                  body_pat='scales',
                                  head_extra=[box(-5.5, -10, -6, 11, 2, 9, ST), box(-1, -12, -5, 2, 2, 6, GL)],
                                  body_extra=[box(-3, 4, -4.5, 6, 6, 1, GL, pattern='swirl')])
    D['ancient_sentinel'] = ('Ancient Sentinel', ST, GL, OVERWORLD,
                             [('onepiece:ancient_glyph_stone', 0, 1), ('minecraft:gold_ingot', 0, 2),
                              ('onepiece:raw_shandora_gold', 1, 3, 'player'), ('minecraft:diamond', 1, 1, 'rare')])

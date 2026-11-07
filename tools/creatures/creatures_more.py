"""The second batch of 28 creatures (shapes + names, eggs, spawn biomes, drops).
gen_creatures.py calls add(S, D). Body-plan helpers keep each creature short:
quadruped (4 legs), biped (2 legs + arms), fish and snake. Sizes are in pixels, y = 24 is the ground.
"""
from gen_creatures import box, part


def quadruped(c, bw, bh, bl, lh, lw, hw, hh, hd, c2=None, eyes='#111111', head_up=0, leg_c=None,
              tail_len=6, tail_w=2, tail_rot=-0.3, tail_c=None, head_extra=(), body_extra=(), body_pat=None,
              head_pat=None, tail_extra=(), neck_w=4):
    bottom = 24 - lh
    top = bottom - bh
    parts = [part('body', (0, 0, 0), [box(-bw / 2, top, -bl / 2, bw, bh, bl, c, pattern=body_pat), *body_extra])]
    head = [box(-hw / 2, -hh + 2, -hd, hw, hh, hd, c2 or c, eyes=eyes, pattern=head_pat)]
    if head_up:
        head.append(box(-neck_w / 2, 0, -neck_w / 2 - 1, neck_w, head_up + 4, neck_w, c))
    parts.append(part('head', (0, top + 2 - head_up, -bl / 2 + (2 if head_up else 0)), head + list(head_extra)))
    lx = bw / 2 - lw / 2
    zf, zb = -bl / 2 + lw / 2 + 1, bl / 2 - lw / 2 - 1
    lc = leg_c or c
    for i, (x, z) in enumerate(((-lx, zf), (lx, zf), (-lx, zb), (lx, zb))):
        parts.append(part('leg%d' % i, (x, bottom, z), [box(-lw / 2, 0, -lw / 2, lw, lh, lw, lc)]))
    if tail_len:
        parts.append(part('tail', (0, top + 1, bl / 2),
                          [box(-tail_w / 2, 0, 0, tail_w, tail_w, tail_len, tail_c or c), *tail_extra], rot=(tail_rot, 0, 0)))
    return parts


def biped(c, bw, bh, bd, lh, lw, arm_len, aw, hw, hh, hd, c2=None, eyes='#111111', leg_c=None, arm_c=None,
          head_extra=(), body_extra=(), body_pat=None, head_pat=None, tail=None):
    bottom = 24 - lh
    top = bottom - bh
    parts = [part('body', (0, 0, 0), [box(-bw / 2, top, -bd / 2, bw, bh, bd, c, pattern=body_pat), *body_extra]),
             part('head', (0, top, 0), [box(-hw / 2, -hh, -hd / 2 - 1, hw, hh, hd, c2 or c, eyes=eyes, pattern=head_pat),
                                        *head_extra]),
             part('arm0', (-bw / 2, top + 1, 0), [box(-aw, 0, -aw / 2, aw, arm_len, aw, arm_c or c)]),
             part('arm1', (bw / 2, top + 1, 0), [box(0, 0, -aw / 2, aw, arm_len, aw, arm_c or c)])]
    lx = bw / 4
    for i, x in enumerate((-lx, lx)):
        parts.append(part('leg%d' % i, (x, bottom, 0), [box(-lw / 2, 0, -lw / 2, lw, lh, lw, leg_c or c)]))
    if tail:
        parts.append(part('tail', (0, bottom - 2, bd / 2), tail))
    return parts


def fish(c, bw, bh, bl, hw, hh, hd, fin, c2=None, eyes='#111111', tail_len=6, flukes=False, fin_h=10,
         head_extra=(), body_extra=(), body_pat='belly', pect=5):
    cy = 14
    parts = [part('body', (0, 0, 0), [box(-bw / 2, cy - bh / 2, -bl / 2, bw, bh, bl, c, pattern=body_pat), *body_extra]),
             part('head', (0, cy, -bl / 2), [box(-hw / 2, -hh / 2, -hd, hw, hh, hd, c2 or c, eyes=eyes), *head_extra])]
    tail = [box(-2, -2, 0, 4, 4, tail_len, c)]
    if flukes:
        tail.append(box(-fin_h / 2, -1, tail_len - 1, fin_h, 2, 5, fin))
    else:
        tail.append(box(-0.5, -fin_h / 2, tail_len - 1, 1, fin_h, 4, fin))
    parts.append(part('tail', (0, cy, bl / 2), tail))
    py = cy + bh / 4
    parts.append(part('wing0', (-bw / 2, py, -bl / 4), [box(-pect, 0, 0, pect, 1, 4, fin)], rot=(0, 0, 0.3)))
    parts.append(part('wing1', (bw / 2, py, -bl / 4), [box(0, 0, 0, pect, 1, 4, fin)], rot=(0, 0, -0.3)))
    return parts


def snake(c, w, length, hw, hh, hd, c2=None, eyes='#ffcc00', tail_len=12, head_extra=(), pat='scales'):
    y = 24 - w
    return [part('body', (0, 0, 0), [box(-w / 2, y, -length / 2, w, w, length, c, pattern=pat)]),
            part('head', (0, y + w / 2, -length / 2), [box(-hw / 2, -hh + w / 2, -hd, hw, hh, hd, c2 or c, eyes=eyes),
                                                       *head_extra]),
            part('tail', (0, y + w / 2, length / 2), [box(-(w - 1) / 2, -(w - 1) / 2, 0, w - 1, w - 1, tail_len, c, pattern=pat),
                                                      box(-(w - 2) / 2, -(w - 2) / 2 + 0.5, tail_len, w - 2, w - 2, tail_len, c)])]


def add(S, D):
    # ================= Passive =================
    S['island_whale'] = fish('#6a7f99', 14, 14, 30, 14, 12, 10, '#4a5f79', c2='#7a8fa9', tail_len=10, flukes=True,
                             fin_h=16, pect=8, head_extra=[box(-5, 4, -10.5, 10, 1, 1, '#ffffff')])
    S['wild_den_den_mushi'] = [
        part('body', (0, 0, 0), [box(-2, 22, -4, 4, 2, 8, '#e8d7a0'),
                                 box(-2.5, 15, -1, 5, 7, 6, '#7a4a9a', pattern='shell')]),
        part('head', (0, 21, -4), [box(-1.5, -3, -2, 3, 3, 2, '#e8d7a0', front=[(0, 2, '#7a3030'), (1, 2, '#7a3030'), (2, 2, '#7a3030')]),
                                   box(-1.5, -6, -1, 1, 3, 1, '#e8d7a0', front=[(0, 0, '#111111')]),
                                   box(0.5, -6, -1, 1, 3, 1, '#e8d7a0', front=[(0, 0, '#111111')])]),
    ]
    S['drum_reindeer'] = quadruped('#8b5a35', 8, 8, 12, 9, 2, 5, 5, 6, c2='#9b6a45', head_up=4, tail_len=2, tail_w=2,
                                   body_pat='speckle', leg_c='#6b4a25',
                                   head_extra=[box(-4, -8, -3, 1, 6, 1, '#d8c8a0'), box(3, -8, -3, 1, 6, 1, '#d8c8a0'),
                                               box(-6, -8, -3, 3, 1, 1, '#d8c8a0'), box(3, -8, -3, 3, 1, 1, '#d8c8a0'),
                                               box(-1, -1, -7, 2, 2, 1, '#3060c0')])
    S['sauropod'] = quadruped('#6b8f5a', 14, 12, 22, 10, 4, 6, 5, 7, head_up=18, neck_w=4, tail_len=18, tail_w=4,
                              tail_rot=0.1, body_pat='scales', leg_c='#5b7f4a',
                              tail_extra=[box(-1, 0.5, 18, 2, 2, 8, '#6b8f5a')])
    S['fuzza'] = [
        part('body', (0, 0, 0), [box(-4, 6, -6, 8, 7, 12, '#e9e2d0', pattern='speckle')]),
        part('head', (0, 7, -5), [box(-2, -8, -2, 4, 9, 4, '#e9e2d0'),
                                  box(-2.5, -12, -5, 5, 5, 6, '#f4efe2', eyes='#111111'),
                                  box(-1, -10, -9, 2, 2, 4, '#e0b030'),
                                  box(-0.5, -15, -3, 1, 3, 4, '#c04040')]),
        part('leg0', (-2, 13, 0), [box(-1, 0, -1, 2, 10, 2, '#e0b030'), box(-2, 10, -3, 4, 1, 4, '#e0b030')]),
        part('leg1', (2, 13, 0), [box(-1, 0, -1, 2, 10, 2, '#e0b030'), box(-2, 10, -3, 4, 1, 4, '#e0b030')]),
        part('wing0', (-4, 7, -4), [box(-1, 0, 0, 1, 6, 14, '#c9c2b0')]),
        part('wing1', (4, 7, -4), [box(0, 0, 0, 1, 6, 14, '#c9c2b0')]),
        part('tail', (0, 7, 6), [box(-3, 0, 0, 6, 2, 6, '#c9c2b0')], rot=(-0.4, 0, 0)),
    ]
    S['hiking_bear'] = biped('#6b4a2e', 10, 12, 7, 8, 4, 10, 3, 8, 7, 7, c2='#7b5a3e', arm_c='#5b3a1e',
                             head_extra=[box(-4.5, -9, -5, 9, 2, 9, '#3a7a3a', pattern='band'),
                                         box(-4, -9, -1, 2, 2, 2, '#6b4a2e'), box(2, -9, -1, 2, 2, 2, '#6b4a2e'),
                                         box(-1.5, -3, -6, 3, 2, 1, '#2a1a10')],
                             body_extra=[box(-4, 11, 3.5, 8, 9, 3, '#a05030', pattern='band')])
    S['long_horse'] = quadruped('#c8a070', 8, 8, 14, 16, 2, 4, 5, 8, head_up=12, neck_w=3, tail_len=7, tail_w=2,
                                tail_c='#5a3a20', leg_c='#b89060',
                                head_extra=[box(-1.5, -6, -1, 1, 2, 1, '#c8a070'), box(0.5, -6, -1, 1, 2, 1, '#c8a070'),
                                            box(-0.5, -4, 1, 1, 12, 2, '#5a3a20')])

    # ================= Neutral =================
    S['triceratops'] = quadruped('#7a8a4a', 12, 10, 18, 8, 4, 8, 7, 9, c2='#8a9a5a', tail_len=10, tail_w=4, tail_rot=0.1,
                                 body_pat='scales', leg_c='#6a7a3a',
                                 head_extra=[box(-7, -10, 0, 14, 10, 2, '#a07040', pattern='band'),
                                             box(-3, -7, -8, 1, 1, 6, '#efe6cf'), box(2, -7, -8, 1, 1, 6, '#efe6cf'),
                                             box(-0.5, -2, -12, 1, 2, 3, '#efe6cf')])
    S['momoo'] = fish('#e8e8e8', 12, 12, 22, 10, 9, 8, '#9a9a9a', tail_len=8, body_pat='spots',
                      head_extra=[box(-7, -6, -4, 3, 2, 2, '#efe6cf'), box(4, -6, -4, 3, 2, 2, '#efe6cf'),
                                  box(-3, 1, -10, 6, 4, 2, '#f0b0b0', front=[(1, 1, '#000000'), (4, 1, '#000000')])])
    S['circus_lion'] = quadruped('#c9933a', 10, 9, 14, 8, 3, 7, 7, 6, tail_len=9, tail_w=1, tail_rot=0.6, leg_c='#b9832a',
                                 head_extra=[box(-6, -8, 0, 12, 12, 3, '#8a5020', pattern='fluff'),
                                             box(-2, -1, -8, 4, 3, 2, '#e0b070', front=[(1, 0, '#2a1a10'), (2, 0, '#2a1a10')])],
                                 tail_extra=[box(-1, -0.5, 8, 2, 2, 2, '#8a5020')])
    S['komainu'] = quadruped('#e8e0d0', 8, 8, 12, 8, 3, 6, 6, 6, tail_len=5, tail_w=3, tail_rot=-0.8, tail_c='#3a8a6a',
                             head_extra=[box(-5, -6, -1, 10, 9, 3, '#3a8a6a', pattern='swirl'),
                                         box(-2, 0, -8, 4, 2, 2, '#e8e0d0', front=[(1, 0, '#c03030'), (2, 0, '#c03030')])],
                             body_extra=[box(-4.5, 7, -6.5, 9, 2, 3, '#c03030', pattern='band')])
    S['wano_wolf'] = quadruped('#d8d8d8', 7, 7, 13, 9, 2, 6, 6, 7, tail_len=8, tail_w=3, tail_rot=0.5, body_pat='fluff',
                               head_extra=[box(-3, -6, -2, 2, 2, 1, '#d8d8d8'), box(1, -6, -2, 2, 2, 1, '#d8d8d8'),
                                           box(-1.5, 0, -10, 3, 3, 3, '#c8c8c8', front=[(1, 0, '#111111')])],
                               body_extra=[box(-4, 6, -7, 8, 3, 3, '#c03030', pattern='band')])
    S['battle_snake'] = snake('#6a4a8a', 4, 20, 5, 4, 5, eyes='#ffcc00', tail_len=12,
                              head_extra=[box(-2, -4.5, -4, 4, 1, 3, '#efe6cf')])
    S['kraken'] = [part('body', (0, 0, 0), [box(-6, 0, -6, 12, 12, 12, '#c0506a', pattern='spots')]),
                   part('head', (0, 12, -6), [box(-4, -2, -1, 8, 3, 1, '#d0607a', eyes='#ffd000')])] + \
        [part('leg%d' % i, (x, 12, z), [box(-1, 0, -1, 2, 12, 2, '#b0405a', pattern='stripes')])
         for i, (x, z) in enumerate(((-4, -4), (4, -4), (-4, 4), (4, 4), (-5, 0), (5, 0), (0, -5), (0, 5)))]
    S['megalo'] = fish('#7a8aa0', 8, 8, 18, 7, 7, 7, '#5a6a80', tail_len=6, fin_h=12,
                       head_extra=[box(-3, 2.5, -7.5, 6, 1, 1, '#ffffff')],
                       body_extra=[box(-0.5, 4, -3, 1, 6, 6, '#5a6a80')])
    S['sea_monkey'] = biped('#a06a3a', 7, 8, 5, 6, 3, 9, 2, 6, 6, 6, c2='#e0b090', arm_c='#906030',
                            head_extra=[box(-4, -5, -1, 1, 2, 2, '#a06a3a'), box(3, -5, -1, 1, 2, 2, '#a06a3a')],
                            tail=[box(-0.5, 0, 0, 1, 1, 8, '#906030')])

    # ================= Hostile =================
    S['tyrannosaurus'] = [
        part('body', (0, 0, 0), [box(-5, 6, -8, 10, 12, 16, '#6a4a2a', pattern='scales')]),
        part('head', (0, 8, -8), [box(-4.5, -9, -12, 9, 7, 12, '#7a5a3a', eyes='#ffcc00')]),
        part('jaw', (0, -2, 0), [box(-4, 0, -11, 8, 3, 11, '#5a3a1a', front=[(x, 0, '#ffffff') for x in range(0, 8, 2)])],
             parent='head'),
        part('arm0', (-5, 11, -6), [box(-1, 0, -1, 1, 4, 2, '#6a4a2a')]),
        part('arm1', (5, 11, -6), [box(0, 0, -1, 1, 4, 2, '#6a4a2a')]),
        part('leg0', (-4, 14, 2), [box(-3, 0, -3, 5, 10, 6, '#5a3a1a')]),
        part('leg1', (4, 14, 2), [box(-2, 0, -3, 5, 10, 6, '#5a3a1a')]),
        part('tail', (0, 9, 8), [box(-3, 0, 0, 6, 6, 12, '#6a4a2a', pattern='scales'), box(-1.5, 1.5, 12, 3, 3, 10, '#6a4a2a')],
             rot=(-0.1, 0, 0)),
    ]
    S['sky_shark'] = fish('#e8f0f8', 8, 8, 18, 7, 7, 7, '#a0c0e0', eyes='#2040a0', tail_len=6, fin_h=12,
                          head_extra=[box(-3, 2.5, -7.5, 6, 1, 1, '#ffffff')],
                          body_extra=[box(-0.5, 4, -3, 1, 6, 6, '#a0c0e0')])
    S['nola'] = snake('#5a7a3a', 6, 24, 8, 6, 9, c2='#6a8a4a', eyes='#ff3020', tail_len=16,
                      head_extra=[box(-3.5, -1, -9.5, 7, 1, 1, '#ffffff')])
    S['humandrill'] = biped('#5a5050', 8, 10, 6, 6, 3, 12, 3, 7, 7, 7, c2='#c04040', arm_c='#4a4040',
                            head_extra=[box(-2, -4, -5.5, 4, 3, 1, '#3060c0')],
                            tail=[box(-0.5, 0, 0, 1, 1, 6, '#4a4040')])
    S['cerberus'] = quadruped('#3a3a3a', 8, 8, 14, 9, 3, 5, 5, 6, c2='#4a4a4a', eyes='#ff3020', tail_len=8, tail_w=2,
                              tail_rot=0.3, tail_c='#d07030', body_pat='fluff',
                              head_extra=[box(-8.5, -2, -5, 4, 4, 5, '#4a4a4a', eyes='#ff3020'),
                                          box(4.5, -2, -5, 4, 4, 5, '#4a4a4a', eyes='#ff3020'),
                                          box(-2, -5, -2, 1, 2, 1, '#3a3a3a'), box(1, -5, -2, 1, 2, 1, '#3a3a3a')])
    S['basilisk'] = quadruped('#4a5a3a', 10, 7, 18, 6, 3, 6, 6, 8, eyes='#ffcc00', tail_len=14, tail_w=4, tail_rot=0.1,
                              body_pat='scales',
                              head_extra=[box(-0.5, -8, -6, 1, 4, 7, '#c03030'), box(-1, 0, -10, 2, 2, 2, '#e0b030')],
                              body_extra=[box(-1, 9, -8, 2, 2, 16, '#c03030')])
    S['manticore'] = quadruped('#b07a3a', 10, 9, 14, 8, 3, 7, 7, 6, c2='#d0a070', tail_len=6, tail_w=2, tail_rot=-1.2,
                               head_extra=[box(-6, -8, 0, 12, 12, 3, '#6a3a1a', pattern='fluff')],
                               tail_extra=[box(-1, -1, 5, 2, 2, 6, '#3a2a20'), box(-0.5, -0.5, 10, 1, 1, 3, '#111111')])
    S['punk_hazard_dragon'] = quadruped('#6a2a2a', 12, 10, 20, 8, 4, 8, 7, 11, c2='#7a3a3a', eyes='#ffcc00',
                                        head_up=6, neck_w=5, tail_len=16, tail_w=5, tail_rot=0.1, body_pat='scales',
                                        head_extra=[box(-3, -9, -2, 1, 4, 1, '#efe6cf'), box(2, -9, -2, 1, 4, 1, '#efe6cf')],
                                        body_extra=[box(-1, 5, -9, 2, 2, 18, '#4a1a1a', pattern='stripes')]) + [
        part('wing0', (-6, 7, -6), [box(-16, 0, 0, 16, 1, 12, '#8a3a3a', pattern='stripes')], rot=(0, 0, 0.4)),
        part('wing1', (6, 7, -6), [box(0, 0, 0, 16, 1, 12, '#8a3a3a', pattern='stripes')], rot=(0, 0, -0.4))]
    S['sea_cat'] = fish('#d08040', 12, 11, 22, 11, 10, 8, '#a06030', eyes='#30c030', tail_len=10, body_pat='stripes',
                        head_extra=[box(-5, -8, -4, 3, 3, 2, '#d08040'), box(2, -8, -4, 3, 3, 2, '#d08040'),
                                    box(-8, 1, -8, 3, 1, 1, '#ffffff'), box(5, 1, -8, 3, 1, 1, '#ffffff')])
    S['homie_tree'] = biped('#6a4a2a', 8, 14, 8, 6, 4, 12, 3, 12, 9, 12, c2='#3a8a3a', eyes=None, arm_c='#5a3a1a',
                            head_pat='fluff',
                            body_extra=[box(-4, 4, -4.5, 8, 6, 1, '#6a4a2a',
                                            front=[(1, 1, '#ffe060'), (6, 1, '#ffe060'), (2, 4, '#2a1a10'), (3, 4, '#2a1a10'),
                                                   (4, 4, '#2a1a10'), (5, 4, '#2a1a10')])])
    S['pacifista'] = biped('#3a3a40', 12, 14, 8, 8, 4, 14, 4, 8, 8, 8, c2='#4a4a50', eyes='#ffd000', arm_c='#2a2a30',
                           head_extra=[box(-4, -10, -2, 2, 2, 2, '#3a3a40'), box(2, -10, -2, 2, 2, 2, '#3a3a40')],
                           body_extra=[box(-5, 3, -4.5, 10, 2, 1, '#c03030'), box(-6.5, 1, -1, 13, 2, 2, '#2a2a30')])
    S['rusukaina_gorilla'] = biped('#2a2a2a', 12, 12, 8, 7, 4, 15, 4, 8, 8, 8, c2='#4a3a3a', eyes='#ff3020',
                                   arm_c='#2a2a2a', body_pat='fluff',
                                   head_extra=[box(-3, -4, -5.5, 6, 3, 1, '#5a4a4a')])

    def d(cid, name, c1, c2, biomes, drops):
        D[cid] = (name, c1, c2, biomes, drops)

    berry = lambda lo, hi: ('onepiece:berry', lo, hi)
    d('island_whale', 'Island Whale', '#6a7f99', '#ffffff',
      ['deep_ocean', 'deep_cold_ocean', 'deep_lukewarm_ocean', 'onepiece:red_line', 'onepiece:east_blue'],
      [('cod', 4, 8, 'smelt'), ('bone', 2, 5), ('prismarine_crystals', 0, 2)])
    d('wild_den_den_mushi', 'Wild Den Den Mushi', '#7a4a9a', '#e8d7a0',
      ['beach', 'swamp', 'mangrove_swamp', 'onepiece:fishman_reef', 'onepiece:sabaody'],
      [('slime_ball', 0, 1)])
    d('drum_reindeer', 'Drum Reindeer', '#8b5a35', '#3060c0',
      ['snowy_plains', 'snowy_taiga', 'grove', 'onepiece:drum_island'],
      [('leather', 0, 2), ('mutton', 1, 2, 'smelt')])
    d('sauropod', 'Little Garden Sauropod', '#6b8f5a', '#5b7f4a',
      ['jungle', 'onepiece:little_garden'],
      [('beef', 4, 8, 'smelt'), ('bone', 2, 5), ('leather', 2, 4)])
    d('fuzza', 'Fuzza', '#e9e2d0', '#e0b030',
      ['meadow', 'windswept_hills', 'stony_peaks', 'onepiece:skypiea'],
      [('feather', 2, 4), ('chicken', 1, 3, 'smelt')])
    d('hiking_bear', 'Hiking Bear', '#6b4a2e', '#3a7a3a',
      ['taiga', 'snowy_taiga', 'old_growth_spruce_taiga', 'onepiece:drum_island'],
      [('salmon', 0, 2, 'smelt'), ('sweet_berries', 0, 3)])
    d('long_horse', 'Long Horse', '#c8a070', '#5a3a20',
      ['plains', 'sunflower_plains', 'savanna', 'onepiece:east_blue'],
      [('leather', 0, 3)])
    d('triceratops', 'Triceratops', '#7a8a4a', '#a07040',
      ['jungle', 'sparse_jungle', 'onepiece:little_garden'],
      [('beef', 2, 5, 'smelt'), ('leather', 1, 3), ('bone', 0, 2)])
    d('momoo', 'Sea Cow', '#e8e8e8', '#222222',
      ['ocean', 'lukewarm_ocean', 'onepiece:east_blue'],
      [('beef', 3, 6, 'smelt'), ('leather', 1, 3)])
    d('circus_lion', 'Circus Lion', '#c9933a', '#8a5020',
      ['savanna', 'savanna_plateau', 'windswept_savanna', 'onepiece:east_blue'],
      [('leather', 1, 3), ('beef', 0, 2, 'smelt')])
    d('komainu', 'Komainu', '#e8e0d0', '#3a8a6a',
      ['cherry_grove', 'onepiece:wano'],
      [('white_wool', 0, 2), ('green_dye', 0, 1)])
    d('wano_wolf', 'Wano Wolf', '#d8d8d8', '#c03030',
      ['taiga', 'snowy_taiga', 'old_growth_pine_taiga', 'onepiece:wano'],
      [('bone', 0, 2), ('white_wool', 0, 1)])
    d('battle_snake', 'Battle Snake', '#6a4a8a', '#efe6cf',
      ['jungle', 'swamp', 'onepiece:amazon_lily'],
      [('leather', 0, 2), ('spider_eye', 0, 1)])
    d('kraken', 'Kraken', '#c0506a', '#ffd000',
      ['deep_ocean', 'deep_lukewarm_ocean', 'deep_cold_ocean', 'onepiece:fishman_reef'],
      [('onepiece:kraken_ink', 2, 5), ('ink_sac', 1, 4), ('glow_ink_sac', 0, 2)])
    d('megalo', 'Megalo Shark', '#7a8aa0', '#ffffff',
      ['warm_ocean', 'lukewarm_ocean', 'onepiece:fishman_reef'],
      [('cod', 1, 3, 'smelt'), ('prismarine_shard', 0, 2)])
    d('sea_monkey', 'Sea Monkey', '#a06a3a', '#e0b090',
      ['warm_ocean', 'lukewarm_ocean', 'beach', 'onepiece:jaya'],
      [('kelp', 1, 3), ('cod', 0, 1, 'smelt')])
    d('tyrannosaurus', 'Tyrannosaurus', '#6a4a2a', '#ffcc00',
      ['jungle', 'onepiece:little_garden'],
      [('beef', 4, 8, 'smelt'), ('bone', 3, 6), berry(8, 20)])
    d('sky_shark', 'Sky Shark', '#e8f0f8', '#2040a0',
      ['warm_ocean', 'onepiece:skypiea'],
      [('cod', 0, 2, 'smelt'), ('prismarine_shard', 0, 1), berry(1, 4)])
    d('nola', 'Sky Python', '#5a7a3a', '#ff3020',
      ['bamboo_jungle', 'jungle', 'onepiece:skypiea'],
      [('leather', 2, 5), ('gold_ingot', 0, 2), berry(10, 25)])
    d('humandrill', 'Humandrill', '#5a5050', '#c04040',
      ['dark_forest', 'pale_garden', 'onepiece:thriller_bark'],
      [('bone', 0, 2), ('iron_nugget', 1, 4), berry(2, 6)])
    d('cerberus', 'Cerberus', '#3a3a3a', '#ff3020',
      ['dark_forest', 'soul_sand_valley', 'onepiece:thriller_bark'],
      [('bone', 1, 3), ('rotten_flesh', 1, 3), berry(3, 8)])
    d('basilisk', 'Basilisk', '#4a5a3a', '#c03030',
      ['nether_wastes', 'basalt_deltas', 'crimson_forest'],
      [('leather', 1, 3), ('blaze_powder', 0, 2), berry(5, 12)])
    d('manticore', 'Manticore', '#b07a3a', '#3a2a20',
      ['soul_sand_valley', 'warped_forest', 'nether_wastes'],
      [('leather', 1, 3), ('spider_eye', 0, 2), berry(5, 12)])
    d('punk_hazard_dragon', 'Punk Hazard Dragon', '#6a2a2a', '#ffcc00',
      ['basalt_deltas', 'badlands', 'onepiece:punk_hazard_burning'],
      [('onepiece:dragon_scale', 2, 5), ('blaze_rod', 1, 3), ('magma_cream', 1, 3), berry(20, 50)])
    d('sea_cat', 'Sea Cat', '#d08040', '#30c030',
      ['ocean', 'deep_ocean', 'warm_ocean', 'onepiece:east_blue'],
      [('salmon', 2, 4, 'smelt'), ('string', 1, 3), berry(3, 8)])
    d('homie_tree', 'Seducing Woods Homie', '#6a4a2a', '#3a8a3a',
      ['dark_forest', 'pale_garden', 'onepiece:whole_cake'],
      [('stick', 2, 6), ('apple', 0, 2), ('sugar', 0, 2), berry(2, 6)])
    d('pacifista', 'Pacifista', '#3a3a40', '#ffd000',
      ['plains', 'onepiece:egghead', 'onepiece:sabaody'],
      [('iron_ingot', 2, 6), ('redstone', 2, 6), ('copper_ingot', 1, 4), berry(15, 40)])
    d('rusukaina_gorilla', 'Rusukaina Gorilla', '#2a2a2a', '#ff3020',
      ['jungle', 'bamboo_jungle', 'onepiece:amazon_lily'],
      [('leather', 1, 3), ('beef', 1, 3, 'smelt'), berry(4, 10)])

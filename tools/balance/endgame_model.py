"""Endgame fight-length model. Usage: python3 endgame_model.py [path/to/source] [--new]
Reads characters.json and npc_kits.json; constants mirror CharacterEntity, TitanLadder, RaidDef, Raids, NewGamePlus.
Fight time = effective health / player damage per second. Two players: 'story end' 15 dps, 'maxed' 25 dps.
Boss hit = one plain melee hit vs netherite Protection IV, as % of a maxed player's 30 health."""
import json, sys, os
src = next((a for a in sys.argv[1:] if not a.startswith('--')), '/mnt/project-files/one-piece-mod/source')
NEW = '--new' in sys.argv
res = os.path.join(src, 'src/main/resources/onepiece')
C = {c['id']: c for c in json.load(open(os.path.join(res, 'characters.json')))['characters']} if isinstance(json.load(open(os.path.join(res, 'characters.json'))), dict) else {c['id']: c for c in json.load(open(os.path.join(res, 'characters.json')))}
K = json.load(open(os.path.join(res, 'npc_kits.json')))
K = K.get('kits', K)
KH = {n: v.get('health', 20) for n, v in K.items() if isinstance(v, dict)} if isinstance(K, dict) else {v['id']: v.get('health', 20) for v in K}

HM, DM, ARM = [1, 2, 3.5], [1, 1.5, 2], [0, 6, 12]
if NEW:
    LAD_H = lambda n: 1 + 0.15 * n
    LAD_D = lambda n: 1 + 0.15 * n
    RAID_RES_CAP = 3
    BOSS_STATS = dict(garp=(3500, 40), marco=(3500, 36), shanks=(6500, 50), rayleigh=(5000, 48), roger=(8000, 58))
    RAID_RES = dict(final_war=0, beasts=1, big_mom=1, blackbeard=1, whitebeard=1, red_hair=2, rocks=1, roger=2)
    NG_FLOOR = lambda cyc: (1000 + 300 * cyc, 14 + 2 * cyc) if cyc > 0 else (0, 0)
else:
    LAD_H = lambda n: 1 + 0.4 * n
    LAD_D = lambda n: 1 + 0.15 * n
    RAID_RES_CAP = 3
    BOSS_STATS = dict(garp=(3500, 40), marco=(3500, 36), shanks=(6500, 50), rayleigh=(7000, 48), roger=(12000, 58))
    RAID_RES = dict(final_war=0, beasts=1, big_mom=1, blackbeard=1, whitebeard=1, red_hair=2, rocks=2, roger=3)
    NG_FLOOR = lambda cyc: (0, 0)
RAID_NG_H = (lambda c: 1 + 0.15 * c) if NEW else (lambda c: 1 + 0.25 * c)
RAID_NG_RES = (lambda c: 0) if NEW else (lambda c: 2 if c >= 5 else 1 if c >= 3 else 0)
LIMIT = 30 if NEW else 25
NG_H = lambda c: 1 + 0.25 * c
NG_D = lambda c: 1 + 0.2 * c
NG_RES = lambda c: 2 if c >= 5 else 1 if c >= 3 else 0

def armor_cut(armor, hit=22):
    return min(20, max(armor / 5, armor - 4 * hit / 8)) / 25

def player_hit(dmg, hp=30):
    cut = min(20, max(4, 20 - 4 * dmg / 20)) / 25
    return dmg * (1 - cut) * (1 - 0.64) / hp * 100

def boss(id, diff=0, rung=0, ng=0, res=0, raid=False):
    c = C[id]
    h, d = c['health'], c['damage']
    h = h * HM[diff] * LAD_H(rung)
    d = d * DM[diff] * LAD_D(rung)
    if raid and id in BOSS_STATS:
        h, d = BOSS_STATS[id]
    if ng:
        h *= RAID_NG_H(ng) if raid else NG_H(ng); d *= NG_D(ng)
        if not raid:
            fh, fd = NG_FLOOR(ng)
            h, d = max(h, fh), max(d, fd)
            res = max(res, NG_RES(ng))
    eff = h / (1 - 0.2 * res) / (1 - armor_cut(ARM[diff]))
    return eff, d

def mmss(s):
    return f"{int(s // 60)}:{int(s % 60):02d}"

def row(name, eff, d):
    print(f"  {name:34s} eff.HP {eff:7.0f}  story-end {mmss(eff / 15):>6s}  maxed {mmss(eff / 25):>6s}  hit {d:5.0f} = {player_hit(d):3.0f}% hp")

print("== Titans on Normal / Hard / Expert ==")
for b in ['kaido', 'big_mom', 'blackbeard', 'whitebeard', 'akainu', 'mihawk', 'imu', 'xebec']:
    for diff, n in enumerate(['N', 'H', 'E']):
        row(f"{b} {n}", *boss(b, diff))
print("== Legend Ladder (Expert x rung) ==")
for b in ['kaido', 'whitebeard', 'akainu']:
    for r in range(1, 6):
        row(f"{b} Legend {r}", *boss(b, 2, r))
print("== New Game+ story bosses (Normal) ==")
for b in ['buggy', 'lucci', 'doflamingo', 'kaido', 'imu']:
    for ng in [0, 1, 3, 5]:
        row(f"{b} NG+{ng}", *boss(b, 0, 0, ng))

RAIDS = {
    'final_war': [["marine*6", "marine_rifle*4", "marine_officer*2"], ["elite_marine*5", "pacifista*3", "vice_admiral*1"], ["boss:garp@2", "seraphim*2", "elite_marine*3"], ["boss:kizaru@1", "boss:akainu@2"]],
    'beasts': [["gifter*8", "pirate_gunner*3"], ["headliner*5", "boss:king@2"], ["boss:kaido@2", "headliner*2"]],
    'big_mom': [["pirate*10", "pirate_gunner*3"], ["boss:katakuri@2", "pirate_captain*3"], ["boss:big_mom@2", "pirate_captain*2"]],
    'blackbeard': [["blackbeard_pirate*8", "pirate_gunner*4"], ["blackbeard_pirate*4", "pirate_captain*4", "boss:magellan@2"], ["boss:blackbeard@2", "blackbeard_pirate*3"]],
    'whitebeard': [["whitebeard_pirate*10"], ["boss:marco@2", "whitebeard_pirate*4"], ["boss:whitebeard@2"]],
    'red_hair': [["pirate*8", "pirate_gunner*4", "pirate_captain*2"], ["pirate_gunner*6", "pirate_captain*4"], ["boss:shanks@2"]],
    'rocks': [["pirate_captain*6", "headliner*4", "blackbeard_pirate*3"], ["boss:whitebeard@1", "boss:big_mom@1"], ["boss:xebec@2"]],
    'roger': [["pirate_captain*8", "whitebeard_pirate*4"], ["boss:rayleigh@2"], ["boss:roger@2"]],
}
print(f"== Raids ({LIMIT} min limit; trash at 2x dps for sweeps) ==")
for rid, waves in RAIDS.items():
    for raiders, ng in [(1, 0), (2, 0), (1, 3), (1, 5)]:
        res = min(RAID_RES_CAP, RAID_RES[rid] + raiders - 1 + RAID_NG_RES(ng))
        total = 0
        for w in waves:
            for s in w:
                if s.startswith('boss:'):
                    i, dd = s[5:].split('@')
                    total += boss(i, int(dd), 0, ng, res, raid=True)[0]
                else:
                    k, n = s.split('*')
                    total += KH.get(k, 30) * round(int(n) * (1 + 0.5 * (raiders - 1))) * (1 + 0.25 * (raiders - 1) + (RAID_NG_H(ng) - 1)) / 2
        for label, dps in [('story-end', 15), ('maxed', 25)]:
            t = total / (dps * raiders)
            flag = '  OVER LIMIT' if t > LIMIT * 60 else ('  tight' if t > 18 * 60 else '')
            if label == 'maxed' or raiders == 1 and ng == 0:
                print(f"  {rid:11s} {raiders}p NG+{ng} {label:9s} {mmss(t):>6s}{flag}")

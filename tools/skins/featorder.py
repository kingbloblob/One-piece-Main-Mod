"""Find/fix feature order cycles between mod biomes and vanilla biomes of the same dimension.
usage: featorder.py <vanilla biome dir> <mod biome dir> [--fix]"""
import json, os, sys
from collections import defaultdict
van, mod = sys.argv[1], sys.argv[2]
fix = '--fix' in sys.argv
def load(d):
    return {f[:-5]: json.load(open(os.path.join(d, f))) for f in os.listdir(d) if f.endswith('.json')}
V, M = load(van), load(mod)
allb = {('minecraft:' + k): v for k, v in V.items()}
allb.update({('onepiece:' + k): v for k, v in M.items()})
# global order from vanilla: index of first appearance in a topological merge
def topo(lists):
    succ = defaultdict(set); nodes = []
    for L in lists:
        for a in L:
            if a not in nodes: nodes.append(a)
        for i in range(len(L) - 1):
            succ[L[i]].add(L[i + 1])
    indeg = {n: 0 for n in nodes}
    for a in succ:
        for b in succ[a]: indeg[b] += 1
    out = []; ready = [n for n in nodes if indeg[n] == 0]
    while ready:
        n = ready.pop(0); out.append(n)
        for b in sorted(succ[n], key=nodes.index):
            indeg[b] -= 1
            if indeg[b] == 0: ready.append(b)
    return out if len(out) == len(nodes) else None
for step in range(11):
    lists = [b['features'][step] for b in allb.values() if len(b['features']) > step and b['features'][step]]
    if topo(lists) is None:
        print('cycle in step', step)
        if fix:
            vorder = topo([b['features'][step] for b in V.values() if len(b['features']) > step]) or []
            for k, b in M.items():
                if len(b['features']) <= step: continue
                L = b['features'][step]
                own = [f for f in L if f not in vorder]
                b['features'][step] = own + sorted([f for f in L if f in vorder], key=vorder.index)
                if b['features'][step] != L:
                    print('  reordered', k)
                    json.dump(b, open(os.path.join(mod, k + '.json'), 'w'), indent=2)

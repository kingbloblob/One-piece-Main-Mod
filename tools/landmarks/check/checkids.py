"""python3 check/checkids.py <landmarks dir> <sid>...  (block_ids.txt: 26.3 client blockstates + the mod's; rebuild it if blocks are added) : prints block ids used by each build that don't exist in 26.3 or the mod."""
import sys, os, collections
D = sys.argv[1]; sys.path.insert(0, D); os.chdir(D)
ok = set(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "block_ids.txt")).read().split())
import pipeline
for sid in sys.argv[2:]:
    m, b, ground, mode, fr = pipeline.prepare(sid, True)
    bad = collections.Counter(st.split("[")[0] for st in b.blocks.values() if st.split("[")[0] not in ok)
    print(sid, "OK" if not bad else "UNKNOWN: " + ", ".join(f"{k} x{v}" for k, v in bad.most_common()))

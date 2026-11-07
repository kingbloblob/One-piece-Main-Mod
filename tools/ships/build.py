"""Build ship templates: python3 build.py <ship id>... [--res DIR] [--previews DIR] [--no-preview]

Each <ship id> is a module in this folder with a build() -> shipkit.Ship function (going_merry.py, thousand_sunny.py...).
Writes data/onepiece/structure/ships/<id>.nbt + data/onepiece/ships/<id>.json under --res (default: the shared source)
and preview pictures under --previews (default /mnt/project-files/one-piece-mod/previews/ships).
`python3 build.py all` builds every ship listed in SHIPS.
"""
import importlib, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import shipkit
# shipkit puts tools/landmarks on the path, which has its own marine_battleship.py / victoria_punk.py: ships first.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

SHIPS = ["going_merry", "thousand_sunny", "marine_warship", "marine_battleship", "big_top", "red_force", "polar_tang",
         "victoria_punk", "miss_love_duck", "bezan_black"]

res = shipkit.RES_DEFAULT
previews = shipkit.PREVIEWS
names = []
for a in sys.argv[1:]:
    if a.startswith("--res="):
        res = a[6:]
    elif a.startswith("--previews="):
        previews = a[11:]
    elif not a.startswith("--"):
        names.append(a)
if names == ["all"]:
    names = SHIPS
for name in names:
    t = time.time()
    m = importlib.import_module(name)
    ship = m.build()
    ship.save(res)
    if "--no-preview" not in sys.argv:
        outs = ship.preview(previews, cuts=getattr(m, "CUTS", ()))
        print("  previews:", ", ".join(outs))
    print(f"  {time.time() - t:.1f}s")

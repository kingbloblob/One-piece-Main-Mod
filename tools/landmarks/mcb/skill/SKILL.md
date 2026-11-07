---
name: "minecraft-builder"
description: "Design and generate Minecraft (Java Edition) structures as .mcfunction command files, using vanilla and modded blocks. Use this skill whenever the user asks to build, design, or generate anything in Minecraft (houses, castles, towers, temples, pagodas, palaces, ruins, statues, villages, parks, plazas, gardens, trees, rocks, cliffs, bridges, arenas, stadiums, show venues, interiors, roofs), mentions /fill, /setblock, .mcfunction, datapacks, or wants a structure made from their mod's custom blocks, even if they don't say \"skill\" or name a file format. Also use it for HUGE builds (whole cities, islands, mountains, megastructures, anything hundreds of blocks across), underwater scenes (reefs, sunken or bubble cities, glass domes, aquariums) and when the user wants to test or showcase blocks they are adding to a mod. For named real or fictional structures (landmarks, cathedrals, cities from shows or games), research the subject first using the research workflow."
---

# Minecraft Builder

Goal: produce builds that look *designed*, not like boxes, and deliver them as a
`.mcfunction` file (or datapack) the user can run in Java Edition. Claude cannot see the
game, so the workflow leans on a build library (`scripts/`) to design with macros, then
inspects numbers, ASCII views and small previews before delivering.

`<skill>` below means the folder this SKILL.md lives in.

## Token budget: read less, cache more

Most of the cost of a build is not the build itself. It is reading large source files,
rewriting scripts, re-viewing images and redoing work in later turns or sessions. The
library source is ~200 KB (mcparts.py alone is ~12k tokens), while everything you need
to *call* it fits in ~3k tokens. So work in this order, and only step down a rung when
the rung above did not answer the question:

1. **The cache indexes** (`mc_shared/INDEX.md`, then `mc_cache/INDEX.md`; see below).
   If this build, a module, a palette or a dossier you need already exists, reuse it.
2. **This file + the API index.** Print signatures and one-line docs instead of reading
   source (about 14x smaller):
   ```bash
   python3 - <skill>/scripts/mcparts.py <<'EOF'   # any modules, e.g. mcbig.py mcreef.py
   import ast,sys
   for f in sys.argv[1:]:
       print("#",f.rsplit('/',1)[-1])
       for n in ast.parse(open(f).read()).body:
           ms=[n] if isinstance(n,ast.FunctionDef) else [m for m in getattr(n,'body',[]) if isinstance(m,ast.FunctionDef)] if isinstance(n,ast.ClassDef) else []
           for m in ms:
               if m.name.startswith('_'): continue
               d=(ast.get_docstring(m) or '').split('\n')[0][:70]
               print(("  ." if m is not n else "")+m.name+"("+ast.unparse(m.args).replace('self, ','')+")"+("  # "+d if d else ""))
   EOF
   ```
   Save it once to `mc_shared/api-<hash>.txt` (hash of the scripts) for all modules and
   read that file afterwards; it is shared by every build.
3. **One function's source**, only when its signature and docstring are not enough:
   `grep -n "def hip_roof" <skill>/scripts/mcparts.py`, then `sed -n` that range. Never
   `cat` a whole script.
4. **One reference file**, picked from the routing table below. Reference files are
   short; read the one that matches the job, not all of them.

Other habits that keep builds cheap without making them worse:
- **Edit, don't rewrite.** Keep the build in a script file plus a small `config.py` of
  numbers. Change a number or a function with a targeted edit instead of re-emitting the
  whole script; rewriting a 200-line script costs far more output tokens than the fix.
- **Quiet output.** Never print command lists or block lists. Print `summary(top=8)`,
  `verify.py` numbers, and at most 2-3 `layer(y)` views for small builds.
- **Numbers before pictures.** Check counts, ratios and bounds with `scripts/verify.py`
  first. When you do look, prefer one `render_elevations()` contact sheet (top + four
  sides in one image) over several separate renders. Previews are downscaled already.
- **View each image once.** After viewing a render or photo, write what you learned
  (numbers, problems) into the cache notes so you never need to view it again.
- **Short chat.** Put the work in code and the facts in cache files; keep messages to the
  user to results, choices and questions.

## The caches: shared library + per-build

Two folders, both kept where they persist between sessions. In a project, put them in
the project's shared files folder so every thread and session uses the same ones
(e.g. `/mnt/project-files/mc_shared/` and `/mnt/project-files/<build>/mc_cache/`);
otherwise next to the outputs.

**`mc_shared/`: one per user, reused by every build.** Anything that is not specific to
one build goes here, so it is computed, researched or designed once ever:
```
mc_shared/
  INDEX.md              one line per item: name | kind | tags | key | one-line note
  api-<hash>.txt        API index, <hash> = key() of the skill's scripts/*.py
  mccache.py            snapshot helper (below), written once ever
  snap/prefab_*.npz     reusable modules: window bays, doors, trees, lanterns, room kits,
                        roof caps, gothic pinnacles, reef creatures...
  palettes/<mod>.json   generated mod palettes with notes filled in
  dossiers/<subject>.md research on real/fictional subjects (castle types, landmarks)
  techniques/<topic>.md technique cards learned from user models (park, imperial-city...)
  prefabs/<kit>.py      parametric prefab code; its fixed-size results live in snap/
  lessons.md            rules learned from the user's in-game feedback
```
**`mc_cache/`: one per build**, only what belongs to that build: `INDEX.md`,
`config.py` (brief + every tunable number), `notes.md` (feedback, what each viewed
image showed), `snap/<stage>.npz` (stage snapshots).

Rules:
- **Shared first.** At the start of any build turn read `mc_shared/INDEX.md`, then the
  build's `mc_cache/INDEX.md` if resuming. These two short files say what exists; open
  other cache files only when an index line says they help.
- **Reuse before you regenerate.** A matching prefab is `restore`d and `stamp`ed, not
  redesigned. A matching dossier or palette is read, not re-researched or regenerated.
  The API index is regenerated only when its hash no longer matches the scripts.
- **Promote what generalizes.** When a build produces something another build could use
  (a good window bay, a tree, a lantern, a dossier, a mod palette, a lesson), save it to
  `mc_shared/` with `shared=True` or `promote(name)` and add an index line with tags.
  Give prefabs parameter-free names plus a version (`prefab_gothic_window_v1`) and keep
  palette-specific variants separate (`..._oak`, `..._spruce`).
- **Cache by stage.** Build large or multi-stage projects as stages (terrain, shell,
  roofs, details, interiors). Each stage restores the previous stage's snapshot, adds its
  part, and snapshots itself, so changing the roof reruns only the roof stage onward.
- **Keys make the cache safe.** A snapshot's key hashes its script, `config.py` and the
  parent stage's key (prefabs: a version string plus the blocks they use). A changed
  input gives a new key, so stale snapshots are rebuilt instead of silently reused.
- **Keep indexes current and append-only.** Add or update index lines in the same turn
  as the cache item. Append to notes and indexes rather than rewriting them; that keeps
  them short, cheap to diff, and stable across sessions.

Prompt caching: content that stays identical at the start of a conversation is cheaper
to re-read on every later turn. So read the stable files (`mc_shared/INDEX.md`, the API
index, the matching reference) once, early, and in that order; then work from them
instead of re-reading or re-printing them later in the conversation.

`mccache.py` (write it into `mc_shared/` once; needs `<skill>/scripts` and `mc_shared`
on `sys.path`; run builds from the build folder or set `MC_CACHE` to its `mc_cache/`):
```python
import hashlib, json, os, shutil, numpy as np
from mcbig import BigBuild
CACHE = os.environ.get("MC_CACHE", os.path.abspath("mc_cache"))  # this build's cache
SHARED = os.environ.get("MC_SHARED", os.path.dirname(os.path.abspath(__file__)))
def key(*parts):  # file paths or plain values -> short hash
    h = hashlib.sha1()
    for p in parts:
        h.update(open(p, "rb").read() if isinstance(p, str) and os.path.isfile(p) else repr(p).encode())
    return h.hexdigest()[:12]
def _path(name, shared): return f"{SHARED if shared else CACHE}/snap/{name}.npz"
def snapshot(b, name, k="", shared=False):
    p = _path(name, shared); os.makedirs(os.path.dirname(p), exist_ok=True)
    arrs = {f"t{tx}_{tz}": t for (tx, tz), t in b.tiles.items()}
    meta = json.dumps({"names": b.names, "y": [b.y_min, b.y_max], "key": k})
    np.savez_compressed(p, _meta=np.array(meta), **arrs)
def restore(name, k="", palette=None):  # build cache first, then the shared library
    for p in (_path(name, False), _path(name, True)):
        if not os.path.exists(p): continue
        z = np.load(p); m = json.loads(str(z["_meta"]))
        if k and m["key"] != k: continue
        b = BigBuild(palette=palette, y_min=m["y"][0], y_max=m["y"][1])
        b.names = m["names"]; b.ids = {n: i for i, n in enumerate(b.names) if i}
        for f in z.files:
            if f != "_meta":
                tx, tz = map(int, f[1:].split("_")); b.tiles[(tx, tz)] = z[f]
        return b
    return None
def cached(name, k, build_fn, palette=None, shared=False):
    b = restore(name, k, palette)
    if b is None:
        b = build_fn(); snapshot(b, name, k, shared); print(f"[cache] built {name}")
    else: print(f"[cache] hit {name}")
    return b
def promote(name):  # copy a build-cache snapshot into the shared library
    os.makedirs(f"{SHARED}/snap", exist_ok=True); shutil.copy2(_path(name, False), _path(name, True))
```
Stage pattern:
```python
from mccache import key, cached, restore, promote
k_roof = key(__file__, "mc_cache/config.py", k_shell)  # k_shell: parent stage's key
def build():
    b = restore("shell", k_shell); gable_roof(b, ...); return b   # only runs on a miss
b = cached("roof", k_roof, build)
```
Prefab pattern: `bay = cached("prefab_window_bay_v1", key("v1", cfg.WALL), make_bay,
shared=True)`, then `b.stamp_many(bay, placements)`. `restore` looks in the build cache
first, then the shared library. Snapshots work for any `BigBuild`; for tiny jobs on
`mcbuild.Build`, skip the stage cache but still reuse shared dossiers and palettes.

## Workflow

1. **Check the caches** (`mc_shared/INDEX.md`, then the build's `mc_cache/INDEX.md`).
   Resume or reuse anything that fits.
2. **Get the palette.** Ask which blocks may be used. For modded blocks you need a
   `palette.json` (see "Modded blocks"). Never invent a modded block ID. With no palette
   yet, build with vanilla blocks and clearly named placeholders the user can swap.
3. **Write a short design brief** (a few lines, before any code): footprint and height in
   blocks, style, silhouette (what makes it recognizable from far away), palette *roles*,
   and 2-3 signature details. For anything beyond a one-off small build, save it at the
   top of `config.py` so later sessions do not need the chat.
4. **Write the build script** (numbers in `config.py`). Paint big forms first (foundation,
   walls, roof), then carve (doors, windows), then detail (trim, lighting, props). Build
   repeated details once as prefabs and stamp them.
5. **Inspect before delivering**, numbers first: `summary()`, `verify.py` checks, then a
   few `layer(y)` views (plus `side()` on `mcbuild`) or one `render_elevations()` sheet. Check: walls closed, door
   reachable, windows on walls, roof covers the footprint, nothing floating, every side
   finished.
6. **Save and deliver** the file, material list and run instructions (below). Say
   honestly what you could not verify in-game and invite feedback. Update `INDEX.md`.

Small builds: `from mcbuild import Build, Palette` (macros: `set, fill, clear, mix, box,
hollow_box, walls, pillar, cylinder, dome, gable_roof, mirror_x`; `b.save("x.mcfunction")`).
Anything with parts, prefabs, stages or previews: `from mcbig import BigBuild` and
`save_function(path)` (one file, `~` coordinates) or `save_sharded(...)` (datapack).
```python
import sys; sys.path.insert(0, "<skill>/scripts"); sys.path.insert(0, "<path to>/mc_shared")
```

## Routing table: what to read for which job

Read only the rows that match. Get function signatures from the API index, not source.

| Job | Read | Use |
|---|---|---|
| Huge build (>~100 blocks, city, island) | `references/huge-builds.md` | `mcbig.BigBuild` (`fill_where`, `heightfield`, `tapered_cylinder`...), `save_sharded`, `stamp_many`; formulas, loops and prefabs, never per-block lists; `render_top` + `render_section` before export; ask for world origin, MC version, and in-game screenshots after each stage |
| Roofs, arches, stairs, trees, ships, ageing | (API index only) | `mcparts`: `gable_roof`, `hip_roof`, `cone_roof`, `arched_opening`, `arcade`, `colonnade`, `square_spiral_stair`, `stair_run`, `tree`, `scatter_trees`, `ship`, `weather`, `family_blocks` |
| Named / real / fictional structure | `references/research-workflow.md` | shared `dossiers/<subject>.md` (reuse; else write it there), `scripts/scaling.py`, `references/block-palettes.md` |
| User photos | photo section of research-workflow | `scripts/photo_tools.py crop` / `palette` |
| Unseen sides, interiors | `references/unseen-sides-and-interiors.md` | `bsp_rooms`, `furnish_room`, `render_elevations`, `verify.flatness` |
| Furnishing rooms | `references/interior-detail-rules.md`, then `mc_shared/techniques/interiors.md` if present | one `PropTracker` per building, always `audit_props` (FAIL = bug); no cake, no repeated novelty props; rooms >17 get zoned vignettes automatically. Then add shape-block furniture from `kit_interiors` (below) and check the density and light rules under "Learned from models" |
| Tavern, inn, dining hall, library, bedroom, kitchen, store room, modern living room | `mc_shared/techniques/interiors.md` if present | `mc_shared/prefabs/kit_interiors.py`: pieces `chair`, `bench`, `stool`, `sofa`, `table_post`, `table_cloth`, `table_group`, `coffee_table`, `bar_counter`, `kitchen_line`, `hearth`, `bed_nook`, `bunk_row`, `bookshelf_aisles`, `reading_table`, `storage_shelves`, `candelabra`, `plant_shelf`, `rug`, `door_mat`, `wall_lights`; whole rooms `tavern_hall`, `dining_hall`, `library`, `bedroom`, `kitchen`, `living_modern`, `storeroom` (prefabs `prefab_int_<room>_v1`). `audit_props` FAILs on set pieces (chest shelving, table decor, bookshelf stacks) are expected: audit the generated rooms, check kit rooms with `mc_shared/tools/iso_render.py` |
| Gothic | `references/techniques/gothic-cathedral.md` | `pointed_opening`, `square_spire`, `pinnacle`, `flying_buttress`, `ridge_cresting` |
| Underwater, reef, bubble, glass dome | `references/techniques/underwater-birdcage-reef.md` | `mcreef` (`birdcage_dome`, `bubble_dome`, `chandelier`, `coral_spire`, `gazebo`, `seabed`, `sand_channel`, `kelp_forest`, `coral_garden`, `jellyfish`, `manta_ray`, `fish_school`, `flood`, `waterlog`); pass the same `keep_dry` to `flood` and `waterlog` |
| East Asian temple, pagoda, shrine | `references/techniques/east-asian-temple.md` | `mcasian` (`temple_hall`, `curved_roof` hip/gable/irimoya, `bay_positions`, `column_row`, `brackets`, `lattice_wall`, `stone_platform`, `front_steps`, `stone_lantern`) |
| Park, plaza, garden, street furniture | `mc_shared/techniques/park.md` if present | prefabs `park_bench`, `picnic_pair`, `lamp_post`, `hedge_rail`, `waterfall_fountain`, `grand_tree` (`mc_shared/prefabs/kit_park_imperial.py`); else the "Learned from models" rules below |
| Arena, stadium, colosseum, show venue, amphitheatre | `mc_shared/techniques/arena.md` if present | `arena_bowl` (round or `oval`, entrance `gaps`), `facade_tier_bay`, `gate_pavilion`, `field_markings` (`mc_shared/prefabs/kit_arena.py`); prefab `prefab_arena_small_v1`; else the rules below |
| Hero tree, big custom tree, rocks, outcrops, nature scene | `mc_shared/techniques/fantasy-nature.md` if present | `feature_tree(H)`, `rock_outcrop` (`mc_shared/prefabs/kit_nature_fantasy.py`); prefab `prefab_nf_feature_tree_h48_v1`; `mcparts.tree` / `scatter_trees` for ordinary trees; else the rules below |
| Fantasy city, cliff or canyon city, walkways, ledges, vines | `mc_shared/techniques/fantasy-nature.md` if present, plus the huge-builds row | `arc_walkway` (curved ledge path + lamps), `dome_tower`, `vine_drape` (run last) from the same kit; else the rules below |
| Medieval tower, keep, belfry, spire, castle towers, grand gothic hall | `mc_shared/techniques/medieval-towers.md` if present, plus the Gothic row | `setback_tower(W)`, `string_course`, `corner_pinnacle`, `spire_cap`, `window_column` (`mc_shared/prefabs/kit_medieval.py`); prefabs `prefab_med_tower_w17_v1`, `_w11_v1`; else the rules below |
| Classical / imperial city, palace, dome | `mc_shared/techniques/imperial-city.md` if present, plus the huge-builds row | `giant_order_facade`, `ribbed_dome` from the same kit; else the rules below |
| User 3D model (glTF/GLB/FBX) | `references/mesh-analysis.md` | material names are blocks (Mineways) -> `mesh_blocks.py`; one `Atlas` material -> `mesh_analyze.py` (needs `pip install scipy`; ~2 min for 850 MB). If the grid shows content only on every other row/layer, the auto block size is half a block: rerun with `--block` doubled. If the bottom layers hold only a few blocks (a flag tip), the export is upside down: flip z. Study in ASCII (top map + per-layer prints), not images. If every texture comes out grey, the glTF uses `KHR_materials_pbrSpecularGlossiness`: copy each `diffuseTexture` into `pbrMetallicRoughness.baseColorTexture` and rerun. To see inside, render with `mc_shared/tools/gltf_shot` and `cut=`. Vanilla or schematic `.nbt` files hold exact block states: read them with `mc_shared/tools/refload.py` and summarize them with `refplan.py`, `refmine.py` and `refdensity.py`. Save the card to `mc_shared/techniques/`, recipes as prefabs, rules to `mc_shared/lessons.md` |
| Before delivering | `mc_shared/lessons.md` + `references/lessons.md` "Rules learned" | grep for the parts you used: `grep -n -i "roof\|reef" <skill>/references/lessons.md` |

Examples live in `examples/` (one per family, e.g. `underwater_cage_demo.py`,
`asian_temple_demo.py`, `gothic_church_demo.py`, `prefab_stamp_demo.py`). Open one only
when you need a working pattern you cannot get from the API index.

## Design principles (this is what makes builds look good)

- **Palette roles, not random blocks.** Pick 3-5 blocks with jobs: *base* (foundation,
  darker/heavier), *wall* (main body), *trim* (corner pillars, beams, window frames),
  *roof*, *accent* (sparing: lanterns, banners, a glowing mod block). Use `mix()` with
  2-3 similar blocks (stone bricks / cracked / mossy) on large surfaces to kill flat texture.
- **Never a flat wall.** Corner pillars that stick out 1 block, recessed or protruding
  window bays, trim bands, buttresses. Vary depth by at least 1 block every ~5 blocks.
- **Roofs carry the silhouette.** Overhang the eaves by 1, use stairs + slabs, add a ridge
  line, dormers or a chimney. Steeper = more fantasy, flatter = more modern.
- **Foundation and ground connection.** A base course 1 block wider or darker than the
  walls grounds the build. Add steps at the door. Extend the foundation 2-3 blocks below
  y=0 so it sits on uneven ground.
- **Windows and doors.** Windows 1-2 wide, evenly spaced, framed with trim, with a sill.
  Doors get a lintel, a lamp, or a porch.
- **Scale and proportion.** Ceilings 3-4 high; a 2-story house is ~9-11 wide minimum.
  Avoid perfect cubes: L/T footprints or a wing.
- **Asymmetry with intent.** Symmetric core plus one off-center feature (tower, lean-to,
  chimney, vines).
- **Lighting.** Hide light sources in the design (lanterns, glowstone behind trim) so the
  inside is safe from mob spawns and looks lived-in at night. Indoors, use about one light
  per 10 floor cells, mostly on the walls (`kit_interiors.wall_lights`). One lantern per
  room is far too dark.
- **Interior.** If walkable, give each room a purpose. Build its furniture from shape
  blocks (stairs, slabs, trapdoors, fences, carpets, signs), not only from job blocks.
- **Learned from models** (park 65x65, imperial city 465x359, arena 305x305, medieval tower 39x156, imperial hall 271x306, cliff city 592x438, hero tree 124 high, tavern, inn, 50 mansion rooms, 115 village houses; details in `mc_shared/techniques/`):
  - Open spaces: a path grid cuts the site into cells with one theme each; edge every path
    (dirt border), boundary (wall + fence + hedge) and basin (stair rim). One hero object
    3-4x taller than the rest. About 1/3 hard surface, 2/3 green.
  - Furniture from odd blocks: wall signs as armrests, open trapdoors as backrests, piston +
    piston head as a table, barrel + leaves as a planter, low wall + fence + lantern as a lamp.
  - Trees: rounded canopy tiers filled only ~35%, branches at each tier, vines and hanging
    lanterns; command-placed leaves always `[persistent=true]`.
  - Cities: raise the civic core on a deck ~7 above the streets; street furniture on a fixed
    rhythm (every 6); a landmark (statue, tower) at the edge as the skyline's focal point.
  - Classical fronts: plinth : giant order : attic about 1 : 6 : 1.4; bay period 8 (3-wide
    pier, 5 gap, loggia recessed); cornice 1 proud with a balustrade every 2; light walls,
    dark roofs; skeletal domes (dark ribs and rings over dark glass, finial) set behind the
    facade.
  - Arenas: field radius ~0.6 of the outer radius, field wall ~6 high with a walkway, stands
    raked 1 up : 2 out with stair seats facing the field, a 3-wide radial aisle per ~19 blocks
    of arc, stands as a 3-thick shell (hollow concourse below). Outer facade ~10 taller than
    the top row, in 3 tiers (arcade, band, attic) with piers through all of them. Entrances
    on the long axis under a pavilion that bridges the gap; outside, a plaza and a ring of
    evenly spaced big trees.
  - Medieval towers: setback tiers (wedding cake), total height 3.5-4.5x the base width W:
    shaft ~1.7W with a string course 1 proud every 8-11 blocks and barred slit windows,
    corbelled overhang band, taper 1 in per 2 up, belfry ~0.5W, lantern stage ~0.35W, copper
    cap + mast + flag. Corner pinnacles (trim shaft, lantern, cross) hide every setback. Walls
    mix stone bricks / cracked / andesite / polished andesite about 55/12/13/20; smooth stone
    for bands and floors; hollow shells with a floor per tier.
  - Grand halls: symmetric cross plan, corner pavilions, a central tower ~2.5x the main block,
    each tier ~0.8 of the one below; caps or small domes on every secondary tower.
  - Fantasy cities: set them in terrain (canyon, cliff, crater) and build the rock as part of
    the city; link levels with ledge paths and stairs that hug the rock (wall rail, lamp every
    4-8). Drape vines last, in 1-wide strips of mixed length from every overhang: about half
    1-3 long, a quarter 10+, the longest ~17.
  - Hero trees: trunk diameter ~H/12 tapering to half, a ~30 deg lean that recovers, a 3-way
    split at half height forking to ~20 tips, flattened cloud pads (width ~1.5x height) only
    in the top half, 5 roots gripping rock, bark mixed from 2-3 woods. Set them on a rock
    outcrop with sharp spires (to ~40% of the tree height), moss only on upward faces.
  - Interiors: tables are fence + pressure plate, fence + carpet, or a top-slab centre with
    upside-down stairs around it facing the centre and carpet placemats. Chairs are bottom
    stairs with the back away from the table, touching it, with wall-sign or open-trapdoor
    armrests. Stools are fence + carpet. Bars and counters are upside-down stairs with the
    solid half toward the staff. Lived-in rooms cover 20-35% of floor cells with furniture
    (aim for that, not 5-15 single props), keep 3 clear ceiling (halls 5), a 1-wide aisle
    between table groups, and a clear path from every door. Put runs (kitchen line,
    shelving, bookshelves) on the walls and table groups in the middle. Taverns have a store
    below and the taproom above. Inns have a hall, a courtyard, and a row of equal guest
    rooms off one corridor.
- **Detail by distance.** Spend detail where players stand close (entrance, main facade,
  tower top); simpler stamped repeats elsewhere. This also keeps scripts short.

## Modded blocks

- `palette.json` lists allowed blocks: `{"blocks": {"mymod:copper_bricks": {"kind": "bricks",
  "family": "copper_bricks", "states": {...}, "notes": "..."}}}`. With `Palette.load()`,
  any non-vanilla ID not in it raises an error with close-match suggestions.
- Generate one from a mod's resources:
  `python <skill>/scripts/make_palette.py <mod folder containing assets/> -o palette.json`,
  then fill in `notes` ("glows", "use for roofs"). Keep it in `mc_shared/palettes/` with
  an index line so it is never regenerated for that mod.
- Choose by `kind`/`family`: a family's `_stairs`/`_slab` for roofs and steps, `_wall` for
  fences and parapets. States use the standard syntax
  (`mymod:foo_stairs[facing=north,half=bottom]`); only use properties listed under `states`.
- Vanilla IDs are not validated offline: stick to well-known names, and tell the user if
  you used one you are unsure exists in their version.

## Delivery and running

- `~` coordinates build from the executing player's position: x east, z south, y up. Tell
  the user to stand at the build's north-west corner, on the floor's ground level.
- Datapack location: `data/<namespace>/function/<name>.mcfunction` (1.21+) or
  `data/<namespace>/functions/<name>.mcfunction` (1.20.6 and earlier). Run with
  `/function <namespace>:<name>`; needs `pack.mcmeta` and op (level 2); `/reload` after edits.
- `/fill` caps at 32,768 blocks; the libraries split automatically. Functions run in one
  tick, so warn the user above ~5,000 commands and use `save_sharded` for huge builds.
- `clear_bbox=True` (mcbuild) / `clear_first=True` (mcbig) removes what is in the area
  first; otherwise carved air is still emitted.
- If the user's mod targets a different MC version, check stair/slab/door state names and
  block IDs for that version before delivering.

## Feedback loop

After delivery, ask what looks off (proportions, palette, roof, boring walls, hollow parts).
Write the user's answer to the build's `mc_cache/notes.md` straight away. Lessons that
would help any build go in `mc_shared/lessons.md` so every later build sees them; when
the skill folder is writable, also add them to `references/lessons.md`.
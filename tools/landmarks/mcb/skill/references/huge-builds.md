# Huge builds (mcbig)

Use `scripts/mcbig.py` (`BigBuild`) instead of `mcbuild.Build` when the build is wider
than ~100 blocks, has more than ~200k blocks, or is a whole city/island/mountain.

## Contents
- Why a different engine
- API cheat sheet
- Workflow for a multi-session mega-build
- Export and running in game
- Performance and limits
- Troubleshooting

## Why a different engine
A single function stops after `maxCommandChainLength` commands (default 65,536), `/fill`
caps at 32,768 blocks, and commands fail in unloaded chunks. So `save_sharded` writes a
datapack of many step files: for each 64x64 tile it forceloads the area, waits, runs the
tile's commands in batches, un-forceloads, and `schedule function` chains to the next
step. Boxes are greedily merged, so 6M blocks became ~69k commands in testing.

## API cheat sheet
`b = BigBuild(palette=None, seed=0, y_min=0, y_max=255)`; y is build-local.
- Primitives: `set, fill, box, clear, hollow_box, walls, pillar, mix`
- Vectorized shapes: `cylinder(cx,y1,cz,r,y2,block,hollow,thickness)`,
  `ring(cx,y1,cz,r_in,r_out,y2,block)`,
  `tapered_cylinder(cx,y1,cz,y2,r_bottom,r_top,block,hollow,thickness)` (cones, tiers),
  `dome(cx,cy,cz,r,block,hollow,thickness)`,
  `heightfield(x1,z1,x2,z2,y_base,height_fn(X,Z),block)` (terraces, slopes)
- Anything else: `fill_where(x1,y1,z1,x2,y2,z2, func, block)` where `func(X, y, Z)`
  returns a bool mask (X is (nx,1), Z is (1,nz), y an int). Use it for arches, canals,
  spirals, torus shapes, radial wedges (`np.arctan2`), noise, etc.
- Later paint overwrites earlier paint, so order is: big forms, then carve with
  `clear`/masks, then detail.
- Inspect: `summary()`, `bounds()`, `render_top(path, px)`, `render_section(path, axis, index, px)`.
  View the PNGs with the image viewer tool and fix problems *before* exporting.

Procedural detail (houses, trees, windows) is written as plain Python loops that call
these primitives; 3,500 houses built in about 0.1 s.

## Reusable modules (prefabs)
Design one perfect unit in a small `BigBuild` (a house, tower, wall segment, gate, lamp
post), then tile it with `stamp` / `stamp_many`:
```python
hut = BigBuild(y_min=0, y_max=30); ...design it around local (0,0,0)...
city.stamp(hut, x, y, z, rot=1, mirror=False)             # rot = 90-degree clockwise turns
city.stamp_many(hut, [(x, y, z, rot, mirror), ...])        # thousands per second
```
Directional states (stairs, doors, logs, fences/walls/panes, trapdoors) rotate and
mirror with the module. Use `include_air=False` to leave surroundings untouched.
Build a few variants (small/medium/tall, three roof styles) and stamp them with seeded
random choice, rotation and mirroring so the city does not look cloned. Stamping 3,600
huts took about 1.5 s.

## Workflow for a multi-session mega-build
1. Decide scale and a **world origin**; keep a `plan.md` of coordinates (centre, tier
   heights, gate angles, canal paths) so later sessions stay consistent.
2. Put each stage in its own script/module (`stage1_layout.py`, `stage2_hull.py`...) that
   regenerates from numbers in one shared `config.py`; never rely on in-memory state
   across sessions. Re-run earlier stages in the same `BigBuild` when later stages need to
   carve into them, then export only what changed, or export the whole thing.
3. After each stage: render top view + 2-3 sections, check against the references,
   export a datapack, and ask the user to run it and send screenshots from set angles
   (aerial, ground-level, one close-up).
4. Fold corrections into `config.py`/the stage script and re-export.

## Export and running in game
```python
stats = b.save_sharded("out", namespace="water7", name="hull",
                       origin=(X, Y, Z), max_commands=4000, step_delay=2,
                       function_dir="function",   # "functions" for MC <= 1.20.6
                       pack_format=48)            # match the user's Minecraft version
```
- Copy the generated pack folder into the world's `datapacks/` folder, then `/reload`
  (or `/datapack enable "file/<pack_name>"`).
- Run `/function <namespace>:<name>/start` standing anywhere; coordinates are absolute.
- Needs operator permissions (level 2). Do not log out mid-run; it continues in
  background via scheduled functions, and prints `tile i/N` progress in chat.
- If the game says the pack is incompatible, set `pack_format` to the right number for
  that version (or enable it anyway). If functions are not found, the folder is probably
  `functions` vs `function` (older vs newer versions).
- `clear_first=True` clears each tile's area before building (use when replacing
  existing terrain/builds); costs a few extra commands per tile.
- To stop a run: `/schedule clear <namespace>:<name>/step_NNNNN` for the next pending
  step, or just leave the world; unfinished tiles stay forceloaded until
  `/forceload remove all`.

## Performance and limits
- Observed: 400x400 island, ~6M solid blocks, 3,500 houses -> 68,899 commands, 89 steps,
  ~92 s of scheduled waiting, 75 MB RAM, 1.4 s export. In-game execution time is the
  real cost: expect several minutes for builds of that size; lower `max_commands` or raise
  `step_delay` if the server stutters.
- Height: world limits are -64..319 on 1.18+ (checked at export via `world_y_min/max`).
- Water: placed water source blocks spread/flow and trigger many block updates.
  Contain water with solid walls, use waterfalls sparingly, place water last and test.
- The `commandModificationBlockLimit` gamerule (default 32,768) must not be lowered.
- Blocks with block entities (chests, signs) and entities (ships as armor stands) are
  not handled by the voxel engine; place them in a separate command list.

## Troubleshooting
- "Unknown block type": a typo or a block missing in that version; use the palette.
- Parts of the build missing: a tile's forceload didn't finish; raise `load_delay`.
- Roofs/stairs face the wrong way: stair `facing` points toward the *rising* side.
- Build lands at the wrong height: `origin` y is the world y of build-local y=0.

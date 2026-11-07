# Lessons and unverified assumptions

Read this before delivering a build. Add a line whenever the user reports a problem or a
result in game confirms or contradicts something here. Keep entries short.

## Unverified (derived, not yet seen in game)
- `hip_roof` corner shapes (outer_left/outer_right) were derived from Minecraft's stair-shape
  rules; confirm the corners look right in game.
- `square_spiral_stair`: steps climb one block each; confirm walkability and headroom.
- `ship()` proportions are a generic sailing-ship look; tune beam/depth/masts per request.
- Default datapack `pack_format` is 48 (Minecraft 1.21/1.21.1); change for other versions.
- `save_sharded` timing (`load_delay=40`, `step_delay=2`) is a guess; raise if tiles come
  out incomplete, lower for speed.
- `furnish_room` block states (bed foot/head facing, anvil, grindstone face/facing, lectern, hanging
  lantern) follow the usual rules but were not seen in game; confirm each shows correctly.
- `furnish_room` accents (candle states, potted_* plant names, bed colours, loom/stonecutter facing) are
  standard 1.20+ names; confirm in the player's version. Tables are low (fence + bottom slab) and carry no
  items because items cannot sit on a half slab; accents go on solid props instead.
- Large-room rule (longer side > 17) was tested on 100 generated halls up to 50x30 (all passed the audit);
  how it looks and feels in game is unverified, so tune zone size and vignette count from feedback.
- Gothic parts (`pointed_opening`, `square_spire`, `pinnacle`, `flying_buttress`, `ridge_cresting`) and
  `examples/gothic_church_demo.py` were checked only in previews; look at scale and silhouette in game.
- Mesh analysis: texture names are matched by eye from `tiles_top.png`; copper roof stage and iron-bar
  finials in the gothic card are inferred.
- `audit_props` thresholds (max 2 of a non-bulk prop, 18 props per 100 cells) are starting points; tune from feedback.
- `bsp_rooms` connectivity was verified only in simulation (60 random layouts, all rooms reachable).
- Mod block names are checked against the palette only; vanilla names are unchecked.

- mcreef parts (`birdcage_dome`, `bubble_dome`, `chandelier`, `coral_spire`, `gazebo`, kelp, coral,
  creatures) were checked only in renders of `examples/underwater_cage_demo.py`; confirm scale in game.
- `flood` + `waterlog`: water fill and `waterlogged=true` on stairs/slabs/panes/fences/chains were verified
  only in the command output. Confirm in game that bubble interiors stay dry and that large water fills
  do not lag or spill when chunks load (water placed by /fill flows only if a neighbour updates).
- Glass colour names from `mesh_blocks.py` are approximate (alpha-blended tiles); trust the hex colour.

- mcasian (`curved_roof`, `temple_hall`, brackets, lanterns) checked only in renders of
  `examples/asian_temple_demo.py`; confirm roof stairs, corner lifts and bracket stair states in game.

## Confirmed in game
(none yet)

## Rules learned
- With trim, make arcade piers at least 3 wide (the trim ring uses two of them).
- Arches below 5 wide look rectangular; use width 5+ for a round top.
- Underwater: call `waterlog` with the same `keep_dry` as `flood`, otherwise waterloggable blocks inside a
  dry bubble get `waterlogged=true` and leak water (caught in testing).
- Model reading: if a glTF's materials are named after blocks (Mineways), use `mesh_blocks.py`; colour
  guessing in `mesh_analyze.py` cannot tell glass/wool/terracotta colours apart reliably.
- Block-size estimate: use the most common vertex spacing over many meshes; one mesh's spacing can be
  sub-block detail and gives an absurd grid.
- Preview renders need real colours for dyed blocks; `block_color` now knows the 16 dyes, terracotta,
  glass tints and reef blocks (slime, emerald, melon, corals, sea lantern).
- Stone lanterns (or any prop taller than ~half the storey) placed under low eaves collide with the roof
  at small scale: put them on open ground beside the steps.
- East Asian roofs: use a concave profile (power ~2) and a lighter edge block on eaves and hips; a
  straight 45-degree roof reads as European.
- Preview colours: mangrove, crimson and cherry are now coloured in `block_color` (they rendered brown).

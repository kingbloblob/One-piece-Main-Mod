# Mapping real materials and colours to Minecraft blocks

Names are vanilla Java IDs. Some are newer than others (mud bricks 1.19, cherry 1.20,
copper 1.17, tuff/calcite 1.17, deepslate 1.17, bamboo 1.20): confirm they exist in the
player's version. Blend 2-3 blocks per surface (about 70/20/10) with `mix()`.

## Contents
- Walls and masonry
- Roofs
- Metals, glass, water
- Wood
- Colour shortcuts
- Gotchas

## Walls and masonry
| Real material | Good blocks |
|---|---|
| Pale limestone, marble | smooth_sandstone, cut_sandstone, calcite, diorite, polished_diorite, quartz_block, smooth_quartz |
| Warm stone, plaster | sandstone, smooth_sandstone, white_terracotta, white_concrete, terracotta |
| Grey masonry | stone_bricks, andesite, polished_andesite, stone, smooth_stone |
| Dark stone, slate | deepslate_bricks, deepslate_tiles, polished_blackstone_bricks, blackstone |
| Red brick | bricks, red_nether_bricks, mud_bricks, red_terracotta |
| Aged stone | blend stone_bricks 70 / mossy_stone_bricks 15 / cracked_stone_bricks 15 |
| Granite, pinkish | granite, polished_granite |

## Roofs
Vanilla terracotta has **no stairs or slabs**. Substitutes with stairs/slabs/walls:
- Orange/red clay tile: brick_stairs, red_sandstone_stairs, red_nether_brick_stairs, granite_stairs, mud_brick_stairs
- Grey slate: deepslate_tile_stairs, cobbled_deepslate_stairs, stone_brick_stairs
- Weathered copper: cut_copper_stairs -> exposed_ -> weathered_ -> oxidized_cut_copper_stairs
- Wood shingle: spruce_stairs, dark_oak_stairs
- Thatch: hay_block, yellow_terracotta, or dried_kelp_block (no stairs; use slabs of nearby wood)
For solid roof colour with full blocks (flat or stepped roofs), the *_terracotta and
*_concrete blocks are fine.

## Metals, glass, water
- Iron work: iron_bars, chain, lantern, iron_block, polished_blackstone for dark ironwork
- Gold: gold_block, yellow_concrete, raw_gold_block (dull)
- Copper stages (new to aged): copper_block, exposed_copper, weathered_copper, oxidized_copper (+ cut_ variants)
- Glass: glass, glass_pane, tinted_glass, stained_glass in a colour; ice and blue_ice for water-like glass
- Water: `minecraft:water` source blocks; waterfalls need a source block at the top and a
  contained path. Seal channels with solid blocks so they do not flood.

## Wood
oak (warm tan), spruce (dark brown), birch (pale), dark_oak (very dark), acacia (orange),
jungle (reddish), mangrove (red-brown), cherry (pink), bamboo_planks (pale yellow),
crimson/warped (nether colours). Use stripped_ logs for clean beams and pillars.

## Colour shortcuts
- Sea/canal blue: light_blue_concrete, cyan_terracotta, blue_terracotta, prismarine, prismarine_bricks, light_blue_stained_glass
- Orange rooftops: orange_terracotta, terracotta, brick_stairs, red_sandstone
- White marble: quartz_block, smooth_quartz, white_concrete, calcite
- Verdigris green: oxidized_copper, warped_planks, warped_wart_block (small accents)
- Warm lights: lantern, shroomlight, glowstone behind trim, sea_lantern (cool)

## Gotchas
- Leaves decay unless `[persistent=true]` (mcparts.tree adds it).
- Stairs/slabs/walls/fences/doors have states (facing, half, type, shape, hinge); use the
  exact state names from the player's version.
- Falling blocks (sand, gravel, concrete_powder) fall when unsupported; avoid them in structures.
- Light level: interiors need light sources to stay mob-free.

# Grand Line biomes: bigger, blended, island-true

Changed 2026-10-24/25 (thread "Make biomes larger and blend smoothly").

## Bigger biomes
The climate noise that picks biomes (temperature and humidity) now changes 2.5x more slowly
(`worldgen/density_function/grand_line/temperature.json` and `vegetation.json`, `xz_scale` 0.5 -> 0.2; vanilla is 0.25).
An island is now usually one biome, and neighbouring islands tend to share a climate, so you sail through "regions"
(a snowy stretch, a desert stretch) instead of a different biome every island.

## Soft edges instead of hard lines
`onepiece:rings` (RingBiomeSource) has two new settings in `worldgen/world_preset/grand_line.json`:

- `edge` (32): neighbouring biomes finger into each other. The climate is read a little to the side of where you stand,
  following a slow wave (about 180 blocks long) plus a fine mottle (about 20 blocks), so a desert/jungle border is a ragged,
  speckled band roughly 40-90 blocks wide: sand patches in the jungle, bushes in the sand, grass colours blending across.
  Beaches and seas are not moved (continentalness, erosion and depth are read exactly), so coasts stay put.
- `blend` (400): the band around each ring edge (East Blue -> Paradise -> New World edge -> deep New World) where patches of
  the next ring's islands appear more and more often. Set both to 0 for the old hard edges.

## What each island got (vanilla plants, ground, colours)
`tools/islands/island_flavour.py` adds vanilla features per island biome (and re-sorts every biome's feature list into
vanilla's order, which Minecraft requires). Highlights:

- East Blue (east_blue, orange_town, conomi_islands, loguetown, marineford): tall grass, wildflowers, fallen oaks, bee oaks,
  birches at Marineford, boulders and leaf litter at Loguetown, coarse-dirt paths.
- Drum Island: snow piles, ice patches, grove spruces, permafrost. Alabasta: cactus, dry grass, dead bushes, fossils, red-sand outcrops.
- Jaya, Little Garden, Amazon Lily, Green Bit, Zou: fallen jungle logs, mega jungle trees, large ferns, vines, mud and Jungle Loam
  (fossils on Little Garden; moss carpets on Zou).
- Skypiea: Island Cloud patches on the ground, meadow flowers, pale sky-green grass. Sabaody: water lilies, bushes.
- Thriller Bark / Kuraigana: pale oaks, pale moss, closed eyeblossoms, giant mushrooms (Thriller Bark), boulders, gravel and
  mossy cobble ruins, Grave Soil. Withered Forest: orange/red/yellow poplars, fallen poplars, leaf litter, dead bushes.
- Wano: meadow flowers, bushes, moss and podzol patches; Kuri: bamboo, badlands oaks, dry grass, coarse dirt.
- Punk Hazard frozen: ice piles and patches; burning: Volcanic Ash, fossils. Elbaph: boulders, mega spruces, fallen spruces.
- Dressrosa / Enies Lobby / God Valley: big oaks, meadow wildflowers, birches (Enies), mossy-cobble ruins, acacias (Dressrosa).
- Whole Cake / Cacao Island: sweet berries, Sugar Sand beaches. Egghead: cyan-grey grass, Permafrost, gravel, no trees.
- Onigashima / Hachinosu: fossils, dry grass, dead bushes, Black Sand and Volcanic Ash. Red Line: dry grass, red sand, gravel.
- Fish-Man Reef: kelp and sea pickles; New World Sea: cold kelp and deep seagrass.

## New plants and soils (One Piece: Nature tab)
100 new blocks from `tools/flora/gen_flora.py`: 24 flowers, 20 two-block plants, 16 grasses, 14 shrubs, 20 ground covers and
6 soils, each tied to its islands. See `flora/flora-guide.md` for the full list and where each grows.
Every plant is craftable (a vanilla plant + the matching dye, or bone meal), flowers give dye, and all of them also grow on
sand, snow, rock, ash, Island Cloud and the new soils.

## Regenerating
- `python3 tools/worldgen/gen_boss_islands.py` rewrites the biomes and then runs `island_look.py` and `island_flavour.py`.
- `island_flavour.py` wants the vanilla 26.3 data (`VANILLA=<unzipped client.jar>`) the first time; afterwards it uses
  `tools/islands/feature_order.json`.
- `python3 tools/flora/gen_flora.py <out> --install <source>` regenerates the flora.

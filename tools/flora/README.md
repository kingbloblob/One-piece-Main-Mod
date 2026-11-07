# Island flora generator (com.onepiecemod.flora)

Flowers, two-block plants, grass tufts, shrubs, ground cover and soils for every Grand Line island biome.
Everything comes from the tables at the top of gen_flora.py; textures are drawn by flora_textures.py (and tools/deco/textures.py).

    python3 gen_flora.py /tmp/flora-out --install /mnt/project-files/one-piece-mod/source
    sh /mnt/project-files/one-piece-mod/tools/build.sh && sh /mnt/project-files/one-piece-mod/tools/rebuild-zip.sh

- Where a plant grows: data/onepiece/tags/worldgen/biome/has_flora_<plant>.json (FloraFeature adds it to those biomes at runtime).
- The soils (Sugar Sand, Black Sand, Volcanic Ash, Grave Soil, Jungle Loam, Permafrost) are placed by the Grand Line
  surface rules: see tools/islands/island_flavour.py (GROUND table).
- FloraPlants.java (plant block classes that also stand on onepiece:flora_plant_soil) is hand-written and copied in as is.
- Shared data/minecraft/tags files are union-merged on install; everything else under src/ is ours and replaced.

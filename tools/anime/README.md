Generator for the anime look (built-in resource pack at source/src/main/resources/resourcepacks/anime_look).
It regrades Minecraft's own textures: brighter, warmer and more saturated colours, flatter cel-style shading,
dark ink edges on items, and lusher grass and leaf colormaps. Menus (gui/) are left to the pirate_menus pack.
Needs python3 + numpy + Pillow. Run it again after each Minecraft update so new and changed textures get the look:
  T=source/src/main/resources/resourcepacks/anime_look/assets/minecraft/textures
  python3 gen_anime_look.py ~/.minecraft/versions/26.3/26.3.jar $T
The output folder is wiped and rewritten each run. pack.mcmeta and pack.png are hand-kept.
Loom keeps the jar at ~/.gradle/caches/fabric-loom/26.3/minecraft-client.jar if there is no launcher install.
After regenerating, check nothing will show up purple, invisible or with stacked animation frames:
  python3 check_assets.py source/src/main/resources
Showroom for judging the look in game (rerun it when the mod gets new blocks):
  python3 gen_showroom.py source/src/main/resources source/src/main/resources/data/onepiece/function/anime_showroom.mcfunction
  In game, stand at the north-west corner and run /function onepiece:anime_showroom. It clears 48 x 13 x 40 blocks
  east and south of you, then builds rows of vanilla and mod blocks, fires, lava, water, a portal, grass and leaves
  in eight biomes, and frozen mobs. Flip "One Piece Anime Look" in Options > Resource Packs to compare.

Art generators for the pirate menu theme (built-in resource pack at source/src/main/resources/resourcepacks/pirate_menus).
All art is original and drawn by these scripts (python3 + numpy + Pillow). Run from any folder:
  G=source/src/main/resources/resourcepacks/pirate_menus/assets/minecraft/textures/gui
  python3 panorama.py $G/title/background 1024
  python3 widgets.py $G
  python3 logo.py $G/title     (needs Caladea Bold at /usr/share/fonts/truetype/crosextra/)
The .png.mcmeta nine-slice files next to the sprites are hand-kept; do not delete them.

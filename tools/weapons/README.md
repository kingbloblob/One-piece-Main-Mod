# Weapon models (life-size 3D melee weapons, named swords, slingshots)

`gen_weapon_models.py` writes the 3D in-hand models for 24 weapons (the guns have their own script in `tools/guns`):

- `assets/onepiece/models/item/<name>_held.json`: the 3D model, built from boxes
- `assets/onepiece/items/<name>.json`: the flat icon in the inventory (display context `gui`), the 3D model everywhere else
- `assets/onepiece/textures/item/weapon_parts.png`: shared material atlas (steel, hamon, black blade, gold, cord wraps, lacquer, gems...)

Run: `python3 -I gen_weapon_models.py <source>/src/main/resources/assets/onepiece [names...]` (no names = all).
Re-run the script instead of hand-editing the JSON.

Sizes are real-world: 1 model pixel is about 6 cm and the player about 29 pixels tall, so katanas are ~16 px, Kikoku ~27,
Yoru ~33, Hassaikai ~29, the bisento and trident ~45. Built from the anime look: Wado white cord + gold guard, Kitetsu red,
Shusui black blade + four-leaf guard, Enma purple, Yoru black cross with green jewels, Kikoku long white-corded nodachi
with a red tassel, Gryphon gold knuckle-bow saber, Soul Solid cane crook, Kiribachi saw teeth, Kaido's studded kanabo,
Whitebeard's black-pole bisento, Katakuri's trident, Enel's gold staff, Clima-Tact with the three weather balls, etc.

Rules (so the arm poses in `anim/client/Poses.java` and the gun convention line up):
- blades and poles point up (+Y), edge toward -Z; each weapon lists its `grip` (where the fist goes)
- third person has no rotation: like the guns, the hand frame points model -Z along the arm, so a blade on +Y sticks
  forward when the arm hangs, like Minecraft's own swords
- first person tilts the weapon and shrinks long ones (scale capped at 15 / length) so they don't fill the screen
- element angles must be -45/-22.5/0/22.5/45; coordinates within -16..32

Checked in the real client (headless) 2026-10-29: armor stands holding every weapon (side view) and first person.

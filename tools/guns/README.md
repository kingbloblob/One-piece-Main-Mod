# Gun models (3D guns in hand)

`gen_gun_models.py` writes the 3D in-hand models for the guns, built from boxes:

- `assets/onepiece/models/item/<gun>_held.json` for flintlock_pistol, marine_rifle, tommy_gun, hand_cannon, senriku
- `assets/onepiece/items/<gun>.json`: the flat icon in the inventory (display context `gui`), the 3D model everywhere else
- `assets/onepiece/textures/item/gun_parts.png`: shared material atlas (wood with grain, iron, steel, brass, black, lens...)
- the slingshots (kabuto, kuro_kabuto) stay flat but stand upright in the fist

Run: `python3 -I gen_gun_models.py <source>/src/main/resources/assets/onepiece`

Rules the models follow (so the arm poses in `anim/client/Poses.java` line up):
- barrel points north (-Z), grip points down; each gun lists its `grip` point (where the fist goes)
- third person transforms have no rotation: the gun points along the arm, so the pose code aims the gun by aiming the arm
- poses: `GunItem.Hold` (PISTOL one hand, RIFLE two hands at the shoulder, SLINGSHOT) in `WeaponItems`; players aim for 2 s after each
  shot, mobs aim while they are fighting; each shot plays `Anim.SHOOT` for the recoil kick (GunItem.fireOnce, HumanNpc.shoot)

Checked in the real client (headless) 2026-10-24, first and third person.

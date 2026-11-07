package com.onepiecemod.world;

import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.LinkedHashMap;
import java.util.Map;

import com.google.gson.Gson;

import net.minecraft.network.chat.Component;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.ai.attributes.AttributeInstance;
import net.minecraft.world.entity.ai.attributes.Attributes;

import com.onepiecemod.character.CharacterData;

/**
 * The gear and stats of the guards that structures spawn: Marine soldiers, pirates, Fish-Men, jailers...
 * Read from src/main/resources/onepiece/guards.json. Edit that file to make guards stronger or weaker.
 *
 * A structure marks a normal Minecraft mob (a vindicator, a pillager, a drowned...) with the tags
 * "onepiece_guard" and "onepiece_kit_<id>". The first time it loads, WorldFeature calls apply().
 */
public class GuardKit {
	public static final String GUARD_TAG = "onepiece_guard";
	public static final String KIT_TAG_PREFIX = "onepiece_kit_";

	public String id;
	public String entity; // only used by the structure generator
	public String name;
	public String mainhand;
	public String offhand;
	public String head;
	public String chest;
	public String legs;
	public String feet;
	public float health;  // 0 = keep the mob's normal health
	public float damage;  // 0 = keep the mob's normal damage

	private static final Map<String, GuardKit> ALL = new LinkedHashMap<>();

	public static GuardKit get(String id) {
		if (ALL.isEmpty()) {
			try (InputStream in = GuardKit.class.getResourceAsStream("/onepiece/guards.json")) {
				GuardKit[] list = new Gson().fromJson(new InputStreamReader(in, StandardCharsets.UTF_8), GuardKit[].class);
				for (GuardKit kit : list) {
					ALL.put(kit.id, kit);
				}
			} catch (Exception e) {
				throw new RuntimeException("Could not read onepiece/guards.json", e);
			}
		}
		return ALL.get(id);
	}

	/** Finds the kit tag on a freshly placed guard and dresses it up. */
	public static void applyFromTags(Mob mob) {
		mob.removeTag(GUARD_TAG);
		String kitId = null;
		for (String tag : mob.entityTags()) {
			if (tag.startsWith(KIT_TAG_PREFIX)) {
				kitId = tag.substring(KIT_TAG_PREFIX.length());
			}
		}
		if (kitId == null) {
			return;
		}
		mob.removeTag(KIT_TAG_PREFIX + kitId);
		GuardKit kit = get(kitId);
		if (kit != null) {
			kit.apply(mob);
		}
	}

	public void apply(Mob mob) {
		equip(mob, EquipmentSlot.MAINHAND, mainhand);
		equip(mob, EquipmentSlot.OFFHAND, offhand);
		equip(mob, EquipmentSlot.HEAD, head);
		equip(mob, EquipmentSlot.CHEST, chest);
		equip(mob, EquipmentSlot.LEGS, legs);
		equip(mob, EquipmentSlot.FEET, feet);

		if (health > 0) {
			AttributeInstance maxHealth = mob.getAttribute(Attributes.MAX_HEALTH);
			if (maxHealth != null) {
				maxHealth.setBaseValue(health);
			}
		}
		if (damage > 0) {
			AttributeInstance attack = mob.getAttribute(Attributes.ATTACK_DAMAGE);
			if (attack != null) {
				attack.setBaseValue(damage);
			}
		}
		mob.setHealth(mob.getMaxHealth());
		if (name != null) {
			mob.setCustomName(Component.literal(name));
		}
		mob.setPersistenceRequired(); // Guards stay put instead of despawning.
	}

	private static void equip(Mob mob, EquipmentSlot slot, String itemId) {
		if (itemId != null && !itemId.isEmpty()) {
			mob.setItemSlot(slot, CharacterData.stack(itemId, 1));
		}
	}
}

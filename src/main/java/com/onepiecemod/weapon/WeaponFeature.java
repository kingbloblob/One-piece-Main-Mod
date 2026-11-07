package com.onepiecemod.weapon;

import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.item.CreativeModeTab;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;

import net.fabricmc.fabric.api.creativetab.v1.FabricCreativeModeTab;
import net.fabricmc.fabric.api.entity.event.v1.ServerLivingEntityEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;

import net.minecraft.core.Registry;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.bounty.MarineEntity;
import com.onepiecemod.character.CharacterEntity;

/**
 * Guns, ammo and melee weapons from the series. OnePieceMod calls initialize().
 *
 * Where to get them:
 *  - Crafted at the stations (see onepiece/station_recipes.json), the stronger ones locked behind bosses or bounty.
 *  - Dropped by the bosses who use them (below).
 *  - Marines sometimes drop bullets.
 */
public class WeaponFeature {
	public static final ResourceKey<CreativeModeTab> TAB_KEY = ResourceKey.create(
			BuiltInRegistries.CREATIVE_MODE_TAB.key(), OnePieceMod.id("weapons")
	);

	public static void initialize() {
		WeaponUpgrades.initialize();
		WeaponItems.initialize();
		MeleeEffects.initialize();
		BlackBlades.initialize();
		ServerTickEvents.END_SERVER_TICK.register(GunItem::tickBursts);

		ServerLivingEntityEvents.AFTER_DEATH.register((entity, source) -> {
			if (!(entity.level() instanceof ServerLevel level)) {
				return;
			}
			if (entity instanceof CharacterEntity boss && boss.isBoss() && boss.isFirstWin()) { // Rematches don't drop it again.
				ItemStack drop = switch (boss.getCharacterId()) {
					case "kaido" -> new ItemStack(WeaponItems.HASSAIKAI);
					case "whitebeard" -> new ItemStack(WeaponItems.MURAKUMOGIRI);
					case "crocodile" -> new ItemStack(WeaponItems.GOLDEN_HOOK);
					case "killer" -> new ItemStack(WeaponItems.PUNISHER);
					case "katakuri" -> new ItemStack(WeaponItems.MOGURA);
					case "enel" -> new ItemStack(WeaponItems.NONOSAMA_BO);
					case "big_mom" -> new ItemStack(WeaponItems.HOMIE_UMBRELLA);
					case "blackbeard" -> new ItemStack(WeaponItems.SENRIKU); // Van Augur is on his crew.
					case "buggy" -> new ItemStack(WeaponItems.BUGGY_KNIFE, 8);
					default -> ItemStack.EMPTY;
				};
				if (!drop.isEmpty()) {
					boss.spawnAtLocation(level, drop);
				}
			} else if (entity instanceof MarineEntity marine) {
				// Marines carry spare rounds; now and then a Seastone one.
				float roll = level.getRandom().nextFloat();
				if (roll < 0.05f) {
					marine.spawnAtLocation(level, new ItemStack(WeaponItems.SEASTONE_BULLET, 2));
				} else if (roll < 0.45f) {
					marine.spawnAtLocation(level, new ItemStack(WeaponItems.BULLET, 2 + level.getRandom().nextInt(3)));
				}
			}
		});

		Registry.register(BuiltInRegistries.CREATIVE_MODE_TAB, TAB_KEY, FabricCreativeModeTab.builder()
				.icon(() -> new ItemStack(WeaponItems.FLINTLOCK_PISTOL))
				.title(Component.literal("One Piece: Weapons"))
				.displayItems((params, output) -> {
					for (Item item : WeaponItems.ALL) {
						output.accept(item);
					}
				})
				.build());
	}
}

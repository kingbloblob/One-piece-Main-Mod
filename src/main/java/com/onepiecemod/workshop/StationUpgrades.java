package com.onepiecemod.workshop;

import java.util.ArrayList;
import java.util.List;

import com.mojang.serialization.Codec;

import net.minecraft.ChatFormatting;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.player.Player;

import net.fabricmc.fabric.api.attachment.v1.AttachmentRegistry;
import net.fabricmc.fabric.api.attachment.v1.AttachmentType;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.crafting.Station;
import com.onepiecemod.crafting.StationRecipe;

/**
 * Which station upgrades each player has built, and what they do when crafting.
 * The upgrades themselves are listed in onepiece/station_upgrades.json (see StationUpgrade).
 */
public class StationUpgrades {
	/** Upgrade ids this player has built. Kept on death. */
	public static final AttachmentType<List<String>> OWNED = AttachmentRegistry.create(
			OnePieceMod.id("station_upgrades"),
			builder -> builder.persistent(Codec.STRING.listOf()).copyOnDeath()
	);

	public static void initialize() {
		// Calling this loads the class, which registers the attachment at startup.
	}

	public static List<String> owned(Player player) {
		List<String> list = player.getAttached(OWNED);
		return list != null ? list : List.of();
	}

	public static boolean has(Player player, String id) {
		return owned(player).contains(id);
	}

	/** How many upgrades of this station the player has built. */
	public static int count(Player player, Station station) {
		int total = 0;
		for (String id : owned(player)) {
			StationUpgrade upgrade = StationUpgrade.get(id);
			if (upgrade != null && upgrade.stationType() == station) {
				total++;
			}
		}
		return total;
	}

	/** Null if the player may build it now (not counting the cost), else why not. "Built" if they already have it. */
	public static String lockReason(ServerPlayer player, StationUpgrade upgrade) {
		if (has(player, upgrade.id)) {
			return "Built";
		}
		List<String> missing = new ArrayList<>();
		List<String> parents = new ArrayList<>();
		for (String parent : upgrade.parents) {
			if (!has(player, parent)) {
				StationUpgrade up = StationUpgrade.get(parent);
				parents.add(up != null ? up.name : parent);
			}
		}
		if (!parents.isEmpty()) {
			missing.add("Build first: " + String.join(", ", parents));
		}
		String gate = costRecipe(upgrade).lockReason(player);
		if (gate != null) {
			missing.add(gate);
		}
		return missing.isEmpty() ? null : String.join("; ", missing);
	}

	/** The upgrade's cost and gates as a station recipe, so the same inventory checks can be used. */
	public static StationRecipe costRecipe(StationUpgrade upgrade) {
		StationRecipe recipe = new StationRecipe();
		recipe.id = "upgrade:" + upgrade.id;
		recipe.station = upgrade.station;
		recipe.result = upgrade.icon;
		recipe.ingredients = upgrade.cost;
		recipe.requires = upgrade.requires;
		return recipe;
	}

	/** Builds the upgrade if the player may. Returns true if it was built. */
	public static boolean build(ServerPlayer player, StationUpgrade upgrade) {
		String locked = lockReason(player, upgrade);
		if (locked != null) {
			player.sendOverlayMessage(Component.literal(locked.equals("Built") ? "You already built that." : "Locked: " + locked)
					.withStyle(ChatFormatting.RED));
			return false;
		}
		StationRecipe cost = costRecipe(upgrade);
		if (!cost.hasIngredients(player)) {
			player.sendOverlayMessage(Component.literal("You don't have everything you need.").withStyle(ChatFormatting.RED));
			return false;
		}
		cost.takeIngredients(player);
		List<String> list = new ArrayList<>(owned(player));
		list.add(upgrade.id);
		player.setAttached(OWNED, list);

		Station station = upgrade.stationType();
		player.sendSystemMessage(Component.literal("Station upgrade built: " + upgrade.name
				+ (station != null ? " (" + station.title() + ")" : "")).withStyle(ChatFormatting.GOLD));
		for (StationUpgrade.Perk perk : upgrade.perks) {
			player.sendSystemMessage(Component.literal("  " + perk.describe()).withStyle(ChatFormatting.YELLOW));
		}
		List<String> unlocked = new ArrayList<>();
		for (StationRecipe recipe : StationRecipe.all().values()) {
			if (recipe.requires != null && upgrade.id.equals(recipe.requires.upgrade)) {
				unlocked.add(recipe.resultStack().getHoverName().getString());
			}
		}
		if (!unlocked.isEmpty()) {
			player.sendSystemMessage(Component.literal("  New recipes: " + String.join(", ", unlocked)).withStyle(ChatFormatting.YELLOW));
		}
		ServerLevel level = player.level();
		level.playSound(null, player.blockPosition(), SoundEvents.SMITHING_TABLE_USE, SoundSource.PLAYERS, 1.0f, 0.8f);
		level.playSound(null, player.blockPosition(), SoundEvents.PLAYER_LEVELUP, SoundSource.PLAYERS, 0.6f, 1.2f);
		level.sendParticles(ParticleTypes.HAPPY_VILLAGER, player.getX(), player.getY() + 1, player.getZ(), 20, 0.6, 0.6, 0.6, 0);
		return true;
	}

	// ---- Perks ----

	/** Total chance from every owned upgrade's perks of this type that apply to the recipe (capped at 75%). */
	public static float chance(Player player, StationRecipe recipe, String type) {
		float total = 0;
		for (String id : owned(player)) {
			StationUpgrade upgrade = StationUpgrade.get(id);
			if (upgrade == null || upgrade.stationType() != recipe.stationType()) {
				continue;
			}
			for (StationUpgrade.Perk perk : upgrade.perks) {
				if (type.equals(perk.type) && perk.appliesTo(recipe.id)) {
					total += perk.chance;
				}
			}
		}
		return Math.min(0.75f, total);
	}

	/** Rolls the "extra result" perk for one craft. */
	public static boolean rollBonus(Player player, StationRecipe recipe) {
		float chance = chance(player, recipe, "bonus");
		return chance > 0 && player.getRandom().nextFloat() < chance;
	}

	/** Rolls the "keep the ingredients" perk for one craft. */
	public static boolean rollSave(Player player, StationRecipe recipe) {
		float chance = chance(player, recipe, "save");
		return chance > 0 && player.getRandom().nextFloat() < chance;
	}
}

package com.onepiecemod.shipcombat;

import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.properties.IntegerProperty;

import com.onepiecemod.ship.HelmBlock;
import com.onepiecemod.ship.ShipFeature;
import com.onepiecemod.ship.ShipUpgrades;
import com.onepiecemod.resource.Resources;
import com.onepiecemod.world.WorldBlocks;

/**
 * Fitting upgrades at a Galley-La Shipyard. Dock your ship next to the Shipyard, then right-click the Crane holding
 * Iron Hull Plating, Reinforced Sailcloth or a Heavy Gun Carriage. The workers fit it to the nearest docked ship
 * (found by her Ship's Wheel) and the upgrade sails with her from then on. Each upgrade goes up to level 5:
 * level 3 is master work and also needs Adam Wood, the treasure tree the Thousand Sunny was built from;
 * levels 4 and 5 are legendary and also need Kokuto black steel (and a Nether Star for level 5). See cost().
 */
public class ShipyardUpgrades {
	/** How far from the Crane a docked ship's wheel may be. */
	private static final int REACH = 24;

	/**
	 * What each level needs besides the upgrade item. Level 3 is master work (Adam Wood);
	 * levels 4 and 5 are legendary: lots of Adam Wood, Kokuto black steel, and a Nether Star for level 5.
	 */
	private record Cost(int adamWood, int kokuto, int netherStars) {
		boolean has(ServerPlayer player) {
			return count(player, WorldBlocks.ADAM_LOG.asItem()) >= adamWood && count(player, Resources.KOKUTO_INGOT) >= kokuto
					&& count(player, Items.NETHER_STAR) >= netherStars;
		}

		void take(ServerPlayer player) {
			ShipyardUpgrades.take(player, WorldBlocks.ADAM_LOG.asItem(), adamWood);
			ShipyardUpgrades.take(player, Resources.KOKUTO_INGOT, kokuto);
			ShipyardUpgrades.take(player, Items.NETHER_STAR, netherStars);
		}

		String explain(int level) {
			StringBuilder text = new StringBuilder("Level " + level + (level > ShipUpgrades.GALLEY_LA_MAX ? " is legendary work" : " is master work")
					+ ": the workers also need " + adamWood + " Adam Wood logs");
			if (kokuto > 0) {
				text.append(", ").append(kokuto).append(" Kokuto Ingots");
			}
			if (netherStars > 0) {
				text.append(" and ").append(netherStars).append(" Nether Star");
			}
			return text.append(". (A Shipwright in your crew finds Adam Wood at the Shipyard; Kokuto is deep underground.)").toString();
		}
	}

	private static Cost cost(int level) {
		return switch (level) {
			case 3 -> new Cost(4, 0, 0);
			case 4 -> new Cost(8, 4, 0);
			case 5 -> new Cost(16, 8, 1);
			default -> new Cost(0, 0, 0);
		};
	}

	private static int count(ServerPlayer player, Item item) {
		return Cannons.countAmmo(player.getInventory(), item);
	}

	/** Called when the Shipyard is used. Returns true if the player was holding an upgrade (fitted or not). */
	public static boolean tryFit(ServerPlayer player, BlockPos crane) {
		ItemStack held = player.getMainHandItem();
		IntegerProperty part;
		String name;
		if (held.is(ShipCombatFeature.HULL_PLATING)) {
			part = HelmBlock.HULL;
			name = "Hull";
		} else if (held.is(ShipCombatFeature.REINFORCED_SAILCLOTH)) {
			part = HelmBlock.SAILS;
			name = "Sails";
		} else if (held.is(ShipCombatFeature.HEAVY_GUN_CARRIAGE)) {
			part = HelmBlock.GUNS;
			name = "Guns";
		} else {
			return false;
		}
		ServerLevel level = (ServerLevel) player.level();
		BlockPos wheel = nearestWheel(level, crane);
		if (wheel == null) {
			player.sendSystemMessage(Component.literal("No docked ship here. Drop anchor with your Ship's Wheel within " + REACH
					+ " blocks of the Crane, then bring the upgrade.").withStyle(ChatFormatting.YELLOW));
			return true;
		}
		BlockState state = level.getBlockState(wheel);
		int level0 = state.getValue(part);
		if (level0 >= ShipUpgrades.MAX_LEVEL) {
			player.sendSystemMessage(Component.literal("Her " + name + " are already legendary (level " + ShipUpgrades.MAX_LEVEL + "). Nothing on the seas beats that.")
					.withStyle(ChatFormatting.YELLOW));
			return true;
		}
		int next = level0 + 1;
		Cost cost = cost(next);
		if (!player.isCreative() && !cost.has(player)) {
			player.sendSystemMessage(Component.literal(cost.explain(next)).withStyle(ChatFormatting.YELLOW));
			return true;
		}
		if (!player.isCreative()) {
			held.shrink(1);
			cost.take(player);
		}
		BlockState upgraded = state.setValue(part, level0 + 1);
		if (next == ShipUpgrades.MAX_LEVEL) {
			com.onepiecemod.advancement.AdvancementFeature.grant(player, "journey/legendary_ship");
		}
		level.setBlock(wheel, upgraded, Block.UPDATE_CLIENTS);
		level.playSound(null, wheel, SoundEvents.ANVIL_USE, SoundSource.BLOCKS, 1.0f, 0.9f);
		level.sendParticles(ParticleTypes.HAPPY_VILLAGER, wheel.getX() + 0.5, wheel.getY() + 1.2, wheel.getZ() + 0.5, 12, 0.6, 0.4, 0.6, 0);
		player.sendSystemMessage(Component.literal("Galley-La fitted the upgrade: " + name + " level " + (level0 + 1) + ". Your ship now has "
				+ ShipUpgrades.describe(upgraded) + ". (It takes effect next time she sets sail.)").withStyle(ChatFormatting.GREEN));
		return true;
	}

	private static BlockPos nearestWheel(ServerLevel level, BlockPos crane) {
		BlockPos best = null;
		double bestDistance = Double.MAX_VALUE;
		for (BlockPos pos : BlockPos.betweenClosed(crane.offset(-REACH, -6, -REACH), crane.offset(REACH, 12, REACH))) {
			if (level.getBlockState(pos).is(ShipFeature.HELM)) {
				double distance = pos.distSqr(crane);
				if (distance < bestDistance) {
					bestDistance = distance;
					best = pos.immutable();
				}
			}
		}
		return best;
	}

	private static void take(ServerPlayer player, Item item, int amount) {
		for (int slot = 0; slot < player.getInventory().getContainerSize() && amount > 0; slot++) {
			ItemStack stack = player.getInventory().getItem(slot);
			if (stack.is(item)) {
				int take = Math.min(amount, stack.getCount());
				stack.shrink(take);
				amount -= take;
			}
		}
	}
}

package com.onepiecemod.building;

import java.util.List;

import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.block.Blocks;

import com.onepiecemod.crew.Crew;
import com.onepiecemod.crew.CrewAttachments;
import com.onepiecemod.crew.CrewRole;
import com.onepiecemod.world.WorldBlocks;

/**
 * Galley-La Shipyard: a little dock with a crane, like the shipyards of Water 7.
 * Once a day its workers cut timber for your ships. Come and collect it; up to 3 days can pile up.
 * With a Shipwright in your crew they also find a piece of rare Adam Wood each day.
 */
public class ShipyardBuilding extends Multiblock {
	private static final int MAX_DAYS_STORED = 3;

	public ShipyardBuilding() {
		super("shipyard_crane", "Galley-La Shipyard");
		fill("planks or wooden slabs for the 3x3 deck under the Crane", Parts.WOOD_DECK, Blocks.SPRUCE_PLANKS.defaultBlockState(), square(-1, 1));
		atLeastAt("water around the deck (10 of the 16 blocks around it must be water)", Parts.WATER, Blocks.STAINED_GLASS.lightBlue().defaultBlockState(), ring(-1, 2), 10);
		fill("logs for the crane post (4 tall, on the north-west corner of the deck)", Parts.POST, Blocks.SPRUCE_LOG.defaultBlockState(), column(-1, -1, 0, 3));
		fill("fences, logs or planks for the crane arm (sticking out from the top of the post)",
				state -> Parts.RAIL.test(state) || Parts.POST.test(state) || Parts.PLANKS.test(state), Blocks.SPRUCE_FENCE.defaultBlockState(),
				List.of(new BlockPos(0, 3, -1), new BlockPos(1, 3, -1)));
		contains("Anchor on the deck", Parts.ANCHOR, new BlockPos(-1, 0, -1), new BlockPos(1, 1, 1), 1);
		contains("Rope Coil on the deck", Parts.ROPE_COIL, new BlockPos(-1, 0, -1), new BlockPos(1, 1, 1), 1);
		contains("Chest or Barrel on the deck", Parts.CHEST, new BlockPos(-1, 0, -1), new BlockPos(1, 1, 1), 1);

		planLine("Find water at least 1 block deep and build a 3x3 deck of planks or wooden slabs on the water's surface.");
		planLine("Leave water all around the deck (at least 10 of the 16 blocks around it). Light blue ghosts mean water.");
		planLine("Put the Shipyard Crane in the middle of the deck.");
		planLine("Crane: a log post 4 tall on the north-west corner of the deck, with 2 fences sticking out east from its top.");
		planLine("On the deck: an Anchor, a Rope Coil and a Chest or Barrel.");
	}

	@Override
	public String purpose() {
		return "Right-click the Crane once a day to collect ship timber from the Galley-La workers. Holding a ship upgrade, "
				+ "right-click it to have the upgrade fitted to your ship docked nearby.";
	}

	@Override
	public void use(ServerPlayer player, BuildingRegistry.Entry entry) {
		// Holding a ship upgrade (hull plating, sailcloth, gun carriage): the workers fit it to your docked ship.
		if (com.onepiecemod.shipcombat.ShipyardUpgrades.tryFit(player, entry.pos())) {
			return;
		}
		ServerLevel level = (ServerLevel) player.level();
		long today = BuildingRegistry.day(level);
		long days = entry.lastDay() < 0 ? 1 : Math.min(MAX_DAYS_STORED, today - entry.lastDay());
		if (days <= 0) {
			long ticksLeft = 24000L - level.getGameTime() % 24000L;
			player.sendSystemMessage(Component.literal("The workers are still cutting today's timber. Come back in about "
					+ Math.max(1, ticksLeft / 1200) + " minutes.").withStyle(ChatFormatting.GRAY));
			return;
		}
		Crew crew = player.getAttached(CrewAttachments.CREW);
		boolean shipwright = crew != null && crew.member(CrewRole.SHIPWRIGHT) != null;
		int stacks = (int) days;
		Parts.give(player, new ItemStack(Items.OAK_PLANKS, 16 * stacks));
		Parts.give(player, new ItemStack(Items.STRING, 4 * stacks));
		Parts.give(player, new ItemStack(Items.IRON_INGOT, 2 * stacks));
		if (shipwright) {
			Parts.give(player, new ItemStack(WorldBlocks.ADAM_LOG, stacks));
		}
		BuildingRegistry.put(level, entry.withLastDay(today));
		level.playSound(null, entry.pos(), SoundEvents.CHAIN_PLACE, SoundSource.BLOCKS, 1.0f, 0.8f);
		player.sendSystemMessage(Component.literal("Galley-La delivery (" + days + (days == 1 ? " day" : " days") + "): "
				+ 16 * stacks + " planks, " + 4 * stacks + " string, " + 2 * stacks + " iron"
				+ (shipwright ? ", and " + stacks + " Adam Wood found by your Shipwright!" : "."))
				.withStyle(ChatFormatting.GREEN));
		if (!shipwright) {
			player.sendSystemMessage(Component.literal("Tip: with a Shipwright in your crew, the workers also find rare Adam Wood.")
					.withStyle(ChatFormatting.GRAY));
		}
	}
}

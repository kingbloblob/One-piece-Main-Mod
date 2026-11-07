package com.onepiecemod.hideout;

import net.minecraft.ChatFormatting;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.Rarity;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.SoundType;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.material.MapColor;

import net.fabricmc.fabric.api.creativetab.v1.CreativeModeTabEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerEntityEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.fabricmc.fabric.api.event.player.PlayerBlockBreakEvents;
import net.fabricmc.fabric.api.object.builder.v1.block.entity.FabricBlockEntityTypeBuilder;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.item.ModItems;

/**
 * Pirate hideouts: claim an island with a Hideout Flag, build it up from a beach camp to a fortress,
 * let your crew live and work there, and hold it when the Navy attacks.
 * OnePieceMod calls initialize() once at startup.
 *
 *  - HideoutFlagBlock + HideoutFlagBlockEntity: the claim, the stash, the look-over of what's built, the daily haul.
 *  - HideoutLevels: the five levels and what each needs.  HideoutHaul: what each crew job brings in.
 *  - HideoutLifeGoal: crewmates who live there gather at the campfire at dusk and sleep in its beds.
 *  - HideoutSiege: Navy attacks, with cannons that fire back.  Hideouts: the saved list of every hideout.
 *  - HideoutPayloads + client/HideoutScreen: the flag's screen.  HideoutCommands: /hideout.
 *
 * Different from a pirate kingdom (empire package): kingdoms are for Emperors and collect taxes with hired
 * guards; a hideout is any crew's home base, defended by its own crewmates and cannons.
 */
public final class HideoutFeature {
	public static final ResourceKey<Block> HIDEOUT_FLAG_KEY = ResourceKey.create(Registries.BLOCK, OnePieceMod.id("hideout_flag"));
	public static final Block HIDEOUT_FLAG = Registry.register(BuiltInRegistries.BLOCK, HIDEOUT_FLAG_KEY,
			new HideoutFlagBlock(BlockBehaviour.Properties.of().mapColor(MapColor.COLOR_BLACK).strength(4.0f, 1200.0f)
					.sound(SoundType.WOOD).noOcclusion().setId(HIDEOUT_FLAG_KEY)));

	public static final ResourceKey<Item> HIDEOUT_FLAG_ITEM_KEY = ResourceKey.create(Registries.ITEM, OnePieceMod.id("hideout_flag"));
	public static final Item HIDEOUT_FLAG_ITEM = Registry.register(BuiltInRegistries.ITEM, HIDEOUT_FLAG_ITEM_KEY,
			new BlockItem(HIDEOUT_FLAG, new Item.Properties().stacksTo(1).rarity(Rarity.UNCOMMON)
					.useBlockDescriptionPrefix().setId(HIDEOUT_FLAG_ITEM_KEY)));

	public static final BlockEntityType<HideoutFlagBlockEntity> HIDEOUT_FLAG_ENTITY = Registry.register(
			BuiltInRegistries.BLOCK_ENTITY_TYPE,
			OnePieceMod.id("hideout_flag"),
			FabricBlockEntityTypeBuilder.create(HideoutFlagBlockEntity::new, HIDEOUT_FLAG).build());

	private HideoutFeature() {
	}

	public static void initialize() {
		Hideouts.initialize();
		HideoutPayloads.initialize();
		HideoutCommands.initialize();
		HideoutSiege.initialize();

		CreativeModeTabEvents.modifyOutputEvent(ModItems.ONE_PIECE_TAB_KEY).register(output -> output.accept(HIDEOUT_FLAG_ITEM));

		ServerTickEvents.END_SERVER_TICK.register(HideoutSiege::tick);

		// Marines left over from an attack that ended (say the server restarted mid-fight) go home.
		ServerEntityEvents.ENTITY_LOAD.register((entity, level) -> HideoutSiege.cleanLeftover(entity));

		// Strangers can't tear down your flag.
		PlayerBlockBreakEvents.BEFORE.register((level, player, pos, state, blockEntity) -> {
			if (blockEntity instanceof HideoutFlagBlockEntity flag && player instanceof ServerPlayer serverPlayer
					&& !HideoutFlagBlock.mayBreak(serverPlayer, flag)) {
				serverPlayer.sendSystemMessage(Component.literal("This flag belongs to the " + flag.crewName((net.minecraft.server.level.ServerLevel) level)
						+ ". Only their crew can take it down.").withStyle(ChatFormatting.RED));
				return false;
			}
			return true;
		});
	}
}

package com.onepiecemod.ship;

import java.util.Map;

import com.mojang.brigadier.arguments.StringArgumentType;
import com.mojang.brigadier.context.CommandContext;

import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.commands.SharedSuggestionProvider;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.util.Mth;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.Rarity;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.phys.Vec3;

import net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback;

import com.onepiecemod.OnePieceMod;

/**
 * The ships you can own from the show, as items (see ShipItem), plus the /ship command for trying any ship out.
 * OnePieceMod calls initialize() right after ShipFeature.
 */
public class ShipModels {
	public static final Item GOING_MERRY = register("going_merry", Rarity.RARE);
	public static final Item THOUSAND_SUNNY = register("thousand_sunny", Rarity.EPIC);

	public static void initialize() {
		ShipTemplates.initialize();
		ShipFeature.addTabItem(GOING_MERRY);
		ShipFeature.addTabItem(THOUSAND_SUNNY);

		// /ship <id> (operators): the named ship appears 40 blocks ahead of you. /ship list names them all.
		CommandRegistrationCallback.EVENT.register((dispatcher, registryAccess, environment) -> dispatcher.register(
				Commands.literal("ship")
						.requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
						.then(Commands.literal("list").executes(ShipModels::list))
						.then(Commands.argument("id", StringArgumentType.word())
								.suggests((context, builder) -> SharedSuggestionProvider.suggest(
										ShipTemplates.specs(context.getSource().getServer()).keySet(), builder))
								.executes(context -> spawn(context, StringArgumentType.getString(context, "id"))))));
	}

	private static Item register(String shipId, Rarity rarity) {
		ResourceKey<Item> key = ResourceKey.create(Registries.ITEM, OnePieceMod.id(shipId));
		Item item = new ShipItem(shipId, new Item.Properties().stacksTo(1).rarity(rarity).setId(key));
		return Registry.register(BuiltInRegistries.ITEM, key, item);
	}

	private static int list(CommandContext<CommandSourceStack> context) {
		Map<String, ShipTemplates.Spec> specs = ShipTemplates.specs(context.getSource().getServer());
		StringBuilder text = new StringBuilder("Ships: ");
		for (ShipTemplates.Spec spec : specs.values()) {
			text.append(spec.id).append(" (").append(spec.name).append(", ").append(spec.blocks).append(" blocks, ")
					.append(spec.faction).append(spec.tiers.isEmpty() ? "" : " tiers " + spec.tiers).append("); ");
		}
		context.getSource().sendSuccess(() -> Component.literal(text.toString()), false);
		return specs.size();
	}

	private static int spawn(CommandContext<CommandSourceStack> context, String id) {
		CommandSourceStack source = context.getSource();
		ServerLevel level = source.getLevel();
		ShipTemplates.Spec spec = ShipTemplates.spec(source.getServer(), id);
		if (spec == null) {
			source.sendFailure(Component.literal("No ship called " + id + ". Try /ship list."));
			return 0;
		}
		float yaw = source.getRotation().y;
		Vec3 ahead = source.getPosition().add(-Mth.sin(yaw * Mth.DEG_TO_RAD) * 40, 0, Mth.cos(yaw * Mth.DEG_TO_RAD) * 40);
		int x = Mth.floor(ahead.x);
		int z = Mth.floor(ahead.z);
		level.getChunk(x >> 4, z >> 4); // make sure the chunk is loaded, or the heightmap reads 0 and the ship sinks
		int surface = level.getHeight(Heightmap.Types.WORLD_SURFACE, x, z);
		ShipEntity ship = ShipTemplates.spawn(level, id, x, surface, z, yaw);
		if (ship == null) {
			source.sendFailure(Component.literal("Couldn't build the " + spec.name + ". Is its template missing?"));
			return 0;
		}
		source.sendSuccess(() -> Component.literal("The " + spec.name + " (" + spec.blocks + " blocks) is at " + ship.blockPosition().toShortString() + "."), true);
		return 1;
	}
}

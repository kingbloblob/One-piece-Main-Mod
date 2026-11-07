package com.onepiecemod.voyage;

import java.util.Arrays;
import java.util.Locale;

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
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Rarity;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.storage.loot.BuiltInLootTables;
import net.minecraft.world.level.storage.loot.parameters.LootContextParams;
import net.minecraft.world.phys.Vec3;

import net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback;
import net.fabricmc.fabric.api.entity.event.v1.ServerLivingEntityEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.fabricmc.fabric.api.creativetab.v1.CreativeModeTabEvents;
import net.fabricmc.fabric.api.loot.v3.LootTableEvents;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.sea.CalmBelt;
import com.onepiecemod.ship.ShipEntity;

/**
 * Sea exploration: what you meet between the islands.
 * - Weather hazards (waterspouts, rogue waves, hail) live with the other sea events in the weather package.
 * - Sea monsters: SeaMonsters. Drifting supply boats: Flotsam. Merchant ships, derelicts and ghost ships: WanderingShips.
 * - Messages in bottles (fishing at sea, flotsam, Island Whales) hold Castaway's Charts to little sandbar caches
 *   (TreasureKind.CASTAWAY in the treasure package).
 * /voyage monster|ship|flotsam ... starts any of them next to you (operators, for testing).
 */
public final class VoyageFeature {
	public static final Item MESSAGE_BOTTLE = register("message_in_a_bottle");

	/** Chance a catch at sea comes with a message in a bottle as well. */
	private static final float BOTTLE_FISHING_CHANCE = 0.025f;

	private VoyageFeature() {
	}

	private static Item register(String name) {
		ResourceKey<Item> key = ResourceKey.create(Registries.ITEM, OnePieceMod.id(name));
		return Registry.register(BuiltInRegistries.ITEM, key,
				new MessageBottleItem(new Item.Properties().setId(key).stacksTo(16).rarity(Rarity.UNCOMMON)));
	}

	public static void initialize() {
		ServerTickEvents.END_SERVER_TICK.register(server -> {
			SeaMonsters.tick(server);
			Flotsam.tick(server);
			WanderingShips.tick(server);
		});
		ServerLifecycleEvents.SERVER_STOPPING.register(server -> {
			SeaMonsters.clear();
			Flotsam.clear();
			WanderingShips.clear();
		});
		ServerLivingEntityEvents.AFTER_DEATH.register((entity, source) -> {
			if (entity.level() instanceof ServerLevel level) {
				SeaMonsters.onDeath(level, entity, source);
			}
		});

		// Now and then, a bottle comes up with the catch when fishing in the sea.
		LootTableEvents.MODIFY_DROPS.register((table, context, drops) -> {
			if (!table.is(BuiltInLootTables.FISHING)) {
				return;
			}
			Vec3 origin = context.getOptional(LootContextParams.ORIGIN);
			ServerLevel level = context.getLevel();
			if (origin == null || level.dimension() != Level.OVERWORLD || context.getRandom().nextFloat() >= BOTTLE_FISHING_CHANCE
					|| !CalmBelt.isOcean(level.getBiome(net.minecraft.core.BlockPos.containing(origin)))) {
				return;
			}
			drops.add(new ItemStack(MESSAGE_BOTTLE));
		});

		CreativeModeTabEvents.modifyOutputEvent(com.onepiecemod.character.CharacterFeature.TAB_KEY).register(output -> output.accept(MESSAGE_BOTTLE));

		registerCommands();
	}

	// ---------- /voyage (operators only) ----------

	private static void registerCommands() {
		CommandRegistrationCallback.EVENT.register((dispatcher, registryAccess, environment) -> dispatcher.register(
				Commands.literal("voyage")
						.requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
						.then(Commands.literal("monster")
								.then(Commands.argument("kind", StringArgumentType.word())
										.suggests((context, builder) -> SharedSuggestionProvider.suggest(
												Arrays.stream(SeaMonsters.Kind.values()).map(k -> k.name().toLowerCase(Locale.ROOT)), builder))
										.executes(VoyageFeature::monster)))
						.then(Commands.literal("ship")
								.then(Commands.argument("kind", StringArgumentType.word())
										.suggests((context, builder) -> SharedSuggestionProvider.suggest(
												Arrays.stream(WanderingShips.Kind.values()).map(k -> k.name().toLowerCase(Locale.ROOT)), builder))
										.executes(VoyageFeature::ship)))
						.then(Commands.literal("flotsam").executes(context -> {
							ServerPlayer player = context.getSource().getPlayerOrException();
							ShipEntity ship = ShipEntity.aboard(player);
							if (ship == null) {
								context.getSource().sendFailure(Component.literal("Stand on a ship out at sea first."));
								return 0;
							}
							boolean done = Flotsam.spawnAhead((ServerLevel) player.level(), ship) != null;
							context.getSource().sendSuccess(() -> Component.literal(done ? "A supply boat is drifting ahead." : "No open water ahead."), false);
							return done ? 1 : 0;
						}))));
	}

	private static int monster(CommandContext<CommandSourceStack> context) throws com.mojang.brigadier.exceptions.CommandSyntaxException {
		ServerPlayer player = context.getSource().getPlayerOrException();
		SeaMonsters.Kind kind;
		try {
			kind = SeaMonsters.Kind.valueOf(StringArgumentType.getString(context, "kind").toUpperCase(Locale.ROOT));
		} catch (IllegalArgumentException e) {
			context.getSource().sendFailure(Component.literal("Unknown monster."));
			return 0;
		}
		ShipEntity ship = ShipEntity.aboard(player);
		if (ship == null) {
			context.getSource().sendFailure(Component.literal("Stand on a ship out at sea first."));
			return 0;
		}
		String problem = SeaMonsters.start((ServerLevel) player.level(), player, ship, kind);
		return report(context, problem, "Here it comes!");
	}

	private static int ship(CommandContext<CommandSourceStack> context) throws com.mojang.brigadier.exceptions.CommandSyntaxException {
		ServerPlayer player = context.getSource().getPlayerOrException();
		WanderingShips.Kind kind;
		try {
			kind = WanderingShips.Kind.valueOf(StringArgumentType.getString(context, "kind").toUpperCase(Locale.ROOT));
		} catch (IllegalArgumentException e) {
			context.getSource().sendFailure(Component.literal("Unknown ship."));
			return 0;
		}
		ShipEntity ship = ShipEntity.aboard(player);
		if (ship == null) {
			context.getSource().sendFailure(Component.literal("Stand on a ship out at sea first."));
			return 0;
		}
		String problem = WanderingShips.start((ServerLevel) player.level(), player, ship, kind);
		return report(context, problem, "A ship is on the horizon.");
	}

	private static int report(CommandContext<CommandSourceStack> context, String problem, String ok) {
		if (problem != null) {
			context.getSource().sendFailure(Component.literal(problem));
			return 0;
		}
		context.getSource().sendSuccess(() -> Component.literal(ok), false);
		return 1;
	}
}

package com.onepiecemod.town;

import java.util.HashSet;

import com.mojang.brigadier.arguments.IntegerArgumentType;
import com.mojang.brigadier.arguments.StringArgumentType;
import com.mojang.brigadier.context.CommandContext;

import net.minecraft.ChatFormatting;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.commands.SharedSuggestionProvider;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.MobCategory;

import net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback;
import net.fabricmc.fabric.api.entity.event.v1.ServerLivingEntityEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.fabricmc.fabric.api.object.builder.v1.entity.FabricDefaultAttributeRegistry;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.character.CharacterEntity;

/**
 * Busy towns: townsfolk with daily routines, port markets, bar brawls and festivals.
 *  - onepiece:townsfolk (TownsfolkEntity): farmers, fishers, merchants, bartenders, cooks, shipwrights, kids, elders...
 *  - Towns: finds the town structures players visit (listed in onepiece/towns.json) and fills them with people.
 *  - Markets, BarBrawls, Festivals: what goes on in town.
 *  - /town for testing (operators).
 * OnePieceMod calls initialize() once while the game loads.
 */
public class TownFeature {
	public static final ResourceKey<EntityType<?>> TOWNSFOLK_KEY = ResourceKey.create(Registries.ENTITY_TYPE, OnePieceMod.id("townsfolk"));
	public static final EntityType<TownsfolkEntity> TOWNSFOLK = Registry.register(
			BuiltInRegistries.ENTITY_TYPE,
			TOWNSFOLK_KEY,
			EntityType.Builder.of(TownsfolkEntity::new, MobCategory.MISC)
					.sized(0.6f, 1.95f)
					.clientTrackingRange(10)
					.build(TOWNSFOLK_KEY)
	);

	/** How close you must be to a boss when it falls for your victory to count for a banquet. */
	private static final double BANQUET_RANGE = 32.0;

	public static void initialize() {
		FabricDefaultAttributeRegistry.register(TOWNSFOLK, TownsfolkEntity.createAttributes());
		TownData.towns(); // Read towns.json now, so a mistake in it shows up while the game loads.

		ServerTickEvents.END_SERVER_TICK.register(Towns::tick);
		ServerLifecycleEvents.SERVER_STOPPED.register(server -> {
			Towns.clear();
			Festivals.clear();
		});
		ServerLivingEntityEvents.AFTER_DEATH.register((entity, source) -> {
			if (entity instanceof CharacterEntity boss && boss.isBoss() && boss.isFirstWin() && entity.level() instanceof ServerLevel level) {
				for (ServerPlayer player : level.players()) {
					if (player.distanceTo(entity) < BANQUET_RANGE) {
						Festivals.bossBeaten(player, boss.getData().name);
					}
				}
			}
		});
		registerCommands();
		// Load the saved town grudges so they register before any world loads.
		if (TownGrudges.GRUDGES == null || TownGrudges.KILLS == null) {
			throw new IllegalStateException("Town grudge attachments missing");
		}
	}

	// ---------- /town (operators only) ----------

	private static void registerCommands() {
		CommandRegistrationCallback.EVENT.register((dispatcher, registryAccess, environment) -> dispatcher.register(
				Commands.literal("town")
						.requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
						.then(Commands.literal("info").executes(TownFeature::info))
						.then(Commands.literal("festival")
								.then(Commands.argument("id", StringArgumentType.word())
										.suggests((context, builder) -> SharedSuggestionProvider.suggest(TownData.festivals().keySet(), builder))
										.executes(TownFeature::festival)))
						.then(Commands.literal("brawl").executes(context -> {
							Town town = here(context);
							boolean started = town != null && BarBrawls.forceStart(town, (ServerLevel) town.level);
							return reply(context, started ? "A brawl breaks out!" : "No bar here, or nobody in it to fight.", started);
						}))
						.then(Commands.literal("trader").executes(context -> {
							Town town = here(context);
							boolean came = town != null && town.scanned && Markets.arrive(town, town.level) != null;
							return reply(context, came ? "A foreign trader has arrived." : "No town here (or it's still being looked over).", came);
						}))
						.then(Commands.literal("spawn")
								.then(Commands.argument("job", StringArgumentType.word())
										.suggests((context, builder) -> SharedSuggestionProvider.suggest(TownData.jobs().keySet(), builder))
										.executes(context -> spawn(context, 1))
										.then(Commands.argument("count", IntegerArgumentType.integer(1, 10))
												.executes(context -> spawn(context, IntegerArgumentType.getInteger(context, "count"))))))));
	}

	private static Town here(CommandContext<CommandSourceStack> context) {
		ServerPlayer player = context.getSource().getPlayer();
		if (player == null) {
			return null;
		}
		Town town = Towns.townOf(player);
		return town != null ? town : Towns.at((ServerLevel) player.level(), player.blockPosition(), 16);
	}

	private static int reply(CommandContext<CommandSourceStack> context, String text, boolean ok) {
		if (ok) {
			context.getSource().sendSuccess(() -> Component.literal(text).withStyle(ChatFormatting.GOLD), false);
		} else {
			context.getSource().sendFailure(Component.literal(text));
		}
		return ok ? 1 : 0;
	}

	private static int info(CommandContext<CommandSourceStack> context) {
		Town town = here(context);
		if (town == null) {
			return reply(context, "You're not in a town. Towns: " + String.join(", ", TownData.towns().keySet()), false);
		}
		int people = Towns.residents(town).size();
		TownData.Festival festival = Festivals.active(town);
		String text = town.name() + " (" + town.structureId + ", " + town.def.culture + "): " + people + "/" + town.def.population + " townsfolk"
				+ (town.scanned ? ", " + town.beds.size() + " beds, " + town.docks.size() + " dock spots, plaza at " + town.plaza.toShortString()
						+ ", bar at " + town.bar.toShortString() : ", still looking the town over")
				+ ". Market: " + (town.def.market ? (Markets.isOpen(town.level) ? "open" : "closed") + (Markets.shipDay(town) ? ", ship day" : "") : "none")
				+ ". Festival: " + (festival != null ? festival.name + " NOW" : Festivals.nextFestival(town))
				+ (BarBrawls.active(town) ? ". A brawl is going on!" : ".");
		return reply(context, text, true);
	}

	private static int festival(CommandContext<CommandSourceStack> context) {
		Town town = here(context);
		String id = StringArgumentType.getString(context, "id");
		if (town == null || TownData.festival(id) == null) {
			return reply(context, town == null ? "You're not in a town." : "No festival called " + id, false);
		}
		Festivals.force(town, id, 20 * 60 * 3);
		return reply(context, "The " + TownData.festival(id).name + " starts now in " + town.name() + " (3 minutes).", true);
	}

	private static int spawn(CommandContext<CommandSourceStack> context, int count) {
		Town town = here(context);
		String job = StringArgumentType.getString(context, "job");
		if (town == null || !town.scanned) {
			return reply(context, "Stand in a town first (and give it a few seconds to look itself over).", false);
		}
		if (!TownData.jobs().containsKey(job)) {
			return reply(context, "No job called " + job, false);
		}
		BlockPos at = BlockPos.containing(context.getSource().getPosition());
		for (int i = 0; i < count; i++) {
			Towns.spawn(town, job, at, i, new HashSet<>());
		}
		return reply(context, "Spawned " + count + " x " + job + " in " + town.name(), true);
	}
}

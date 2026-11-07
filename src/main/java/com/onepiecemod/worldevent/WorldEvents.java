package com.onepiecemod.worldevent;

import org.jetbrains.annotations.Nullable;

import com.mojang.brigadier.arguments.FloatArgumentType;
import com.mojang.brigadier.arguments.IntegerArgumentType;
import com.mojang.brigadier.arguments.StringArgumentType;

import net.minecraft.ChatFormatting;
import net.minecraft.commands.Commands;
import net.minecraft.commands.SharedSuggestionProvider;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.tags.FluidTags;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.levelgen.Heightmap;

import net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;

/**
 * World events: the world reacting to what you do.
 *  - IslandTrouble + IslandBusterCall + Ruins: make trouble on an island and the Navy Buster Calls it (and it rebuilds).
 *  - MarineFleets: Marine fleets crossing the sea.
 *  - EmperorTerritories: the Four Emperors' waters, and how each Emperor feels about you.
 *  - Reverie: the kings' meeting at Mary Geoise every few days, and what they decide.
 *  - WorldNews: the headlines all of this makes.
 *  - RareEvents: rare big events every few days (surprise Buster Calls, meteor showers, treasure convoys, armadas, cyclones).
 *  - IslandEvents: short island events (gang raids, Thriller Bark zombies, kneeling for a Celestial Dragon, washed-up supplies).
 * Players: /island (trouble here, standing with each Emperor), /tribute. Operators: /worldevent ...
 * OnePieceMod calls initialize() once, after ship combat and NPCs (fleets steer after ship combat's captains).
 */
public class WorldEvents {
	public static void initialize() {
		WorldNews.HEADLINES.identifier(); // Load the attachments.
		Ruins.SAVED.identifier();
		IslandTrouble.SAVED.identifier();
		EmperorTerritories.STANDING.identifier();
		Reverie.SAVED.identifier();

		IslandTrouble.initialize();
		IslandBusterCall.initialize();
		EmperorTerritories.initialize();
		IslandEvents.initialize();

		ServerTickEvents.END_SERVER_TICK.register(server -> {
			IslandTrouble.tick(server);
			IslandBusterCall.tick(server);
			Ruins.tick(server);
			MarineFleets.tick(server);
			EmperorTerritories.tick(server);
			Reverie.tick(server);
			IslandEvents.tick(server);
			RareEvents.tick(server);
		});
		ServerLifecycleEvents.SERVER_STOPPING.register(server -> {
			IslandBusterCall.stopAll();
			IslandEvents.stopAll();
			RareEvents.stopAll();
			Ruins.save(server);
			IslandTrouble.save(server);
			Ruins.unload();
			IslandTrouble.unload();
			MarineFleets.clear();
			Reverie.unload();
		});
		registerCommands();
	}

	// ---- Shared helpers ----

	/** The heading (yaw) that points along dx, dz. Ships move along (-sin yaw, cos yaw). */
	static float yawTowards(double dx, double dz) {
		return (float) Math.toDegrees(Math.atan2(-dx, dz));
	}

	/** The Y just above the sea if this column is open sea at least 5 blocks deep, otherwise null. */
	@Nullable
	static Integer deepWaterSurface(ServerLevel level, int x, int z) {
		if (!level.hasChunkAt(new BlockPos(x, 0, z))) {
			return null;
		}
		int top = level.getHeight(Heightmap.Types.WORLD_SURFACE, x, z);
		int floor = level.getHeight(Heightmap.Types.OCEAN_FLOOR, x, z);
		if (!level.getFluidState(new BlockPos(x, top - 1, z)).is(FluidTags.WATER) || top - floor < 5) {
			return null;
		}
		return top;
	}

	/** Dry ground min-max blocks from a spot, at about the same height. Null if there's none. */
	@Nullable
	static BlockPos landingSpot(ServerLevel level, BlockPos around, int min, int max, RandomSource random) {
		for (int attempt = 0; attempt < 20; attempt++) {
			double angle = random.nextDouble() * Math.PI * 2;
			int distance = min + random.nextInt(Math.max(1, max - min + 1));
			int x = Mth.floor(around.getX() + Math.cos(angle) * distance);
			int z = Mth.floor(around.getZ() + Math.sin(angle) * distance);
			if (!level.hasChunkAt(new BlockPos(x, 0, z))) {
				continue;
			}
			BlockPos pos = new BlockPos(x, level.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, x, z), z);
			if (level.getBlockState(pos.below()).isSolid() && level.getFluidState(pos).isEmpty() && Math.abs(pos.getY() - around.getY()) < 16) {
				return pos;
			}
		}
		return null;
	}

	// ---- Commands ----

	private static void registerCommands() {
		CommandRegistrationCallback.EVENT.register((dispatcher, registryAccess, environment) -> {
			dispatcher.register(Commands.literal("island").executes(context -> {
				ServerPlayer player = context.getSource().getPlayerOrException();
				ServerLevel level = (ServerLevel) player.level();
				player.sendSystemMessage(IslandTrouble.describe(level, player));
				EmperorTerritories.Territory here = EmperorTerritories.territoryAt(level, player.blockPosition());
				player.sendSystemMessage(Component.literal(here != null ? "You're in " + here.emperor() + "'s territory." : "No Emperor rules here.")
						.withStyle(ChatFormatting.GOLD));
				player.sendSystemMessage(Component.literal("How the Emperors see you:").withStyle(ChatFormatting.GOLD));
				EmperorTerritories.describe(player, player::sendSystemMessage);
				player.sendSystemMessage(Component.literal(Reverie.status(level.getServer())).withStyle(ChatFormatting.LIGHT_PURPLE));
				return 1;
			}));
			dispatcher.register(Commands.literal("tribute").executes(context -> {
				ServerPlayer player = context.getSource().getPlayerOrException();
				player.sendSystemMessage(EmperorTerritories.payTribute(player));
				return 1;
			}));
			dispatcher.register(Commands.literal("worldevent")
					.requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
					.then(Commands.literal("trouble")
							.then(Commands.argument("amount", FloatArgumentType.floatArg(0, 100)).executes(context -> {
								ServerPlayer player = context.getSource().getPlayerOrException();
								IslandTrouble.set((ServerLevel) player.level(), player, FloatArgumentType.getFloat(context, "amount"));
								player.sendSystemMessage(IslandTrouble.describe((ServerLevel) player.level(), player));
								return 1;
							})))
					.then(Commands.literal("bustercall")
							.executes(context -> {
								String error = IslandBusterCall.startHere(context.getSource().getPlayerOrException());
								return reply(context.getSource(), error, "Buster Call ordered on this island.");
							})
							.then(Commands.literal("stop").executes(context -> {
								int stopped = IslandBusterCall.stopAll();
								return reply(context.getSource(), null, "Stopped " + stopped + " Buster Call(s). Ruins rebuild in 10 minutes.");
							})))
					.then(Commands.literal("restore").executes(context -> {
						int blocks = Ruins.rebuildNow(context.getSource().getServer().overworld().getGameTime());
						return reply(context.getSource(), null, "Rebuilding " + blocks + " blocks now (only near players: far chunks rebuild when loaded).");
					}))
					.then(Commands.literal("fleet")
							.executes(context -> reply(context.getSource(), MarineFleets.send((ServerLevel) context.getSource().getPlayerOrException().level(),
									context.getSource().getPlayerOrException(), false), "A Marine fleet is on its way past you."))
							.then(Commands.literal("royal").executes(context -> reply(context.getSource(),
									MarineFleets.send((ServerLevel) context.getSource().getPlayerOrException().level(),
											context.getSource().getPlayerOrException(), true), "A royal convoy is on its way past you."))))
					.then(Commands.literal("reverie")
							.then(Commands.literal("start").executes(context -> {
								Reverie.start(context.getSource().getServer());
								return 1;
							}))
							.then(Commands.literal("stop").executes(context -> {
								Reverie.stop(context.getSource().getServer());
								return 1;
							})))
					.then(Commands.literal("standing")
							.then(Commands.argument("emperor", StringArgumentType.word())
									.suggests((context, builder) -> SharedSuggestionProvider.suggest(
											EmperorTerritories.all().stream().map(EmperorTerritories.Territory::id), builder))
									.then(Commands.argument("value", IntegerArgumentType.integer(-100, 100)).executes(context -> {
										ServerPlayer player = context.getSource().getPlayerOrException();
										EmperorTerritories.Territory territory = EmperorTerritories.byId(StringArgumentType.getString(context, "emperor"));
										if (territory == null) {
											return reply(context.getSource(), "Emperors: kaido, big_mom, blackbeard, shanks", "");
										}
										EmperorTerritories.set(player, territory, IntegerArgumentType.getInteger(context, "value"));
										return reply(context.getSource(), null, territory.emperor() + " standing set to "
												+ EmperorTerritories.standing(player, territory) + " (" + EmperorTerritories.mood(player, territory) + ").");
									}))))
					.then(Commands.literal("islandevent")
							.executes(context -> reply(context.getSource(),
									IslandEvents.startById(context.getSource().getPlayerOrException(), null), "Island event started."))
							.then(Commands.literal("stop").executes(context -> reply(context.getSource(),
									IslandEvents.stop(context.getSource().getPlayerOrException()) ? null : "No island event running.", "Island event stopped.")))
							.then(Commands.argument("id", StringArgumentType.word())
									.suggests((context, builder) -> SharedSuggestionProvider.suggest(IslandEvents.ids(), builder))
									.executes(context -> reply(context.getSource(), IslandEvents.startById(context.getSource().getPlayerOrException(),
											StringArgumentType.getString(context, "id")), "Island event started."))))
					.then(RareEvents.command())
					.then(Commands.literal("news").executes(context -> {
						for (String line : WorldNews.recent(context.getSource().getServer(), 8)) {
							context.getSource().sendSuccess(() -> Component.literal(line).withStyle(ChatFormatting.GRAY), false);
						}
						return 1;
					})));
		});
	}

	private static int reply(net.minecraft.commands.CommandSourceStack source, @Nullable String error, String ok) {
		if (error != null) {
			source.sendFailure(Component.literal(error));
			return 0;
		}
		source.sendSuccess(() -> Component.literal(ok).withStyle(ChatFormatting.GOLD), true);
		return 1;
	}
}

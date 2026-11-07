package com.onepiecemod.arena;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;
import java.util.function.Function;

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
import net.minecraft.network.chat.ClickEvent;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.MutableComponent;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.tags.DamageTypeTags;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;

import net.fabricmc.fabric.api.attachment.v1.AttachmentRegistry;
import net.fabricmc.fabric.api.attachment.v1.AttachmentType;
import net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback;
import net.fabricmc.fabric.api.creativetab.v1.CreativeModeTabEvents;
import net.fabricmc.fabric.api.entity.event.v1.ServerLivingEntityEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerEntityEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.fabricmc.fabric.api.networking.v1.ServerPlayConnectionEvents;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.bounty.Bounty;
import com.onepiecemod.character.Locations;
import com.onepiecemod.crew.CrewAttachments;
import com.onepiecemod.crew.CrewmateEntity;
import com.onepiecemod.item.ModItems;
import com.onepiecemod.story.StoryPlaces;

/**
 * Arena games: Corrida Colosseum tournaments (Dressrosa) and Davy Back Fights (Long Ring Long Land).
 *
 * - Colosseum Ticket: use it inside the Corrida Colosseum to enter a cup (anywhere else it points the way there).
 * - Davy Back Flag: plant it (use it on dry ground) with your crew to challenge a rival pirate crew.
 * - The Foxy Pirates challenge every captain who walks into the Davy Back Fight arena, once a day.
 * - /colosseum and /davyback (records, picks, giving up; operators can start either anywhere for testing).
 * OnePieceMod calls initialize() once while the game loads.
 */
public class ArenaFeature {
	public static final AttachmentType<ArenaRecord> RECORD = AttachmentRegistry.create(OnePieceMod.id("arena_record"),
			builder -> builder.persistent(ArenaRecord.CODEC).copyOnDeath());

	public static final Item COLOSSEUM_TICKET = registerItem("colosseum_ticket", ArenaItem.Ticket::new, new Item.Properties().stacksTo(16));
	public static final Item DAVY_BACK_FLAG = registerItem("davy_back_flag", ArenaItem.Flag::new, new Item.Properties().stacksTo(4));

	public static final String COLOSSEUM = "corrida_colosseum";
	public static final String DAVY_BACK = "davy_back_stage";

	private static final Map<UUID, ArenaMatch> MATCHES = new HashMap<>();
	/** Foxy's open challenges: player -> game time it runs out. */
	private static final Map<UUID, Long> FOXY_OFFERS = new HashMap<>();
	/** Last day each player saw the Colosseum's welcome, so it shows once a day. */
	private static final Map<UUID, Long> COLOSSEUM_HINT = new HashMap<>();
	private static final Map<UUID, Long> TICKET_COOLDOWN = new HashMap<>();
	private static final List<Entity> STALE = new ArrayList<>();
	private static final String RUN_TAG = "onepiece_arena_" + Long.toHexString(System.nanoTime() & 0xffffff);

	public static void initialize() {
		// No Marine squads, raids or hunts barge into a Davy Back Fight or a Colosseum match (seen in the 2026-11-01 playtest).
		com.onepiecemod.bounty.NavyCalm.register(player -> MATCHES.containsKey(player.getUUID()));
		CreativeModeTabEvents.modifyOutputEvent(ModItems.ONE_PIECE_TAB_KEY).register(output -> {
			output.accept(COLOSSEUM_TICKET);
			output.accept(DAVY_BACK_FLAG);
		});

		ServerTickEvents.END_SERVER_TICK.register(ArenaFeature::tick);

		// Fighters left over from before a restart (their match is gone) are cleared away.
		ServerEntityEvents.ENTITY_LOAD.register((entity, level) -> {
			if (entity.entityTags().contains(ArenaMatch.TAG) && !entity.entityTags().contains(RUN_TAG)) {
				STALE.add(entity);
			}
		});

		// Nobody dies in the arena: falling there loses the game instead.
		ServerLivingEntityEvents.ALLOW_DEATH.register((entity, source, amount) -> {
			if (entity instanceof ServerPlayer player && !source.is(DamageTypeTags.BYPASSES_INVULNERABILITY)) {
				ArenaMatch match = MATCHES.get(player.getUUID());
				if (match != null) {
					player.setHealth(1.0f);
					match.playerDown(player);
					return false;
				}
			}
			return true;
		});

		// Crewmates stay out of the Colosseum and out of the captains' duel.
		// Nobody from outside joins a match either (like the Colosseum's own boss): the arena is sealed while it runs.
		ServerLivingEntityEvents.ALLOW_DAMAGE.register((entity, source, amount) -> {
			Entity attacker = source.getEntity();
			if (attacker instanceof net.minecraft.world.entity.Mob && !(attacker instanceof CrewmateEntity)) {
				ArenaMatch victimMatch = entity instanceof ServerPlayer player ? MATCHES.get(player.getUUID()) : matchOf(entity);
				ArenaMatch attackerMatch = matchOf(attacker);
				if ((victimMatch != null || attackerMatch != null) && victimMatch != attackerMatch) {
					return false;
				}
			}
			if (source.getEntity() instanceof CrewmateEntity crewmate && crewmate.getCaptainId() != null) {
				ArenaMatch match = MATCHES.get(crewmate.getCaptainId());
				if (match != null && match.owns(entity) && !match.crewMayFight(entity)) {
					return false;
				}
			}
			return true;
		});

		ServerPlayConnectionEvents.DISCONNECT.register((handler, server) -> {
			ArenaMatch match = MATCHES.remove(handler.getPlayer().getUUID());
			if (match != null) {
				match.cleanup();
			}
		});

		registerCommands();
	}

	/** The match an arena fighter belongs to, or null. */
	private static ArenaMatch matchOf(Entity entity) {
		if (!entity.entityTags().contains(ArenaMatch.TAG)) {
			return null;
		}
		for (ArenaMatch match : MATCHES.values()) {
			if (match.owns(entity)) {
				return match;
			}
		}
		return null;
	}

	public static String runTag() {
		return RUN_TAG;
	}

	public static ArenaRecord record(ServerPlayer player) {
		ArenaRecord record = player.getAttached(RECORD);
		return record != null ? record : ArenaRecord.EMPTY;
	}

	public static boolean inMatch(ServerPlayer player) {
		return MATCHES.containsKey(player.getUUID());
	}

	private static void start(ServerPlayer player, ArenaMatch match) {
		MATCHES.put(player.getUUID(), match);
	}

	private static void tick(MinecraftServer server) {
		if (!STALE.isEmpty()) {
			for (Entity entity : STALE) {
				entity.discard();
			}
			STALE.clear();
		}
		if (!MATCHES.isEmpty()) {
			for (Map.Entry<UUID, ArenaMatch> entry : new ArrayList<>(MATCHES.entrySet())) {
				if (!entry.getValue().run(server)) {
					entry.getValue().cleanup();
					MATCHES.remove(entry.getKey());
				}
			}
		}
		if (server.getTickCount() % 40 == 0) {
			for (ServerPlayer player : server.getPlayerList().getPlayers()) {
				checkPlaces(player);
			}
		}
	}

	/** Welcomes players at the Colosseum, and has Foxy challenge captains at the Davy Back Fight arena. */
	private static void checkPlaces(ServerPlayer player) {
		if (inMatch(player) || player.isSpectator() || player.level().dimension() != Level.OVERWORLD) {
			return;
		}
		ServerLevel level = (ServerLevel) player.level();
		long day = level.getGameTime() / 24000L;
		if (!Long.valueOf(day).equals(COLOSSEUM_HINT.get(player.getUUID())) && StoryPlaces.isInside(level, player.blockPosition(), COLOSSEUM)) {
			COLOSSEUM_HINT.put(player.getUUID(), day);
			ArenaMatch.say(player, "Gatz", "Welcome to the Corrida Colosseum! Show a Colosseum Ticket to fight in today's tournament!");
			player.sendSystemMessage(Component.literal("Use a Colosseum Ticket here to enter a cup. Crafted from paper, a gold nugget and 2 Berries.")
					.withStyle(ChatFormatting.GRAY));
		}
		if (player.getAttached(CrewAttachments.CREW) != null && record(player).foxyDay() != day
				&& StoryPlaces.isInside(level, player.blockPosition(), DAVY_BACK)) {
			player.setAttached(RECORD, record(player).withFoxyDay(day));
			FOXY_OFFERS.put(player.getUUID(), level.getGameTime() + 20 * 60);
			ArenaMatch.say(player, "Foxy", "Fehehe! A new crew on Long Ring Long Land! I, Foxy the Silver Fox, challenge you to a Davy Back Fight!");
			player.sendSystemMessage(Component.literal("[Accept the Davy Back Fight]").withStyle(style -> style
					.withColor(ChatFormatting.GREEN)
					.withClickEvent(new ClickEvent.RunCommand("/davyback accept")))
					.append(Component.literal("  (the offer stands for a minute; lose a game and Foxy takes one of your crewmates!)")
							.withStyle(ChatFormatting.GRAY)));
		}
	}

	// ---------- Items ----------

	/** Colosseum Ticket used: show the cups at the Colosseum, or point the way there. */
	static void useTicket(ServerPlayer player) {
		if (inMatch(player)) {
			player.sendSystemMessage(Component.literal("You're already in a match.").withStyle(ChatFormatting.RED));
			return;
		}
		ServerLevel level = (ServerLevel) player.level();
		if (!StoryPlaces.isInside(level, player.blockPosition(), COLOSSEUM)) {
			long now = level.getGameTime();
			Long last = TICKET_COOLDOWN.get(player.getUUID());
			if (last != null && now - last < 100) {
				return;
			}
			TICKET_COOLDOWN.put(player.getUUID(), now);
			// Searching for the Colosseum can take many seconds: do it in the background, never on the server thread.
			if (level.dimension() != Level.OVERWORLD || !Locations.findLater(player, COLOSSEUM, ArenaFeature::pointToColosseum)) {
				pointToColosseum(player, Optional.empty());
			}
			return;
		}
		if (colosseumClosed(player)) {
			return;
		}
		showCups(player);
	}

	private static void pointToColosseum(ServerPlayer player, Optional<Locations.Found> found) {
		player.sendSystemMessage(Component.literal(found.map(f -> "This ticket is for the Corrida Colosseum in Dressrosa, about "
				+ Locations.distance(player.blockPosition(), f.pos()) + " blocks " + Locations.direction(player.blockPosition(), f.pos())
				+ " of here. Use it inside the Colosseum.")
				.orElse("This ticket is for the Corrida Colosseum in Dressrosa, out in the New World.")).withStyle(ChatFormatting.YELLOW));
	}

	/** Before the Dressrosa chapter the gates stay shut (story gate). Tells the player and returns true when closed. */
	private static boolean colosseumClosed(ServerPlayer player) {
		if (com.onepiecemod.story.StoryGates.colosseumOpen(player)) {
			return false;
		}
		ArenaMatch.say(player, "Gatz", "Sorry, no rookies off the street! Fighters are invited once they make a name in the New World. (Opens at the Dressrosa chapter.)");
		return true;
	}

	private static void showCups(ServerPlayer player) {
		ArenaRecord record = record(player);
		MutableComponent menu = Component.literal("Corrida Colosseum, choose a cup: ").withStyle(ChatFormatting.GOLD);
		for (CorridaTournament.Cup cup : CorridaTournament.Cup.values()) {
			boolean open = cup.ordinal() <= record.corridaBest() + 1;
			String label = "[" + cup.title() + ", " + cup.tickets() + " ticket" + (cup.tickets() > 1 ? "s" : "") + "] ";
			menu.append(Component.literal(open ? label : "[" + cup.title() + ": win the one before] ").withStyle(style -> open
					? style.withColor(ChatFormatting.GREEN).withClickEvent(new ClickEvent.RunCommand("/colosseum enter " + cup.name().toLowerCase()))
					: style.withColor(ChatFormatting.DARK_GRAY)));
		}
		player.sendSystemMessage(menu);
	}

	/** Davy Back Flag planted: a rival crew answers. Returns true if the flag was used up. */
	static boolean plantFlag(ServerPlayer player, BlockPos at) {
		if (inMatch(player)) {
			player.sendSystemMessage(Component.literal("You're already in a match.").withStyle(ChatFormatting.RED));
			return false;
		}
		if (player.getAttached(CrewAttachments.CREW) == null) {
			player.sendSystemMessage(Component.literal("A Davy Back Fight is between two crews. Start one first (U key or /crew create <name>).")
					.withStyle(ChatFormatting.RED));
			return false;
		}
		if (player.isInWater() || player.isPassenger()) {
			player.sendSystemMessage(Component.literal("Plant the flag on dry land, so both crews have room to line up.").withStyle(ChatFormatting.RED));
			return false;
		}
		startDavyBack(player, at, false);
		return true;
	}

	private static void startDavyBack(ServerPlayer player, BlockPos at, boolean foxy) {
		int tier = Math.min(4, Bounty.threatLevel(player));
		RivalCrew rival = foxy ? RivalCrew.foxy(tier, record(player).taken(), player.getRandom())
				: RivalCrew.random(tier, record(player).taken(), player.getRandom());
		if (!foxy) {
			ArenaMatch.say(player, rival.captainName, "A Davy Back Flag? The " + rival.crewName + " accept your challenge!");
		}
		start(player, new DavyBackFight(player, at, rival));
	}

	private static void startCorrida(ServerPlayer player, CorridaTournament.Cup cup) {
		start(player, new CorridaTournament(player, arenaCentre(player), cup));
	}

	/**
	 * The middle of the Corrida Colosseum the player stands in (so walking in through a gate still puts the ring
	 * on the sand), at the player's height. Outside the Colosseum (operators testing) it is where the player stands.
	 */
	private static BlockPos arenaCentre(ServerPlayer player) {
		ServerLevel level = (ServerLevel) player.level();
		ResourceKey<net.minecraft.world.level.levelgen.structure.Structure> key =
				ResourceKey.create(Registries.STRUCTURE, OnePieceMod.id(COLOSSEUM));
		var start = level.structureManager().getStructureWithPieceAt(player.blockPosition(), holder -> holder.is(key));
		if (!start.isValid()) {
			return player.blockPosition();
		}
		var box = start.getBoundingBox();
		// The arena floor is open to the sky, so the top block in the middle column is the sand.
		int x = box.getCenter().getX();
		int z = box.getCenter().getZ();
		int y = level.getHeight(net.minecraft.world.level.levelgen.Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, x, z);
		if (Math.abs(y - player.getBlockY()) <= 32) {
			return new BlockPos(x, y, z);
		}
		return player.blockPosition();
	}

	// ---------- Commands ----------

	private static void registerCommands() {
		CommandRegistrationCallback.EVENT.register((dispatcher, registryAccess, environment) -> {
			dispatcher.register(Commands.literal("colosseum")
					.executes(context -> showRecord(context.getSource().getPlayerOrException()))
					.then(Commands.literal("record").executes(context -> showRecord(context.getSource().getPlayerOrException())))
					.then(Commands.literal("enter")
							.then(Commands.argument("cup", StringArgumentType.word())
									.suggests((context, builder) -> SharedSuggestionProvider.suggest(List.of("rookie", "veteran", "champion"), builder))
									.executes(ArenaFeature::enterCommand)))
					.then(Commands.literal("giveup").executes(context -> giveUp(context.getSource().getPlayerOrException())))
					.then(Commands.literal("start")
							.requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
							.then(Commands.argument("cup", StringArgumentType.word())
									.suggests((context, builder) -> SharedSuggestionProvider.suggest(List.of("rookie", "veteran", "champion"), builder))
									.executes(context -> {
										ServerPlayer player = context.getSource().getPlayerOrException();
										CorridaTournament.Cup cup = CorridaTournament.Cup.byName(StringArgumentType.getString(context, "cup"));
										if (cup == null || inMatch(player)) {
											return 0;
										}
										startCorrida(player, cup);
										return 1;
									}))));

			dispatcher.register(Commands.literal("davyback")
					.executes(context -> showRecord(context.getSource().getPlayerOrException()))
					.then(Commands.literal("record").executes(context -> showRecord(context.getSource().getPlayerOrException())))
					.then(Commands.literal("accept").executes(context -> {
						ServerPlayer player = context.getSource().getPlayerOrException();
						Long until = FOXY_OFFERS.remove(player.getUUID());
						if (until == null || player.level().getGameTime() > until || inMatch(player)) {
							player.sendSystemMessage(Component.literal("Nobody is waiting for your answer.").withStyle(ChatFormatting.GRAY));
							return 0;
						}
						startDavyBack(player, player.blockPosition(), true);
						return 1;
					}))
					.then(Commands.literal("pick")
							.then(Commands.argument("code", IntegerArgumentType.integer())
									.then(Commands.argument("choice", StringArgumentType.word())
											.executes(context -> {
												ServerPlayer player = context.getSource().getPlayerOrException();
												if (MATCHES.get(player.getUUID()) instanceof DavyBackFight fight) {
													fight.pickCommand(player, IntegerArgumentType.getInteger(context, "code"),
															StringArgumentType.getString(context, "choice"));
												}
												return 1;
											}))))
					.then(Commands.literal("giveup").executes(context -> giveUp(context.getSource().getPlayerOrException())))
					.then(Commands.literal("start")
							.requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
							.executes(context -> startTest(context, false))
							.then(Commands.literal("foxy").executes(context -> startTest(context, true)))));
		});
	}

	private static int startTest(CommandContext<CommandSourceStack> context, boolean foxy) throws com.mojang.brigadier.exceptions.CommandSyntaxException {
		ServerPlayer player = context.getSource().getPlayerOrException();
		if (inMatch(player) || player.getAttached(CrewAttachments.CREW) == null) {
			context.getSource().sendFailure(Component.literal("You need a crew and no match running."));
			return 0;
		}
		startDavyBack(player, player.blockPosition(), foxy);
		return 1;
	}

	private static int enterCommand(CommandContext<CommandSourceStack> context) throws com.mojang.brigadier.exceptions.CommandSyntaxException {
		ServerPlayer player = context.getSource().getPlayerOrException();
		CorridaTournament.Cup cup = CorridaTournament.Cup.byName(StringArgumentType.getString(context, "cup"));
		if (cup == null || inMatch(player)) {
			return 0;
		}
		if (!StoryPlaces.isInside((ServerLevel) player.level(), player.blockPosition(), COLOSSEUM)) {
			player.sendSystemMessage(Component.literal("Cups are fought inside the Corrida Colosseum.").withStyle(ChatFormatting.RED));
			return 0;
		}
		if (colosseumClosed(player)) {
			return 0;
		}
		if (cup.ordinal() > record(player).corridaBest() + 1) {
			player.sendSystemMessage(Component.literal("Win the " + CorridaTournament.Cup.values()[cup.ordinal() - 1].title() + " first.")
					.withStyle(ChatFormatting.RED));
			return 0;
		}
		if (!player.getAbilities().instabuild) {
			int tickets = count(player, COLOSSEUM_TICKET);
			if (tickets < cup.tickets()) {
				player.sendSystemMessage(Component.literal("The " + cup.title() + " costs " + cup.tickets() + " Colosseum Tickets (you have "
						+ tickets + ").").withStyle(ChatFormatting.RED));
				return 0;
			}
			take(player, COLOSSEUM_TICKET, cup.tickets());
		}
		startCorrida(player, cup);
		return 1;
	}

	private static int giveUp(ServerPlayer player) {
		ArenaMatch match = MATCHES.remove(player.getUUID());
		if (match == null) {
			player.sendSystemMessage(Component.literal("You're not in a match.").withStyle(ChatFormatting.GRAY));
			return 0;
		}
		match.forfeit(player, "You gave up.");
		match.cleanup();
		return 1;
	}

	private static int showRecord(ServerPlayer player) {
		ArenaRecord record = record(player);
		String best = record.corridaBest() < 0 ? "none yet" : CorridaTournament.Cup.values()[record.corridaBest()].title();
		player.sendSystemMessage(Component.literal("Corrida Colosseum: " + record.corridaWins() + " cups won (best: " + best + ").")
				.withStyle(ChatFormatting.GOLD));
		player.sendSystemMessage(Component.literal("Davy Back Fights: " + record.dbfWins() + " won, " + record.dbfLosses() + " lost"
				+ (record.foxyBeaten() ? ". You have beaten Foxy!" : ".")).withStyle(ChatFormatting.GOLD));
		if (record.taken().isEmpty()) {
			player.sendSystemMessage(Component.literal("No rival crew has any of your crewmates.").withStyle(ChatFormatting.GRAY));
		} else {
			for (ArenaRecord.Taken taken : record.taken()) {
				player.sendSystemMessage(Component.literal(" - " + taken.name() + " (Lv " + taken.level() + ") sails with the " + taken.heldBy()
						+ ". Win any Davy Back Fight game to take them back.").withStyle(ChatFormatting.YELLOW));
			}
		}
		return 1;
	}

	private static int count(ServerPlayer player, Item item) {
		int total = 0;
		for (int i = 0; i < player.getInventory().getContainerSize(); i++) {
			ItemStack stack = player.getInventory().getItem(i);
			if (stack.is(item)) {
				total += stack.getCount();
			}
		}
		return total;
	}

	private static void take(ServerPlayer player, Item item, int amount) {
		for (int i = 0; i < player.getInventory().getContainerSize() && amount > 0; i++) {
			ItemStack stack = player.getInventory().getItem(i);
			if (stack.is(item)) {
				int taken = Math.min(amount, stack.getCount());
				stack.shrink(taken);
				amount -= taken;
			}
		}
		player.getInventory().setChanged();
	}

	private static Item registerItem(String name, Function<Item.Properties, Item> factory, Item.Properties properties) {
		ResourceKey<Item> key = ResourceKey.create(Registries.ITEM, OnePieceMod.id(name));
		Item item = factory.apply(properties.setId(key));
		Registry.register(BuiltInRegistries.ITEM, key, item);
		return item;
	}
}

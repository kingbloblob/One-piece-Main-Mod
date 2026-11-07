package com.onepiecemod.crewship;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

import net.minecraft.ChatFormatting;
import net.minecraft.commands.Commands;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Registry;
import net.minecraft.core.UUIDUtil;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.MutableComponent;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.SoundType;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.material.MapColor;

import net.fabricmc.fabric.api.attachment.v1.AttachmentRegistry;
import net.fabricmc.fabric.api.attachment.v1.AttachmentType;
import net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback;
import net.fabricmc.fabric.api.event.player.PlayerBlockBreakEvents;
import net.fabricmc.fabric.api.object.builder.v1.block.entity.FabricBlockEntityTypeBuilder;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.advancement.AdvancementFeature;
import com.onepiecemod.crew.CrewAttachments;
import com.onepiecemod.crew.CrewmateEntity;
import com.onepiecemod.multiplayer.PlayerCrews;
import com.onepiecemod.ship.ShipEntity;
import com.onepiecemod.ship.ShipFeature;
import com.onepiecemod.ship.ShipInteractions;
import com.onepiecemod.ship.ShipLayout;

/**
 * Crew ships: make one ship your crew's floating home base, like the Straw Hats' Thousand Sunny.
 * OnePieceMod calls initialize() once at startup.
 *
 *  - ShipLogBlock + ShipLogBlockEntity: put it on your ship, sneak + right-click to make her your home ship.
 *    Its locker gets the daily haul. HomeShips: the saved list (one home ship per captain).
 *  - ShipRoom + CrewShipSurvey: the 12 rooms a ship can have (a workstation room for each crew job, plus a
 *    captain's cabin, garden and bath), found from the blocks around their main block.
 *  - CrewShipLevels: five levels from Pirate Sloop to Dream Ship.
 *  - CrewShipLife + ShipPostGoal: crewmates set to Work aboard live there: they work in their room by day and
 *    sleep in the bunks at night, docked or at sea, and their rooms give the crew perks.
 *  - CrewShipHaul: what each job brings in once a day.
 */
public final class CrewShipFeature {
	public static final String SHIP_LOG_ID = "onepiece:ship_log";

	public static final ResourceKey<Block> SHIP_LOG_KEY = ResourceKey.create(Registries.BLOCK, OnePieceMod.id("ship_log"));
	public static final Block SHIP_LOG = Registry.register(BuiltInRegistries.BLOCK, SHIP_LOG_KEY,
			new ShipLogBlock(BlockBehaviour.Properties.of().mapColor(MapColor.WOOD).strength(2.5f).sound(SoundType.WOOD)
					.noOcclusion().setId(SHIP_LOG_KEY)));

	public static final ResourceKey<Item> SHIP_LOG_ITEM_KEY = ResourceKey.create(Registries.ITEM, OnePieceMod.id("ship_log"));
	public static final Item SHIP_LOG_ITEM = Registry.register(BuiltInRegistries.ITEM, SHIP_LOG_ITEM_KEY,
			new BlockItem(SHIP_LOG, new Item.Properties().stacksTo(1).useBlockDescriptionPrefix().setId(SHIP_LOG_ITEM_KEY)));

	public static final BlockEntityType<ShipLogBlockEntity> SHIP_LOG_ENTITY = Registry.register(
			BuiltInRegistries.BLOCK_ENTITY_TYPE, OnePieceMod.id("ship_log"),
			FabricBlockEntityTypeBuilder.create(ShipLogBlockEntity::new, SHIP_LOG).build());

	/** On a crewmate: the homeId of the home ship they live aboard. */
	public static final AttachmentType<UUID> STATIONED = AttachmentRegistry.create(
			OnePieceMod.id("ship_post"), builder -> builder.persistent(UUIDUtil.CODEC));

	private CrewShipFeature() {
	}

	public static void initialize() {
		ShipFeature.addTabItem(SHIP_LOG_ITEM);
		CrewShipLife.initialize();

		// Using the log on a sailing ship (ShipInteractions finds the block you're looking at).
		ShipInteractions.blockUse = CrewShipFeature::useOnShip;
		// Home-ship bonuses on top of the crew's own (ShipCrewHelp sets the handling once a second).
		com.onepiecemod.shipcombat.ShipCrewHelp.homeShipBonus = ship -> new float[] {CrewShipLife.speedBonus(ship), CrewShipLife.turnBonus(ship)};

		// Only the crew can take the log off their home ship; taking it off ends her time as home.
		PlayerBlockBreakEvents.BEFORE.register((level, player, pos, state, blockEntity) -> {
			if (blockEntity instanceof ShipLogBlockEntity log && player instanceof ServerPlayer serverPlayer && !serverPlayer.isCreative()
					&& isHome(serverPlayer.level().getServer(), log) && !CrewShipLife.isCrew(serverPlayer.level().getServer(), serverPlayer, log.owner())) {
				serverPlayer.sendSystemMessage(Component.literal("This is the " + crewName(serverPlayer.level().getServer(), log.owner())
						+ "'s home ship. Only their crew can take the Ship's Log.").withStyle(ChatFormatting.RED));
				return false;
			}
			return true;
		});
		PlayerBlockBreakEvents.AFTER.register((level, player, pos, state, blockEntity) -> {
			if (blockEntity instanceof ShipLogBlockEntity log && player instanceof ServerPlayer serverPlayer && isHome(serverPlayer.level().getServer(), log)) {
				HomeShips.remove(serverPlayer.level().getServer(), log.owner());
				PlayerCrews.tell(serverPlayer.level().getServer(), log.owner(), Component.literal(
						"The Ship's Log was taken down: your ship is no longer the crew's home. Put a log back to make her home again.")
						.withStyle(ChatFormatting.YELLOW));
			}
		});

		CommandRegistrationCallback.EVENT.register((dispatcher, registryAccess, environment) -> dispatcher.register(
				Commands.literal("crew").then(Commands.literal("ship").executes(context -> {
					ServerPlayer player = context.getSource().getPlayerOrException();
					shipInfo(player);
					return 1;
				}))));
	}

	private static boolean isHome(MinecraftServer server, ShipLogBlockEntity log) {
		return log.owner() != null && HomeShips.isCurrent(server, log.owner(), log.homeId());
	}

	static String crewName(MinecraftServer server, UUID owner) {
		ServerPlayer captain = server.getPlayerList().getPlayer(owner);
		if (captain != null && captain.getAttached(CrewAttachments.CREW) != null) {
			return captain.getAttached(CrewAttachments.CREW).name();
		}
		HomeShips.HomeShip home = HomeShips.of(server, owner);
		if (home != null && !home.crewName().isEmpty()) {
			return home.crewName();
		}
		return PlayerCrews.crewName(server, owner);
	}

	// ---- Using the Ship's Log ----

	/** Right-clicking a docked log: sneak = claim / report, otherwise open the locker. */
	static void useDocked(ServerPlayer player, ShipLogBlockEntity log) {
		MinecraftServer server = player.level().getServer();
		if (player.isShiftKeyDown()) {
			if (!isHome(server, log)) {
				if (claim(player, log)) {
					CrewShipLife.resurvey(player.getUUID());
					report(player, log.getLevel(), null, log.getBlockPos());
				}
			} else if (CrewShipLife.isCrew(server, player, log.owner())) {
				report(player, log.getLevel(), null, log.getBlockPos());
			} else {
				player.sendSystemMessage(Component.literal("This is the " + crewName(server, log.owner()) + "'s home ship.").withStyle(ChatFormatting.YELLOW));
			}
			return;
		}
		if (isHome(server, log) && !CrewShipLife.isCrew(server, player, log.owner())) {
			player.sendSystemMessage(Component.literal("The locker belongs to the " + crewName(server, log.owner()) + ".").withStyle(ChatFormatting.RED));
			return;
		}
		if (!isHome(server, log)) {
			player.sendOverlayMessage(Component.literal("Sneak + right-click to make this ship your crew's home.").withStyle(ChatFormatting.GOLD));
		}
		player.openMenu(log);
	}

	/** Right-clicking the log on a sailing ship. True if handled (false lets the locker open as ship storage). */
	static boolean useOnShip(ShipEntity ship, int index, ServerPlayer player) {
		ShipLayout.ShipBlock block = ship.getLayout().blocks.get(index);
		if (!block.state().is(SHIP_LOG)) {
			return false;
		}
		MinecraftServer server = player.level().getServer();
		BlockEntity saved = block.nbt().isPresent()
				? BlockEntity.loadStatic(BlockPos.ZERO, block.state(), block.nbt().get(), player.level().registryAccess()) : null;
		if (!(saved instanceof ShipLogBlockEntity log)) {
			return false;
		}
		if (player.isShiftKeyDown()) {
			if (!isHome(server, log)) {
				// Write the claim into the ship's saved blocks; close any open lockers first so they don't undo it.
				ShipInteractions.closeAll(ship, (ServerLevel) player.level());
				if (claim(player, log)) {
					ship.getLayout().setNbt(index, log.saveWithFullMetadata(player.level().registryAccess()));
					CrewShipLife.rescan(ship);
					report(player, player.level(), ship, block.pos());
				}
			} else if (CrewShipLife.isCrew(server, player, log.owner())) {
				report(player, player.level(), ship, block.pos());
			} else {
				player.sendSystemMessage(Component.literal("This is the " + crewName(server, log.owner()) + "'s home ship.").withStyle(ChatFormatting.YELLOW));
			}
			return true;
		}
		if (isHome(server, log) && !CrewShipLife.isCrew(server, player, log.owner())) {
			player.sendSystemMessage(Component.literal("The locker belongs to the " + crewName(server, log.owner()) + ".").withStyle(ChatFormatting.RED));
			return true;
		}
		return false;
	}

	/** Makes the log's ship the player's crew home. False (with a message) if they can't. */
	private static boolean claim(ServerPlayer player, ShipLogBlockEntity log) {
		MinecraftServer server = player.level().getServer();
		boolean hasCrew = player.getAttached(CrewAttachments.CREW) != null || PlayerCrews.captainOf(server, player.getUUID()) != null;
		if (!hasCrew) {
			player.sendSystemMessage(Component.literal("You need a crew to have a home ship. Start one with /crew create <name>.").withStyle(ChatFormatting.RED));
			return false;
		}
		HomeShips.HomeShip old = HomeShips.of(server, player.getUUID());
		UUID homeId = UUID.randomUUID();
		String name = crewName(server, player.getUUID());
		log.claim(player.getUUID(), player.getName().getString(), homeId);
		HomeShips.put(server, player.getUUID(), new HomeShips.HomeShip(homeId, name, 0, old != null ? old.best() : 0, "",
				java.util.Optional.empty(), -1L));
		player.level().playSound(null, player.blockPosition(), SoundEvents.BOOK_PAGE_TURN, SoundSource.PLAYERS, 1f, 1f);
		player.sendSystemMessage(Component.literal("This ship is now the home of the " + name + "!"
				+ (old != null ? " (Your old ship's log is just a locker now.)" : "")).withStyle(ChatFormatting.GOLD));
		player.sendSystemMessage(Component.literal("Set crewmates to Work while they stand aboard and they'll live here: working in their "
				+ "room by day, sleeping in the bunks at night. Build rooms to level her up, like the Thousand Sunny.").withStyle(ChatFormatting.YELLOW));
		AdvancementFeature.grant(player, "pirate/home_ship");
		return true;
	}

	// ---- The report ----

	/** /crew ship */
	private static void shipInfo(ServerPlayer player) {
		MinecraftServer server = player.level().getServer();
		UUID owner = player.getUUID();
		HomeShips.HomeShip home = HomeShips.of(server, owner);
		if (home == null) {
			UUID captain = PlayerCrews.captainOf(server, owner);
			if (captain != null && HomeShips.of(server, captain) != null) {
				owner = captain;
				home = HomeShips.of(server, captain);
			}
		}
		if (home == null) {
			player.sendSystemMessage(Component.literal("Your crew has no home ship yet. Craft a Ship's Log, put it on your ship and "
					+ "sneak + right-click it.").withStyle(ChatFormatting.YELLOW));
			return;
		}
		CrewShipLife.Home live = CrewShipLife.home(owner);
		if (live == null) {
			player.sendSystemMessage(Component.literal("Your home ship (a " + CrewShipLevels.NAMES[Math.min(home.level(), CrewShipLevels.MAX)]
					+ ") isn't nearby" + home.dockPos().map(pos -> ": last moored at " + pos.toShortString() + ".").orElse(".")).withStyle(ChatFormatting.YELLOW));
			return;
		}
		send(player, lines(server, crewName(server, owner), live.survey, live.stationed));
	}

	private static void report(ServerPlayer player, net.minecraft.world.level.Level level, ShipEntity ship, BlockPos logPos) {
		MinecraftServer server = player.level().getServer();
		UUID owner = player.getUUID();
		HomeShips.HomeShip saved = HomeShips.of(server, owner);
		if (saved == null) {
			UUID captain = PlayerCrews.captainOf(server, owner);
			owner = captain != null ? captain : owner;
		}
		CrewShipLife.Home live = CrewShipLife.home(owner);
		CrewShipSurvey survey;
		List<CrewmateEntity> stationed = new ArrayList<>();
		if (live != null && (ship != null ? live.ship == ship : live.ship == null && live.log.equals(logPos))) {
			survey = live.survey;
			stationed = live.stationed;
		} else if (ship != null) {
			Map<BlockPos, BlockState> blocks = new HashMap<>();
			for (ShipLayout.ShipBlock block : ship.getLayout().blocks) {
				blocks.put(block.pos(), block.state());
			}
			survey = CrewShipSurvey.of(blocks, ship.getLayout().helm);
		} else {
			Map<BlockPos, BlockState> blocks = CrewShipLife.floodFill(level, logPos);
			BlockPos helm = blocks.entrySet().stream().filter(e -> e.getValue().is(ShipFeature.HELM)).map(Map.Entry::getKey).findFirst().orElse(null);
			survey = CrewShipSurvey.of(blocks, helm);
		}
		send(player, lines(server, crewName(server, owner), survey, stationed));
	}

	private static void send(ServerPlayer player, List<Component> lines) {
		for (Component line : lines) {
			player.sendSystemMessage(line);
		}
	}

	/** The home ship report: level, rooms (and who works there), counts, and what the next level needs. */
	static List<Component> lines(MinecraftServer server, String crewName, CrewShipSurvey survey, List<CrewmateEntity> stationed) {
		List<Component> lines = new ArrayList<>();
		int level = CrewShipLevels.levelFor(survey, stationed.size());
		lines.add(Component.literal("=== " + crewName + " home ship: " + CrewShipLevels.NAMES[level] + " (level " + level + "/"
				+ CrewShipLevels.MAX + ") ===").withStyle(ChatFormatting.GOLD));
		lines.add(Component.literal(CrewShipLevels.perk(level)).withStyle(ChatFormatting.GRAY));
		MutableComponent rooms = Component.literal("Rooms: ").withStyle(ChatFormatting.AQUA);
		boolean first = true;
		for (ShipRoom room : ShipRoom.values()) {
			if (!first) {
				rooms.append(Component.literal(", ").withStyle(ChatFormatting.DARK_GRAY));
			}
			first = false;
			boolean built = survey.has(room);
			String who = "";
			if (built && room.role != null) {
				CrewmateEntity worker = stationed.stream().filter(c -> c.getRole() == room.role).findFirst().orElse(null);
				who = worker != null ? " (" + worker.getDisplayName().getString().replaceAll(" Lv.*", "") + ")" : " (no " + room.role.title() + ")";
			}
			rooms.append(Component.literal((built ? "✔ " : "✘ ") + room.title + who).withStyle(built ? ChatFormatting.GREEN : ChatFormatting.DARK_GRAY));
		}
		lines.add(rooms);
		lines.add(Component.literal("Bunks " + survey.bunks.size() + " · Chests/barrels " + survey.storage + " · Cannons " + survey.cannons
				+ " · Crew stationed " + stationed.size()).withStyle(ChatFormatting.AQUA));
		if (level < CrewShipLevels.MAX) {
			lines.add(Component.literal("Next: " + CrewShipLevels.NAMES[level + 1]).withStyle(ChatFormatting.YELLOW));
			for (CrewShipLevels.Need need : CrewShipLevels.needs(level + 1, survey, stationed.size())) {
				if (!need.done()) {
					String count = need.need() > 1 ? " " + need.have() + "/" + need.need() : "";
					lines.add(Component.literal("  ✘ " + need.text() + count).withStyle(ChatFormatting.RED));
				}
			}
			// Tell them how to build the first missing room.
			for (ShipRoom room : ShipRoom.values()) {
				if (!survey.has(room) && room.role != null) {
					lines.add(Component.literal("  Tip: a " + room.title + " (" + room.role.title() + ") = " + room.hint + ".").withStyle(ChatFormatting.GRAY));
					break;
				}
			}
		}
		return lines;
	}
}

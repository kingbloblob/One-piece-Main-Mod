package com.onepiecemod.npc;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;

import com.mojang.brigadier.arguments.IntegerArgumentType;
import com.mojang.brigadier.arguments.StringArgumentType;
import com.mojang.brigadier.context.CommandContext;

import net.minecraft.ChatFormatting;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.commands.SharedSuggestionProvider;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.Mob;

import net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerEntityEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;

import com.onepiecemod.bounty.BountyFeature;
import com.onepiecemod.shipcombat.ShipCombatFeature;
import com.onepiecemod.world.GuardKit;

/**
 * Pirate and Marine NPCs. They are two mod entities that share one brain (HumanNpc):
 *  - onepiece:marine (bounty.MarineEntity): Marines, CP agents, Pacifista, Seraphim, Impel Down jailers.
 *  - onepiece:sea_pirate (shipcombat.SeaPirateEntity): pirates of every crew, Fish-Men, Baroque Works, bandits, bounty hunters.
 * Each one rolls its own look, crew, rank, name, weapon and fighting style from a kit in onepiece/npc_kits.json.
 *
 * This class:
 *  - dresses structure guards (structures place them with the tags onepiece_guard + onepiece_kit_<id>),
 *  - swaps any old vanilla stand-in (a vindicator "Marine Soldier", a pillager "Pirate Gunner"...) for a real NPC,
 *  - sends pirate gangs and Marine patrols around islands and beaches (NpcPatrols),
 *  - adds /npc for testing.
 * OnePieceMod calls initialize() once while the game loads.
 */
public class NpcFeature {
	/** Vanilla mobs that older structures used as pirates and Marines. */
	private static final Set<String> VANILLA_STAND_INS = Set.of("minecraft:zombie", "minecraft:skeleton", "minecraft:vindicator",
			"minecraft:pillager", "minecraft:drowned", "minecraft:husk", "minecraft:wither_skeleton", "minecraft:stray");

	private record Swap(ServerLevel level, Mob old, String kitId) {}

	private static final List<Swap> SWAPS = new ArrayList<>();
	/** Guard names from guards.json ("Marine Soldier") -> NPC kit, to find vanilla guards in worlds made before this. */
	private static final Map<String, String> KIT_BY_GUARD_NAME = new HashMap<>();

	public static void initialize() {
		for (String id : NpcKit.all().keySet()) {
			GuardKit guard = GuardKit.get(id);
			if (guard != null && guard.name != null) {
				KIT_BY_GUARD_NAME.put(guard.name, id);
			}
		}

		// Vanilla guards from worlds made before the NPCs existed (their tags were already used up).
		ServerEntityEvents.ENTITY_LOAD.register((entity, level) -> {
			if (entity instanceof Mob mob && !(mob instanceof HumanNpc) && mob.isPersistenceRequired() && mob.hasCustomName()
					&& VANILLA_STAND_INS.contains(BuiltInRegistries.ENTITY_TYPE.getKey(mob.getType()).toString())) {
				String kitId = KIT_BY_GUARD_NAME.get(mob.getCustomName().getString());
				if (kitId != null) {
					SWAPS.add(new Swap(level, mob, kitId));
				}
			}
		});
		// Swapping waits for the end of the tick: adding entities while a chunk is still loading them isn't safe.
		ServerTickEvents.END_SERVER_TICK.register(NpcFeature::tick);

		NpcPatrols.initialize();
		registerCommands();
	}

	/**
	 * Called by WorldFeature when a structure guard loads for the first time. Returns true if it was a pirate or Marine
	 * and is now handled here; false leaves it to GuardKit (Fish-Men warriors, samurai, beasts...).
	 */
	public static boolean claimGuard(Mob mob, ServerLevel level) {
		String kitId = null;
		for (String tag : mob.entityTags()) {
			if (tag.startsWith(GuardKit.KIT_TAG_PREFIX)) {
				kitId = tag.substring(GuardKit.KIT_TAG_PREFIX.length());
			}
		}
		NpcKit kit = NpcKit.get(kitId);
		if (kit == null) {
			return false;
		}
		mob.removeTag(GuardKit.GUARD_TAG);
		mob.removeTag(GuardKit.KIT_TAG_PREFIX + kitId);
		if (mob instanceof HumanNpc npc && npc.isMarineSide() == kit.isMarine()) {
			npc.applyKit(kit, mob.getRandom());
			npc.makeGuard();
			com.onepiecemod.dungeon.DungeonBosses.afterGuardDressed(npc); // a dungeon's mini-boss gets its boss stats
		} else {
			SWAPS.add(new Swap(level, mob, kitId)); // A vanilla mob from an old template, or the wrong side's entity.
		}
		return true;
	}

	private static void tick(MinecraftServer server) {
		if (!SWAPS.isEmpty()) {
			List<Swap> todo = new ArrayList<>(SWAPS);
			SWAPS.clear();
			for (Swap swap : todo) {
				if (!swap.old().isRemoved()) {
					HumanNpc npc = spawn(swap.level(), swap.kitId(), swap.old().blockPosition(), swap.old().getYRot());
					if (npc != null) {
						npc.makeGuard();
						// a dungeon mini-boss placed as the wrong entity keeps its boss tag
						for (String tag : swap.old().entityTags()) {
							if (tag.startsWith(com.onepiecemod.dungeon.DungeonBosses.TAG_PREFIX)) {
								npc.addTag(tag);
							}
						}
						com.onepiecemod.dungeon.DungeonBosses.afterGuardDressed(npc);
						swap.old().discard();
					}
				}
			}
		}
		NpcPatrols.tick(server);
	}

	/** The entity type a kit uses: Marines are onepiece:marine, everyone else onepiece:sea_pirate. */
	public static EntityType<? extends HumanNpc> typeFor(NpcKit kit) {
		return kit.isMarine() ? BountyFeature.MARINE : ShipCombatFeature.SEA_PIRATE;
	}

	/** Makes, dresses and adds one NPC. Returns null if the kit doesn't exist. */
	public static HumanNpc spawn(ServerLevel level, String kitId, BlockPos pos, float yaw) {
		NpcKit kit = NpcKit.get(kitId);
		if (kit == null) {
			return null;
		}
		HumanNpc npc = typeFor(kit).create(level, EntitySpawnReason.EVENT);
		if (npc == null) {
			return null;
		}
		npc.snapTo(pos.getX() + 0.5, pos.getY(), pos.getZ() + 0.5, yaw, 0);
		npc.applyKit(kit, level.getRandom());
		level.addFreshEntity(npc);
		return npc;
	}

	// ---------- /npc (operators only) ----------

	private static void registerCommands() {
		CommandRegistrationCallback.EVENT.register((dispatcher, registryAccess, environment) -> dispatcher.register(
				Commands.literal("npc")
						.requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
						.then(Commands.literal("spawn")
								.then(Commands.argument("kit", StringArgumentType.word())
										.suggests((context, builder) -> SharedSuggestionProvider.suggest(NpcKit.all().keySet(), builder))
										.executes(context -> spawnCommand(context, 1))
										.then(Commands.argument("count", IntegerArgumentType.integer(1, 20))
												.executes(context -> spawnCommand(context, IntegerArgumentType.getInteger(context, "count"))))))
						.then(Commands.literal("patrol")
								.executes(context -> {
									ServerPlayer player = context.getSource().getPlayerOrException();
									boolean sent = NpcPatrols.sendPatrol(player, true);
									context.getSource().sendSuccess(() -> Component.literal(sent ? "A patrol is on its way."
											: "Nobody patrols here (or there's no dry ground nearby).").withStyle(ChatFormatting.GOLD), false);
									return sent ? 1 : 0;
								}))
						.then(Commands.literal("kits")
								.executes(context -> {
									context.getSource().sendSuccess(() -> Component.literal("NPC kits: " + String.join(", ", NpcKit.all().keySet()))
											.withStyle(ChatFormatting.GOLD), false);
									return NpcKit.all().size();
								}))));
	}

	private static int spawnCommand(CommandContext<CommandSourceStack> context, int count) {
		String kitId = StringArgumentType.getString(context, "kit");
		if (NpcKit.get(kitId) == null) {
			context.getSource().sendFailure(Component.literal("No NPC kit called " + kitId + ". Try /npc kits"));
			return 0;
		}
		ServerLevel level = context.getSource().getLevel();
		BlockPos here = BlockPos.containing(context.getSource().getPosition());
		for (int i = 0; i < count; i++) {
			BlockPos pos = here.offset(level.getRandom().nextInt(7) - 3, 0, level.getRandom().nextInt(7) - 3);
			spawn(level, kitId, pos, level.getRandom().nextFloat() * 360f);
		}
		context.getSource().sendSuccess(() -> Component.literal("Spawned " + count + " x " + kitId).withStyle(ChatFormatting.GOLD), true);
		return count;
	}
}

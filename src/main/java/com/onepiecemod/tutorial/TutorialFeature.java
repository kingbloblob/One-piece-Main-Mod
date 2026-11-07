package com.onepiecemod.tutorial;

import java.util.ArrayList;
import java.util.List;
import java.util.Set;

import com.mojang.brigadier.context.CommandContext;
import com.mojang.brigadier.exceptions.CommandSyntaxException;
import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;

import io.netty.buffer.ByteBuf;

import net.minecraft.ChatFormatting;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.network.chat.Component;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.vehicle.boat.AbstractBoat;
import net.minecraft.world.item.Item;

import net.fabricmc.fabric.api.attachment.v1.AttachmentRegistry;
import net.fabricmc.fabric.api.attachment.v1.AttachmentType;
import net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.fabricmc.fabric.api.event.player.UseItemCallback;
import net.fabricmc.fabric.api.networking.v1.PayloadTypeRegistry;
import net.fabricmc.fabric.api.networking.v1.ServerPlayConnectionEvents;
import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.crew.Crew;
import com.onepiecemod.crew.CrewAttachments;
import com.onepiecemod.item.ModItems;
import com.onepiecemod.power.FruitAbilities;
import com.onepiecemod.power.ModAttachments;
import com.onepiecemod.race.RaceAttachments;
import com.onepiecemod.sea.SeaItems;
import com.onepiecemod.ship.ShipEntity;
import com.onepiecemod.stats.StatTraining;
import com.onepiecemod.stats.StatsAttachments;
import com.onepiecemod.stats.StatsData;
import com.onepiecemod.story.StoryData;
import com.onepiecemod.story.StoryProgress;

/**
 * "First Voyage": a guided first hour. It walks through the steps in TutorialStep one at a time, in five parts:
 * Castaway (race, Crafter's Journal, keys, HUD, quest tree), Set Sail (boat, Log Pose, Foosha, Luffy),
 * Pirate Life (first Pirate Level, crew, crewmate), Captain (your own ship) and Devil Fruit
 * (find, eat, use). The current step shows in the inventory screen (tutorial/client/TutorialOverlay) and in chat.
 * Alongside it, TutorialTips explains keys the first time they become useful (first Haki, first style, first helm...).
 *
 * It never hands out power: each step only gives 3 Pirate XP, so slow progression stays slow.
 * Every step is checked from what the player already did, so nothing needs to happen in order.
 * Commands: /tutorial (show the current step), /tutorial off, /tutorial on, /tutorial skip, /tutorial restart.
 * OnePieceMod calls initialize() once while the game loads.
 */
public class TutorialFeature {
	/** Pirate XP for each finished step. */
	private static final int STEP_XP = 3;
	/** How often steps are checked, in ticks (20 ticks = 1 second). */
	private static final int EVERY = 20;
	/** Things only the player's game can see (opening a screen), reported with a Seen message. */
	private static final Set<String> SEEABLE = Set.of("journal", "hud", "quests", "keys");
	/** Save format: 1 = the first 10-step guide, 2 = the 16-step guide in parts. */
	private static final int VERSION = 2;
	/** The steps of version 1, in their old order, to move old saves to the new order. */
	private static final String[] OLD_STEPS = {"RACE", "JOURNAL", "HUD", "QUESTS", "FOOSHA", "LUFFY", "LEVEL", "CREW", "CREWMATE", "FRUIT"};

	/**
	 * A player's progress in the guide. Saved on the player and kept when they die.
	 *
	 * @param step how many steps are done (TutorialStep.COUNT once the guide is finished)
	 * @param seen screens the player has opened, like "quests"
	 * @param off  true when the player turned the guide off
	 * @param paid the most steps ever done, so /tutorial restart doesn't pay the XP twice
	 * @param version the save format (VERSION); saves from before the parts had no version and read as 1
	 */
	public record Progress(int step, List<String> seen, boolean off, int paid, int version) {
		public static final Progress START = new Progress(0, List.of(), false, 0, VERSION);
		public static final Codec<Progress> CODEC = RecordCodecBuilder.create(instance -> instance.group(
				Codec.INT.optionalFieldOf("step", 0).forGetter(Progress::step),
				Codec.STRING.listOf().optionalFieldOf("seen", List.of()).forGetter(Progress::seen),
				Codec.BOOL.optionalFieldOf("off", false).forGetter(Progress::off),
				Codec.INT.optionalFieldOf("paid", 0).forGetter(Progress::paid),
				Codec.INT.optionalFieldOf("v", 1).forGetter(Progress::version)
		).apply(instance, Progress::new));

		public boolean finished() {
			return step >= TutorialStep.COUNT;
		}

		Progress withStep(int newStep) {
			return new Progress(newStep, seen, off, Math.max(paid, newStep), version);
		}

		Progress withOff(boolean newOff) {
			return new Progress(step, seen, newOff, paid, version);
		}

		Progress withSeen(String what) {
			if (seen.contains(what)) {
				return this;
			}
			List<String> list = new ArrayList<>(seen);
			list.add(what);
			return new Progress(step, list, off, paid, version);
		}
	}

	public static final AttachmentType<Progress> PROGRESS = AttachmentRegistry.create(
			OnePieceMod.id("tutorial"),
			builder -> builder.persistent(Progress.CODEC).copyOnDeath()
	);

	/**
	 * Server -> player: what the guide panel should show.
	 *
	 * @param step     the current step's position, or TutorialStep.COUNT when done
	 * @param off      true when the panel should be hidden
	 * @param progress a short "30/50 XP" style note for the step, or ""
	 * @param tips     ids of the tips the player has seen, in the order they were seen (for the Voyage Log book)
	 */
	public record Sync(int step, boolean off, String progress, List<String> tips) implements CustomPacketPayload {
		public static final Type<Sync> TYPE = new Type<>(OnePieceMod.id("tutorial_sync"));
		public static final StreamCodec<ByteBuf, Sync> CODEC = StreamCodec.composite(
				ByteBufCodecs.VAR_INT, Sync::step,
				ByteBufCodecs.BOOL, Sync::off,
				ByteBufCodecs.STRING_UTF8, Sync::progress,
				ByteBufCodecs.STRING_UTF8.apply(ByteBufCodecs.list()), Sync::tips,
				Sync::new
		);

		@Override
		public Type<? extends CustomPacketPayload> type() {
			return TYPE;
		}
	}

	/** Player -> server: "I opened this screen" ("journal", "hud", "quests" or "keys"). */
	public record Seen(String what) implements CustomPacketPayload {
		public static final Type<Seen> TYPE = new Type<>(OnePieceMod.id("tutorial_seen"));
		public static final StreamCodec<ByteBuf, Seen> CODEC = StreamCodec.composite(
				ByteBufCodecs.STRING_UTF8, Seen::what,
				Seen::new
		);

		@Override
		public Type<? extends CustomPacketPayload> type() {
			return TYPE;
		}
	}

	public static void initialize() {
		PayloadTypeRegistry.clientboundPlay().register(Sync.TYPE, Sync.CODEC);
		PayloadTypeRegistry.serverboundPlay().register(Seen.TYPE, Seen.CODEC);

		ServerPlayNetworking.registerGlobalReceiver(Seen.TYPE, (payload, context) -> {
			if (SEEABLE.contains(payload.what())) {
				ServerPlayer player = context.player();
				set(player, get(player).withSeen(payload.what()));
			}
		});

		// Right-clicking the Log Pose reads it (LogPoseItem shows where the needle points).
		UseItemCallback.EVENT.register((player, level, hand) -> {
			if (player instanceof ServerPlayer serverPlayer && player.getItemInHand(hand).is(SeaItems.LOG_POSE)) {
				set(serverPlayer, get(serverPlayer).withSeen("log_pose"));
			}
			return InteractionResult.PASS;
		});

		ServerPlayConnectionEvents.JOIN.register((handler, sender, server) -> server.execute(() -> join(handler.player)));

		ServerTickEvents.END_SERVER_TICK.register(server -> {
			if (server.getTickCount() % EVERY != 0) {
				return;
			}
			for (ServerPlayer player : server.getPlayerList().getPlayers()) {
				check(player);
			}
		});

		CommandRegistrationCallback.EVENT.register((dispatcher, registryAccess, environment) -> dispatcher.register(
				Commands.literal("tutorial")
						.executes(TutorialFeature::show)
						.then(Commands.literal("off").executes(context -> turn(context, true)))
						.then(Commands.literal("on").executes(context -> turn(context, false)))
						.then(Commands.literal("skip").executes(TutorialFeature::skip))
						.then(Commands.literal("restart").executes(TutorialFeature::restart))
		));
	}

	public static Progress get(ServerPlayer player) {
		Progress progress = player.getAttached(PROGRESS);
		if (progress == null) {
			return Progress.START;
		}
		if (progress.version() < VERSION) {
			progress = upgrade(player, progress);
			set(player, progress);
		}
		return progress;
	}

	/**
	 * Moves a save from the first 10-step guide to the new order. The step they were on keeps its place,
	 * so new steps before it (keys, boat, Log Pose) are skipped: they already know those.
	 * Tips for things they already have are marked seen, so they don't get ten tips at once.
	 */
	private static Progress upgrade(ServerPlayer player, Progress old) {
		int step = newIndex(old.step());
		int paid = newIndex(old.paid());
		Progress progress = new Progress(step, old.seen(), old.off(), Math.max(paid, step), VERSION);
		return TutorialTips.markKnown(player, progress);
	}

	private static int newIndex(int oldIndex) {
		if (oldIndex <= 0) {
			return 0;
		}
		if (oldIndex >= OLD_STEPS.length) {
			return TutorialStep.COUNT;
		}
		return TutorialStep.valueOf(OLD_STEPS[oldIndex]).ordinal();
	}

	private static void set(ServerPlayer player, Progress progress) {
		player.setAttached(PROGRESS, progress);
	}

	private static void join(ServerPlayer player) {
		if (player.getAttached(PROGRESS) == null) {
			// Players who were already sailing before the guide existed don't need it: start it switched off.
			boolean veteran = StoryProgress.orStart(player).chapter() >= 2;
			Progress start = Progress.START.withOff(veteran);
			set(player, veteran ? TutorialTips.markKnown(player, start) : start);
			if (veteran) {
				player.sendSystemMessage(Component.literal("New: a First Voyage guide for new pirates. Type /tutorial on if you want it.")
						.withStyle(ChatFormatting.DARK_AQUA));
			} else {
				player.sendSystemMessage(Component.literal("Welcome aboard, castaway! Your First Voyage guide shows in your inventory (")
						.withStyle(ChatFormatting.GOLD)
						.append(Component.keybind("key.inventory"))
						.append(Component.literal("). Type /tutorial for the steps, /tutorial off to hide it.")));
			}
		}
		sync(player);
	}

	/** Notes what the player is doing, shows any new tip, moves past every step already done, then tells their game what to show. */
	private static void check(ServerPlayer player) {
		Progress before = get(player);
		Progress progress = observe(player, before);
		if (!progress.off()) {
			progress = TutorialTips.check(player, progress);
		}
		if (progress != before) {
			set(player, progress);
		}
		if (progress.off() || progress.finished()) {
			if (progress != before) {
				sync(player); // A new tip for the Voyage Log.
			}
			return;
		}
		int step = progress.step();
		while (step < TutorialStep.COUNT && done(player, progress, TutorialStep.at(step))) {
			TutorialStep finished = TutorialStep.at(step);
			step++;
			announce(player, finished, TutorialStep.at(step), step);
			if (step > progress.paid()) {
				StatTraining.addXp(player, STEP_XP, false);
			}
		}
		if (step != progress.step()) {
			set(player, progress.withStep(step));
			player.level().playSound(null, player.blockPosition(),
					step >= TutorialStep.COUNT ? SoundEvents.UI_TOAST_CHALLENGE_COMPLETE : SoundEvents.EXPERIENCE_ORB_PICKUP,
					SoundSource.PLAYERS, 0.6f, 1.2f);
		}
		sync(player);
	}

	private static boolean done(ServerPlayer player, Progress progress, TutorialStep step) {
		StoryProgress story = StoryProgress.orStart(player);
		return switch (step) {
			case RACE -> RaceAttachments.get(player) != null;
			case JOURNAL -> progress.seen().contains("journal");
			case KEYS -> progress.seen().contains("keys");
			case HUD -> progress.seen().contains("hud");
			case QUESTS -> progress.seen().contains("quests");
			case BOAT -> progress.seen().contains("boat") || reachedFoosha(story);
			case LOG_POSE -> progress.seen().contains("log_pose") || reachedFoosha(story);
			case FOOSHA -> reachedFoosha(story);
			case LUFFY -> story.completed("dream");
			case LEVEL -> StatsAttachments.get(player).spentPoints() > 0;
			case CREW -> player.getAttached(CrewAttachments.CREW) != null;
			case CREWMATE -> {
				Crew crew = player.getAttached(CrewAttachments.CREW);
				yield crew != null && (crew.size() > 0 || crew.hires() > 0);
			}
			case SHIP -> progress.seen().contains("ship");
			case FRUIT -> ateFruit(player) || carriesFruit(player);
			case EAT -> ateFruit(player);
			case POWER -> progress.seen().contains("power");
		};
	}

	/** Records things that are only true for a moment (sitting in a boat, holding the helm, a fruit move on cooldown). */
	private static Progress observe(ServerPlayer player, Progress progress) {
		if (player.getVehicle() instanceof AbstractBoat || ShipEntity.aboard(player) != null) {
			progress = progress.withSeen("boat");
		}
		if (player.getVehicle() instanceof ShipEntity) {
			progress = progress.withSeen("ship");
		}
		if (ateFruit(player) && (FruitAbilities.secondsLeft(player, false) > 0 || FruitAbilities.secondsLeft(player, true) > 0)) {
			progress = progress.withSeen("power");
		}
		return progress;
	}

	/** True once the "reach" goal of Chapter 1 ("A Hat and a Dream") is done, or the chapter is behind them. */
	private static boolean reachedFoosha(StoryProgress story) {
		int index = StoryData.indexOf("dream");
		StoryData.Chapter chapter = StoryData.chapter(index);
		if (index < 0 || chapter == null) {
			return story.chapter() > 0;
		}
		if (story.chapter() != index) {
			return story.chapter() > index;
		}
		for (int i = 0; i < chapter.goals.size(); i++) {
			if ("reach".equals(chapter.goals.get(i).type)) {
				return story.goalDone(i);
			}
		}
		return false;
	}

	/** True if the player has eaten a Devil Fruit. */
	static boolean ateFruit(ServerPlayer player) {
		String eaten = player.getAttached(ModAttachments.DEVIL_FRUIT);
		return eaten != null && !eaten.isEmpty();
	}

	/** True if the player carries a Devil Fruit. */
	static boolean carriesFruit(ServerPlayer player) {
		for (Item fruit : ModItems.DEVIL_FRUITS.values()) {
			if (player.getInventory().countItem(fruit) > 0) {
				return true;
			}
		}
		return false;
	}

	private static String progressText(ServerPlayer player, TutorialStep step) {
		if (step == TutorialStep.LEVEL) {
			StatsData stats = StatsAttachments.get(player);
			if (stats.level() == 0) {
				return stats.xpIntoLevel() + "/" + StatsData.xpForNextLevel(0) + " XP";
			}
			return stats.freePoints() > 0 ? "point ready!" : "";
		}
		return "";
	}

	private static void announce(ServerPlayer player, TutorialStep finished, TutorialStep next, int done) {
		player.sendSystemMessage(Component.literal("✔ First Voyage " + done + "/" + TutorialStep.COUNT + ": " + finished.title)
				.withStyle(ChatFormatting.GREEN));
		if (next != null && next.part != finished.part) {
			player.sendSystemMessage(Component.literal("⚓ Part " + (finished.part.ordinal() + 1) + " done! Part " + (next.part.ordinal() + 1)
					+ ": " + next.part.title).withStyle(ChatFormatting.AQUA, ChatFormatting.BOLD));
		}
		if (next != null) {
			player.sendSystemMessage(Component.literal("Next: " + next.title + ". ").withStyle(ChatFormatting.GOLD)
					.append(next.hintComponent().copy().withStyle(ChatFormatting.GRAY)));
		} else {
			player.sendSystemMessage(Component.literal("First Voyage complete! You know the ropes now. ")
					.withStyle(ChatFormatting.GOLD, ChatFormatting.BOLD)
					.append(Component.literal("Press ").withStyle(style -> style.withBold(false).withColor(ChatFormatting.YELLOW)))
					.append(Component.keybind("key.onepiece.quest_tree").withStyle(style -> style.withBold(false).withColor(ChatFormatting.YELLOW)))
					.append(Component.literal(" any time to see where the story goes next.").withStyle(style -> style.withBold(false).withColor(ChatFormatting.YELLOW))));
		}
	}

	private static void sync(ServerPlayer player) {
		if (!ServerPlayNetworking.canSend(player, Sync.TYPE)) {
			return;
		}
		Progress progress = get(player);
		TutorialStep step = TutorialStep.at(progress.step());
		List<String> tips = new ArrayList<>();
		for (String seen : progress.seen()) {
			if (seen.startsWith("tip:")) {
				tips.add(seen.substring(4));
			}
		}
		ServerPlayNetworking.send(player, new Sync(progress.step(), progress.off(),
				step == null ? "" : progressText(player, step), tips));
	}

	private static int show(CommandContext<CommandSourceStack> context) throws CommandSyntaxException {
		ServerPlayer player = context.getSource().getPlayerOrException();
		Progress progress = get(player);
		if (progress.finished()) {
			player.sendSystemMessage(Component.literal("You finished the First Voyage guide. /tutorial restart runs it again.")
					.withStyle(ChatFormatting.GOLD));
			return 1;
		}
		player.sendSystemMessage(Component.literal("=== First Voyage (" + progress.step() + "/" + TutorialStep.COUNT + " done) ===")
				.withStyle(ChatFormatting.GOLD));
		for (int i = 0; i < TutorialStep.COUNT; i++) {
			TutorialStep step = TutorialStep.at(i);
			if (i == 0 || TutorialStep.at(i - 1).part != step.part) {
				player.sendSystemMessage(Component.literal("Part " + (step.part.ordinal() + 1) + ": " + step.part.title).withStyle(ChatFormatting.AQUA));
			}
			boolean done = i < progress.step();
			player.sendSystemMessage(Component.literal((done ? " ✔ " : i == progress.step() ? " ➜ " : " • ") + step.title)
					.withStyle(done ? ChatFormatting.GREEN : i == progress.step() ? ChatFormatting.YELLOW : ChatFormatting.GRAY));
		}
		TutorialStep current = TutorialStep.at(progress.step());
		player.sendSystemMessage(current.hintComponent().copy().withStyle(ChatFormatting.WHITE));
		if (progress.off()) {
			player.sendSystemMessage(Component.literal("The guide is off. /tutorial on shows it again.").withStyle(ChatFormatting.DARK_GRAY));
		}
		return 1;
	}

	private static int turn(CommandContext<CommandSourceStack> context, boolean off) throws CommandSyntaxException {
		ServerPlayer player = context.getSource().getPlayerOrException();
		set(player, get(player).withOff(off));
		player.sendSystemMessage(Component.literal(off ? "First Voyage guide hidden. /tutorial on brings it back."
				: "First Voyage guide is back. It shows in your inventory.").withStyle(ChatFormatting.GOLD));
		sync(player);
		return 1;
	}

	private static int restart(CommandContext<CommandSourceStack> context) throws CommandSyntaxException {
		ServerPlayer player = context.getSource().getPlayerOrException();
		// Steps are checked from what the player already did, so done ones tick off again at once (without XP twice).
		Progress old = get(player);
		set(player, new Progress(0, old.seen(), false, old.paid(), VERSION));
		player.sendSystemMessage(Component.literal("First Voyage restarted.").withStyle(ChatFormatting.GOLD));
		return 1;
	}

	/** Moves past the current step without doing it (no XP), for steps a player doesn't want, like eating a fruit. */
	private static int skip(CommandContext<CommandSourceStack> context) throws CommandSyntaxException {
		ServerPlayer player = context.getSource().getPlayerOrException();
		Progress progress = get(player);
		TutorialStep current = TutorialStep.at(progress.step());
		if (current == null) {
			player.sendSystemMessage(Component.literal("You finished the First Voyage guide already.").withStyle(ChatFormatting.GOLD));
			return 0;
		}
		// Not eating the fruit means there's no power to use either, so that skips both.
		int to = current == TutorialStep.EAT ? TutorialStep.POWER.ordinal() + 1 : progress.step() + 1;
		// Skipping counts as paid, so doing it later (after a restart) doesn't pay either.
		set(player, new Progress(to, progress.seen(), progress.off(), Math.max(progress.paid(), to), VERSION));
		player.sendSystemMessage(Component.literal("Skipped: " + current.title + ".").withStyle(ChatFormatting.GRAY));
		TutorialStep next = TutorialStep.at(to);
		if (next != null) {
			player.sendSystemMessage(Component.literal("Next: " + next.title + ". ").withStyle(ChatFormatting.GOLD)
					.append(next.hintComponent().copy().withStyle(ChatFormatting.GRAY)));
		}
		sync(player);
		return 1;
	}
}

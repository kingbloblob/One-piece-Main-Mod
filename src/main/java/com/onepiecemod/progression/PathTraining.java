package com.onepiecemod.progression;

import java.util.List;
import java.util.Set;

import com.mojang.brigadier.arguments.IntegerArgumentType;
import com.mojang.brigadier.arguments.StringArgumentType;
import com.mojang.brigadier.context.CommandContext;
import com.mojang.brigadier.exceptions.CommandSyntaxException;

import net.minecraft.ChatFormatting;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.commands.arguments.EntityArgument;
import net.minecraft.network.chat.ClickEvent;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.HoverEvent;
import net.minecraft.network.chat.MutableComponent;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.item.ItemStack;

import net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback;
import net.fabricmc.fabric.api.event.player.UseEntityCallback;

import com.onepiecemod.character.CharacterEntity;
import com.onepiecemod.character.CharacterFeature;
import com.onepiecemod.haki.HakiAttachments;
import com.onepiecemod.haki.HakiPowers;
import com.onepiecemod.progression.CombatPaths.Choice;
import com.onepiecemod.progression.CombatPaths.Haki;
import com.onepiecemod.progression.CombatPaths.Tier;
import com.onepiecemod.style.FightingStyle;
import com.onepiecemod.style.StyleAttachments;
import com.onepiecemod.style.StyleMastery;

/**
 * Picking paths at a trainer.
 *
 *   /haki paths                         show the Haki upgrade tree (anywhere)
 *   /haki train <haki> <tier> <a|b>     learn one, standing next to a Haki trainer (the [Train] buttons run this)
 *   /style paths [style]                show a style's upgrade tree (default: the style you're using)
 *   /style train <style> <tier> <a|b>   learn one, standing next to that style's master
 * Operators: /haki addxp <player> <haki> <amount>, /haki resetpaths <player>, /style addmastery <player> <style> <amount>.
 *
 * Sneak + right-click Hancock or Shanks to see the Haki tree. Rayleigh shows it after his lesson,
 * and a style master shows their style's tree when you sneak + right-click them after learning it.
 */
public final class PathTraining {
	private PathTraining() {
	}

	/** How close (in blocks) a trainer has to be. */
	private static final double TRAINER_RANGE = 12;
	private static final Set<String> HAKI_TRAINERS_ALL = Set.of("rayleigh", "shanks");
	private static final Set<String> HAKI_TRAINERS_BASIC = Set.of("hancock");

	public static void initialize() {
		CombatPaths.initialize();

		CommandRegistrationCallback.EVENT.register((dispatcher, registryAccess, environment) -> {
			dispatcher.register(Commands.literal("haki")
					.then(Commands.literal("paths").executes(context -> {
						showHaki(context.getSource().getPlayerOrException());
						return 1;
					}))
					.then(Commands.literal("train")
							.then(Commands.argument("haki", StringArgumentType.word())
									.suggests((context, builder) -> {
										for (Haki haki : Haki.values()) {
											builder.suggest(haki.id());
										}
										return builder.buildFuture();
									})
									.then(Commands.argument("tier", IntegerArgumentType.integer(1, 3))
											.then(Commands.argument("path", StringArgumentType.word())
													.executes(PathTraining::trainHaki)))))
					// Operator helpers for testing and servers: add Haki training, clear someone's paths.
					.then(Commands.literal("addxp")
							.requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
							.then(Commands.argument("player", EntityArgument.player())
									.then(Commands.argument("haki", StringArgumentType.word())
											.suggests((context, builder) -> {
												for (Haki haki : Haki.values()) {
													builder.suggest(haki.id());
												}
												return builder.buildFuture();
											})
											.then(Commands.argument("amount", IntegerArgumentType.integer(1))
													.executes(PathTraining::addHakiXp)))))
					.then(Commands.literal("resetpaths")
							.requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
							.then(Commands.argument("player", EntityArgument.player()).executes(context -> {
								ServerPlayer target = EntityArgument.getPlayer(context, "player");
								target.removeAttached(CombatPaths.PATHS);
								context.getSource().sendSuccess(() -> Component.literal("Cleared " + target.getName().getString()
										+ "'s Haki and style paths."), true);
								return 1;
							}))));
			dispatcher.register(Commands.literal("style")
					.then(Commands.literal("paths")
							.executes(context -> {
								ServerPlayer player = context.getSource().getPlayerOrException();
								FightingStyle active = StyleAttachments.active(player);
								if (active == null) {
									fail(player, "You don't know a fighting style yet. Type /style to see how to learn one.");
									return 0;
								}
								showStyle(player, active);
								return 1;
							})
							.then(Commands.argument("style", StringArgumentType.word())
									.suggests((context, builder) -> {
										for (FightingStyle style : FightingStyle.values()) {
											builder.suggest(style.id());
										}
										return builder.buildFuture();
									})
									.executes(context -> {
										ServerPlayer player = context.getSource().getPlayerOrException();
										FightingStyle style = FightingStyle.byId(StringArgumentType.getString(context, "style"));
										if (style == null) {
											fail(player, "That's not a style. Type /style to see them all.");
											return 0;
										}
										showStyle(player, style);
										return 1;
									})))
					.then(Commands.literal("train")
							.then(Commands.argument("style", StringArgumentType.word())
									.then(Commands.argument("tier", IntegerArgumentType.integer(1, 3))
											.then(Commands.argument("path", StringArgumentType.word())
													.executes(PathTraining::trainStyle)))))
					.then(Commands.literal("addmastery")
							.requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
							.then(Commands.argument("player", EntityArgument.player())
									.then(Commands.argument("style", StringArgumentType.word())
											.then(Commands.argument("amount", IntegerArgumentType.integer(1))
													.executes(context -> {
														ServerPlayer target = EntityArgument.getPlayer(context, "player");
														FightingStyle style = FightingStyle.byId(StringArgumentType.getString(context, "style"));
														if (style == null) {
															context.getSource().sendFailure(Component.literal("No such style."));
															return 0;
														}
														StyleMastery.add(target, style, IntegerArgumentType.getInteger(context, "amount"));
														return 1;
													}))))));
		});

		// Hancock and Shanks show the Haki tree when you sneak + right-click them (Rayleigh does it after his lesson).
		UseEntityCallback.EVENT.register((player, level, hand, entity, hitResult) -> {
			if (hand != InteractionHand.MAIN_HAND || !player.isShiftKeyDown()
					|| !(entity instanceof CharacterEntity trainer) || trainer.isBoss()) {
				return InteractionResult.PASS;
			}
			String id = trainer.getCharacterId();
			if (!"hancock".equals(id) && !"shanks".equals(id)) {
				return InteractionResult.PASS;
			}
			if (player instanceof ServerPlayer serverPlayer) {
				say(serverPlayer, trainer.getData().name, "shanks".equals(id)
						? "So you want to sharpen your will? Pick your own path. Nobody can walk it for you."
						: "Hmph. Kuja warriors train Haki from birth. Choose how you'll fight, and don't waste my time.");
				showHaki(serverPlayer);
			}
			return InteractionResult.SUCCESS;
		});
	}

	private static int addHakiXp(CommandContext<CommandSourceStack> context) throws CommandSyntaxException {
		ServerPlayer target = EntityArgument.getPlayer(context, "player");
		Haki haki = Haki.byId(StringArgumentType.getString(context, "haki"));
		int amount = IntegerArgumentType.getInteger(context, "amount");
		if (haki == null) {
			context.getSource().sendFailure(Component.literal("Use observation, armament or conqueror."));
			return 0;
		}
		switch (haki) {
			case OBSERVATION -> HakiPowers.addObservationXp(target, amount);
			case ARMAMENT -> HakiPowers.addArmamentXp(target, amount);
			case CONQUEROR -> {
				if (!HakiAttachments.get(target).conqueror()) {
					HakiAttachments.set(target, HakiAttachments.get(target).withConqueror(true));
				}
				HakiPowers.addConquerorXp(target, amount);
			}
		}
		context.getSource().sendSuccess(() -> Component.literal("Gave " + target.getName().getString() + " "
				+ haki.title() + " training (now level " + haki.level(target) + ")."), true);
		return 1;
	}

	// ---- Menus ----

	public static void showHaki(ServerPlayer player) {
		player.sendSystemMessage(Component.literal("=== Haki Paths ===").withStyle(ChatFormatting.GOLD, ChatFormatting.BOLD));
		player.sendSystemMessage(Component.literal("Pick one upgrade per tier. Trainers: Rayleigh and Shanks (all), Boa Hancock (Observation, Armament).")
				.withStyle(ChatFormatting.GRAY));
		for (Haki haki : Haki.values()) {
			int level = haki.level(player);
			if (haki == Haki.CONQUEROR && level == 0) {
				player.sendSystemMessage(Component.literal(haki.title() + ": not awakened.").withStyle(ChatFormatting.DARK_GRAY));
				continue;
			}
			player.sendSystemMessage(Component.literal(haki.title() + " (level " + level + ")").withStyle(ChatFormatting.AQUA));
			for (Tier tier : haki.tiers()) {
				showTier(player, tier, haki.key(tier.number()), level, "level",
						"/haki train " + haki.id() + " " + tier.number() + " ");
			}
		}
	}

	public static void showStyle(ServerPlayer player, FightingStyle style) {
		player.sendSystemMessage(Component.literal("=== " + style.title() + " Paths ===").withStyle(ChatFormatting.GOLD, ChatFormatting.BOLD));
		if (!StyleAttachments.knows(player, style)) {
			player.sendSystemMessage(Component.literal("You haven't learned this style yet.").withStyle(ChatFormatting.GRAY));
			return;
		}
		int mastery = CombatPaths.styleLevel(player, style);
		player.sendSystemMessage(Component.literal("Mastery " + mastery + ". Train with " + capitalize(style.master())
				+ ". Pick one upgrade per tier.").withStyle(ChatFormatting.GRAY));
		for (Tier tier : CombatPaths.styleTiers(style)) {
			showTier(player, tier, CombatPaths.styleKey(style, tier.number()), mastery, "mastery",
					"/style train " + style.id() + " " + tier.number() + " ");
		}
	}

	private static void showTier(ServerPlayer player, Tier tier, String key, int level, String levelWord, String command) {
		String chosen = CombatPaths.chosen(player, key);
		boolean open = level >= tier.levelNeeded() && CombatPaths.bossBeaten(player, tier.bossNeeded());
		String needs = levelWord + " " + tier.levelNeeded() + ", " + tier.berries() + " Berries"
				+ (tier.bossNeeded() == null ? "" : ", beat " + capitalize(tier.bossNeeded()));
		player.sendSystemMessage(Component.literal(" Tier " + tier.number() + " (" + needs + ")" + (open ? "" : ": locked"))
				.withStyle(open ? ChatFormatting.WHITE : ChatFormatting.DARK_GRAY));
		for (String letter : new String[] {"a", "b"}) {
			Choice choice = tier.choice(letter);
			MutableComponent line = Component.literal("   ");
			if (letter.equals(chosen)) {
				line.append(Component.literal("[Chosen] ").withStyle(ChatFormatting.GREEN, ChatFormatting.BOLD));
			} else if (open) {
				String label = chosen == null ? "[Train] " : "[Switch] ";
				line.append(Component.literal(label).withStyle(style -> style.withColor(ChatFormatting.YELLOW).withBold(true)
						.withClickEvent(new ClickEvent.RunCommand(command + letter))
						.withHoverEvent(new HoverEvent.ShowText(Component.literal("Click to learn " + choice.name()
								+ " for " + tier.berries() + " Berries (trainer must be nearby)")))));
			} else {
				line.append(Component.literal("[Locked] ").withStyle(ChatFormatting.DARK_GRAY));
			}
			line.append(Component.literal(choice.name() + ": ").withStyle(letter.equals(chosen) ? ChatFormatting.GREEN : ChatFormatting.WHITE));
			line.append(Component.literal(choice.effect()).withStyle(ChatFormatting.GRAY));
			player.sendSystemMessage(line);
		}
	}

	// ---- Training ----

	private static int trainHaki(CommandContext<CommandSourceStack> context) throws CommandSyntaxException {
		ServerPlayer player = context.getSource().getPlayerOrException();
		Haki haki = Haki.byId(StringArgumentType.getString(context, "haki"));
		int number = IntegerArgumentType.getInteger(context, "tier");
		String letter = StringArgumentType.getString(context, "path").toLowerCase();
		if (haki == null || number > haki.tiers().size() || !(letter.equals("a") || letter.equals("b"))) {
			fail(player, "No such path. Type /haki paths to see them.");
			return 0;
		}
		Tier tier = haki.tiers().get(number - 1);
		CharacterEntity trainer = nearbyTrainer(player, id -> HAKI_TRAINERS_ALL.contains(id)
				|| (haki != Haki.CONQUEROR && HAKI_TRAINERS_BASIC.contains(id)));
		if (trainer == null && !player.isCreative()) {
			fail(player, haki == Haki.CONQUEROR
					? "You need a trainer for that: find Rayleigh or Shanks (their Vivre Cards point the way)."
					: "You need a trainer for that: find Rayleigh, Shanks or Boa Hancock (their Vivre Cards point the way).");
			return 0;
		}
		if (haki == Haki.CONQUEROR && haki.level(player) == 0) {
			fail(player, "You don't have Conqueror's Haki.");
			return 0;
		}
		boolean done = train(player, tier, haki.key(number), number > 1 ? haki.key(number - 1) : null,
				haki.level(player), haki.title() + " level", letter);
		if (done) {
			if (trainer != null) {
				say(player, trainer.getData().name, "Good. Now go use it in a real fight.");
			}
			com.onepiecemod.anim.CombatAnims.play(player, com.onepiecemod.anim.Anim.POWER_UP);
		}
		return done ? 1 : 0;
	}

	private static int trainStyle(CommandContext<CommandSourceStack> context) throws CommandSyntaxException {
		ServerPlayer player = context.getSource().getPlayerOrException();
		FightingStyle style = FightingStyle.byId(StringArgumentType.getString(context, "style"));
		int number = IntegerArgumentType.getInteger(context, "tier");
		String letter = StringArgumentType.getString(context, "path").toLowerCase();
		if (style == null || !(letter.equals("a") || letter.equals("b"))) {
			fail(player, "No such path. Type /style paths to see them.");
			return 0;
		}
		if (!StyleAttachments.knows(player, style)) {
			fail(player, "Learn " + style.title() + " first.");
			return 0;
		}
		CharacterEntity trainer = nearbyTrainer(player, id -> id.equals(style.master()));
		if (trainer == null && !player.isCreative()) {
			fail(player, "Only " + capitalize(style.master()) + " can train you in " + style.title()
					+ ". Find them (their Vivre Card points the way).");
			return 0;
		}
		Tier tier = CombatPaths.styleTiers(style).get(number - 1);
		boolean done = train(player, tier, CombatPaths.styleKey(style, number),
				number > 1 ? CombatPaths.styleKey(style, number - 1) : null,
				CombatPaths.styleLevel(player, style), style.title() + " mastery", letter);
		if (done && trainer != null) {
			say(player, trainer.getData().name, "That's your own way of fighting now. Polish it.");
		}
		return done ? 1 : 0;
	}

	/** Checks the requirements, takes the Berries and saves the choice. Creative skips the checks. */
	private static boolean train(ServerPlayer player, Tier tier, String key, String previousKey, int level,
			String levelName, String letter) {
		String chosen = CombatPaths.chosen(player, key);
		Choice choice = tier.choice(letter);
		if (letter.equals(chosen)) {
			fail(player, "You already walk the path of " + choice.name() + ".");
			return false;
		}
		boolean free = player.isCreative();
		if (!free) {
			if (level < tier.levelNeeded()) {
				fail(player, "Tier " + tier.number() + " needs " + levelName + " " + tier.levelNeeded() + " (you have " + level + ").");
				return false;
			}
			if (!CombatPaths.bossBeaten(player, tier.bossNeeded())) {
				fail(player, "Tier " + tier.number() + " opens after you beat " + capitalize(tier.bossNeeded()) + ".");
				return false;
			}
			if (previousKey != null && CombatPaths.chosen(player, previousKey) == null) {
				fail(player, "Pick a tier " + (tier.number() - 1) + " upgrade first.");
				return false;
			}
			Inventory inventory = player.getInventory();
			int berries = inventory.countItem(CharacterFeature.BERRY);
			if (berries < tier.berries()) {
				fail(player, "Training costs " + tier.berries() + " Berries (you have " + berries + ").");
				return false;
			}
			take(inventory, tier.berries());
		}
		CombatPaths.set(player, key, letter);
		player.sendSystemMessage(Component.literal((chosen == null ? "Learned " : "Switched to ") + choice.name() + "!")
				.withStyle(ChatFormatting.GOLD, ChatFormatting.BOLD));
		player.sendSystemMessage(Component.literal(choice.effect()).withStyle(ChatFormatting.YELLOW));
		player.level().playSound(null, player.getX(), player.getY(), player.getZ(), SoundEvents.PLAYER_LEVELUP,
				SoundSource.PLAYERS, 0.8f, 0.8f);
		return true;
	}

	// ---- Helpers ----

	private static CharacterEntity nearbyTrainer(ServerPlayer player, java.util.function.Predicate<String> isTrainer) {
		List<CharacterEntity> near = player.level().getEntitiesOfClass(CharacterEntity.class,
				player.getBoundingBox().inflate(TRAINER_RANGE),
				character -> character.isAlive() && !character.isBoss() && isTrainer.test(character.getCharacterId()));
		return near.isEmpty() ? null : near.get(0);
	}

	private static void take(Inventory inventory, int amount) {
		for (int i = 0; i < inventory.getContainerSize() && amount > 0; i++) {
			ItemStack stack = inventory.getItem(i);
			if (stack.is(CharacterFeature.BERRY)) {
				int taken = Math.min(amount, stack.getCount());
				stack.shrink(taken);
				amount -= taken;
			}
		}
		inventory.setChanged();
	}

	private static void say(ServerPlayer player, String name, String text) {
		player.sendSystemMessage(Component.literal("<" + name + "> " + text));
	}

	private static void fail(ServerPlayer player, String text) {
		player.sendSystemMessage(Component.literal(text).withStyle(ChatFormatting.RED));
	}

	private static String capitalize(String id) {
		String spaced = id.replace('_', ' ');
		return Character.toUpperCase(spaced.charAt(0)) + spaced.substring(1);
	}
}

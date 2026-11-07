package com.onepiecemod.endgame;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

import it.unimi.dsi.fastutil.ints.IntArrayList;
import it.unimi.dsi.fastutil.ints.IntList;

import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.core.component.DataComponents;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ClientboundSetSubtitleTextPacket;
import net.minecraft.network.protocol.game.ClientboundSetTitleTextPacket;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.RandomSource;
import net.minecraft.world.entity.projectile.FireworkRocketEntity;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.component.FireworkExplosion;
import net.minecraft.world.item.component.Fireworks;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.Vec3;

import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;

import com.onepiecemod.character.CharacterEntity;
import com.onepiecemod.character.CharacterFeature;
import com.onepiecemod.sound.ModSounds;
import com.onepiecemod.story.StoryProgress;
import com.onepiecemod.worldevent.WorldNews;

/**
 * The Laugh Tale finale. Once a player finishes the story (talks to Roger at Laugh Tale), a short scene plays:
 * Roger tells the story of the Void Century, the ground shakes and Joy Boy's treasure chest rises out of the island,
 * then the title, fireworks, a world-wide headline and the Raid Den Den Mushi. One Minecraft day later the World Government
 * strikes back with the Final War raid, wherever the player is (as soon as they stand on dry land in the Overworld).
 */
public class Finale {
	private static final int CHECK_EVERY = 40;
	/** How long after the finale the Final War comes. */
	private static final long FINAL_WAR_DELAY = 24000L;
	/** A warning this long before the Final War. */
	private static final long WARNING = 1200L;
	/** Players watching the finale scene, and how many ticks into it they are. */
	private static final Map<UUID, Integer> SCENES = new HashMap<>();
	private static final int SCENE_END = 20 * 22;

	public static void initialize() {
		// No Marine hunts, Navy raids or bounty hunters during the finale scene or in the minute before the Final War.
		// Imu, the final boss: every win drops another Joy Boy's Treasure Chest and Imu's Wanted Poster, so you can fight again.
		net.fabricmc.fabric.api.entity.event.v1.ServerLivingEntityEvents.AFTER_DEATH.register((entity, source) -> {
			if (entity instanceof CharacterEntity boss && boss.isBoss() && boss.getCharacterId().equals("imu")
					&& source.getEntity() instanceof ServerPlayer killer && entity.level() instanceof ServerLevel level) {
				boss.spawnAtLocation(level, new ItemStack(EndgameFeature.JOY_BOY_CHEST_ITEM));
				boss.spawnAtLocation(level, com.onepiecemod.character.CharacterData.stack("onepiece:wanted_poster_imu", 1));
				killer.sendSystemMessage(Component.literal("Imu dropped a Joy Boy's Treasure Chest, and a Wanted Poster to call Imu back for a rematch.")
						.withStyle(ChatFormatting.GOLD));
			}
		});
		com.onepiecemod.bounty.NavyCalm.register(player -> SCENES.containsKey(player.getUUID()) || finalWarSoon(player));
		ServerTickEvents.END_SERVER_TICK.register(server -> {
			tickScenes(server);
			if (server.getTickCount() % CHECK_EVERY != 0) {
				return;
			}
			for (ServerPlayer player : server.getPlayerList().getPlayers()) {
				check(server, player);
			}
		});
	}

	private static void check(MinecraftServer server, ServerPlayer player) {
		StoryProgress story = StoryProgress.of(player);
		if (story == null || !story.finished()) {
			return;
		}
		EndgameData data = EndgameData.of(player);
		long now = server.overworld().getGameTime();
		if (!data.hasFlag("finale")) {
			if (!SCENES.containsKey(player.getUUID())) {
				startScene(player);
			}
			return;
		}
		if (data.hasFlag("final_war")) {
			return;
		}
		long due = data.timer("final_war");
		if (due - now <= WARNING && !data.hasFlag("final_war_warned")) {
			EndgameData.set(player, data.withFlag("final_war_warned"));
			player.sendSystemMessage(Component.literal("Your Den Den Mushi crackles: \"All ships, converge on " + player.getName().getString()
					+ ". This is the Final War.\" The Navy is almost here!").withStyle(ChatFormatting.AQUA));
			ModSounds.play(player, ModSounds.DEN_DEN_MUSHI_CALL);
			return;
		}
		if (now >= due && player.level().dimension() == Level.OVERWORLD && player.isAlive() && Raids.raidOf(player) == null
				&& !player.isCreative() && !player.isSpectator()) {
			RaidDef war = RaidDef.get("final_war");
			if (Raids.start(player, war) == null) {
				EndgameData.set(player, EndgameData.of(player).withFlag("final_war"));
				WorldNews.report(server, "FINAL WAR! The World Government sends every Admiral after " + player.getName().getString() + "!",
						ChatFormatting.AQUA);
			}
		}
	}

	private static boolean finalWarSoon(ServerPlayer player) {
		EndgameData data = EndgameData.of(player);
		return data.hasFlag("finale") && !data.hasFlag("final_war")
				&& data.timer("final_war") - player.level().getServer().overworld().getGameTime() <= WARNING;
	}

	/** Starts the finale scene. Also used by /endgame finale. Leaving mid-scene plays it again next time. */
	public static void startScene(ServerPlayer player) {
		SCENES.put(player.getUUID(), 0);
	}

	private static void tickScenes(MinecraftServer server) {
		SCENES.entrySet().removeIf(entry -> {
			ServerPlayer player = server.getPlayerList().getPlayer(entry.getKey());
			if (player == null) {
				return true;
			}
			int tick = entry.getValue();
			entry.setValue(tick + 1);
			sceneStep(server, player, tick);
			return tick >= SCENE_END;
		});
	}

	/** The scene, one beat every few seconds. */
	private static void sceneStep(MinecraftServer server, ServerPlayer player, int tick) {
		ServerLevel level = (ServerLevel) player.level();
		CharacterEntity roger = findRoger(level, player);
		if (roger != null && tick % 10 == 0) {
			roger.getLookControl().setLookAt(player);
		}
		switch (tick) {
			case 0 -> {
				player.connection.send(new ClientboundSetSubtitleTextPacket(Component.literal("The end of the Grand Line").withStyle(ChatFormatting.GRAY)));
				player.connection.send(new ClientboundSetTitleTextPacket(Component.literal("Laugh Tale").withStyle(ChatFormatting.GOLD)));
				say(player, "Roger", "Wahahaha! So you really made it. Come on, I'll show you what I found.");
			}
			case 80 -> say(player, "Roger", "Eight hundred years ago a great kingdom stood against the world. They lost, and the world erased them.");
			case 160 -> {
				say(player, "Roger", "A man named Joy Boy left a promise here. And a treasure. And the funniest joke you'll ever hear.");
				level.playSound(null, player.blockPosition(), SoundEvents.GENERIC_EXPLODE.value(), SoundSource.AMBIENT, 0.8f, 0.5f);
				level.playSound(null, player.blockPosition(), SoundEvents.BEACON_ACTIVATE, SoundSource.AMBIENT, 1.5f, 0.6f);
				player.addEffect(new net.minecraft.world.effect.MobEffectInstance(net.minecraft.world.effect.MobEffects.NAUSEA, 80, 0, false, false));
			}
			case 220 -> raiseTreasure(level, player);
			case 300 -> {
				say(player, "Roger", "...Wahahahaha! See? Now you know too. I can't stop laughing!");
				if (roger != null) {
					com.onepiecemod.anim.CombatAnims.play(roger, com.onepiecemod.anim.Anim.POWER_UP);
				}
			}
			case SCENE_END -> play(server, player);
			default -> {
			}
		}
		if (tick > 160 && tick < 220 && tick % 5 == 0) {
			Vec3 at = treasureSpot(player);
			level.sendParticles(ParticleTypes.CAMPFIRE_COSY_SMOKE, at.x, at.y + 0.2, at.z, 4, 0.6, 0.1, 0.6, 0.01);
			level.sendParticles(ParticleTypes.END_ROD, at.x, at.y + 0.5, at.z, 3, 0.4, 0.6, 0.4, 0.02);
		}
	}

	private static void say(ServerPlayer player, String who, String line) {
		player.sendSystemMessage(Component.literal(who + ": ").withStyle(ChatFormatting.GOLD)
				.append(Component.literal(line).withStyle(ChatFormatting.ITALIC, ChatFormatting.WHITE)));
	}

	private static CharacterEntity findRoger(ServerLevel level, ServerPlayer player) {
		List<CharacterEntity> found = level.getEntitiesOfClass(CharacterEntity.class, player.getBoundingBox().inflate(24),
				character -> !character.isBoss() && character.getCharacterId().equals("roger"));
		return found.isEmpty() ? null : found.get(0);
	}

	/** Three blocks in front of the player, on the ground. */
	private static Vec3 treasureSpot(ServerPlayer player) {
		Direction facing = player.getDirection();
		BlockPos pos = player.blockPosition().relative(facing, 3);
		return Vec3.atBottomCenterOf(pos);
	}

	/**
	 * Joy Boy's chest: the one in the treasure room if it's close, otherwise a new one bursts out of the ground in front
	 * of the player (or, with no room for it, the treasure goes straight into their bag).
	 */
	private static void raiseTreasure(ServerLevel level, ServerPlayer player) {
		BlockPos chest = findChest(level, player.blockPosition());
		if (chest == null) {
			BlockPos front = BlockPos.containing(treasureSpot(player));
			for (BlockPos spot : List.of(front, front.above(), player.blockPosition().relative(player.getDirection().getOpposite(), 2))) {
				if (level.getBlockState(spot).canBeReplaced() && level.getFluidState(spot).isEmpty()
						&& level.getBlockState(spot.below()).isFaceSturdy(level, spot.below(), Direction.UP)) {
					level.setBlockAndUpdate(spot, EndgameFeature.JOY_BOY_CHEST.defaultBlockState()
							.setValue(JoyBoyChestBlock.FACING, player.getDirection().getOpposite()));
					chest = spot;
					break;
				}
			}
		}
		if (chest == null) {
			openTreasure(player, player.blockPosition());
			return;
		}
		level.sendParticles(ParticleTypes.TOTEM_OF_UNDYING, chest.getX() + 0.5, chest.getY() + 1, chest.getZ() + 0.5, 60, 0.6, 0.8, 0.6, 0.3);
		level.sendParticles(ParticleTypes.END_ROD, chest.getX() + 0.5, chest.getY() + 1, chest.getZ() + 0.5, 30, 0.3, 1.5, 0.3, 0.05);
		level.playSound(null, chest, SoundEvents.BEACON_POWER_SELECT, SoundSource.BLOCKS, 1.5f, 0.8f);
		say(player, "Roger", "There it is. Joy Boy's chest. Go on, open it.");
	}

	/** A Joy Boy's chest near this spot (the treasure room), or null. */
	private static BlockPos findChest(ServerLevel level, BlockPos around) {
		for (BlockPos pos : BlockPos.betweenClosed(around.offset(-16, -8, -16), around.offset(16, 8, 16))) {
			BlockState state = level.getBlockState(pos);
			if (state.is(EndgameFeature.JOY_BOY_CHEST) && state.getValue(JoyBoyChestBlock.TREASURE)) {
				return pos.immutable();
			}
		}
		return null;
	}

	/** Someone opens Joy Boy's chest: sealed until they finish the story, then the One Piece's riches, once per playthrough. */
	public static void openTreasure(ServerPlayer player, BlockPos pos) {
		ServerLevel level = (ServerLevel) player.level();
		StoryProgress story = StoryProgress.of(player);
		if (story == null || !story.finished()) {
			player.sendSystemMessage(Component.literal("The chest is sealed with an ancient lock. Only someone who has heard the whole story at Laugh Tale can open it.")
					.withStyle(ChatFormatting.GRAY, ChatFormatting.ITALIC));
			level.playSound(null, pos, SoundEvents.CHEST_LOCKED, SoundSource.BLOCKS, 1.0f, 0.8f);
			return;
		}
		EndgameData data = EndgameData.of(player);
		if (data.hasFlag("finale_treasure")) {
			player.sendSystemMessage(Component.literal("You already took your share of the One Piece. The rest waits for whoever comes next.")
					.withStyle(ChatFormatting.GRAY, ChatFormatting.ITALIC));
			return;
		}
		EndgameData.set(player, data.withFlag("finale_treasure"));
		for (ItemStack stack : List.of(
				new ItemStack(Items.GOLD_BLOCK, 32), new ItemStack(Items.DIAMOND_BLOCK, 4), new ItemStack(Items.EMERALD_BLOCK, 8),
				new ItemStack(Items.ENCHANTED_GOLDEN_APPLE, 2), new ItemStack(Items.NETHERITE_INGOT, 2), new ItemStack(Items.NETHER_STAR, 1),
				new ItemStack(CharacterFeature.BERRY, 128), new ItemStack(Items.HEART_OF_THE_SEA, 1), new ItemStack(Items.TOTEM_OF_UNDYING, 1))) {
			Raids.give(player, stack, stack.getCount());
		}
		level.sendParticles(ParticleTypes.TOTEM_OF_UNDYING, pos.getX() + 0.5, pos.getY() + 1, pos.getZ() + 0.5, 80, 0.5, 1.0, 0.5, 0.4);
		level.sendParticles(ParticleTypes.WAX_ON, pos.getX() + 0.5, pos.getY() + 1, pos.getZ() + 0.5, 40, 0.8, 0.6, 0.8, 0.1);
		level.playSound(null, pos, SoundEvents.CHEST_OPEN, SoundSource.BLOCKS, 1.0f, 0.6f);
		level.playSound(null, pos, SoundEvents.UI_TOAST_CHALLENGE_COMPLETE, SoundSource.PLAYERS, 1.0f, 1.2f);
		player.sendSystemMessage(Component.literal("The lid swings open. Gold and jewels pour into your hands. The One Piece is yours.")
				.withStyle(ChatFormatting.GOLD));
	}

	/** The end of the finale scene. */
	public static void play(MinecraftServer server, ServerPlayer player) {
		long now = server.overworld().getGameTime();
		EndgameData.set(player, EndgameData.of(player).withFlag("finale").withTimer("final_war", now + FINAL_WAR_DELAY));

		player.connection.send(new ClientboundSetSubtitleTextPacket(Component.literal("A new era begins").withStyle(ChatFormatting.YELLOW)));
		player.connection.send(new ClientboundSetTitleTextPacket(Component.literal("THE ONE PIECE").withStyle(ChatFormatting.GOLD, ChatFormatting.BOLD)));
		ServerLevel level = (ServerLevel) player.level();
		level.playSound(null, player.blockPosition(), SoundEvents.UI_TOAST_CHALLENGE_COMPLETE, SoundSource.PLAYERS, 1.5f, 0.7f);
		fireworks(level, player.blockPosition(), 10, 0xffd23f);

		for (String line : List.of(
				"Roger wipes his eyes. \"The world will want you dead now, you know. Wahahaha! Good. Let them come.\"",
				"Every Den Den Mushi in the world rings at once. Your name is on all of them.")) {
			player.sendSystemMessage(Component.literal(line).withStyle(ChatFormatting.ITALIC, ChatFormatting.GRAY));
		}
		WorldNews.report(server, player.getName().getString() + " laughed with Gol D. Roger at Laugh Tale! The Great Pirate Era is reborn.",
				ChatFormatting.GOLD);

		Raids.give(player, new ItemStack(EndgameFeature.RAID_DEN_DEN_MUSHI), 1);
		player.sendSystemMessage(Component.literal("THE ENDGAME IS OPEN").withStyle(ChatFormatting.GOLD, ChatFormatting.BOLD));
		player.sendSystemMessage(Component.literal(" - In one day the World Government strikes back: the Final War. Be ready.").withStyle(ChatFormatting.AQUA));
		player.sendSystemMessage(Component.literal(" - Your Raid Den Den Mushi calls out the Emperors' crews: beat an Emperor on Hard to open their raid.")
				.withStyle(ChatFormatting.LIGHT_PURPLE));
		player.sendSystemMessage(Component.literal(" - Read the true history on the Poneglyphs and finish the post-game to unlock New Game+. Type /endgame any time.").withStyle(ChatFormatting.DARK_RED));
	}

	/** Some fireworks around a spot. */
	public static void fireworks(ServerLevel level, BlockPos at, int count, int color) {
		RandomSource random = level.getRandom();
		FireworkExplosion.Shape[] shapes = FireworkExplosion.Shape.values();
		for (int i = 0; i < count; i++) {
			IntList colors = new IntArrayList();
			colors.add(color);
			colors.add(0xffffff);
			FireworkExplosion explosion = new FireworkExplosion(shapes[random.nextInt(shapes.length)], colors, new IntArrayList(), true, true);
			ItemStack rocket = new ItemStack(Items.FIREWORK_ROCKET);
			rocket.set(DataComponents.FIREWORKS, new Fireworks(1 + random.nextInt(3), List.of(explosion)));
			double x = at.getX() + 0.5 + random.nextInt(17) - 8;
			double z = at.getZ() + 0.5 + random.nextInt(17) - 8;
			level.addFreshEntity(new FireworkRocketEntity(level, x, at.getY() + 1, z, rocket));
		}
	}
}

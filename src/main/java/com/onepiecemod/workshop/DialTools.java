package com.onepiecemod.workshop;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;

import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.Holder;
import net.minecraft.core.component.DataComponents;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.BlockTags;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.JukeboxPlayable;
import net.minecraft.world.item.JukeboxSong;
import net.minecraft.world.item.component.CustomData;
import net.minecraft.world.item.component.ItemLore;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;

import net.fabricmc.fabric.api.entity.event.v1.ServerLivingEntityEvents;
import net.fabricmc.fabric.api.message.v1.ServerMessageEvents;

import com.onepiecemod.util.Motion;

/**
 * What the Skypiea Dials from the Dial Bench do. Each use wears the Dial down a little.
 *
 *  Tone Dial:   sneak + use to record. Say something in chat within 30 seconds and the Dial keeps it,
 *               or hold a music disc in your other hand to record its song. Use it to play it back.
 *  Jet Dial:    a far stronger Breath Dial: shoots you forward, then lets you float down.
 *  Water Dial:  puts out fire on you and around you; aimed at a block, it pours out a water source.
 *  Milky Dial:  lays a road of solid cloud ahead of you (over water and gaps too). It melts after 30 s.
 *  Eisen Dial:  puts up a wall of solid cloud in front of you. It melts after 30 s.
 *  Axe Dial:    a blade of wind that cuts everything in a line ahead.
 *  Reject Dial: use to brace for 3 seconds. Hits you take while braced go into the Dial instead.
 *               Use it again to slam the stored force into what you look at, double. It hurts you too.
 */
public class DialTools {
	public enum Kind { TONE, JET, WATER, MILKY, EISEN, AXE, REJECT }

	/** Players recording with a Tone Dial: until when (game time). */
	private static final Map<UUID, Long> RECORDING = new HashMap<>();
	/** Reject Dial: what each player has stored. */
	private static final Map<UUID, Brace> BRACES = new HashMap<>();

	private static final int RECORD_TICKS = 600;
	private static final int BRACE_TICKS = 60;
	/** Stored force fades if you don't use it within a minute. */
	private static final int STORE_TICKS = 1200;
	private static final float MAX_STORED = 40.0f;

	private static final class Brace {
		long bracedUntil;
		long expires;
		float stored;
	}

	public static void initialize() {
		// Tone Dial: the next chat message of a player who is recording goes into their Dial.
		ServerMessageEvents.CHAT_MESSAGE.register((message, sender, params) -> {
			Long until = RECORDING.remove(sender.getUUID());
			if (until == null || sender.level().getGameTime() > until) {
				return;
			}
			ItemStack dial = heldTone(sender);
			if (dial.isEmpty()) {
				return;
			}
			String text = message.signedContent();
			if (text.length() > 200) {
				text = text.substring(0, 200);
			}
			CompoundTag tag = new CompoundTag();
			tag.putString("tone_text", text);
			tag.putString("tone_by", sender.getName().getString());
			dial.set(DataComponents.CUSTOM_DATA, CustomData.of(tag));
			dial.set(DataComponents.LORE, new ItemLore(List.of(
					Component.literal("Recorded: \"" + shorten(text, 40) + "\"").withStyle(ChatFormatting.GRAY))));
			sender.sendOverlayMessage(Component.literal("Recorded into your Tone Dial.").withStyle(ChatFormatting.AQUA));
			sender.level().playSound(null, sender.blockPosition(), SoundEvents.NOTE_BLOCK_CHIME.value(), SoundSource.PLAYERS, 0.8f, 1.6f);
		});

		// Reject Dial: soak up hits while braced.
		ServerLivingEntityEvents.ALLOW_DAMAGE.register((entity, source, amount) -> {
			if (!(entity instanceof ServerPlayer player)) {
				return true;
			}
			Brace brace = BRACES.get(player.getUUID());
			long now = player.level().getGameTime();
			if (brace == null || now > brace.bracedUntil || !holding(player, WorkshopItems.REJECT_DIAL)) {
				return true;
			}
			brace.stored = Math.min(MAX_STORED, brace.stored + amount);
			brace.expires = now + STORE_TICKS;
			player.level().playSound(null, player.blockPosition(), SoundEvents.SHIELD_BLOCK.value(), SoundSource.PLAYERS, 1.0f, 0.6f);
			player.level().sendParticles(ParticleTypes.ENCHANTED_HIT, player.getX(), player.getY() + 1, player.getZ(), 10, 0.4, 0.5, 0.4, 0.1);
			player.sendOverlayMessage(Component.literal("Reject Dial stored " + Math.round(brace.stored) + " force").withStyle(ChatFormatting.GOLD));
			return false;
		});
	}

	public static class DialToolItem extends Item {
		private final Kind kind;

		public DialToolItem(Kind kind, Properties properties) {
			super(properties);
			this.kind = kind;
		}

		@Override
		public InteractionResult use(Level level, Player player, InteractionHand hand) {
			ItemStack stack = player.getItemInHand(hand);
			if (!(level instanceof ServerLevel serverLevel) || !(player instanceof ServerPlayer serverPlayer)) {
				return InteractionResult.SUCCESS;
			}
			int cooldown = switch (kind) {
				case TONE -> tone(serverLevel, serverPlayer, stack);
				case JET -> jet(serverLevel, serverPlayer);
				case WATER -> water(serverLevel, serverPlayer);
				case MILKY -> milky(serverLevel, serverPlayer);
				case EISEN -> eisen(serverLevel, serverPlayer);
				case AXE -> axe(serverLevel, serverPlayer);
				case REJECT -> reject(serverLevel, serverPlayer);
			};
			if (cooldown > 0) {
				stack.hurtAndBreak(1, player, hand);
				player.getCooldowns().addCooldown(stack, cooldown);
			}
			return InteractionResult.SUCCESS;
		}
	}

	// ---- Each Dial. They return the cooldown in ticks, or 0 if nothing happened (no wear, no cooldown). ----

	private static int tone(ServerLevel level, ServerPlayer player, ItemStack dial) {
		if (player.isShiftKeyDown()) {
			ItemStack other = player.getOffhandItem() == dial ? player.getMainHandItem() : player.getOffhandItem();
			if (other.has(DataComponents.JUKEBOX_PLAYABLE)) {
				CompoundTag tag = new CompoundTag();
				tag.putString("tone_song", BuiltInRegistries.ITEM.getKey(other.getItem()).toString());
				dial.set(DataComponents.CUSTOM_DATA, CustomData.of(tag));
				dial.set(DataComponents.LORE, new ItemLore(List.of(
						Component.literal("Recorded: ").append(other.getHoverName()).withStyle(ChatFormatting.GRAY))));
				player.sendOverlayMessage(Component.literal("Recorded the song into your Tone Dial.").withStyle(ChatFormatting.AQUA));
				level.playSound(null, player.blockPosition(), SoundEvents.NOTE_BLOCK_CHIME.value(), SoundSource.PLAYERS, 0.8f, 1.6f);
				return 0;
			}
			RECORDING.put(player.getUUID(), level.getGameTime() + RECORD_TICKS);
			player.sendOverlayMessage(Component.literal("Tone Dial is listening: say something in chat (30 s)").withStyle(ChatFormatting.AQUA));
			level.playSound(null, player.blockPosition(), SoundEvents.NOTE_BLOCK_BIT.value(), SoundSource.PLAYERS, 0.8f, 1.2f);
			return 0;
		}
		CustomData data = dial.get(DataComponents.CUSTOM_DATA);
		CompoundTag tag = data != null ? data.copyTag() : new CompoundTag();
		String text = tag.getStringOr("tone_text", "");
		String song = tag.getStringOr("tone_song", "");
		if (!text.isEmpty()) {
			Component line = Component.literal("[Tone Dial] ").withStyle(ChatFormatting.AQUA)
					.append(Component.literal(tag.getStringOr("tone_by", "?") + ": ").withStyle(ChatFormatting.WHITE))
					.append(Component.literal("\"" + text + "\"").withStyle(ChatFormatting.YELLOW));
			for (ServerPlayer near : level.players()) {
				if (near.distanceToSqr(player) <= 32 * 32) {
					near.sendSystemMessage(line);
				}
			}
			level.playSound(null, player.blockPosition(), SoundEvents.NOTE_BLOCK_CHIME.value(), SoundSource.PLAYERS, 1.0f, 1.0f);
			return 20;
		}
		if (!song.isEmpty()) {
			Optional<Holder<SoundEvent>> sound = songSound(level, song);
			if (sound.isPresent()) {
				level.playSound(null, player.getX(), player.getY(), player.getZ(), sound.get(), SoundSource.RECORDS, 2.0f, 1.0f);
				player.sendOverlayMessage(Component.literal("The Tone Dial plays its song.").withStyle(ChatFormatting.AQUA));
				return 200;
			}
		}
		player.sendOverlayMessage(Component.literal("It's empty. Sneak + use to record a message, or hold a music disc in your other hand.")
				.withStyle(ChatFormatting.GRAY));
		return 0;
	}

	private static Optional<Holder<SoundEvent>> songSound(ServerLevel level, String itemId) {
		Item item = BuiltInRegistries.ITEM.getValue(Identifier.parse(itemId));
		JukeboxPlayable playable = new ItemStack(item).get(DataComponents.JUKEBOX_PLAYABLE);
		if (playable == null) {
			return Optional.empty();
		}
		return Optional.of(playable.song().value().soundEvent());
	}

	private static int jet(ServerLevel level, ServerPlayer player) {
		Vec3 look = player.getLookAngle();
		player.setDeltaMovement(look.x * 2.6, Math.max(0.45, look.y * 2.0 + 0.35), look.z * 2.6);
		Motion.sync(player);
		player.resetFallDistance();
		player.addEffect(new MobEffectInstance(MobEffects.SLOW_FALLING, 50, 0));
		level.sendParticles(ParticleTypes.GUST_EMITTER_SMALL, player.getX(), player.getY(), player.getZ(), 1, 0, 0, 0, 0);
		level.sendParticles(ParticleTypes.CLOUD, player.getX(), player.getY(), player.getZ(), 20, 0.4, 0.2, 0.4, 0.05);
		level.playSound(null, player.blockPosition(), SoundEvents.WIND_CHARGE_BURST.value(), SoundSource.PLAYERS, 1.2f, 0.7f);
		return 80;
	}

	private static int water(ServerLevel level, ServerPlayer player) {
		player.clearFire();
		for (LivingEntity entity : level.getEntitiesOfClass(LivingEntity.class, player.getBoundingBox().inflate(5.0))) {
			entity.clearFire();
		}
		BlockPos centre = player.blockPosition();
		for (BlockPos pos : BlockPos.betweenClosed(centre.offset(-4, -2, -4), centre.offset(4, 3, 4))) {
			if (level.getBlockState(pos).is(BlockTags.FIRE)) {
				level.removeBlock(pos, false);
			}
		}
		HitResult hit = player.pick(5.0, 1.0f, false);
		if (hit instanceof BlockHitResult blockHit && hit.getType() == HitResult.Type.BLOCK) {
			BlockPos target = blockHit.getBlockPos().relative(blockHit.getDirection());
			if (level.dimension() == Level.NETHER) {
				player.sendOverlayMessage(Component.literal("The water hisses away in this heat.").withStyle(ChatFormatting.GRAY));
			} else if (level.getBlockState(target).canBeReplaced() && level.mayInteract(player, target)) {
				level.setBlockAndUpdate(target, Blocks.WATER.defaultBlockState());
			}
		}
		level.sendParticles(ParticleTypes.SPLASH, player.getX(), player.getY() + 1, player.getZ(), 60, 1.5, 0.8, 1.5, 0.2);
		level.playSound(null, player.blockPosition(), SoundEvents.BUCKET_EMPTY, SoundSource.PLAYERS, 1.0f, 1.0f);
		return 40;
	}

	private static int milky(ServerLevel level, ServerPlayer player) {
		Direction forward = player.getDirection();
		Direction side = forward.getClockWise();
		double slope = Math.max(-0.7, Math.min(0.7, player.getLookAngle().y));
		BlockPos start = player.blockPosition().below();
		int placed = 0;
		for (int i = 1; i <= 16; i++) {
			BlockPos row = start.relative(forward, i).above((int) Math.round(slope * i));
			for (int w = -1; w <= 1; w++) {
				placed += placeCloud(level, player, row.relative(side, w)) ? 1 : 0;
			}
		}
		return finishCloud(level, player, placed);
	}

	private static int eisen(ServerLevel level, ServerPlayer player) {
		Direction forward = player.getDirection();
		Direction side = forward.getClockWise();
		BlockPos base = player.blockPosition().relative(forward, 3);
		int placed = 0;
		for (int w = -2; w <= 2; w++) {
			for (int h = 0; h < 3; h++) {
				placed += placeCloud(level, player, base.relative(side, w).above(h)) ? 1 : 0;
			}
		}
		return finishCloud(level, player, placed);
	}

	private static boolean placeCloud(ServerLevel level, ServerPlayer player, BlockPos pos) {
		BlockState state = level.getBlockState(pos);
		if (!state.canBeReplaced() || !level.mayInteract(player, pos) || !level.getEntities((Entity) null, new AABB(pos)).isEmpty()) {
			return false;
		}
		level.setBlockAndUpdate(pos, WorkshopItems.MILKY_CLOUD.defaultBlockState());
		return true;
	}

	private static int finishCloud(ServerLevel level, ServerPlayer player, int placed) {
		if (placed == 0) {
			player.sendOverlayMessage(Component.literal("No room for a cloud there.").withStyle(ChatFormatting.GRAY));
			return 0;
		}
		level.sendParticles(ParticleTypes.CLOUD, player.getX(), player.getY() + 0.5, player.getZ(), 30, 1.0, 0.3, 1.0, 0.05);
		level.playSound(null, player.blockPosition(), SoundEvents.WOOL_PLACE, SoundSource.PLAYERS, 1.0f, 0.7f);
		return 100;
	}

	private static int axe(ServerLevel level, ServerPlayer player) {
		Vec3 eye = player.getEyePosition();
		Vec3 look = player.getLookAngle();
		java.util.Set<LivingEntity> hit = new java.util.HashSet<>();
		for (double d = 1.0; d <= 12.0; d += 0.5) {
			Vec3 point = eye.add(look.scale(d));
			BlockPos pos = BlockPos.containing(point);
			if (!level.getBlockState(pos).getCollisionShape(level, pos).isEmpty()) {
				break;
			}
			if (d % 1.0 == 0) {
				level.sendParticles(ParticleTypes.SWEEP_ATTACK, point.x, point.y, point.z, 1, 0, 0, 0, 0);
			}
			for (LivingEntity entity : level.getEntitiesOfClass(LivingEntity.class, new AABB(point, point).inflate(0.7))) {
				if (entity != player && entity.isAlive() && hit.add(entity)) {
					entity.hurtServer(level, player.damageSources().playerAttack(player), 9.0f);
				}
			}
		}
		level.playSound(null, player.blockPosition(), SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.PLAYERS, 1.2f, 0.6f);
		return 40;
	}

	private static int reject(ServerLevel level, ServerPlayer player) {
		long now = level.getGameTime();
		Brace brace = BRACES.computeIfAbsent(player.getUUID(), id -> new Brace());
		if (now > brace.expires) {
			brace.stored = 0;
		}
		if (brace.stored <= 0) {
			brace.bracedUntil = now + BRACE_TICKS;
			brace.expires = now + STORE_TICKS;
			player.sendOverlayMessage(Component.literal("Bracing: hits in the next 3 seconds go into the Reject Dial").withStyle(ChatFormatting.GOLD));
			level.playSound(null, player.blockPosition(), SoundEvents.ARMOR_EQUIP_IRON.value(), SoundSource.PLAYERS, 1.0f, 0.7f);
			return 0; // Bracing is free; the release wears the Dial.
		}
		LivingEntity target = lookedAt(level, player, 6.0);
		if (target == null) {
			player.sendOverlayMessage(Component.literal("Look at something within 6 blocks to release the force.").withStyle(ChatFormatting.GRAY));
			return 0;
		}
		float force = brace.stored;
		brace.stored = 0;
		brace.bracedUntil = 0;
		target.hurtServer(level, player.damageSources().playerAttack(player), force * 2.0f + 4.0f);
		Vec3 push = target.position().subtract(player.position()).normalize().scale(1.5 + force / 20.0);
		target.push(push.x, 0.4, push.z);
		Motion.sync(target);
		// Canon: the Reject Dial is so strong it hurts the one who uses it.
		player.hurtServer(level, player.damageSources().magic(), Math.max(1.0f, force * 0.4f));
		level.sendParticles(ParticleTypes.EXPLOSION, target.getX(), target.getY() + 1, target.getZ(), 2, 0.2, 0.2, 0.2, 0);
		level.playSound(null, target.blockPosition(), SoundEvents.GENERIC_EXPLODE.value(), SoundSource.PLAYERS, 1.0f, 1.3f);
		return 400;
	}

	// ---- Helpers ----

	private static LivingEntity lookedAt(ServerLevel level, ServerPlayer player, double range) {
		Vec3 eye = player.getEyePosition();
		Vec3 look = player.getLookAngle();
		LivingEntity best = null;
		double bestDistance = range;
		for (LivingEntity entity : level.getEntitiesOfClass(LivingEntity.class, player.getBoundingBox().inflate(range))) {
			if (entity == player || !entity.isAlive()) {
				continue;
			}
			Optional<Vec3> clip = entity.getBoundingBox().inflate(0.4).clip(eye, eye.add(look.scale(range)));
			if (clip.isPresent()) {
				double distance = clip.get().distanceTo(eye);
				if (distance < bestDistance && player.hasLineOfSight(entity)) {
					best = entity;
					bestDistance = distance;
				}
			}
		}
		return best;
	}

	private static boolean holding(Player player, Item item) {
		return player.getMainHandItem().is(item) || player.getOffhandItem().is(item);
	}

	private static ItemStack heldTone(Player player) {
		if (player.getMainHandItem().is(WorkshopItems.TONE_DIAL)) {
			return player.getMainHandItem();
		}
		return player.getOffhandItem().is(WorkshopItems.TONE_DIAL) ? player.getOffhandItem() : ItemStack.EMPTY;
	}

	private static String shorten(String text, int max) {
		return text.length() <= max ? text : text.substring(0, max - 3) + "...";
	}
}

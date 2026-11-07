package com.onepiecemod.power;

import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.Registries;
import net.minecraft.tags.FluidTags;
import net.minecraft.tags.TagKey;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.phys.AABB;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.ship.ShipDecks;
import com.onepiecemod.world.SeastoneEffects;
import com.onepiecemod.world.WorldBlocks;

/**
 * The one rule for "is the sea draining this Devil Fruit user right now?", used by the power key, passive powers,
 * Zoan forms, awakening, fruit bosses and bounty hunters.
 *
 * A fruit user is drained when:
 *  - they are in the sea at least waist deep (puddles, shallows and rain are fine), and not aboard a ship,
 *  - they touch Seastone: holding it, or standing on / leaning on a block in the onepiece:seastone tag,
 *  - or Seastone has sealed them for a while (cuffs, a Jitte hit, a Seastone bullet; see seal).
 */
public final class SeaWeakness {
	private SeaWeakness() {
	}

	/** Blocks made of Seastone: the Seastone Block and the Seastone Bricks set (Impel Down, Marine cells). */
	public static final TagKey<Block> SEASTONE_BLOCKS = TagKey.create(Registries.BLOCK, OnePieceMod.id("seastone"));

	/** How deep the water must be, in blocks above your feet, before the sea takes your strength. About waist high. */
	public static final double DRAIN_DEPTH = 0.8;

	public static boolean isDrained(LivingEntity entity) {
		return isInSea(entity) || isSealed(entity) || touchesSeastone(entity);
	}

	/** Waist deep or deeper in water, and not standing on (or inside) a sailing ship. */
	public static boolean isInSea(LivingEntity entity) {
		if (!entity.isInWater() || entity.getFluidHeight(FluidTags.WATER) < DRAIN_DEPTH && !entity.isUnderWater()) {
			return false;
		}
		return ShipDecks.shipOf(entity) == null;
	}

	/** Seastone keeps this fruit user sealed until the saved time runs out. */
	public static boolean isSealed(LivingEntity entity) {
		Long until = entity.getAttached(ModAttachments.SEASTONE_SEALED);
		return until != null && entity.level().getGameTime() < until;
	}

	/** Seals a fruit user's powers for this many ticks (a longer seal already in place is kept). */
	public static void seal(LivingEntity entity, int ticks) {
		long until = entity.level().getGameTime() + ticks;
		Long current = entity.getAttached(ModAttachments.SEASTONE_SEALED);
		if (current == null || current < until) {
			entity.setAttached(ModAttachments.SEASTONE_SEALED, until);
		}
	}

	public static void unseal(LivingEntity entity) {
		entity.removeAttached(ModAttachments.SEASTONE_SEALED);
	}

	/** Holding Seastone, or touching a Seastone block with your feet or body. */
	public static boolean touchesSeastone(LivingEntity entity) {
		if (isSeastoneItem(entity.getMainHandItem()) || isSeastoneItem(entity.getOffhandItem())) {
			return true;
		}
		Level level = entity.level();
		// The body's box, a hair bigger so leaning on a wall counts, and reaching down to the block underfoot.
		AABB box = entity.getBoundingBox().inflate(0.05, 0, 0.05).expandTowards(0, -0.1, 0);
		for (BlockPos pos : BlockPos.betweenClosed(BlockPos.containing(box.minX, box.minY, box.minZ),
				BlockPos.containing(box.maxX, box.maxY, box.maxZ))) {
			if (level.getBlockState(pos).is(SEASTONE_BLOCKS)) {
				return true;
			}
		}
		return false;
	}

	public static boolean isSeastoneItem(ItemStack stack) {
		return stack.is(WorldBlocks.RAW_SEASTONE) || stack.is(WorldBlocks.SEASTONE_INGOT)
				|| stack.is(WorldBlocks.SEASTONE_BLOCK.asItem()) || stack.is(WorldBlocks.SEASTONE_JITTE)
				|| stack.is(WorldBlocks.SEASTONE_CUFFS);
	}

	/** Only fruit users care. Short for SeastoneEffects.isFruitUser(entity) && isDrained(entity). */
	public static boolean drainsFruitUser(LivingEntity entity) {
		return SeastoneEffects.isFruitUser(entity) && isDrained(entity);
	}

	/** Players only: the overlay line shown when they try a move while drained. */
	public static String reason(Player player) {
		if (isInSea(player)) {
			return "The sea drains your strength. Your Devil Fruit power won't answer.";
		}
		if (isSealed(player)) {
			long seconds = Math.max(1, (player.getAttached(ModAttachments.SEASTONE_SEALED) - player.level().getGameTime() + 19) / 20);
			return "Seastone seals your power for " + seconds + " more seconds.";
		}
		return "Touching Seastone. Your Devil Fruit power won't answer.";
	}
}

package com.onepiecemod.weapon;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.function.Consumer;

import net.minecraft.ChatFormatting;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.item.component.TooltipDisplay;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;

import com.onepiecemod.anim.Anim;
import com.onepiecemod.anim.CombatAnims;

/**
 * A gun or slingshot. Right-click to fire one shot from the ammo you carry.
 *
 * Shots are instant (like a real bullet): a line goes out from your eyes and hits the first
 * creature or block in the way. Ammo in your off hand is used first, so you can pick which kind to fire.
 * In Creative mode no ammo is used up.
 *
 * Guns hold a few rounds (the magazine). When it's empty the gun reloads, which takes a moment.
 * Stop shooting for 3 seconds and it tops itself up. Hold sneak to aim: steadier shots and less kick
 * (and scoped guns zoom in, see WeaponClient). Hitting the head does 50% more damage (see Shot).
 */
public class GunItem extends Item {
	/**
	 * How a gun shoots.
	 * damage: hit points per shot (2 = one heart). cooldown: ticks between shots (20 = 1 second).
	 * range: blocks. spread: how far off-target shots can go (0 = perfect aim).
	 * burst: shots per trigger pull (the Tommy Gun fires 3). ammo: which ammo family it takes.
	 * magazine: rounds before it must reload (0 = never reloads, like a slingshot). reload: ticks a reload takes.
	 * recoil: how far (degrees) each shot kicks your view up.
	 */
	public record Stats(float damage, int cooldown, double range, float spread, int burst, Ammo.Kind ammo,
			int magazine, int reload, float recoil) {
		Stats withSpread(float newSpread) {
			return new Stats(damage, cooldown, range, newSpread, burst, ammo, magazine, reload, recoil);
		}
	}

	/** How it's held in the hands (see anim/client/Poses): one hand, both hands against the shoulder, or a slingshot. */
	public enum Hold { PISTOL, RIFLE, SLINGSHOT }

	/** Aiming (sneaking) makes shots this much steadier and kick this much less. */
	public static final float AIM_SPREAD = 0.35f;
	public static final float AIM_RECOIL = 0.5f;
	/** Ticks without shooting before a gun tops up its magazine by itself. */
	private static final int TOP_UP_AFTER = 60;

	/**
	 * Set by WeaponClient: kicks your own view when you fire. Only ever called on the client side,
	 * so it stays null on a dedicated server.
	 */
	public static volatile RecoilHook clientRecoil;

	public interface RecoilHook {
		/** degrees per round, rounds in the burst, ticks between rounds. */
		void kick(float degrees, int rounds, int ticksBetween);
	}

	private final Stats stats;
	private final Hold hold;

	public GunItem(Stats stats, Hold hold, Properties properties) {
		super(properties);
		this.stats = stats;
		this.hold = hold;
	}

	public Stats stats() {
		return stats;
	}

	public Hold hold() {
		return hold;
	}

	/** True if this gun zooms in while you aim: Senriku always, others once a Scope is fitted. */
	public boolean zooms(ItemStack stack) {
		return this == WeaponItems.SENRIKU || WeaponUpgrades.hasPart(stack, WeaponUpgrades.SCOPE);
	}

	@Override
	public InteractionResult use(Level level, Player player, InteractionHand hand) {
		ItemStack gun = player.getItemInHand(hand);
		// CONSUME, not SUCCESS: no arm swing. The shot plays a recoil animation instead (see fireOnce).
		if (!(level instanceof ServerLevel serverLevel) || !(player instanceof ServerPlayer shooter)) {
			// Your own view kicks straight away, without waiting for the server.
			RecoilHook hook = clientRecoil;
			if (hook != null && level.isClientSide() && !findAmmo(player).isEmpty()) {
				float kick = effectiveStats(gun).recoil() * (player.isShiftKeyDown() ? AIM_RECOIL : 1.0f);
				hook.kick(kick, stats.burst(), 3);
			}
			return InteractionResult.CONSUME;
		}
		Stats current = effectiveStats(gun);
		boolean aiming = shooter.isShiftKeyDown();
		long now = serverLevel.getGameTime();
		topUpIfIdle(gun, shooter, now);
		if (!fireOnce(shooter, serverLevel, current, gun, aiming)) {
			shooter.sendOverlayMessage(Component.literal("Out of ammo! " + ammoHint()).withStyle(ChatFormatting.RED));
			level.playSound(null, player.getX(), player.getY(), player.getZ(), SoundEvents.DISPENSER_FAIL, SoundSource.PLAYERS, 0.6f, 1.4f);
			return InteractionResult.FAIL;
		}
		for (int round = 1; round < stats.burst(); round++) {
			PENDING.add(new PendingShot(shooter, this, current, serverLevel.getServer().getTickCount() + round * 3, hand, aiming));
		}
		LAST_SHOT.put(shooter.getUUID(), now);
		gun.hurtAndBreak(1, player, hand.asEquipmentSlot());

		int cooldown = current.cooldown();
		if (current.magazine() > 0) {
			int left = rounds(gun, current) - stats.burst();
			if (left <= 0) {
				// Empty: reload now. The magazine is full again once the wait is over.
				gun.set(WeaponUpgrades.ROUNDS, current.magazine());
				cooldown = Math.max(cooldown, current.reload());
				level.playSound(null, player.getX(), player.getY(), player.getZ(), SoundEvents.CROSSBOW_LOADING_START.value(), SoundSource.PLAYERS, 0.8f, 0.8f);
				shooter.sendOverlayMessage(Component.literal("Reloading...").withStyle(ChatFormatting.GOLD));
				scheduleClick(shooter, serverLevel, cooldown);
			} else {
				gun.set(WeaponUpgrades.ROUNDS, left);
				showAmmo(shooter, left, current.magazine());
				if (cooldown >= 30) {
					scheduleClick(shooter, serverLevel, cooldown);
				}
			}
		} else {
			showAmmo(shooter, -1, 0);
			if (cooldown >= 30) {
				scheduleClick(shooter, serverLevel, cooldown);
			}
		}
		player.getCooldowns().addCooldown(gun, cooldown);
		return InteractionResult.CONSUME;
	}

	/** Rounds left in the magazine (a gun that hasn't been fired yet is full). */
	public static int rounds(ItemStack gun, Stats stats) {
		return Math.min(stats.magazine(), gun.getOrDefault(WeaponUpgrades.ROUNDS, stats.magazine()));
	}

	/** Stopped shooting for a while: the gun fills its magazine again. */
	private void topUpIfIdle(ItemStack gun, ServerPlayer shooter, long now) {
		Long last = LAST_SHOT.get(shooter.getUUID());
		if (stats.magazine() > 0 && gun.has(WeaponUpgrades.ROUNDS) && (last == null || now - last > TOP_UP_AFTER)) {
			gun.remove(WeaponUpgrades.ROUNDS);
		}
	}

	@Override
	public void inventoryTick(ItemStack stack, ServerLevel level, Entity owner, EquipmentSlot slot) {
		// Tops up while you hold it, with a click so you know it's full again.
		if (stats.magazine() > 0 && slot != null && slot.getType() == EquipmentSlot.Type.HAND && owner instanceof ServerPlayer player
				&& stack.has(WeaponUpgrades.ROUNDS) && !player.getCooldowns().isOnCooldown(stack)) {
			Long last = LAST_SHOT.get(player.getUUID());
			if (last == null || level.getGameTime() - last > TOP_UP_AFTER) {
				stack.remove(WeaponUpgrades.ROUNDS);
				level.playSound(null, player.getX(), player.getY(), player.getZ(), SoundEvents.CROSSBOW_LOADING_END.value(), SoundSource.PLAYERS, 0.6f, 1.3f);
			}
		}
	}

	/**
	 * This gun's stats after its parts (WeaponUpgrades) and enchantments (WeaponEnchantments).
	 */
	public Stats effectiveStats(ItemStack gun) {
		float damage = stats.damage();
		double cooldown = stats.cooldown();
		double reload = stats.reload();
		double range = stats.range();
		float spread = stats.spread();
		if (WeaponUpgrades.hasPart(gun, WeaponUpgrades.LONG_BARREL)) {
			damage += 3.0f;
		}
		if (WeaponUpgrades.hasPart(gun, WeaponUpgrades.HAIR_TRIGGER)) {
			cooldown *= 0.7;
			reload *= 0.7;
		}
		if (WeaponUpgrades.hasPart(gun, WeaponUpgrades.SCOPE)) {
			range *= 1.5;
			spread *= 0.5f;
		}
		int quickDraw = WeaponEnchantments.level(gun, WeaponEnchantments.QUICK_DRAW);
		cooldown *= 1.0 - 0.15 * quickDraw;
		reload *= 1.0 - 0.15 * quickDraw;
		int snipersEye = WeaponEnchantments.level(gun, WeaponEnchantments.SNIPERS_EYE);
		range *= 1.0 + 0.25 * snipersEye;
		spread *= Math.max(0.0f, 1.0f - 0.25f * snipersEye);
		return new Stats(damage, Math.max(4, (int) Math.round(cooldown)), range, spread, stats.burst(), stats.ammo(),
				stats.magazine(), Math.max(10, (int) Math.round(reload)), stats.recoil());
	}

	/** Same as effectiveStats(gun); kept for older callers. */
	public Stats effectiveStats(ItemStack gun, Level level) {
		return effectiveStats(gun);
	}

	/** Uses one round of ammo and fires it. False if the player has no ammo this gun takes. */
	private boolean fireOnce(ServerPlayer shooter, ServerLevel level, Stats current, ItemStack gun, boolean aiming) {
		ItemStack ammoStack = findAmmo(shooter);
		if (ammoStack.isEmpty()) {
			return false;
		}
		Ammo ammo = GunAddons.firesAs(ammoStack);
		ItemStack round = ammoStack.copyWithCount(1); // An add-on round's data, before the stack is used up.
		if (!shooter.getAbilities().instabuild) {
			ammoStack.shrink(1);
		}
		muzzleFlash(shooter, level, ammo, shooter.getOffhandItem() == gun);
		Shot.fire(shooter, level, aiming ? current.withSpread(current.spread() * AIM_SPREAD) : current, ammo, gun, round);
		CombatAnims.play(shooter, Anim.SHOOT);
		return true;
	}

	/** A puff of flame and smoke at the end of the barrel (slingshots don't have one). */
	private void muzzleFlash(ServerPlayer shooter, ServerLevel level, Ammo ammo, boolean leftHand) {
		if (hold == Hold.SLINGSHOT) {
			return;
		}
		Vec3 look = shooter.getLookAngle();
		Vec3 right = look.cross(new Vec3(0, 1, 0));
		right = right.lengthSqr() < 1.0E-4 ? Vec3.ZERO : right.normalize();
		// Far enough ahead that it doesn't fill your own screen.
		Vec3 at = shooter.getEyePosition().add(look.scale(1.8)).add(right.scale(leftHand ? -0.35 : 0.35)).add(0, -0.25, 0);
		boolean big = ammo == Ammo.CANNONBALL;
		level.sendParticles(ParticleTypes.SMALL_FLAME, at.x, at.y, at.z, big ? 3 : 1, 0.01, 0.01, 0.01, 0.0);
		level.sendParticles(big ? ParticleTypes.LARGE_SMOKE : ParticleTypes.SMOKE, at.x, at.y, at.z, big ? 3 : 1, 0.02, 0.02, 0.02, 0.01);
	}

	/** "4/6  ·  37 Bullets" above the hotbar after each shot. rounds -1 = no magazine. */
	private void showAmmo(ServerPlayer shooter, int rounds, int magazine) {
		int carried = 0;
		Inventory inventory = shooter.getInventory();
		for (int slot = 0; slot < inventory.getContainerSize(); slot++) {
			ItemStack stack = inventory.getItem(slot);
			if (fits(stack)) {
				carried += stack.getCount();
			}
		}
		String kind = switch (stats.ammo()) {
			case BULLET -> "Bullets";
			case CANNONBALL -> "Cannonballs";
			case STAR -> "Stars";
		};
		boolean creative = shooter.getAbilities().instabuild;
		String carriedText = creative ? "unlimited " + kind : carried + " " + kind;
		String text = rounds >= 0 ? rounds + "/" + magazine + "  ·  " + carriedText : carriedText;
		boolean low = !creative && carried == 0;
		shooter.sendOverlayMessage(Component.literal(text).withStyle(low ? ChatFormatting.RED : ChatFormatting.GOLD));
	}

	/** Off hand first, then the rest of the inventory. */
	private ItemStack findAmmo(Player player) {
		ItemStack offhand = player.getOffhandItem();
		if (fits(offhand)) {
			return offhand;
		}
		Inventory inventory = player.getInventory();
		for (int slot = 0; slot < inventory.getContainerSize(); slot++) {
			ItemStack stack = inventory.getItem(slot);
			if (fits(stack)) {
				return stack;
			}
		}
		return ItemStack.EMPTY;
	}

	private boolean fits(ItemStack stack) {
		Ammo ammo = GunAddons.firesAs(stack); // Add-on rounds (see GunAddons) fit the guns their base ammo fits.
		return ammo != null && ammo.kind() == stats.ammo();
	}

	private String ammoHint() {
		return switch (stats.ammo()) {
			case BULLET -> "Needs Bullets or Seastone Bullets.";
			case CANNONBALL -> "Needs Cannonballs.";
			case STAR -> "Needs Lead Stars, Exploding Stars, Tabasco Stars or Pop Greens.";
		};
	}

	@Override
	public void appendHoverText(ItemStack stack, TooltipContext context, TooltipDisplay displayComponent, Consumer<Component> textConsumer, TooltipFlag type) {
		// The numbers include this gun's parts and enchantments.
		Stats current = effectiveStats(stack);
		textConsumer.accept(Component.literal(String.format("%.0f damage, %.1fs between shots, %.0f block range",
				current.damage(), current.cooldown() / 20.0, current.range())).withStyle(ChatFormatting.GRAY));
		if (current.burst() > 1) {
			textConsumer.accept(Component.literal("Fires " + current.burst() + " rounds per pull").withStyle(ChatFormatting.GRAY));
		}
		if (current.magazine() > 0) {
			textConsumer.accept(Component.literal(String.format("Holds %d rounds, %.1fs reload", current.magazine(), current.reload() / 20.0))
					.withStyle(ChatFormatting.GRAY));
		}
		textConsumer.accept(Component.literal(zooms(stack) ? "Sneak to aim and zoom in" : "Sneak to aim").withStyle(ChatFormatting.DARK_GRAY));
		textConsumer.accept(Component.literal(ammoHint()).withStyle(ChatFormatting.DARK_GRAY));
		WeaponUpgrades.describe(stack).forEach(textConsumer);
	}

	// ---- Bursts and reload clicks: things that happen a few ticks after the trigger pull ----

	private record PendingShot(ServerPlayer shooter, GunItem gun, Stats stats, int atTick, InteractionHand hand, boolean aiming) {}

	private record PendingClick(ServerPlayer shooter, int atTick) {}

	private static final List<PendingShot> PENDING = new ArrayList<>();
	private static final List<PendingClick> CLICKS = new ArrayList<>();
	/** Game time of each player's last shot, for the 3-second top-up. */
	private static final Map<UUID, Long> LAST_SHOT = new HashMap<>();

	/** A soft click when the gun is ready again, so you hear the reload finish. */
	private static void scheduleClick(ServerPlayer shooter, ServerLevel level, int ticks) {
		CLICKS.add(new PendingClick(shooter, level.getServer().getTickCount() + ticks));
	}

	/** Called every server tick by WeaponFeature. */
	static void tickBursts(MinecraftServer server) {
		int now = server.getTickCount();
		if (!CLICKS.isEmpty()) {
			CLICKS.removeIf(click -> {
				if (click.atTick() > now) {
					return false;
				}
				ServerPlayer p = click.shooter();
				if (p.isAlive() && !p.hasDisconnected()) {
					p.level().playSound(null, p.getX(), p.getY(), p.getZ(), SoundEvents.CROSSBOW_LOADING_END.value(), SoundSource.PLAYERS, 0.6f, 1.3f);
				}
				return true;
			});
		}
		if (now % 1200 == 0) {
			LAST_SHOT.keySet().removeIf(id -> server.getPlayerList().getPlayer(id) == null);
		}
		if (PENDING.isEmpty()) {
			return;
		}
		for (PendingShot shot : new ArrayList<>(PENDING)) {
			if (shot.atTick() > now) {
				continue;
			}
			PENDING.remove(shot);
			ServerPlayer shooter = shot.shooter();
			ItemStack held = shooter.getItemInHand(shot.hand());
			// Stop the burst if the shooter died, left, or put the gun away.
			if (shooter.isAlive() && !shooter.hasDisconnected() && held.is(shot.gun())
					&& shooter.level() instanceof ServerLevel level) {
				shot.gun().fireOnce(shooter, level, shot.stats(), held, shot.aiming());
			}
		}
	}
}

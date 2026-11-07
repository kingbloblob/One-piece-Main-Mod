package com.onepiecemod.anim.client;

import java.util.HashMap;
import java.util.Map;
import java.util.Set;

import net.minecraft.client.renderer.entity.state.HumanoidRenderState;
import net.minecraft.client.renderer.entity.state.LivingEntityRenderState;
import net.minecraft.tags.ItemTags;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;

import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayConnectionEvents;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;
import net.fabricmc.fabric.api.client.rendering.v1.FabricRenderState;
import net.fabricmc.fabric.api.client.rendering.v1.RenderStateDataKey;

import com.onepiecemod.anim.Anim;
import com.onepiecemod.anim.CombatAnims;
import com.onepiecemod.character.CharacterEntity;
import com.onepiecemod.npc.CombatStyle;
import com.onepiecemod.npc.HumanNpc;
import com.onepiecemod.weapon.GunItem;
import com.onepiecemod.weapon.WeaponItems;

/**
 * The player's-game side of custom animations. It remembers which animation each entity is playing
 * (sent by the server, see CombatAnims), works out plain melee swings itself (a sword swing becomes a slash,
 * a chop or a stab; a bare-handed swing a punch), and hands all that to the model each frame (see Poses).
 *
 * Only players and this mod's own mobs are animated; vanilla zombies and skeletons are left alone.
 */
public final class AnimClient {
	/** What the model needs to know this frame. Set on the render state by LivingEntityRendererAnimMixin. */
	public record Frame(Anim anim, float progress, Anim melee, float hurt, Stance stance, Idle idle, GunItem.Hold gun, float aim) {
	}

	/** How a mob holds itself while it's fighting. */
	public enum Stance { NONE, FISTS, SWORD }

	/** How a mob stands around when there's nothing to fight. */
	public enum Idle { NONE, ARMS_CROSSED, HANDS_ON_HIPS, SWORD_ON_SHOULDER }

	public static final RenderStateDataKey<Frame> KEY = RenderStateDataKey.create(() -> "onepiece:anim");

	/** Characters who fight with their feet, never their fists. */
	private static final Set<String> KICKERS = Set.of("sanji", "zeff", "bon_clay", "jabra", "kalifa");

	private static final class Track {
		Anim anim;
		float start;
		int ticks;
		int swings;
		boolean wasSwinging;
		float lastShot = -1000;
		float aim;
		float aimTime;
	}

	/** How long (ticks) a player keeps aiming after a shot. */
	private static final float AIM_AFTER_SHOT = 40;

	private static final Map<Integer, Track> TRACKS = new HashMap<>();

	private AnimClient() {
	}

	/** OnePieceModClient calls this once. */
	public static void initialize() {
		ClientPlayNetworking.registerGlobalReceiver(CombatAnims.Play.TYPE, (payload, context) -> {
			Anim anim = Anim.byId(payload.anim());
			Entity entity = context.client().level == null ? null : context.client().level.getEntity(payload.entityId());
			if (anim != null && entity instanceof LivingEntity) {
				Track track = TRACKS.computeIfAbsent(entity.getId(), id -> new Track());
				track.anim = anim;
				track.start = entity.tickCount;
				track.ticks = payload.ticks();
				if (anim == Anim.SHOOT) {
					track.lastShot = entity.tickCount;
				}
			}
		});
		ClientPlayConnectionEvents.DISCONNECT.register((handler, client) -> TRACKS.clear());
		// Forget entities that are gone, every few seconds.
		ClientTickEvents.END_CLIENT_TICK.register(client -> {
			if (client.level != null && client.level.getGameTime() % 100 == 0) {
				TRACKS.keySet().removeIf(id -> client.level.getEntity(id) == null);
			}
		});
	}

	/** Ticks since this entity last fired a gun (big if never). The first-person recoil uses it. */
	public static float ticksSinceShot(Entity entity, float partialTick) {
		Track track = TRACKS.get(entity.getId());
		return track == null ? 1000 : entity.tickCount + partialTick - track.lastShot;
	}

	/** Called while Minecraft gathers what it needs to draw an entity this frame. */
	public static void extract(LivingEntity entity, LivingEntityRenderState state, float partialTick) {
		if (!(state instanceof HumanoidRenderState) || !animated(entity)) {
			return;
		}
		Track track = TRACKS.computeIfAbsent(entity.getId(), id -> new Track());

		Anim anim = null;
		float progress = 0;
		if (track.anim != null) {
			progress = (entity.tickCount + partialTick - track.start) / track.ticks;
			if (progress >= 1 || progress < 0 || entity.isDeadOrDying()) {
				track.anim = null;
			} else {
				anim = track.anim;
			}
		}

		boolean swinging = entity.isSwinging();
		if (swinging && !track.wasSwinging) {
			track.swings++;
		}
		track.wasSwinging = swinging;

		float hurt = 0;
		if (entity.hurtTime > 0 && !entity.isDeadOrDying()) {
			hurt = Math.max(0, Math.min(1, (entity.hurtTime - partialTick) / Math.max(1, entity.hurtDuration)));
		}

		Stance stance = Stance.NONE;
		Idle idle = Idle.NONE;
		if (entity instanceof Mob mob && !(entity instanceof Player)) {
			ItemStack main = mob.getMainHandItem();
			if (mob.isAggressive()) {
				stance = isBlade(main) || bigWeapon(main, 0) != null ? Stance.SWORD : main.isEmpty() ? Stance.FISTS : Stance.NONE;
			} else if (entity instanceof CharacterEntity) {
				// Each character always picks the same idle pose, so they look like themselves.
				if (isBlade(main)) {
					idle = (entity.getUUID().hashCode() & 1) == 0 ? Idle.SWORD_ON_SHOULDER : Idle.NONE;
				} else if (main.isEmpty() && mob.getOffhandItem().isEmpty()) {
					idle = switch (Math.floorMod(entity.getUUID().hashCode(), 3)) {
						case 0 -> Idle.ARMS_CROSSED;
						case 1 -> Idle.HANDS_ON_HIPS;
						default -> Idle.NONE;
					};
				}
			}
		}

		// Guns: held like a gun, raised to aim while a mob fights, while a player sneaks, or for a moment after a shot.
		GunItem.Hold gun = entity.getMainHandItem().getItem() instanceof GunItem item ? item.hold() : null;
		float aim = 0;
		if (gun != null) {
			float now = entity.tickCount + partialTick;
			boolean aiming = entity instanceof Mob mob && !(entity instanceof Player) ? mob.isAggressive()
					: now - track.lastShot < AIM_AFTER_SHOT || entity.isShiftKeyDown(); // sneaking = aiming
			// Raise or lower the gun smoothly, over about 4 ticks.
			float step = Math.max(0, Math.min(1, (now - track.aimTime) / 4));
			track.aim = Math.max(0, Math.min(1, track.aim + (aiming ? step : -step)));
			track.aimTime = now;
			aim = track.aim;
		}

		((FabricRenderState) state).setData(KEY, new Frame(anim, progress, melee(entity, track.swings), hurt, stance, idle, gun, aim));
	}

	/** Players and this mod's own person-shaped mobs. */
	private static boolean animated(LivingEntity entity) {
		return entity instanceof Player || entity.getClass().getName().startsWith("com.onepiecemod.");
	}

	private static boolean isBlade(ItemStack stack) {
		return !stack.isEmpty() && stack.is(ItemTags.SWORDS);
	}

	/**
	 * The mod's big non-sword weapons swing their own way: Kaido's club smashes down, polearms sweep
	 * and stab, staffs swat and jab, claws and hooks rake. Null for anything else.
	 */
	private static Anim bigWeapon(ItemStack main, int swings) {
		if (main.is(WeaponItems.HASSAIKAI)) {
			return swings % 2 == 0 ? Anim.CHOP : Anim.GROUND_SLAM;
		}
		if (main.is(WeaponItems.MURAKUMOGIRI) || main.is(WeaponItems.MOGURA)) {
			return switch (swings % 3) {
				case 0 -> Anim.SPIN_SLASH;
				case 1 -> Anim.THRUST;
				default -> Anim.CHOP;
			};
		}
		if (main.is(WeaponItems.NONOSAMA_BO) || main.is(WeaponItems.SORCERY_CLIMA_TACT)) {
			return swings % 2 == 0 ? Anim.SLASH : Anim.THRUST;
		}
		if (main.is(WeaponItems.PUNISHER) || main.is(WeaponItems.NEKO_NO_TE)) {
			return swings % 2 == 0 ? Anim.CLAW : Anim.CROSS_SLASH;
		}
		if (main.is(WeaponItems.GOLDEN_HOOK)) {
			return swings % 2 == 0 ? Anim.CLAW : Anim.SLASH;
		}
		return null;
	}

	/** Which animation a plain melee swing turns into. Null keeps Minecraft's own arm swing (tools, blocks, guns). */
	private static Anim melee(LivingEntity entity, int swings) {
		ItemStack main = entity.getMainHandItem();
		if (isBlade(main)) {
			return switch (swings % 3) {
				case 0 -> Anim.SLASH;
				case 1 -> Anim.CHOP;
				default -> Anim.THRUST;
			};
		}
		Anim heavy = bigWeapon(main, swings);
		if (heavy != null) {
			return heavy;
		}
		if (main.is(ItemTags.AXES)) {
			return Anim.CHOP;
		}
		if (!main.isEmpty()) {
			return null;
		}
		boolean kicker = entity instanceof CharacterEntity character && KICKERS.contains(character.getCharacterId())
				|| entity instanceof com.onepiecemod.crew.CrewmateEntity crewmate && crewmate.getRole() == com.onepiecemod.crew.CrewRole.COOK;
		if (kicker) {
			return swings % 3 == 2 ? Anim.SPIN_KICK : Anim.KICK;
		}
		if (entity instanceof HumanNpc npc && npc.getStyle() == CombatStyle.HEAVY) {
			return swings % 2 == 0 ? Anim.CHOP : Anim.UPPERCUT;
		}
		return switch (swings % 4) {
			case 0, 2 -> Anim.PUNCH;
			case 1 -> Anim.PUNCH_LEFT;
			default -> Anim.UPPERCUT;
		};
	}
}

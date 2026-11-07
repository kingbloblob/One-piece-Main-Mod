package com.onepiecemod.anim;

import io.netty.buffer.ByteBuf;

import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;

import net.fabricmc.fabric.api.event.player.AttackEntityCallback;
import net.fabricmc.fabric.api.networking.v1.PayloadTypeRegistry;
import net.fabricmc.fabric.api.networking.v1.PlayerLookup;
import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.fx.MoveStyle;
import com.onepiecemod.style.FightingStyle;
import com.onepiecemod.style.StyleAttachments;
import com.onepiecemod.style.Technique;

/**
 * Picks which body animation (see Anim) goes with each move, and tells every nearby player's game to play it.
 * Moves call this with one line: bosses (BossAbility), pirate and Marine NPCs (HumanNpc), fighting style
 * techniques (StyleMoves), Devil Fruit moves (MoveFx) and Haki (HakiPowers).
 * It only changes how the model moves: damage, range and timing of the moves are untouched.
 * Plain melee swings (sword cuts, punches) are worked out by the player's game itself, see anim/client/AnimClient.
 */
public final class CombatAnims {
	private CombatAnims() {
	}

	/** Server -> players: "entity N plays animation A for T ticks". */
	public record Play(int entityId, int anim, int ticks) implements CustomPacketPayload {
		public static final Type<Play> TYPE = new Type<>(OnePieceMod.id("combat_anim"));
		public static final StreamCodec<ByteBuf, Play> CODEC = StreamCodec.composite(
				ByteBufCodecs.VAR_INT, Play::entityId,
				ByteBufCodecs.VAR_INT, Play::anim,
				ByteBufCodecs.VAR_INT, Play::ticks,
				Play::new
		);

		@Override
		public Type<? extends CustomPacketPayload> type() {
			return TYPE;
		}
	}

	/** OnePieceMod calls this once. */
	public static void initialize() {
		PayloadTypeRegistry.clientboundPlay().register(Play.TYPE, Play.CODEC);

		// Black Leg: Sanji never punches. Bare-handed hits become kicks, every third one a spinning kick.
		AttackEntityCallback.EVENT.register((player, level, hand, target, hitResult) -> {
			if (!level.isClientSide() && player.getMainHandItem().isEmpty()
					&& StyleAttachments.active(player) == FightingStyle.BLACK_LEG) {
				play(player, player.tickCount % 3 == 0 ? Anim.SPIN_KICK : Anim.KICK);
			}
			return InteractionResult.PASS;
		});
	}

	/** Plays an animation on an entity for everyone who can see it (and for the entity itself, if it's a player). */
	public static void play(LivingEntity entity, Anim anim) {
		play(entity, anim, anim.ticks);
	}

	public static void play(LivingEntity entity, Anim anim, int ticks) {
		if (entity == null || anim == null || entity.level().isClientSide()) {
			return;
		}
		Play payload = new Play(entity.getId(), anim.ordinal(), Math.max(1, ticks));
		for (ServerPlayer player : PlayerLookup.tracking(entity)) {
			if (player != entity) {
				ServerPlayNetworking.send(player, payload);
			}
		}
		if (entity instanceof ServerPlayer self) {
			ServerPlayNetworking.send(self, payload);
		}
	}

	/** Boss special attacks, by their "power" in characters.json (see BossAbility). */
	public static void bossPower(LivingEntity boss, String power) {
		Anim anim = switch (power) {
			case "punch", "magma" -> Anim.PUNCH;
			case "sword" -> Anim.SPIN_SLASH;
			case "fire", "dragon", "ice", "poison" -> Anim.CAST;
			case "petrify", "sand", "shadow", "smoke", "curse" -> Anim.POINT;
			case "lightning", "soul", "string" -> Anim.SUMMON;
			case "teleport" -> Anim.DASH;
			case "quake", "forest" -> Anim.GROUND_SLAM;
			case "gravity" -> Anim.CHOP;
			case "pull", "darkness" -> Anim.CAST;
			case "beast" -> Anim.POUNCE;
			case "paw" -> Anim.UPPERCUT;
			case "haki" -> Anim.ROAR;
			case "heal" -> Anim.POWER_UP;
			default -> null; // "rocks" picks another power, which plays its own animation.
		};
		if (anim != null) {
			// Big bosses move a little slower, so you can see it coming.
			play(boss, anim, Math.round(anim.ticks * 1.3f));
		}
	}

	/** Fighting style techniques (see StyleMoves). */
	public static void technique(Player player, Technique technique) {
		Anim anim = switch (technique) {
			case ONI_GIRI, HOMURA_GIRI, YAHAZU_GIRI -> Anim.SLASH;
			case TATSUMAKI -> Anim.SPIN_SLASH;
			case POUND_HO, TOGEN_TOTSUKA, ODENS_SCAR, KITSUNEBI_BLADE -> Anim.CHOP;
			case PARADISE_TOTSUKA, CUT_THE_FLAMES -> Anim.CROSS_SLASH;
			case GAVOTTE, SHIGAN -> Anim.THRUST;
			case ASURA, DIABLE_JAMBE, IFRIT_JAMBE, BOILING_WILL, SOUL_SOLID -> Anim.POWER_UP;
			case CONCASSE -> Anim.HEEL_DROP;
			case PARTY_TABLE, RANKYAKU -> Anim.SPIN_KICK;
			case THOUSAND_BRICK, FIST_OF_LOVE_PUNCH, HIKEN -> Anim.PUNCH;
			case UCHIMIZU -> Anim.FLICK;
			case SAMEHADA, TEKKAI -> Anim.GUARD;
			case BURAIKAN, ROKUOGAN -> Anim.CAST;
			case SORU -> Anim.DASH;
			case RYU_NO_KAGIZUME -> Anim.CLAW;
			case RYU_NO_IBUKI, GALAXY_IMPACT -> Anim.GROUND_SLAM;
			case CANNONBALL -> Anim.THROW;
			case LULLABY -> Anim.SUMMON;
			case LEAD_STAR, KAEN_BOSHI, POP_GREEN, FIREBIRD_STAR -> Anim.SHOOT;
			default -> null;
		};
		play(player, anim);
	}

	/** Devil Fruit moves that fly from your hand, by the shape they draw (see MoveFx.beam). */
	public static void fruitMove(LivingEntity user, MoveStyle style) {
		play(user, switch (style) {
			case ARM, FIST, CRACK -> user.getRandom().nextBoolean() ? Anim.PUNCH : Anim.PUNCH_LEFT;
			case BEAM, ORB -> Anim.CAST;
			case SPEAR, BOLT -> Anim.POINT;
			case SLASH -> Anim.SLASH;
			case CLAW -> Anim.CLAW;
			case PILLAR, SPIKES, RING -> Anim.GROUND_SLAM;
			case SPHERE, TORNADO -> Anim.SUMMON;
			default -> Anim.CAST;
		});
	}
}

package com.onepiecemod.crew;

import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

import net.minecraft.network.FriendlyByteBuf;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;
import net.minecraft.server.level.ServerPlayer;

import net.fabricmc.fabric.api.networking.v1.PayloadTypeRegistry;
import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;

import com.onepiecemod.OnePieceMod;

/**
 * Messages between the server and players' games for the crew window (U key, or the Recruitment Board).
 * The server decides everything: the window only shows what it's sent and asks for actions.
 */
public class CrewPayloads {
	/** One hired crewmate, as the window shows it. */
	public record Member(String role, String name, int variant, String personality, int level, int xp, int xpNeeded,
			float health, float maxHealth, int mode, String where, boolean nearby) {
		void write(FriendlyByteBuf buf) {
			buf.writeUtf(role);
			buf.writeUtf(name);
			buf.writeVarInt(variant);
			buf.writeUtf(personality);
			buf.writeVarInt(level);
			buf.writeVarInt(xp);
			buf.writeVarInt(xpNeeded);
			buf.writeFloat(health);
			buf.writeFloat(maxHealth);
			buf.writeVarInt(mode);
			buf.writeUtf(where);
			buf.writeBoolean(nearby);
		}

		static Member read(FriendlyByteBuf buf) {
			return new Member(buf.readUtf(), buf.readUtf(), buf.readVarInt(), buf.readUtf(), buf.readVarInt(), buf.readVarInt(),
					buf.readVarInt(), buf.readFloat(), buf.readFloat(), buf.readVarInt(), buf.readUtf(), buf.readBoolean());
		}
	}

	/** Server -> player: the whole crew. `open` = open the window if it isn't already. */
	public record View(boolean open, boolean hasCrew, String crewName, int nextPrice, int berries, String notice,
			List<Member> members) implements CustomPacketPayload {
		public static final Type<View> TYPE = new Type<>(OnePieceMod.id("crew_view"));
		public static final StreamCodec<FriendlyByteBuf, View> CODEC = StreamCodec.ofMember(View::write, View::read);

		private void write(FriendlyByteBuf buf) {
			buf.writeBoolean(open);
			buf.writeBoolean(hasCrew);
			buf.writeUtf(crewName);
			buf.writeVarInt(nextPrice);
			buf.writeVarInt(berries);
			buf.writeUtf(notice);
			buf.writeVarInt(members.size());
			members.forEach(member -> member.write(buf));
		}

		private static View read(FriendlyByteBuf buf) {
			boolean open = buf.readBoolean();
			boolean hasCrew = buf.readBoolean();
			String crewName = buf.readUtf();
			int nextPrice = buf.readVarInt();
			int berries = buf.readVarInt();
			String notice = buf.readUtf();
			int count = buf.readVarInt();
			List<Member> members = new ArrayList<>();
			for (int i = 0; i < count; i++) {
				members.add(Member.read(buf));
			}
			return new View(open, hasCrew, crewName, nextPrice, berries, notice, members);
		}

		/** The hired crewmate in this role, or null. */
		public Member member(CrewRole role) {
			for (Member member : members) {
				if (member.role().equals(role.id())) {
					return member;
				}
			}
			return null;
		}

		@Override
		public Type<? extends CustomPacketPayload> type() {
			return TYPE;
		}
	}

	/** One recruit at the tavern. */
	public record Recruit(String name, int variant, String personality, int price, int health, int damage) {}

	/** Server -> player: today's 3 recruits for a role. problem = why they can't hire right now ("" = they can). */
	public record Recruits(String role, int listCode, String problem, List<Recruit> recruits) implements CustomPacketPayload {
		public static final Type<Recruits> TYPE = new Type<>(OnePieceMod.id("crew_recruits"));
		public static final StreamCodec<FriendlyByteBuf, Recruits> CODEC = StreamCodec.ofMember(Recruits::write, Recruits::read);

		private void write(FriendlyByteBuf buf) {
			buf.writeUtf(role);
			buf.writeVarInt(listCode);
			buf.writeUtf(problem);
			buf.writeVarInt(recruits.size());
			for (Recruit recruit : recruits) {
				buf.writeUtf(recruit.name());
				buf.writeVarInt(recruit.variant());
				buf.writeUtf(recruit.personality());
				buf.writeVarInt(recruit.price());
				buf.writeVarInt(recruit.health());
				buf.writeVarInt(recruit.damage());
			}
		}

		private static Recruits read(FriendlyByteBuf buf) {
			String role = buf.readUtf();
			int listCode = buf.readVarInt();
			String problem = buf.readUtf();
			int count = buf.readVarInt();
			List<Recruit> recruits = new ArrayList<>();
			for (int i = 0; i < count; i++) {
				recruits.add(new Recruit(buf.readUtf(), buf.readVarInt(), buf.readUtf(), buf.readVarInt(), buf.readVarInt(), buf.readVarInt()));
			}
			return new Recruits(role, listCode, problem, recruits);
		}

		@Override
		public Type<? extends CustomPacketPayload> type() {
			return TYPE;
		}
	}

	/**
	 * Player -> server: a button in the crew window.
	 * action: open, mode (arg = mode number), recruits, hire (arg = candidate 0-2, code = list code),
	 * dismiss, create (text = crew name).
	 */
	public record Action(String action, String role, int arg, int code, String text) implements CustomPacketPayload {
		public static final Type<Action> TYPE = new Type<>(OnePieceMod.id("crew_action"));
		public static final StreamCodec<FriendlyByteBuf, Action> CODEC = StreamCodec.ofMember(Action::write, Action::read);

		private void write(FriendlyByteBuf buf) {
			buf.writeUtf(action);
			buf.writeUtf(role);
			buf.writeVarInt(arg);
			buf.writeVarInt(code);
			buf.writeUtf(text, 64);
		}

		private static Action read(FriendlyByteBuf buf) {
			return new Action(buf.readUtf(), buf.readUtf(), buf.readVarInt(), buf.readVarInt(), buf.readUtf(64));
		}

		@Override
		public Type<? extends CustomPacketPayload> type() {
			return TYPE;
		}
	}

	public static void initialize() {
		PayloadTypeRegistry.clientboundPlay().register(View.TYPE, View.CODEC);
		PayloadTypeRegistry.clientboundPlay().register(Recruits.TYPE, Recruits.CODEC);
		PayloadTypeRegistry.serverboundPlay().register(Action.TYPE, Action.CODEC);
		ServerPlayNetworking.registerGlobalReceiver(Action.TYPE, (payload, context) -> handle(context.player(), payload));
	}

	/** True if this player has the mod's window (players on a vanilla client get chat instead). */
	public static boolean hasWindow(ServerPlayer player) {
		return player != null && ServerPlayNetworking.canSend(player, View.TYPE);
	}

	/** Opens the crew window for this player. */
	public static void open(ServerPlayer player) {
		send(player, true, "");
	}

	/** Updates the crew window if the player has it open (does nothing otherwise). */
	public static void refresh(ServerPlayer player) {
		if (player != null) {
			send(player, false, "");
		}
	}

	private static void send(ServerPlayer player, boolean open, String notice) {
		if (hasWindow(player)) {
			ServerPlayNetworking.send(player, view(player, open, notice));
		}
	}

	private static View view(ServerPlayer player, boolean open, String notice) {
		Crew crew = player.getAttached(CrewAttachments.CREW);
		int berries = CrewHiring.berries(player);
		if (crew == null) {
			return new View(open, false, "", CrewHiring.cost(0), berries, notice, List.of());
		}
		List<Member> members = new ArrayList<>();
		for (CrewRole role : CrewRole.values()) {
			UUID id = crew.member(role);
			if (id == null) {
				continue;
			}
			CrewmateEntity crewmate = CrewRoster.find(player.level().getServer(), id);
			if (crewmate == null) {
				members.add(new Member(role.id(), role.title(), 0, "", 0, 0, 0, 0, 0, CrewMode.FOLLOW.ordinal(),
						"Far away (not loaded)", false));
				continue;
			}
			boolean sameWorld = crewmate.level() == player.level();
			int distance = sameWorld ? (int) Math.sqrt(crewmate.distanceToSqr(player)) : -1;
			String where = crewmate.isKnockedOut() ? "Knocked out"
					: !sameWorld ? "In another world" : distance <= 16 ? "With you" : distance + " blocks away";
			int level = crewmate.getCrewLevel();
			members.add(new Member(role.id(), crewmate.getName().getString(), crewmate.getVariantIndex(),
					crewmate.getPersonality().name(), level, crewmate.getXp(),
					level >= CrewLevels.MAX_LEVEL ? 0 : CrewLevels.xpToNext(level),
					crewmate.getHealth(), crewmate.getMaxHealth(), crewmate.getMode().ordinal(), where, true));
		}
		return new View(open, true, crew.name(), CrewHiring.cost(crew.hires()), berries, notice, members);
	}

	private static void sendRecruits(ServerPlayer player, CrewRole role) {
		Crew crew = player.getAttached(CrewAttachments.CREW);
		if (crew == null || !hasWindow(player)) {
			return;
		}
		String problem = CrewHiring.hireProblem(player, role);
		List<Recruit> recruits = new ArrayList<>();
		for (CrewCandidates.Candidate candidate : CrewCandidates.forRole(player, crew, role)) {
			recruits.add(new Recruit(candidate.name(), candidate.variantIndex(), candidate.personality().name(),
					candidate.price(), candidate.health(), candidate.damage()));
		}
		ServerPlayNetworking.send(player, new Recruits(role.id(), CrewCandidates.listCode(player, crew),
				problem == null ? "" : problem, recruits));
	}

	private static void handle(ServerPlayer player, Action action) {
		CrewRole role = CrewRole.byId(action.role());
		Crew crew = player.getAttached(CrewAttachments.CREW);
		switch (action.action()) {
			case "open" -> open(player);
			case "call" -> CrewCommands.callCrew(player);
			case "recruits" -> {
				if (role != null) {
					sendRecruits(player, role);
				}
			}
			case "hire" -> {
				if (role != null) {
					String problem = CrewHiring.tryHire(player, role, action.arg(), action.code());
					send(player, false, problem == null ? "" : problem);
					if (problem != null) {
						sendRecruits(player, role); // Stay on the recruits page, with a fresh list if the day changed.
					}
				}
			}
			case "mode" -> {
				CrewmateEntity crewmate = role != null && crew != null && crew.member(role) != null
						? CrewRoster.find(player.level().getServer(), crew.member(role)) : null;
				if (crewmate != null && action.arg() >= 0 && action.arg() < CrewMode.values().length) {
					crewmate.setMode(CrewMode.values()[action.arg()]);
				}
				send(player, false, crewmate == null ? "That crewmate is too far away to hear you." : "");
			}
			case "dismiss" -> {
				if (role != null && crew != null && crew.member(role) != null) {
					CrewHiring.dismiss(player.level().getServer(), crew.member(role));
					player.setAttached(CrewAttachments.CREW, crew.withoutMember(role));
					send(player, false, "Your " + role.title() + " left the crew.");
				}
			}
			case "create" -> {
				String name = action.text().trim();
				if (crew != null) {
					send(player, false, "You already lead a crew.");
				} else if (name.isEmpty() || name.length() > 32) {
					send(player, false, "Pick a crew name between 1 and 32 letters.");
				} else {
					CrewCommands.createCrew(player, name);
					send(player, false, "");
				}
			}
			default -> {
			}
		}
	}
}

package com.onepiecemod.hideout;

import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.NonNullList;
import net.minecraft.core.UUIDUtil;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.ContainerHelper;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.inventory.AbstractContainerMenu;
import net.minecraft.world.inventory.ChestMenu;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.entity.BaseContainerBlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;

import com.onepiecemod.bounty.Bounty;
import com.onepiecemod.crew.Crew;
import com.onepiecemod.crew.CrewAttachments;
import com.onepiecemod.crew.CrewMode;
import com.onepiecemod.crew.CrewRole;
import com.onepiecemod.crew.CrewmateEntity;
import com.onepiecemod.multiplayer.PlayerCrews;
import com.onepiecemod.weapon.WeaponItems;

/**
 * The heart of a pirate hideout. While its chunk is loaded it:
 *  - looks over the claim every ~25 seconds (beds, cannons, buildings...) and works out the hideout's level;
 *  - once a day collects the crew's haul into its 27-slot stash (see {@link HideoutHaul});
 *  - lets crew who rest here heal (level 2+), and heals crewmates faster (level 4+);
 *  - feeds the cannons from the stash during a Navy attack (see {@link HideoutSiege}).
 */
public class HideoutFlagBlockEntity extends BaseContainerBlockEntity {
	private static final int SURVEY_PAUSE_TICKS = 20 * 20;
	/** Days of haul that pile up while nobody's around. */
	private static final int MAX_DAYS_SAVED = 3;

	private NonNullList<ItemStack> items = NonNullList.withSize(27, ItemStack.EMPTY);
	private UUID owner;
	private String ownerName = "";
	private long lastHaulDay = -1;
	/** The day the Navy last broke in: no haul until the next day. */
	private long raidedDay = -1;
	private int hideoutLevel;
	private final List<String> report = new ArrayList<>();

	// Surveying (not saved: it is redone after loading).
	private HideoutSurvey survey = new HideoutSurvey();
	private HideoutSurvey scanning;
	private int scanX;
	private int pause;
	private boolean surveyed;

	public HideoutFlagBlockEntity(BlockPos pos, BlockState state) {
		super(HideoutFeature.HIDEOUT_FLAG_ENTITY, pos, state);
	}

	public UUID owner() {
		return owner;
	}

	public String ownerName() {
		return ownerName;
	}

	public int level() {
		return hideoutLevel;
	}

	public HideoutSurvey survey() {
		return survey;
	}

	public boolean surveyed() {
		return surveyed;
	}

	public List<String> report() {
		return report;
	}

	void claim(ServerPlayer player) {
		owner = player.getUUID();
		ownerName = player.getName().getString();
		lastHaulDay = day(player.level());
		setChanged();
	}

	static long day(Level level) {
		return level.getOverworldClockTime() / 24000L;
	}

	/** The captain or anyone in their player crew (or an allied crew). */
	public boolean isCrew(ServerPlayer player) {
		if (owner == null) {
			return false;
		}
		if (owner.equals(player.getUUID())) {
			return true;
		}
		UUID ownerCrew = PlayerCrews.captainOf(player.level().getServer(), owner);
		UUID theirs = PlayerCrews.crewKey(player.level().getServer(), player);
		UUID key = ownerCrew != null ? ownerCrew : owner;
		return key.equals(theirs) || (theirs != null && PlayerCrews.allied(player.level().getServer(), key, theirs));
	}

	public String crewName(ServerLevel level) {
		ServerPlayer captain = level.getServer().getPlayerList().getPlayer(owner);
		Crew crew = captain != null ? captain.getAttached(CrewAttachments.CREW) : null;
		if (crew != null) {
			return crew.name();
		}
		Hideouts.Hideout saved = Hideouts.of(level.getServer(), owner);
		return saved != null && !saved.crewName().isEmpty() ? saved.crewName() : ownerName + "'s crew";
	}

	// ---- Ticking ----

	public static void serverTick(Level level, BlockPos pos, BlockState state, HideoutFlagBlockEntity flag) {
		if (!(level instanceof ServerLevel serverLevel) || flag.owner == null) {
			return;
		}
		flag.applyPending(serverLevel);
		flag.surveyStep(serverLevel);
		if ((level.getGameTime() + pos.asLong()) % 100 == 0) {
			flag.comfort(serverLevel);
		}
		if ((level.getGameTime() + pos.asLong()) % 200 == 0) {
			flag.dailyHaul(serverLevel);
		}
	}

	private void surveyStep(ServerLevel level) {
		if (scanning == null) {
			if (pause-- > 0) {
				return;
			}
			scanning = new HideoutSurvey();
			scanX = -Hideouts.RADIUS;
		}
		scanning.scanSlice(level, worldPosition, scanX++);
		if (scanX <= Hideouts.RADIUS) {
			return;
		}
		scanning.checkBuildings(level, worldPosition);
		survey = scanning;
		scanning = null;
		pause = SURVEY_PAUSE_TICKS;
		surveyed = true;
		updateLevel(level);
	}

	private void updateLevel(ServerLevel level) {
		int residents = residents(level).size();
		int newLevel = HideoutLevels.levelFor(survey, residents);
		int old = this.hideoutLevel;
		if (newLevel < old && HideoutSiege.isUnderAttack(owner)) {
			return; // Mid-fight (crew knocked out, a bed blown off...): judge the place once the fighting is over.
		}
		this.hideoutLevel = newLevel;
		setChanged();
		Hideouts.Hideout saved = Hideouts.of(level.getServer(), owner);
		if (saved != null && saved.pos().equals(worldPosition)) {
			Hideouts.put(level.getServer(), owner, saved.withStats(crewName(level), newLevel, defence(level)));
		}
		ServerPlayer captain = level.getServer().getPlayerList().getPlayer(owner);
		if (captain != null && newLevel != old) {
			if (newLevel > old) {
				captain.sendSystemMessage(Component.literal("Your hideout is now a " + HideoutLevels.NAMES[newLevel] + "! "
						+ HideoutLevels.perk(newLevel)).withStyle(ChatFormatting.GOLD));
				level.playSound(null, worldPosition, SoundEvents.PLAYER_LEVELUP, SoundSource.BLOCKS, 1.0f, 0.9f);
			} else {
				captain.sendSystemMessage(Component.literal("Your hideout dropped to " + HideoutLevels.NAMES[newLevel]
						+ ": something it needs is gone. Check the flag.").withStyle(ChatFormatting.YELLOW));
			}
		}
	}

	/** Navy losses and supply crates from attacks while the captain was away. */
	private void applyPending(ServerLevel level) {
		if (level.getGameTime() % 40 != 0) {
			return;
		}
		Hideouts.Hideout saved = Hideouts.of(level.getServer(), owner);
		if (saved == null || !saved.pos().equals(worldPosition) || (saved.lossPercent() == 0 && saved.crates() == 0)) {
			return;
		}
		if (saved.lossPercent() > 0) {
			loseShare(level, saved.lossPercent() / 100f);
			raidedDay = day(level);
		}
		for (int i = 0; i < saved.crates(); i++) {
			HideoutSiege.supplyCrate(level, this);
		}
		Hideouts.put(level.getServer(), owner, saved.pendingApplied());
	}

	/** Crewmates of this captain set to Work inside the claim. */
	public List<CrewmateEntity> residents(ServerLevel level) {
		Hideouts.Hideout saved = Hideouts.of(level.getServer(), owner);
		// Counted by where they were told to work, so chasing a Marine out of the claim doesn't make them move out.
		AABB box = new AABB(worldPosition).inflate(Hideouts.RADIUS + 32, 48, Hideouts.RADIUS + 32);
		return level.getEntitiesOfClass(CrewmateEntity.class, box, crewmate -> owner.equals(crewmate.getCaptainId())
				&& crewmate.getMode() == CrewMode.WORK && crewmate.isAlive()
				&& (saved == null || saved.contains(crewmate.getWorkPos() != null ? Vec3.atCenterOf(crewmate.getWorkPos()) : crewmate.position())));
	}

	/** How hard the hideout is to take: level, cannons with ammo, the crew living here and a Watchtower. */
	public int defence(ServerLevel level) {
		int rating = 5 * this.hideoutLevel;
		if (cannonballs() > 0) {
			rating += 3 * Math.min(survey.cannons.size(), 12);
		}
		for (CrewmateEntity crewmate : residents(level)) {
			boolean fighter = crewmate.getRole() == CrewRole.SWORDSMAN || crewmate.getRole() == CrewRole.SNIPER;
			rating += (3 + crewmate.getCrewLevel()) * (fighter ? 2 : 1);
		}
		if (survey.buildings.contains("alarm_bell")) {
			rating += 6;
		}
		rating += com.onepiecemod.baseworks.BaseUpgrades.defenceBonus(level.getServer(), owner, survey.cannons.size()); // Builder's Ledger upgrades.
		return rating;
	}

	private void comfort(ServerLevel level) {
		if (this.hideoutLevel < 2 || HideoutSiege.isUnderAttack(owner)) {
			return;
		}
		Hideouts.Hideout saved = Hideouts.of(level.getServer(), owner);
		if (saved == null) {
			return;
		}
		for (ServerPlayer player : level.players()) {
			if (saved.contains(player.position()) && isCrew(player) && player.getHealth() < player.getMaxHealth()
					&& player.getLastHurtByMobTimestamp() + 200 < player.tickCount) {
				player.addEffect(new MobEffectInstance(MobEffects.REGENERATION, 120, com.onepiecemod.baseworks.BaseUpgrades.restAmplifier(level.getServer(), owner), true, false, true));
			}
		}
		if (this.hideoutLevel >= 4) {
			for (CrewmateEntity crewmate : residents(level)) {
				if (crewmate.getHealth() < crewmate.getMaxHealth() && !crewmate.isKnockedOut()) {
					crewmate.heal(2.0f);
				}
			}
		}
	}

	// ---- Daily haul ----

	private void dailyHaul(ServerLevel level) {
		long today = day(level);
		if (lastHaulDay < 0) {
			lastHaulDay = today;
			setChanged();
			return;
		}
		if (today <= lastHaulDay || !surveyed) {
			return;
		}
		long days = Math.min(MAX_DAYS_SAVED, today - lastHaulDay);
		lastHaulDay = today;
		setChanged();
		runHaul(level, (int) days, false);
	}

	/** Collects the crew's haul for this many days. forced = /hideout haul (testing). */
	void runHaul(ServerLevel level, int days, boolean forced) {
		ServerPlayer captain = level.getServer().getPlayerList().getPlayer(owner);
		if (!forced && raidedDay >= 0 && day(level) <= raidedDay + 1) {
			report.clear();
			report.add("Day " + day(level) + ": no haul. The crew spent the day patching up after the Navy broke in.");
			if (captain != null) {
				captain.sendSystemMessage(Component.literal("[Hideout] " + report.get(0)).withStyle(ChatFormatting.GRAY));
			}
			return;
		}
		List<CrewmateEntity> residents = residents(level);
		report.clear();
		if (residents.isEmpty()) {
			report.add("Day " + day(level) + ": nobody lives here yet. Set crewmates to Work inside the claim.");
			return;
		}
		boolean full = false;
		for (int d = 0; d < days; d++) {
			HideoutHaul.Haul haul = HideoutHaul.roll(residents, this.hideoutLevel, level.getRandom());
			com.onepiecemod.baseworks.BaseUpgrades.boostHaul(level.getServer(), owner, haul.items(), level.getRandom()); // Storehouse upgrade.
			if (d == 0) {
				report.addAll(haul.lines());
			}
			for (ItemStack stack : haul.items()) {
				full |= !store(stack);
			}
		}
		for (ItemStack extra : com.onepiecemod.baseworks.BaseUpgrades.dailyExtras(level.getServer(), owner, days)) {
			full |= !store(extra); // Smuggler's Cove upgrade.
		}
		report.add(0, "Day " + day(level) + (days > 1 ? " (" + days + " days)" : "") + ": the crew's haul is in the stash.");
		if (full) {
			report.add("The stash is full! Some of the haul was lost.");
		}
		setChanged();
		if (captain != null) {
			captain.sendSystemMessage(Component.literal("[Hideout] Your crew brought in the day's haul" + (days > 1 ? " (" + days + " days)" : "")
					+ ". Check the flag's stash.").withStyle(ChatFormatting.GOLD));
			for (int i = 1; i < report.size(); i++) {
				captain.sendSystemMessage(Component.literal("  " + report.get(i)).withStyle(ChatFormatting.GRAY));
			}
		}
	}

	/** Puts a stack into the stash. Returns false if some of it didn't fit. */
	public boolean store(ItemStack stack) {
		for (int i = 0; i < items.size() && !stack.isEmpty(); i++) {
			ItemStack slot = items.get(i);
			if (!slot.isEmpty() && ItemStack.isSameItemSameComponents(slot, stack) && slot.getCount() < slot.getMaxStackSize()) {
				int move = Math.min(stack.getCount(), slot.getMaxStackSize() - slot.getCount());
				slot.grow(move);
				stack.shrink(move);
			}
		}
		for (int i = 0; i < items.size() && !stack.isEmpty(); i++) {
			if (items.get(i).isEmpty()) {
				items.set(i, stack.copy());
				stack.setCount(0);
			}
		}
		setChanged();
		return stack.isEmpty();
	}

	// ---- Cannonballs ----

	public int cannonballs() {
		int count = 0;
		for (ItemStack stack : items) {
			if (stack.is(WeaponItems.CANNONBALL)) {
				count += stack.getCount();
			}
		}
		return count;
	}

	/** Takes one cannonball out of the stash for a cannon. False if there are none. */
	public boolean takeCannonball() {
		for (ItemStack stack : items) {
			if (stack.is(WeaponItems.CANNONBALL)) {
				stack.shrink(1);
				setChanged();
				return true;
			}
		}
		return false;
	}

	/** The Navy carries off this share of the stash (whole stacks, picked at random). */
	public int loseShare(ServerLevel level, float share) {
		List<Integer> full = new ArrayList<>();
		for (int i = 0; i < items.size(); i++) {
			if (!items.get(i).isEmpty()) {
				full.add(i);
			}
		}
		int take = Math.round(full.size() * share);
		for (int n = 0; n < take && !full.isEmpty(); n++) {
			items.set(full.remove(level.getRandom().nextInt(full.size())), ItemStack.EMPTY);
		}
		setChanged();
		return take;
	}

	void markRaided(ServerLevel level) {
		raidedDay = day(level);
		setChanged();
	}

	// ---- Right-click ----

	void use(ServerPlayer player) {
		if (owner == null) {
			player.sendSystemMessage(Component.literal("This flag belongs to nobody.").withStyle(ChatFormatting.GRAY));
			return;
		}
		if (!isCrew(player)) {
			ServerLevel level = (ServerLevel) player.level();
			player.sendSystemMessage(Component.literal("This is the hideout of the " + crewName(level) + ". You'd better leave before they spot you.")
					.withStyle(ChatFormatting.YELLOW));
			return;
		}
		HideoutPayloads.open(player, this);
	}

	void openStash(ServerPlayer player) {
		if (isCrew(player)) {
			player.openMenu(this);
		}
	}

	/** Sets every crewmate of the captain that is inside the claim (and not already working) to Work where they stand. */
	int stationCrew(ServerPlayer player) {
		ServerLevel level = (ServerLevel) player.level();
		Hideouts.Hideout saved = Hideouts.of(level.getServer(), owner);
		if (saved == null) {
			return 0;
		}
		int count = 0;
		AABB box = new AABB(worldPosition).inflate(Hideouts.RADIUS, 40, Hideouts.RADIUS);
		for (CrewmateEntity crewmate : level.getEntitiesOfClass(CrewmateEntity.class, box,
				c -> player.getUUID().equals(c.getCaptainId()) && c.getMode() != CrewMode.WORK && saved.contains(c.position()))) {
			crewmate.setMode(CrewMode.WORK);
			count++;
		}
		return count;
	}

	public boolean ownerNear(ServerLevel level, double range) {
		ServerPlayer captain = level.getServer().getPlayerList().getPlayer(owner);
		return captain != null && captain.level() == level && captain.distanceToSqr(Vec3.atCenterOf(worldPosition)) < range * range;
	}

	/** The captain's Navy threat level, if they're online (else the last one saved). */
	public int threat(ServerLevel level) {
		ServerPlayer captain = level.getServer().getPlayerList().getPlayer(owner);
		if (captain != null) {
			return Bounty.threatLevel(captain);
		}
		Hideouts.Hideout saved = Hideouts.of(level.getServer(), owner);
		return saved != null ? saved.threat() : 0;
	}

	/** The flag is being broken: the stash drops (done by the container code) and the hideout is abandoned. */
	@Override
	public void preRemoveSideEffects(BlockPos pos, BlockState state) {
		super.preRemoveSideEffects(pos, state);
		if (owner != null && level instanceof ServerLevel serverLevel) {
			Hideouts.Hideout saved = Hideouts.of(serverLevel.getServer(), owner);
			if (saved != null && saved.pos().equals(pos)) {
				Hideouts.remove(serverLevel.getServer(), owner);
				ServerPlayer captain = serverLevel.getServer().getPlayerList().getPlayer(owner);
				if (captain != null) {
					captain.sendSystemMessage(Component.literal("Your hideout's flag came down. The land is no longer yours, "
							+ "and the crew living there is on their own until you plant a new flag.").withStyle(ChatFormatting.YELLOW));
				}
			}
		}
	}

	// ---- Container ----

	@Override
	public int getContainerSize() {
		return items.size();
	}

	@Override
	protected NonNullList<ItemStack> getItems() {
		return items;
	}

	@Override
	protected void setItems(NonNullList<ItemStack> items) {
		this.items = items;
	}

	@Override
	protected Component getDefaultName() {
		return Component.literal("Hideout Stash");
	}

	@Override
	protected AbstractContainerMenu createMenu(int id, Inventory inventory) {
		return ChestMenu.threeRows(id, inventory, this);
	}

	// ---- Saving ----

	@Override
	protected void saveAdditional(ValueOutput output) {
		super.saveAdditional(output);
		ContainerHelper.saveAllItems(output, items);
		if (owner != null) {
			output.store("Owner", UUIDUtil.CODEC, owner);
		}
		output.putString("OwnerName", ownerName);
		output.putLong("LastHaulDay", lastHaulDay);
		output.putLong("RaidedDay", raidedDay);
		output.putInt("Level", hideoutLevel);
		output.putString("Report", String.join("\n", report));
	}

	@Override
	protected void loadAdditional(ValueInput input) {
		super.loadAdditional(input);
		items = NonNullList.withSize(getContainerSize(), ItemStack.EMPTY);
		ContainerHelper.loadAllItems(input, items);
		owner = input.read("Owner", UUIDUtil.CODEC).orElse(null);
		ownerName = input.getStringOr("OwnerName", "");
		lastHaulDay = input.getLongOr("LastHaulDay", -1L);
		raidedDay = input.getLongOr("RaidedDay", -1L);
		hideoutLevel = input.getIntOr("Level", 0);
		report.clear();
		String text = input.getStringOr("Report", "");
		if (!text.isEmpty()) {
			report.addAll(List.of(text.split("\n")));
		}
	}
}

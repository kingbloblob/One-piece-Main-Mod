package com.onepiecemod.sea.client;

import net.minecraft.client.animation.KeyframeAnimation;

import com.onepiecemod.client.Keyframes;

import net.minecraft.client.model.EntityModel;
import net.minecraft.client.model.geom.ModelLayerLocation;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.client.model.geom.PartPose;
import net.minecraft.client.model.geom.builders.CubeListBuilder;
import net.minecraft.client.model.geom.builders.LayerDefinition;
import net.minecraft.client.model.geom.builders.MeshDefinition;
import net.minecraft.client.model.geom.builders.PartDefinition;
import net.minecraft.util.Mth;

import com.onepiecemod.OnePieceMod;

/**
 * The Sea King's shape: a big head with an opening jaw, then five body segments that get thinner
 * toward a tail fin. Each segment hangs off the one before it, so a small wiggle on each one
 * adds up to a snake-like swimming wave. The renderer draws all of it 14 times bigger.
 * Body styles (horns, whiskers, frills...) add parts on top: see createBodyLayer(int).
 *
 * Sizes are in pixels (16 pixels = 1 block before scaling). The front of the model is -Z.
 */
public class SeaKingModel extends EntityModel<SeaKingRenderer.State> {
	public static final ModelLayerLocation LAYER = new ModelLayerLocation(OnePieceMod.id("sea_king"), "main");
	/** One model per body style (SeaKingEntity.STYLES). Style 0 uses LAYER. */
	public static final ModelLayerLocation[] LAYERS = new ModelLayerLocation[com.onepiecemod.sea.SeaKingEntity.MODEL_STYLES];

	static {
		LAYERS[0] = LAYER;
		for (int i = 1; i < LAYERS.length; i++) {
			LAYERS[i] = new ModelLayerLocation(OnePieceMod.id("sea_king"), "style" + i);
		}
	}
	private static final int SEGMENTS = 5;

	private final ModelPart body;
	private final ModelPart head;
	private final ModelPart jaw;
	private final ModelPart[] segments = new ModelPart[SEGMENTS];
	/** The Mecha-Shark (style 6) gets a bigger, blunter head. */
	private final boolean shark;
	// Keyframe animations (Minecraft's own system): a lunging bite and a flinch when hit.
	private final KeyframeAnimation bite;
	private final KeyframeAnimation flinch;

	public SeaKingModel(ModelPart root) {
		super(root);
		this.body = root.getChild("body");
		this.head = body.getChild("head");
		this.jaw = head.getChild("jaw");
		ModelPart parent = body;
		for (int i = 0; i < SEGMENTS; i++) {
			segments[i] = parent.getChild("segment" + i);
			parent = segments[i];
		}
		this.shark = segments[0].hasChild("dorsal");
		this.bite = new Keyframes(0.6f)
				.rot("jaw", 0, 0, 0, 0).rot("jaw", 0.15f, 55, 0, 0).rot("jaw", 0.28f, -5, 0, 0).rot("jaw", 0.6f, 0, 0, 0)
				.rot("head", 0, 0, 0, 0).rot("head", 0.15f, -18, 0, 0).rot("head", 0.28f, 10, 0, 0).rot("head", 0.6f, 0, 0, 0)
				.pos("head", 0, 0, 0, 0).pos("head", 0.28f, 0, 0, -4).pos("head", 0.6f, 0, 0, 0)
				.rot("segment0", 0, 0, 0, 0).rot("segment0", 0.2f, 8, 0, 0).rot("segment0", 0.6f, 0, 0, 0)
				.build().bake(root);
		this.flinch = new Keyframes(0.5f)
				.rot("head", 0, 0, 0, 0).rot("head", 0.1f, -30, 15, 0).rot("head", 0.5f, 0, 0, 0)
				.rot("jaw", 0, 0, 0, 0).rot("jaw", 0.1f, 40, 0, 0).rot("jaw", 0.5f, 0, 0, 0)
				.rot("segment1", 0, 0, 0, 0).rot("segment1", 0.1f, 0, 25, 0).rot("segment1", 0.5f, 0, 0, 0)
				.rot("segment3", 0, 0, 0, 0).rot("segment3", 0.15f, 0, -30, 0).rot("segment3", 0.5f, 0, 0, 0)
				.build().bake(root);
	}

	public static LayerDefinition createBodyLayer() {
		return createBodyLayer(0);
	}

	/**
	 * Body styles seen in the show. They all share the serpent body, head and jaw (so they animate the same) and add parts:
	 * 0 serpent, 1 horned (bull-like), 2 whiskered (catfish), 3 frilled (dragon-like, like the Lord of the Coast),
	 * 4 toad-headed (bulging eyes, fat cheeks, front legs), 5 armoured (plates along the back).
	 * Two more are only for the Egghead sea bosses (never rolled for wild ones), with their own textures (sea_king_7/8.png,
	 * tools/sea_kings/gen_mecha_sea_kings.py): 6 Mecha-Shark (thick shark body, tall dorsal fin, pectoral fins, crescent tail),
	 * 7 Sea Beast Weapon (Lilith's cyborg Sea King: steel back plates, a cannon on its head, laser pods, a red visor).
	 * The extra parts use the bottom of the texture (y 96 and down); tools/sea_kings/gen_sea_king_styles.py paints them.
	 */
	public static LayerDefinition createBodyLayer(int style) {
		MeshDefinition mesh = new MeshDefinition();
		PartDefinition root = mesh.getRoot();
		PartDefinition body = root.addOrReplaceChild("body", CubeListBuilder.create(), PartPose.offset(0.0f, 16.0f, 8.0f));

		CubeListBuilder headCubes = CubeListBuilder.create()
				.texOffs(0, 0).addBox(-5.0f, -5.0f, -10.0f, 10, 8, 10) // skull
				.texOffs(40, 0).addBox(-4.0f, -3.0f, -18.0f, 8, 4, 8) // upper snout
				.texOffs(0, 90).addBox(-3.5f, 1.0f, -17.0f, 1, 2, 1) // fangs
				.texOffs(0, 90).addBox(2.5f, 1.0f, -17.0f, 1, 2, 1);
		if (style != 6) {
			headCubes.texOffs(104, 0).addBox(-0.5f, -10.0f, -9.0f, 1, 5, 8); // crest on top of the head (not on a shark)
		}
		PartDefinition head = body.addOrReplaceChild("head", headCubes, PartPose.ZERO);
		head.addOrReplaceChild("jaw", CubeListBuilder.create()
						.texOffs(72, 0).addBox(-4.0f, 0.0f, -8.0f, 8, 3, 8),
				PartPose.offset(0.0f, 1.0f, -10.0f)); // Hinged at the back, so it swings open.
		addHeadExtras(head, style);

		// Body segments, each thinner than the last: width, height.
		float[][] sizes = {{9, 8}, {8, 7}, {7, 6}, {6, 5}, {5, 4}};
		int[][] uvs = {{0, 20}, {44, 20}, {0, 42}, {40, 42}, {0, 62}};
		PartDefinition parent = body;
		for (int i = 0; i < SEGMENTS; i++) {
			float width = sizes[i][0];
			float height = sizes[i][1];
			boolean shark = style == 6;
			CubeListBuilder cubes = CubeListBuilder.create()
					.texOffs(uvs[i][0], uvs[i][1]).addBox(-width / 2, -height / 2, 0.0f, (int) width, (int) height, 12);
			if (!shark) {
				cubes.texOffs(56, 62).addBox(-0.5f, -height / 2 - 3.0f, 2.0f, 1, 3, 8); // fin along the back
			}
			if (shark && i == 0) {
				cubes.texOffs(0, 96).addBox(-5.5f, -5.0f, 0.0f, 11, 10, 12); // a shark's thick chest
			} else if (shark && i == 1) {
				cubes.texOffs(46, 96).addBox(-5.0f, -4.5f, 0.0f, 10, 9, 12);
			}
			if (style == 7) {
				cubes.texOffs(0, 96).addBox(-3.0f, -height / 2 - 3.0f, 1.0f, 6, 3, 10); // steel plate
				if (i == 0) {
					cubes.texOffs(0, 110).addBox(width / 2, -2.0f, 3.0f, 2, 2, 6); // laser pods
					cubes.texOffs(0, 110).mirror().addBox(-width / 2 - 2.0f, -2.0f, 3.0f, 2, 2, 6);
					cubes.mirror(false);
				}
			}
			if (i == 0 && !shark) {
				// Two flippers near the front.
				cubes.texOffs(76, 62).addBox(width / 2, 2.0f, 2.0f, 8, 1, 6);
				cubes.texOffs(76, 62).mirror().addBox(-width / 2 - 8.0f, 2.0f, 2.0f, 8, 1, 6);
			}
			if (i == SEGMENTS - 1 && !shark) {
				cubes.texOffs(36, 62).mirror(false).addBox(-0.5f, -6.0f, 8.0f, 1, 12, 8); // tail fin
			}
			if (style == 3) {
				// Frilled: tall spines along the back instead of the low fin.
				cubes.texOffs(96, 96).addBox(-0.5f, -height / 2 - 6.0f, 3.0f, 1, 6, 6);
			}
			if (style == 5) {
				// Armoured: a shell plate on every segment.
				cubes.texOffs(20, 113).addBox(-3.0f, -height / 2 - 3.0f, 1.0f, 6, 3, 10);
			}
			if (style == 4 && i == 0) {
				// Toad-headed: two stubby front legs.
				cubes.texOffs(52, 113).addBox(width / 2 - 1.0f, 2.0f, 1.0f, 3, 8, 3);
				cubes.texOffs(52, 113).mirror().addBox(-width / 2 - 2.0f, 2.0f, 1.0f, 3, 8, 3);
				cubes.mirror(false);
			}
			// The first segment starts at the back of the head, the others at the end of the one before.
			parent = parent.addOrReplaceChild("segment" + i, cubes, PartPose.offset(0.0f, 0.0f, i == 0 ? 0.0f : 12.0f));
			if (shark && i == 0) {
				// The tall dorsal fin, leaning back, and two big pectoral fins drooping out to the sides.
				parent.addOrReplaceChild("dorsal", CubeListBuilder.create().texOffs(90, 96).addBox(-0.5f, -14.0f, 0.0f, 1, 14, 10),
						PartPose.offsetAndRotation(0.0f, -4.5f, 1.0f, -0.45f, 0.0f, 0.0f));
				parent.addOrReplaceChild("pectoral_right", CubeListBuilder.create().texOffs(0, 118).addBox(0.0f, 0.0f, 0.0f, 12, 1, 8),
						PartPose.offsetAndRotation(5.0f, 3.0f, 1.0f, 0.0f, -0.3f, 0.45f));
				parent.addOrReplaceChild("pectoral_left", CubeListBuilder.create().texOffs(0, 118).mirror().addBox(-12.0f, 0.0f, 0.0f, 12, 1, 8),
						PartPose.offsetAndRotation(-5.0f, 3.0f, 1.0f, 0.0f, 0.3f, -0.45f));
			}
			if (shark && i == SEGMENTS - 1) {
				// A crescent tail: a long upper lobe and a short lower one.
				parent.addOrReplaceChild("tail_upper", CubeListBuilder.create().texOffs(112, 96).addBox(-0.5f, -16.0f, 0.0f, 1, 16, 6),
						PartPose.offsetAndRotation(0.0f, -1.0f, 10.0f, -0.75f, 0.0f, 0.0f));
				parent.addOrReplaceChild("tail_lower", CubeListBuilder.create().texOffs(58, 117).addBox(-0.5f, 0.0f, 0.0f, 1, 7, 4),
						PartPose.offsetAndRotation(0.0f, 1.0f, 10.0f, 0.6f, 0.0f, 0.0f));
			}
		}

		return LayerDefinition.create(mesh, 128, 128);
	}

	private static void addHeadExtras(PartDefinition head, int style) {
		switch (style) {
			case 1 -> { // Horned: two big horns sweeping up and back, with dark tips.
				for (int side = -1; side <= 1; side += 2) {
					PartDefinition horn = head.addOrReplaceChild(side < 0 ? "horn_left" : "horn_right", CubeListBuilder.create()
									.texOffs(0, 96).addBox(-1.5f, -1.5f, 0.0f, 3, 3, 10),
							PartPose.offsetAndRotation(side * 4.0f, -4.0f, -6.0f, 0.9f, side * 0.5f, 0.0f));
					horn.addOrReplaceChild("tip", CubeListBuilder.create().texOffs(26, 96).addBox(-1.0f, -1.0f, 0.0f, 2, 2, 5),
							PartPose.offsetAndRotation(0.0f, 0.0f, 9.0f, -0.6f, 0.0f, 0.0f));
				}
			}
			case 2 -> { // Whiskered: long catfish barbels from the snout, a long pair and a short pair.
				for (int side = -1; side <= 1; side += 2) {
					head.addOrReplaceChild(side < 0 ? "whisker_left" : "whisker_right", CubeListBuilder.create()
									.texOffs(40, 96).addBox(-0.5f, -0.5f, 0.0f, 1, 1, 16),
							PartPose.offsetAndRotation(side * 3.5f, 0.0f, -15.0f, 0.35f, side * 2.3f, 0.0f));
					head.addOrReplaceChild(side < 0 ? "whisker_left2" : "whisker_right2", CubeListBuilder.create()
									.texOffs(40, 96).addBox(-0.5f, -0.5f, 0.0f, 1, 1, 16),
							PartPose.offsetAndRotation(side * 4.5f, 1.0f, -6.0f, 0.6f, side * 2.0f, 0.0f));
				}
			}
			case 3 -> { // Frilled: a fan of skin on each side of the head, like a dragon.
				for (int side = -1; side <= 1; side += 2) {
					head.addOrReplaceChild(side < 0 ? "frill_left" : "frill_right", CubeListBuilder.create()
									.texOffs(74, 96).addBox(-0.5f, -12.0f, 0.0f, 1, 12, 10),
							PartPose.offsetAndRotation(side * 5.0f, 0.0f, -6.0f, -0.3f, 0.0f, side * 0.7f));
				}
			}
			case 4 -> { // Toad-headed: big bulging eyes on top and fat cheeks.
				for (int side = -1; side <= 1; side += 2) {
					head.addOrReplaceChild(side < 0 ? "eye_left" : "eye_right", CubeListBuilder.create()
									.texOffs(110, 96).addBox(-2.0f, -4.0f, -2.0f, 4, 4, 4),
							PartPose.offset(side * 3.5f, -4.0f, -7.0f));
					head.addOrReplaceChild(side < 0 ? "cheek_left" : "cheek_right", CubeListBuilder.create()
									.texOffs(0, 113).addBox(side < 0 ? -4.0f : 0.0f, -2.5f, -3.0f, 4, 5, 6),
							PartPose.offset(side * 5.0f, 0.0f, -5.0f));
				}
			}
			case 6 -> // Mecha-Shark: a red visor over its eyes.
					head.addOrReplaceChild("visor", CubeListBuilder.create().texOffs(68, 118).addBox(-5.0f, -4.0f, -10.6f, 10, 1, 1), PartPose.ZERO);
			case 7 -> { // Sea Beast Weapon: a cannon bolted to its head and a red visor.
				head.addOrReplaceChild("cannon", CubeListBuilder.create()
								.texOffs(58, 96).addBox(-2.5f, -8.0f, -8.0f, 5, 3, 5)
								.texOffs(32, 96).addBox(-1.5f, -10.0f, -17.0f, 3, 3, 10),
						PartPose.ZERO);
				head.addOrReplaceChild("visor", CubeListBuilder.create().texOffs(78, 96).addBox(-5.0f, -4.0f, -10.6f, 10, 1, 1), PartPose.ZERO);
			}
			default -> {
			}
		}
	}

	@Override
	public void setupAnim(SeaKingRenderer.State state) {
		super.setupAnim(state);
		float time = state.ageInTicks;
		// Swim faster when it's moving fast.
		float effort = 0.4f + Math.min(state.walkAnimationSpeed, 1.0f) * 0.6f;

		body.xRot = state.xRot * Mth.DEG_TO_RAD; // Tilt up or down while diving or rising.
		head.yRot = state.yRot * Mth.DEG_TO_RAD * 0.5f;
		head.xRot = Mth.sin(time * 0.08f) * 0.05f;
		if (shark) {
			head.xScale = 1.3f;
			head.yScale = 1.3f;
			head.zScale = 1.15f;
		}
		// Jaws hang a little open, and gape wide when it's hunting someone.
		jaw.xRot = (state.aggressive ? 0.55f : 0.12f) + Mth.sin(time * 0.15f) * 0.08f;

		for (int i = 0; i < SEGMENTS; i++) {
			segments[i].yRot = Mth.sin(time * 0.2f * effort - i * 0.9f) * (0.12f + i * 0.05f) * effort;
			segments[i].xRot = Mth.sin(time * 0.1f - i * 0.7f) * 0.05f;
		}
		if (state.attack >= 0) {
			bite.apply((long) (state.attack * 600.0f), 1.0f);
		}
		if (state.hurt >= 0) {
			flinch.apply((long) (state.hurt * 500.0f), 1.0f);
		}
	}
}

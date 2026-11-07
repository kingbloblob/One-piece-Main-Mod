# Researching a structure before building it

Use this whenever the user names a real or fictional structure (a cathedral, a castle, a
landmark, a city from a show or game, a vehicle) or asks for accuracy, "life size" or
"high detail". Skip it for generic requests like "a medieval house".

## Contents
- Depth levels (hard caps)
- Keeping it cheap
- Working from reference photos plus detail research
- Steps
- Source and copyright rules
- Dossier template
- Verifying the build against the research

## Depth levels (hard caps)
| Level | When | Searches | Page fetches | Image searches |
|---|---|---|---|---|
| Quick | familiar, simple subject | 3 | 0 | 1 |
| Standard | named landmark or notable building | 8 | 2 | 2 |
| Deep | huge/complex or fictional city, or the user wants accuracy | 15 | 4 | 4 |

Pick the lowest level that works and say which in one line. Exceed a cap only when a
build-driving unknown is still open, and say why in one line. If web tools are
unavailable, use what you know, label every number as unverified, and ask the user for
reference images or dimensions.

## Keeping it cheap (read before searching)
Token cost comes from search results (about 2-3k each), fetched pages (5-20k each),
images (about 1k each) and redoing research in every session. So:
1. **Gap-first.** Before any search, draft the dossier from what you already know and
   from the user's images, marking unknowns with `?`. Then list at most 8 *build-driving
   unknowns*: facts that change what blocks get placed (overall dimensions, level
   heights, counts and spacing of repeated elements, plan shape, colour and material
   roles, signature features). Search only those. Skip history, architects, dates, and
   interiors unless the user asked.
2. **One search per unknown**, short queries with units ("dome diameter metres"). Answer
   from the snippets. Stop at two agreeing sources or flag the number as an estimate. Never
   re-run a near-duplicate query.
3. **Fetch sparingly.** Fetch only one authoritative page for a table of numbers, and pass
   `text_content_token_limit` (about 3000) so a long page is truncated.
4. **Images are the expensive part.** Reuse images the user supplied. For new ones, get at
   most one elevation, one aerial and one plan view. After viewing an image, write the
   numbers and ratios you learned into the dossier and do not view it again.
5. **Numeric checks before pictures.** Use `scripts/verify.py` (`measure`, `silhouette`,
   `count_openings`, `report`) to compare the build to the dossier. Look at a preview only
   when a number fails or for a final check. Previews are auto-downscaled (max 640 px).
6. **Reuse.** Keep `dossier.md` and `config.py` in the project. Later sessions read those
   two files and never redo the research. Start a fresh chat per build stage and carry only
   the dossier, config and stage plan, so long chat history is not re-read every turn.
7. **Keep the dossier terse:** tables and numbers, about 300-500 words.

## Working from reference photos plus detail research
Use this when the user supplies photos (say 3-6) and also wants small details researched.
1. **Role-tag each photo once** (overall, aerial, front elevation, detail). View each
   photo at most once in full. Write 3-6 observations per photo into a `Photo notes`
   section of the dossier: counts, ratios, colours, repeated elements, each marked
   certain or uncertain. From then on work from the notes.
2. **Zoom with crops, not new searches.** To inspect a detail that is visible in a photo
   (window shape, gate arch, roof tiles, railings), run `scripts/photo_tools.py crop` on the
   user's file and view the small crop. A crop costs a few hundred tokens.
3. **Palette from the photo.** Run `photo_tools.py palette` with `--box` on the subject
   (not the sky or water, which dominate otherwise) to get dominant colours and nearest
   blocks. Treat the matches as suggestions; confirm with `references/block-palettes.md`.
4. **Sort details into three tiers and spend research by tier:**
   - *A, silhouette* (overall form, tiers, towers, roofline): from photos and numbers. Always built.
   - *B, mid-scale rhythm* (window/arch patterns, buttresses, balconies, roof texture):
     from photos and crops. Built as **modules** and stamped everywhere.
   - *C, micro details* (props, signs, ironwork, plants, ropes): research only for
     **hero zones** (entrance, main facade, tower top). One search per detail family, never per item.
5. **Detail catalog.** For every module in tier B/C write a recipe in the dossier (size,
   blocks, a one-line note on what the photo shows). Build each once in a small `BigBuild`,
   then `stamp_many` with seeded variation (rotation, mirroring, 2-3 colour variants).
6. **Ask for a must-have list.** Before researching details, ask the user for up to five
   details that matter most and anything to ignore. Research only those.
7. **Level of detail by distance.** Fine detail on the parts seen up close; simpler
   repeats at the edges and rooftops. A massive build cannot be uniformly detailed.

## Steps
1. **Disambiguate.** Which structure, version and era (a cathedral before/after fire; a
   fictional location in the manga vs the anime vs the film)? Ask only if the answer
   changes the build.
2. **Search per sub-question, separately** (combined queries return shallow results):
   overall dimensions (footprint, height, key diameters); plan/layout (shape, symmetry,
   number of bays, towers, gates); materials and colours; signature features that make it
   recognisable from far away; construction period/style vocabulary; surroundings (water,
   terrain, neighbours); for fiction: canon sources (official material, reputable fan
   wikis) and note when sources conflict or the thing is never given exact dimensions.
3. **Gather visuals.** Use image search when available and look at the pictures:
   prefer elevations, plans, aerial views and several angles. Also study any images the
   user supplied. Record what each view reveals (e.g. "aerial: 8 radial canals").
4. **Triage.** For each key number record value, source and confidence. Keep ranges when
   sources disagree. Mark estimates read off images as estimates.
5. **Write `dossier.md`** (terse; see the template) with the template below and keep it in the project; later
   sessions read it instead of redoing the research.
6. **Scale.** Run `scripts/scaling.py` with the real dimensions to get blocks per metre,
   scaled sizes, and warnings where features fall below playable minimums (doors, ceilings).
   Respect world height (-64..319 on 1.18+). State the chosen scale to the user.
7. **Map materials** with `references/block-palettes.md`; pick 3-5 palette roles.
8. **Plan stages**, each with a checkable result (see "Verifying").
9. **Report** to the user in a few lines: what you found, what is assumed, what will be
   simplified, and the main sources by name.

## Source and copyright rules
- Paraphrase; do not copy passages. Quote at most a short phrase, and only one per source.
- Cite sources by name/URL in the dossier and mention the main ones to the user.
- Images are references for you to study; never reproduce or trace copyrighted artwork
  pixel for pixel. Build from described proportions and features.
- Prefer authoritative sources (heritage bodies, architects, museums, official
  publications); treat forums and unsourced listicles as weak.
- Do not invent specifics. If a feature is unknown, say so and choose a reasonable
  design, flagged as "design choice".

## Dossier template
```markdown
# <Structure> dossier
Depth: quick|standard|deep      Scale: <blocks per metre>, <largest dimension> blocks
## Identity
what it is, version/era, why it is recognisable (3 bullets)
## Key dimensions (value | source | confidence)
## Layout and geometry (plan, symmetry, counts of repeated elements)
## Signature features (5-10, ordered by importance for the silhouette)
## Materials and colours -> block palette roles (base, wall, trim, roof, accent)
## Surroundings and terrain
## Unknowns and design choices
## Stage plan (each stage: what, how to check)
## Sources
```

## Verifying the build against the research
After each stage, run the numeric checks in `scripts/verify.py` first, then render
`render_top()` and `render_section()` only if a check fails or for a final look. Compare:
- Height-to-width ratio of the whole and of the main parts (tower vs base, dome vs drum).
- Counts of repeated features (arches, bays, towers, gates) against the dossier.
- Silhouette: does the outline read as the subject from far away?
- Palette: do roles and proportions of colours match the reference images?
Fix the config numbers, not the output, and re-export.

# In-House Digital Shoe Last Creation: Technical Research to Rewrite the M1 Last Module

## TL;DR
- **In-house parametric last creation from UK size + brief + reference images is feasible and should be architected as template-morphing of a base last mesh driven by a measurement-validation loop, not free scratch modeling** — the fit-critical zone (heel-to-ball) is derived deterministically from published UK grading rules and foot-to-last allowances, while the toe/style zone forward of the ball line is stylistically free and image-driven.
- **The fit guarantee is achievable in code**: encode UK size→last-length (barleycorn, 8.46mm/size), ball-girth grading (6.35mm/size), width-fitting girth steps (6mm/fitting), a 15–17mm round-toe length allowance, feather-edge and instep girth allowances, then computationally measure the candidate mesh (cross-section perimeters at defined stations) and iterate until all girths/lengths match target within ±2–3mm (SATRA tolerance).
- **For 3D-printed Goodyear-welting lasts, print in ABS/ASA (PLA and PETG fail at the ~120°C heat-set step; PETG suffered "catastrophic failure"), ~5mm wall thickness for nailing, ~50% core infill, a copper-pipe thimble insert for the lasting pin, and a working hinge (e.g., the 3DShoemaker "alpha" spring hinge) for de-lasting after welting.**

## Key Findings

**1. The last is not the foot.** A last is an abstract volumetric form: deeper in the midfoot, sharp 90° "feather edge" where upper meets sole, clipped at the topline, flared and extended at the toe, and pitched for a specific heel height. Critically, the last is designed *for one heel height* — changing heel height more than a few millimeters throws off the balance, flex-point position and toe spring. This means **heel height must be an explicit input parameter to last generation**, not an afterthought.

**2. The "fitting zone vs style zone" principle is the key architectural insight.** Everything behind the ball/joint line (heel curve, seat, waist, instep, ball girth, heel-to-ball length) is fit-critical and must be computed from measurements + allowances. Everything forward of the ball line (toe box shape, length extension, toe spring profile) is stylistic freedom. Crockett & Jones' own last guide confirms this: on their square-toe 348 last "the wearer may find that they have an inch of space at the front of the toe box. This is for aesthetics and will not have an effect on the heel to ball fitting." This cleanly separates the deterministic (fit) pipeline from the image/brief-driven (style) pipeline.

**3. UK sizing is a barleycorn length system with a separate girth/width system.** Length: size 0 = 4 inches of last length; each full size = +1 barleycorn = 1/3 inch = 8.46–8.47mm; each half size = 1/6 inch = 4.23mm. Adult sizing continues the same progression (adult UK 1 ≈ children's 13½ + 1). The last is longer than the foot by roughly 1½–2 barleycorns.

**4. Concrete numeric grading rules that can be encoded directly:**
- Length grade: **8.46mm per full UK size, 4.23mm per half size** (SATRA/Fibre2Fashion, Wikipedia).
- Ball/joint girth grade: **6.35mm (1/4 inch) per full size** (Shoemakers Academy: "The ball girth of a last typically grades at a rate of 1/4 inch and 6.35mm per whole size").
- Width fitting grade (UK, Barker Shoes): **6mm (1/4 inch) between E, F, G, H fittings, established across the instep; 3mm (1/8 inch) for the intermediate FX fitting.** F is the standard British men's fitting; E is narrow — and E is the standard fitting used by Edward Green and Gaziano & Girling (Sons of Henrey's Size Guide: "Edward Green uses a more narrow fitting as their standard… Gaziano & Girling… uses a more narrow fitting as their standard," advising sizing down half a size; Shoegazing confirms "E is the standard at G&G").
- Instep girth grades ~1/4 inch/size; tread width +1/12 inch/size; waist +1/16 inch/size; heel girth ~1/2 size per size (historic English grading, Leno *Manufacture of Boots and Shoes*).
- One width fitting up ≈ same girth as the next full length size up (Shoegazing: a UK10 F ≈ UK9.5 G ≈ UK10.5 E in girth).

**5. A usable numeric UK men's size run (length + ball girth).** From the Best & Less Footwear Standard (Sept 2014), men's UK sizes with insole-corrected effective length (mm) and joint/ball girth (mm):

| UK size | Length min–max (mm) | Ball/joint girth (mm) |
|---|---|---|
| 6 | 251–262 | 226–231 |
| 7 | 260–271 | 232–237 |
| 8 | 268–279 | 238–243 |
| 9 | 277–288 | 244–249 |
| 10 | 285–296* | 250–255 |
| 11 | 294–305 | 256–260 |
| 12 | 302–313 | 261–266 |
| 13 | 310–321 | 271–275 |

*document shows 286, almost certainly a typo for 296 given the +~10mm/size pattern. Note the ball-girth grade here is ~6mm/size, confirming the 1/4-inch rule. The document states acceptable girth tolerance is **±3mm**, and "Footwear with very soft uppers could safely be made on a last that is 5mm under the given measurements." These are foot/fitting figures; the *last* ball girth = foot ball girth + feather-edge allowance (a few mm).

**6. Foot-to-last allowances (the fit logic to encode):**
- **Length/toe allowance**: 3DShoemaker builds lasts "generally 17mm longer than the length of the intended foot. This is assuming the toe shape is round. If it is a pointed toe, more space is needed." Wikipedia gives the general shoe-cavity rule as 15–20mm longer than the foot. Pointed/chisel toes add a percentage forward of the toes — 3DShoemaker's own charts state "we might say a particular pointed toe shoe last has 5% extra length. So to get the true length, find your size on the chart and add 5% to the length."
- **Girth allowances are ADDITIVE, not reductive.** Two positive allowances are added to foot girth to get last girth: **feather-edge compensation** (the last's sharp sole edge creates empty space, so girths crossing the bottom must be enlarged) and **instep girth fill-up** (arch void above the foot). So last ball girth ≈ foot ball girth + small feather-edge allowance; the last must be built larger to accommodate lining + stretch during lasting.
- **Sock/insert stack** adds to girth and length: nylon 0.5mm, dress sock 1mm, casual 1.5mm, sport 2mm, wool 3mm; sock lining 0.5mm (default), footbed/functional orthotic 2mm, accommodative orthotic 3mm.
- **Heel-to-ball proportion**: the treadline/ball line sits so the metatarsal joint aligns with the widest part and flex point. In foot tracings, the ball line point is ~41% across the ball line from the first ball joint; heel width is taken at 1/6 of foot length along the heel axis. The Brannock formula assumes the foot is ~2/3 inch (~17mm) shorter than the last.

**7. Toe spring and heel height standards for men's dress shoes:**
- **Heel height** (men's welted dress): commonly ~1 inch (25mm); Edward Green Oxfords ~0.75"/19mm, Crockett & Jones ~1"/25mm, Gaziano & Girling/European ~1⅛"/28–29mm, up to ~1.25"/32mm. Gaziano & Girling standard cited as 28mm slightly tapered for a single leather sole. Dress range: ~22–30mm.
- **Toe spring** (leather-soled dress): the stiffer/more rigid the sole, the more toe spring needed. Patent/industry figures place ~10mm as a low value, ~20mm mid, ~30mm high; for a leather-soled dress shoe ~8–15mm is typical. Toe spring is a function of heel height AND sole stiffness — it must be co-solved with heel height.

**8. Digital/parametric last generation — the field's methods:**
- **Cross-section parametric modeling** is the classical and dominant CAD approach: the last is defined by a series of cross-sectional curves along its axis (e.g., a patented last defined by 85 cross-sections at 3mm spacing from heel to toe), with girths/widths controlled per station and surfaces lofted (NURBS/SubD) through them.
- **Template morphing / global grading + local deformation**: take a base last mesh and deform it to hit target measurements. Cheng & Perng and others use "global grading with local deformation"; Amza/Zapciu/Popescu (MATEC 2019) parameterize a scanned last by replacing intersection curves with parameterized splines driven by a handful of foot measurements (foot length L, joint height, toe height, and five girth curve lengths A–E) — directly analogous to the proposed pipeline.
- **Statistical shape models (SSM)**: Boppana & Anderson (2021, arXiv 2007.11077) built a parametric SSM from 4D foot scans (30 subjects); Conrad et al. (2019, Nike, 4199 subjects) modeled male/female foot shape differences via PCA. These reconstruct feet, not lasts, but give the foot-shape priors a last must accommodate.
- **3DShoemaker (Rhino plugin) is the most instructive existing parameter vocabulary** and closely mirrors the proposed system. It is "fully parametric," builds a last from a template (body and toe independently), and exposes: size index, width index, functional vs full last length, ball girth, waist girth, instep girth, ball width, heel width, instep width, heel height, toe spring, wedge angle, plus allowances (sock thickness, insert depth, feather-edge, instep fill-up). Fit customizations are ±5mm increments on toe box width, heel width, instep height, ball girth. It uses SubD geometry, supports clipping-plane cross-section inspection, and outputs 3D-printable lasts with hinges and flattened patterns. Commercial peers: Shoemaster/ELAST, Romans CAD 3D Last, Newlast EasyLast3D, xShoe4Rhino.

**9. Image-inspired design should be classification-into-a-template-library, not image-to-mesh.** Romans CAD "Scan Line" already converts 2D photos/hand sketches into style lines on a digital 3D last — prior art for the practical approach. The recommended pipeline: a vision model classifies reference images into a parameterized toe-shape template library (round, almond, chisel, square, elongated) and extracts a toe profile/silhouette curve, mapping to toe-spring, toe-box width/height, and length-extension parameters. Direct image-to-3D reconstruction is neither necessary nor reliable for the fit-critical form.

**10. 3D printing lasts that survive Goodyear welting — hard practitioner data:**
- **Material**: The single most important production finding — Amza et al. (MATEC 2019) tested PLA, PETG, ABS lasts through a real shoe process including a 120°C/30-min oven step: "lasts made from PLA and PETG have softened considerably… PETG parts suffered catastrophic failure… Lasts 3D printed from ABS filament held their form throughout the process and did not soften or deform, offering identical behavior to commercially sourced polymer lasts." **Therefore: any heat-set/heat-lasting process rules out PLA and PETG — use ABS or ASA.** Production HDPE lasts (framas) melt at ~120°C, so printed lasts must match that heat class.
- **BUT for room-temperature hand lasting/nailing**, 3DShoemaker (a decade of experience) settled on **PETG**: "much less brittle than PLA, and softer, making it much better for receiving nails during the lasting process," advising sharp skinny nails. So material choice depends on whether the process is heated (ABS/ASA) or cold nail-and-tack (PETG acceptable).
- **Wall thickness/infill**: "print enough perimeters to get about 5mm wall thickness so the nails aren't just penetrating a thin shell." Podohub prints only 5mm wall + lattice interior ("that is plenty strong, solid lasts are overkill"). Amza used dense core (50% infill, 1.2mm walls) + sparse shell (8% infill) with topology optimization for 40–60% material savings.
- **Thimble/lasting-pin insert**: hammer a section of **1/2" copper pipe** into the thimble hole "as otherwise the plastic can break" when worked on a lasting pin/jack.
- **Hinge for de-lasting**: the 3DShoemaker "alpha" hinge uses an elliptical spring + wood screws (#8 deck screws) or dowel pins; Prusa Slicer can also split a solid last with dowel-pin reconnection. A working hinge/split is essential to remove the last after welting without damaging the shoe.
- **Printer/settings**: proven on desktop FDM (Prusa i3 MK4, Bambu X1C, Creality CR-10, Zortrax M200); 0.6mm nozzle, thin hot layers for layer adhesion, enclosure + heated bed to prevent warping (important for ABS/ASA). A pair can take ~a full day to print.
- **Surface/feather edge**: layer height affects feather-edge sharpness; orient and post-process (sanding, filling) the sole/feather edge; base can be sanded after support removal. Shrinkage compensation matters more for ABS/ASA than PLA.

**11. Fit validation standards and tolerances:**
- **SATRA digital last assessment** measures a 3D last file at defined landmarks and compares to SATRA guidelines and the SATRA Global Foot Dimensions database (thousands of 3D scans), reporting a % population coverage by comparing effective length and joint (ball) girth — "the two most important measurements in footwear fit." SATRA STD 223 is the physical last-assessment jig; STD 219 the size stick; TP4 the on-foot fit assessment. This is the reference model for the measurement-validation loop.
- **ISO 9407:2019 Mondopoint** defines foot length (heel to most prominent toe) and foot width (1st–5th metatarsal heads) in mm; length grading interval normally 5mm (7.5mm for specialist). ISO/TS 19407 covers system conversion; ISO/TS 19408 the vocabulary. Mondopoint is the only system based on foot (not last) length — useful as the internal metric datum.
- **Tolerances**: ball-girth acceptable tolerance **±3mm** (Best & Less); 3DShoemaker recommends not deviating more than **5%** from a nearby last's measurement; soft uppers tolerate a last up to 5mm under.
- **Foot variability the last must anticipate**: per SATRA Bulletin (2018, n=2,890 UK subjects), 19% of UK men have a foot-length difference >4mm between feet, 31% differ in joint girth by >4mm, and 15.3% by >6mm ("approximately one UK width fitting") — so size for the larger foot and expect left/right asymmetry. Foot volume also rises ~5% over a seated workday (Winkel et al., Eur. J. Appl. Physiol. 1986: the foot "swelled by 3.5%" in the first 4h and a further "1.9%" over the last 4h) — build in girth headroom accordingly.

## Details

### A. Recommended architecture for the M1 Last module

**Hybrid: template-morphing driven by a parametric measurement schema, with a closed measurement-validation loop.** This is the consensus of both the academic literature (global grading + local deformation) and the one directly-comparable production tool (3DShoemaker). Concretely:

1. **Inputs**: UK size (+ half size), width fitting (default F men's, or E for a slim dress last), design brief (parsed for style: oxford/derby/loafer, toe shape, formality), reference images, target heel height (default 25mm dress), and optional individual foot measurements for bespoke.

2. **Compute target last measurements (fit logic engine)** — a deterministic module:
   - Last stick length = foot length + toe allowance (≈15–17mm round; +% for pointed/chisel). Or directly from UK size: last length ≈ (size × 8.46mm) + 4-inch base, cross-checked against the numeric table.
   - Ball/joint girth = base girth for size (table) graded 6.35mm/size, + width-fitting offset (6mm/fitting from F), + feather-edge allowance; snug dress fit ≈ foot ball girth + small allowance.
   - Waist, instep, long/short heel girths, heel width, tread width graded from the base last per the grading ratios (instep ~1/4"/size, tread +1/12", waist +1/16", heel ~½ size).
   - Heel height and toe spring co-solved (toe spring scales with heel height and sole stiffness).

3. **Select and morph a base last template** (per toe-family) using RBF/cage/cross-section scaling so the fit-zone cross-sections hit target girths/widths and the heel curve/seat match, while the toe zone takes the image-derived style. NURBS/SubD lofting through the scaled cross-sections yields a smooth watertight surface with a defined feather edge.

4. **Measurement-validation loop** — the fit guarantee:
   - Computationally measure the candidate mesh: stick length (tip-to-tip bounding), girths as **cross-section perimeters at defined stations** (ball line, waist, instep, heel), widths, heel-curve profile. Girth = perimeter of the planar section (or geodesic loop) at each landmark plane, mirroring how SATRA/tape measures a physical last.
   - Compare to targets; if any dimension exceeds tolerance (±2–3mm girth, ±1 barleycorn-fraction length), adjust the driving parameters and re-morph. Iterate to convergence.
   - Optional virtual fit check: register a representative foot mesh (from an SSM or scan) of that UK size inside the last cavity and verify clearance (toe-box height above toes, no negative clearance at ball, heel grip).

5. **Outputs**: (a) rendered last + shoe model; (b) flattened 2D patterns (mean form/insole from the last surface); (c) 3D-printable production last with hinge, thimble hole, 5mm walls, print-ready STL split.

### B. Why not pure cross-section parametric from scratch, or pure SSM?
Pure from-scratch cross-section lofting gives maximum control but is fragile (smoothness, feather-edge continuity, plausibility) and slow to make production-grade — 3DShoemaker itself notes achieving a smooth last is "challenging" with a purely parametric approach and leans on templates + SubD + sculpting. Pure SSMs model feet, not lasts, and no released model maps foot→last directly (Conrad/Nike published no footwear linkage). Template-morphing inherits a known-good, printable, feather-edged base geometry and only deforms it — the lowest-risk path to a manufacturable last.

### C. Toe shape × fit interaction
Round toe = baseline 15–17mm allowance. Almond/chisel/pointed/elongated add length forward of the ball line (a percentage, ~5%+) so the foot still fills to the same effective (heel-to-ball) point — the extra is empty style volume, confirmed by C&J's 348 square-toe "inch of space… will not affect heel-to-ball fitting." Square/chisel also change toe-box cross-section width/height. All of this lives entirely in the style zone and is safe to drive from images.

### D. Open-source templates and data
GrabCAD/Cults3D host last meshes (licensing varies — verify commercial-use rights before using as morphable templates). 3DShoemaker sells parametric templates and per-size measured lasts. Academic foot datasets exist (Boppana/Anderson 4D scans; Conrad/Nike 4199-subject SSM — not publicly released as a usable model). The proposed pipeline should build/curate its own small library of feather-edged base lasts per toe family and per heel height, since these carry the production-critical geometry.

## Recommendations

**Stage 1 — Deterministic fit engine + numeric tables (build first, highest certainty).** Encode: UK size→length (8.46mm/size, 4.23mm/half), ball-girth grade (6.35mm/size), width steps (6mm/fitting from F, 3mm FX), the men's size→length/ball-girth table above, and the allowance stack (toe 15–17mm round, feather-edge, instep fill-up, sock/insert). Output target measurement vectors per (size, width, style). *Benchmark to advance:* target vectors for UK 6–12 F reproduce the published table within ±3mm.

**Stage 2 — Base last library + morphing.** Curate/model 3–5 base lasts (one per toe family) at the default 25mm dress heel height, each with a clean feather edge and hinge-ready topology. Implement cross-section/RBF morphing to hit Stage-1 targets in the fit zone. *Benchmark:* re-measured morphed mesh matches targets within ±2–3mm girth after the validation loop.

**Stage 3 — Measurement-validation loop.** Implement automated mesh measurement (cross-section perimeters at ball/waist/instep/heel stations, stick length, widths, heel curve) and the iterate-to-tolerance controller. Add the optional foot-in-last clearance check. *Benchmark:* loop converges to ±2mm on all fit-zone girths; a virtual foot of that size shows positive clearance everywhere and ≥ a defined toe-box height above the longest toe.

**Stage 4 — Image/brief → style parameters.** LLM/vision classifier maps brief + images to toe family + toe-box width/height + toe spring + length extension. Keep it constrained to the style zone. *Benchmark:* classifier selects the correct toe family on a labeled test set and the resulting last passes Stage-3 validation unchanged (proving style edits never break fit).

**Stage 5 — Production print spec.** Default to **ASA or ABS** if any heat-set/heat-lasting step is used (PLA/PETG fail at ~120°C); allow **PETG** only for purely cold hand-lasting. 5mm walls in nailing zones, ~50% core / sparse-shell infill or lattice, copper-pipe (1/2") thimble insert, working hinge (alpha spring or dowel-pin split) for de-lasting, enclosure + heated bed, 0.6mm nozzle, feather-edge orientation + sanding pass, shrinkage compensation for ABS/ASA. *Benchmark:* a printed last survives a full welting + lasting cycle (leather pulled with pliers, tacked, welted, de-lasted) without crushing, nail pull-out, hinge failure, or heat deformation.

**Thresholds that change the plan:** if heated processes are NOT used, PETG becomes the default (easier printing, better nail-holding) and the heat-resistance constraint relaxes. If bespoke individual fit is required, add real foot measurements/scans as direct inputs and shift the fit engine from size-table grading to per-foot allowances. If girth validation cannot converge within tolerance for a given style, the toe/style zone is encroaching on the fit zone — flag and constrain the style parameters.

## Caveats
- **Per-size waist, instep, long-heel girths and tread width in a single authoritative UK men's dress-last table were not found in free sources.** The strongest free numeric table (Best & Less) gives only length + ball girth; full girth sets require OCR of the 3DShoemaker/Podohub grading-chart JPG, a 3DShoemaker product page's "Show Measurements" output, or the paid SATRA Global Foot Dimensions report. Treat the secondary girths as grade-derived estimates until validated against a purchased last or SATRA data.
- **No single authoritative SATRA numeric foot-girth→last-girth reduction figure exists in free sources.** Free evidence indicates a small *positive* allowance (feather-edge + fill-up), not a reduction; bespoke makers often aim for last ball girth ≈ foot ball girth for a snug welted fit. The precise number should be validated empirically or from a SATRA/textbook purchase.
- **The 120°C failure finding (Amza et al.) is from one canvas-shoe vulcanizing process, not specifically Goodyear welting.** Goodyear welting is largely a room-temperature mechanical process (pulling, tacking, stitching) — so PETG may in fact survive it — but any heat-setting of the toe puff/counter or heat-forming step reintroduces the heat constraint. Validate against your actual process temperatures.
- **Consumer/retail and encyclopedia sources (Grokipedia, brand blogs, forums) were used for corroboration only**; grading increments, allowances and print findings are anchored to primary/technical sources (SATRA, ISO, the MATEC paper, 3DShoemaker practitioner docs, Shoemakers Academy, Barker).
- **Heel height is a hard design constraint, not a slider**: a last is balanced for one heel height. If the brief demands a non-standard heel height, generate a base last for that height rather than re-pitching an existing one.
- Half-size girth increment (~3mm) is inferred (half of the 6.35mm full-size grade), consistent with Barker's 3mm half-width step, but not stated verbatim in a single source.
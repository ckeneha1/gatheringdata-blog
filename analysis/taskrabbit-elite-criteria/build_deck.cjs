// Build a Google-Slides-ready .pptx walking through the Elite Metric Regroup
// methodology using the recreated (synthetic) figures.
//
//   node build_deck.js   ->   Elite_Metric_Regroup_methodology.pptx
//
// Upload the .pptx to Google Drive and "Open with Google Slides" to convert.

const { execSync } = require("child_process");
const GROOT = execSync("npm root -g").toString().trim();
const pptxgen = require(GROOT + "/pptxgenjs");
const path = require("path");

const DIR = "/Users/connorkenehan/github/gatheringdata-blog/analysis/taskrabbit-elite-criteria";
const FIG = path.join(DIR, "figures");

// ---- palette (Taskrabbit brand: deep forest green + cream, orange accent) ----
const GREEN = "13301F";      // deep forest green (dark slides)
const GREEN2 = "1B5E20";     // accent green
const CREAM = "FBF8E9";      // cream text on dark
const INK = "1A2E22";        // near-black green ink (text on light)
const MUTED = "6B7B70";      // muted caption
const ORANGE = "E08A3C";     // highlight accent
const CARD = "F1F4EE";       // light green-grey card tint
const WHITE = "FFFFFF";
const CREAM_BG = "FFFCE4";          // content-slide background, matches the charts
const CHART_RATIO = 1300 / 728;

const pres = new pptxgen();
pres.layout = "LAYOUT_16x9";          // 10" x 5.625"
pres.author = "Connor Kenehan";
pres.title = "Elite Metric Regroup — Methodology";
const W = 10, H = 5.625;

const F = "Calibri";
const FH = "Century Schoolbook";      // serif headers, safe-list

function footer(slide, n) {
  slide.addText("Synthetic data — not real Taskrabbit data", {
    x: 0.45, y: H - 0.34, w: 5, h: 0.25, fontFace: F, fontSize: 8,
    color: MUTED, align: "left", margin: 0,
  });
  slide.addText(String(n), {
    x: W - 0.8, y: H - 0.34, w: 0.4, h: 0.25, fontFace: F, fontSize: 9,
    color: MUTED, align: "right", margin: 0,
  });
}

function title(slide, text, color = INK) {
  slide.addText(text, {
    x: 0.5, y: 0.32, w: W - 1.0, h: 0.7, fontFace: FH, fontSize: 24,
    bold: true, color, align: "left", valign: "middle", margin: 0,
  });
}

// A full-width chart centred under the title, with an optional caption beneath.
function chartSlide(n, titleText, img, caption) {
  const slide = pres.addSlide();
  slide.background = { color: CREAM_BG };
  title(slide, titleText);
  const h = 3.48, w = h * CHART_RATIO;            // ~6.21 wide
  const x = (W - w) / 2, y = 1.12;
  slide.addImage({ path: path.join(FIG, img), x, y, w, h,
    shadow: { type: "outer", color: "000000", blur: 7, offset: 2, angle: 90, opacity: 0.16 } });
  if (caption) {
    slide.addText(caption, {
      x: 0.6, y: y + h + 0.08, w: W - 1.2, h: 0.5, fontFace: F, fontSize: 12,
      color: MUTED, align: "center", valign: "top", margin: 0,
    });
  }
  footer(slide, n);
  return slide;
}

// Chart slide that preserves an image's own aspect ratio (fits within a box).
function chartSlideFit(n, titleText, img, ratio, caption) {
  const slide = pres.addSlide();
  slide.background = { color: CREAM_BG };
  title(slide, titleText);
  const maxH = 3.5, maxW = 8.9;
  let h = maxH, w = h * ratio;
  if (w > maxW) { w = maxW; h = w / ratio; }
  const x = (W - w) / 2, y = 1.12;
  slide.addImage({ path: path.join(FIG, img), x, y, w, h,
    shadow: { type: "outer", color: "000000", blur: 7, offset: 2, angle: 90, opacity: 0.16 } });
  if (caption) {
    slide.addText(caption, {
      x: 0.6, y: Math.min(y + h + 0.08, 4.72), w: W - 1.2, h: 0.5, fontFace: F,
      fontSize: 12, color: MUTED, align: "center", valign: "top", margin: 0,
    });
  }
  footer(slide, n);
  return slide;
}

// Dark section-divider slide.
function divider(titleText, sub) {
  const slide = pres.addSlide();
  slide.background = { color: GREEN };
  slide.addText(titleText, {
    x: 0.8, y: 1.7, w: 8.4, h: 0.9, fontFace: FH, fontSize: 33, bold: true,
    color: CREAM, margin: 0 });
  if (sub) slide.addText(sub, {
    x: 0.82, y: 2.75, w: 8.3, h: 1.4, fontFace: F, fontSize: 16, color: "C9D6C2",
    align: "left", margin: 0 });
  return slide;
}

// ===========================================================================
// 1. Title (dark)
// ===========================================================================
let s = pres.addSlide();
s.background = { color: GREEN };
s.addText("Elite Metric Regroup", {
  x: 0.7, y: 1.7, w: 8.6, h: 1.0, fontFace: FH, fontSize: 46, bold: true,
  color: CREAM, align: "left", margin: 0,
});
s.addText("Defining Tasker supply quality tiers — a methodology walkthrough", {
  x: 0.72, y: 2.75, w: 8.6, h: 0.5, fontFace: F, fontSize: 18, color: "C9D6C2",
  align: "left", margin: 0,
});
s.addText([
  { text: "Synthetic recreation", options: { bold: true, color: ORANGE } },
  { text: "  ·  no proprietary data  ·  shapes & findings reproduced for presentation", options: { color: "9FB098" } },
], { x: 0.72, y: 3.5, w: 8.6, h: 0.4, fontFace: F, fontSize: 12, align: "left", margin: 0 });

// ===========================================================================
// 2. The question (light, numbered refinement)
// ===========================================================================
s = pres.addSlide();
s.background = { color: CREAM_BG };
title(s, 'Finding a metric for "good"');
const steps = [
  ["1", "Which Taskers perform well…", "Start from raw performance."],
  ["2", "…at our business objectives…", "Invoice volume, revenue volume, and close rate."],
  ["3", "…relative to their peers?", "Compared to other Taskers in the same metro-category (metcat)."],
];
let yy = 1.5;
steps.forEach(([num, head, sub]) => {
  s.addShape(pres.shapes.OVAL, { x: 0.7, y: yy, w: 0.62, h: 0.62, fill: { color: GREEN } });
  s.addText(num, { x: 0.7, y: yy, w: 0.62, h: 0.62, fontFace: FH, fontSize: 22, bold: true,
    color: CREAM, align: "center", valign: "middle", margin: 0 });
  s.addText([
    { text: head, options: { bold: true, color: INK, fontSize: 19, breakLine: true } },
    { text: sub, options: { color: MUTED, fontSize: 13 } },
  ], { x: 1.55, y: yy - 0.08, w: 7.6, h: 0.8, fontFace: F, align: "left", valign: "middle", margin: 0 });
  yy += 1.05;
});
s.addText("The unit of analysis becomes a Tasker within a metcat — every metric is computed relative to local peers.", {
  x: 0.7, y: 4.85, w: 8.6, h: 0.4, fontFace: F, fontSize: 12.5, italic: true, color: GREEN2, margin: 0 });
footer(s, 2);

// ===========================================================================
// 3-6. The comet + eyeball partitioning
// ===========================================================================
chartSlide(3, "Plotting & comparing each Tasker", "fig_12_comet.png",
  "x = rolling cumulative % of metcat invoices (top contributors at left) · y = close rate · hue = rolling % of revenue.");
chartSlide(4, "How does each Tasker compare to their metcat?", "fig_13_annotated_good_cohort.png",
  "Top-left: high volume AND high close rate relative to peers — our intuitive 'good' Taskers.");
chartSlide(5, "Can we group like Taskers…", "fig_14_annotated_groups.png",
  "The shape suggests natural groupings along the volume axis — but where exactly are the cut points?");
chartSlide(6, "…then partition them into tiers?", "fig_15_annotated_tiers.png",
  "Eyeballing tiers is fast, but it's biased and not reproducible. Can we do better?");

// ===========================================================================
// 7. Two ways to partition (light, two cards)
// ===========================================================================
s = pres.addSlide();
s.background = { color: CREAM_BG };
title(s, "Two ways to partition");
const cards = [
  ["Visual inspection", "“eyeball it”", [["Pro", "Quick to do once"], ["Con", "Not iterable; human bias"]]],
  ["Unsupervised learning", "k-means clustering", [["Pro", "Iterative discovery of hidden patterns"], ["Con", "Very dependent on a few inputs"]]],
];
cards.forEach((c, i) => {
  const cx = 0.7 + i * 4.5;
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: cx, y: 1.45, w: 4.1, h: 3.1, rectRadius: 0.08,
    fill: { color: i === 1 ? CARD : WHITE },
    line: { color: i === 1 ? GREEN2 : "D8DED2", width: i === 1 ? 1.5 : 1 },
    shadow: { type: "outer", color: "000000", blur: 6, offset: 2, angle: 90, opacity: 0.1 } });
  s.addText(c[0], { x: cx + 0.3, y: 1.65, w: 3.5, h: 0.45, fontFace: FH, fontSize: 19, bold: true, color: INK, margin: 0 });
  s.addText(c[1], { x: cx + 0.3, y: 2.12, w: 3.5, h: 0.35, fontFace: F, fontSize: 13, italic: true, color: MUTED, margin: 0 });
  let cy = 2.75;
  c[2].forEach(([k, v]) => {
    s.addText([
      { text: k + ": ", options: { bold: true, color: k === "Pro" ? GREEN2 : ORANGE } },
      { text: v, options: { color: INK } },
    ], { x: cx + 0.3, y: cy, w: 3.5, h: 0.55, fontFace: F, fontSize: 13.5, margin: 0, valign: "top" });
    cy += 0.62;
  });
});
footer(s, 7);

// ===========================================================================
// 8-9. Naive k-means fails
// ===========================================================================
chartSlide(8, "A quick pass at k-means doesn't seem helpful", "fig_17_annotated_naive_k4.png",
  "Clustering on {close rate, rolling invoices, rolling revenue} just re-discovers the volume axis → vertical stripes.");

s = pres.addSlide();
s.background = { color: CREAM_BG };
title(s, "…and adding clusters doesn't fix it");
const trip = ["fig_17_naive_k4.png", "fig_18_naive_k5.png", "fig_19_naive_k6.png"];
const labs = ["K = 4", "K = 5", "K = 6"];
const tw = 2.96, th = tw / CHART_RATIO;
trip.forEach((im, i) => {
  const tx = 0.42 + i * 3.08;
  s.addText(labs[i], { x: tx, y: 1.5, w: tw, h: 0.3, fontFace: F, fontSize: 13, bold: true,
    color: GREEN2, align: "center", margin: 0 });
  s.addImage({ path: path.join(FIG, im), x: tx, y: 1.85, w: tw, h: th,
    shadow: { type: "outer", color: "000000", blur: 5, offset: 1, angle: 90, opacity: 0.14 } });
});
s.addText("Whatever k we pick, the clusters stratify on volume alone and the 'good' cohort stays too large to base an Elite program on.", {
  x: 0.7, y: 1.85 + th + 0.35, w: 8.6, h: 0.6, fontFace: F, fontSize: 12.5, color: MUTED, align: "center", margin: 0 });
footer(s, 9);

// ===========================================================================
// 10. Insight divider (dark)
// ===========================================================================
s = pres.addSlide();
s.background = { color: GREEN };
s.addText("The fix: add a behavioral floor", {
  x: 0.8, y: 1.7, w: 8.4, h: 0.8, fontFace: FH, fontSize: 34, bold: true, color: CREAM, margin: 0 });
s.addText([
  { text: "Tasker-fault cancellations", options: { bold: true, color: ORANGE } },
  { text: " are an axis that is genuinely independent of volume. Feeding the clustering one orthogonal feature — instead of three collinear volume features — is what turns a useless partition into a defensible tiering.", options: { color: "C9D6C2" } },
], { x: 0.82, y: 2.7, w: 8.2, h: 1.4, fontFace: F, fontSize: 16, align: "left", margin: 0 });

// ===========================================================================
// 11-14. Cancel floor + clustering that works
// ===========================================================================
chartSlide(11, "Adding tasker-fault cancels improves the results", "fig_25_annotated_elite_box.png",
  "Now y = cancel rate. Elite candidates = high volume (low rolling rank) AND a low cancel floor.");
chartSlide(12, "Why it was worth doing: Volume × Reliability", "fig_27_annotated_matrix.png",
  "k=4 now resolves into four interpretable cohorts — three volume bands at low cancel, plus a high-cancel 'needs support' group.");
chartSlide(13, "What happens at a high cluster count?", "fig_28_annotated_k15.png",
  "Push k to 15 and the best-of-the-best cohort progressively shrinks — 'how elite' is a choice of k.");
chartSlide(14, "Cohorts hold up across feature pairs", "fig_29_annotated_circle.png",
  "Rolling invoices vs rolling revenue: the same cohorts tile cleanly along the diagonal.");

// ===========================================================================
// 15. Results table (light)
// ===========================================================================
s = pres.addSlide();
s.background = { color: CREAM_BG };
title(s, "Resulting US Tasker quality tiers");
const hdr = (t) => ({ text: t, options: { bold: true, color: CREAM, fill: { color: GREEN }, fontSize: 12, align: "center", valign: "middle" } });
const cell = (t, b = false, c = INK) => ({ text: t, options: { color: c, bold: b, fontSize: 12, align: "center", valign: "middle" } });
const lcell = (t, b = false, c = INK) => ({ text: t, options: { color: c, bold: b, fontSize: 12, align: "left", valign: "middle" } });
const rows = [
  [hdr("Tier"), hdr("Taskers"), hdr("% supply"), hdr("Monthly revenue"), hdr("Monthly invoices"), hdr("Cancel %")],
  [lcell("Cohort 1 — Elite", true, GREEN2), cell("1,400"), cell("2.4%"), cell("$580"), cell("12.9"), cell("2.6%")],
  [lcell("Cohort 1 — Total"), cell("6,069"), cell("10.4%"), cell("$416"), cell("9.4"), cell("3.1%")],
  [lcell("Cohort 2"), cell("12,533"), cell("21.4%"), cell("$141"), cell("3.5"), cell("4.1%")],
  [lcell("Cohort 3"), cell("35,916"), cell("61.3%"), cell("$22"), cell("0.6"), cell("2.0%")],
  [lcell("Cohort 4 — needs support"), cell("4,053"), cell("6.9%"), cell("$11"), cell("0.3"), cell("80.3%")],
];
s.addTable(rows, {
  x: 0.35, y: 1.35, w: 9.3, h: 2.7, colW: [2.7, 1.4, 1.3, 1.5, 1.3, 1.1],
  border: { pt: 0.5, color: "D8DED2" }, align: "center", valign: "middle",
  rowH: [0.55, 0.42, 0.42, 0.42, 0.42, 0.42],
  fill: { color: WHITE }, color: INK,
});
s.addText([
  { text: "Reproduces the deck's tiering: ", options: { color: MUTED } },
  { text: "cohort split ≈ 10 / 21 / 61 / 7%", options: { bold: true, color: GREEN2 } },
  { text: " (deck 11 / 23 / 58 / 8) and Elite ≈ 13 invoices / $580 (deck 12 / $530).", options: { color: MUTED } },
], { x: 0.5, y: 4.35, w: 9.0, h: 0.6, fontFace: F, fontSize: 12, align: "left", margin: 0 });
footer(s, 15);

// ===========================================================================
// 16-18. Model-evaluation section (technical rigor)
// ===========================================================================
divider("Did we pick the right model?",
  "Clustering has no ground-truth accuracy, so we pressure-tested the choice with the "
  + "conventional toolkit: internal validity, resample stability, and business recovery "
  + "— across eight unsupervised methods.");

chartSlideFit(16, "No k is statistically \"correct\" — so k=4 is a business call",
  "fig_model_selection.png", 2.619,
  "Elbow is smooth, silhouette flat, GMM BIC never bottoms: the supply is a continuum. "
  + "k=4 is chosen for legibility; the question is which method renders it best.");

chartSlideFit(17, "Accuracy vs interpretability across eight methods",
  "fig_accuracy_interpretability.png", 1.500,
  "K-means is the sweet spot — top validity + stability AND interpretable. HDBSCAN only "
  + "looks clean because it drops ~70% of Taskers as noise; fuzzy c-means ≈ k-means but flags boundary cases.");

// ===========================================================================
// 19-21. Impact section (post-rollout outcome)
// ===========================================================================
divider("What happened after rollout",
  "Shareable result: 1.5× as many Taskers met the Elite cancellation bar as before — "
  + "broad downward pressure on tasker-fault cancellation. Each avoided cancellation is a "
  + "booking that now completes: +1 invoice at $135.");

chartSlideFit(18, "Projected annual impact of the cancellation floor",
  "fig_impact_scenarios.png", 1.727,
  "Central case: ~+$2.9M/yr and ~+21k invoices (a ~1.4% lift), plausible range $1.8M–$4.1M. "
  + "Direct recovered-invoice channel only — reliability-driven retention upside is unmodeled.");

chartSlideFit(19, "Impact is a range, not a point",
  "fig_impact_sensitivity.png", 1.440,
  "Revenue as a function of the two uncertain levers — cancellation reduction and the "
  + "completion factor. The honest deliverable is the grid, with the central cell highlighted.");

// ===========================================================================
// Takeaways (dark)
// ===========================================================================
s = pres.addSlide();
s.background = { color: GREEN };
s.addText("What this shows", {
  x: 0.8, y: 0.7, w: 8.4, h: 0.7, fontFace: FH, fontSize: 30, bold: true, color: CREAM, margin: 0 });
const takeaways = [
  "Frame 'good' as performance relative to local peers (metcat), not absolute counts.",
  "Naive k-means on collinear volume features just re-finds volume — too coarse to act on.",
  "One orthogonal behavioral feature (tasker-fault cancels) unlocks a Volume × Reliability tiering.",
  "Pressure-tested it: k-means is the most valid + stable of eight methods, and stays interpretable.",
  "Post-rollout: 1.5× more Taskers held the cancellation bar → ~+$2.9M/yr, ~+21k invoices (central).",
];
s.addText(takeaways.map((t, i) => ({
  text: t, options: { bullet: { code: "2022" }, color: CREAM, breakLine: true, paraSpaceAfter: 9,
    fontSize: 14 },
})), { x: 0.85, y: 1.5, w: 8.3, h: 3.4, fontFace: F, align: "left", valign: "top" });
s.addText("Methodology recreated on fully synthetic data — no Taskrabbit data used.", {
  x: 0.85, y: 5.08, w: 8.3, h: 0.35, fontFace: F, fontSize: 11, italic: true, color: "9FB098", margin: 0 });

pres.writeFile({ fileName: path.join(DIR, "Elite_Metric_Regroup_methodology.pptx") })
  .then((fn) => console.log("wrote", fn));

import { useState, useEffect } from "react";

// ---------------------------------------------------------------------------
// Data — derived from UESP scrape via fetch_data.py + build_dataset.py
// Yield rates: spawn_count_in_region / global_max_spawn_count × 4.0 (scaled 0–4)
// global_max = 503 (Dragon's Tongue in Winterhold/Eastmarch). Only ingredients
// that appear in at least one canonical potion pair are included.
// ---------------------------------------------------------------------------

const REGIONS = {
  "The Rift (Southeast)": { "Ancestor Moth Wing": 0.3, "Bear Claws": 0.3, "Bleeding Crown": 0.477, "Blisterwort": 0.262, "Blue Mountain Flower": 0.891, "Canis Root": 0.692, "Charred Skeever Hide": 0.072, "Chaurus Eggs": 0.087, "Deathbell": 0.167, "Elves Ear": 0.111, "Fly Amanita": 0.485, "Garlic": 0.183, "Giant Lichen": 0.016, "Glowing Mushroom": 2.831, "Hanging Moss": 0.008, "Imp Stool": 0.247, "Jazbay Grapes": 0.032, "Juniper Berries": 0.016, "Large Antlers": 0.3, "Namira's Rot": 0.231, "Nightshade": 0.064, "Nirnroot": 0.111, "Purple Mountain Flower": 0.692, "Red Mountain Flower": 0.883, "Salt Pile": 0.366, "Scaly Pholiota": 0.032, "Skeever Tail": 0.024, "Slaughterfish Egg": 0.048, "Swamp Fungal Pod": 0.048, "White Cap": 0.358 },
  "Hjaalmarch / The Pale (North)": { "Abecean Longfin": 0.3, "Bear Claws": 0.3, "Bleeding Crown": 0.485, "Blisterwort": 0.573, "Blue Mountain Flower": 0.239, "Canis Root": 0.525, "Charred Skeever Hide": 0.064, "Chaurus Eggs": 0.08, "Chicken's Egg": 0.032, "Creep Cluster": 0.032, "Deathbell": 1.121, "Elves Ear": 0.048, "Fly Amanita": 0.509, "Garlic": 0.056, "Giant Lichen": 0.835, "Glowing Mushroom": 0.302, "Hagraven Feathers": 0.024, "Imp Stool": 0.668, "Juvenile Mudcrab": 0.3, "Large Antlers": 0.3, "Lavender": 0.429, "Luna Moth Wing": 0.04, "Namira's Rot": 0.628, "Nightshade": 0.215, "Scaly Pholiota": 0.032, "Skeever Tail": 0.095, "Slaughterfish Egg": 0.04, "Snowberries": 1.002, "Swamp Fungal Pod": 0.891, "Thistle Branch": 0.016, "Tundra Cotton": 0.429, "White Cap": 0.477 },
  "The Reach / Haafingar (West)": { "Abecean Longfin": 0.3, "Bear Claws": 0.3, "Bleeding Crown": 0.175, "Blisterwort": 0.087, "Blue Dartwing": 0.016, "Blue Mountain Flower": 0.231, "Canis Root": 0.024, "Chicken's Egg": 0.095, "Creep Cluster": 0.016, "Deathbell": 0.135, "Dragon's Tongue": 0.064, "Elves Ear": 0.358, "Fly Amanita": 0.787, "Garlic": 0.358, "Giant Lichen": 0.056, "Glowing Mushroom": 1.177, "Grass Pod": 1.01, "Hagraven Feathers": 0.151, "Hanging Moss": 1.845, "Hawk's Egg": 0.3, "Imp Stool": 0.215, "Jazbay Grapes": 0.119, "Juniper Berries": 2.449, "Juvenile Mudcrab": 0.3, "Large Antlers": 0.3, "Lavender": 0.111, "Luna Moth Wing": 0.016, "Namira's Rot": 0.223, "Nightshade": 0.111, "Nirnroot": 0.294, "Purple Mountain Flower": 0.485, "Red Mountain Flower": 0.557, "Skeever Tail": 0.087, "Slaughterfish Egg": 0.08, "Snowberries": 0.056, "Swamp Fungal Pod": 0.032, "Thistle Branch": 0.064, "Tundra Cotton": 0.159, "White Cap": 0.223, "Wild Grass Pod": 1.59 },
  "Whiterun Hold (Central Plains)": { "Bleeding Crown": 0.183, "Blisterwort": 0.024, "Blue Dartwing": 0.048, "Blue Mountain Flower": 0.414, "Charred Skeever Hide": 0.024, "Chaurus Eggs": 0.08, "Creep Cluster": 0.04, "Deathbell": 0.103, "Dragon's Tongue": 0.04, "Elves Ear": 0.143, "Garlic": 0.087, "Glowing Mushroom": 0.732, "Grass Pod": 0.008, "Hagraven Feathers": 0.04, "Hawk's Egg": 0.3, "Imp Stool": 0.151, "Jazbay Grapes": 0.032, "Large Antlers": 0.3, "Lavender": 0.907, "Nightshade": 0.159, "Nirnroot": 0.048, "Purple Mountain Flower": 0.62, "Red Mountain Flower": 0.167, "Salt Pile": 0.064, "Scaly Pholiota": 0.056, "Skeever Tail": 0.064, "Slaughterfish Egg": 0.056, "Thistle Branch": 0.366, "Tundra Cotton": 1.543, "White Cap": 0.159 },
  "Winterhold / Eastmarch (Northeast)": { "Bear Claws": 0.3, "Bleeding Crown": 0.024, "Blisterwort": 0.048, "Blue Dartwing": 0.016, "Canis Root": 0.048, "Charred Skeever Hide": 0.048, "Chaurus Eggs": 0.103, "Chicken's Egg": 0.048, "Creep Cluster": 1.869, "Deathbell": 0.032, "Dragon's Tongue": 4.0, "Elves Ear": 0.048, "Fly Amanita": 0.207, "Giant Lichen": 0.016, "Glowing Mushroom": 0.763, "Grass Pod": 0.374, "Hagraven Feathers": 0.056, "Hanging Moss": 0.016, "Jazbay Grapes": 2.537, "Juvenile Mudcrab": 0.3, "Namira's Rot": 0.087, "Nightshade": 0.119, "Nirnroot": 0.024, "Purple Mountain Flower": 0.326, "Red Mountain Flower": 0.469, "Salt Pile": 0.072, "Scaly Pholiota": 0.024, "Slaughterfish Egg": 0.056, "Snowberries": 0.628, "Thistle Branch": 0.27, "White Cap": 0.286 },
  "Falkreath (South)": { "Bear Claws": 0.3, "Blisterwort": 0.08, "Blue Mountain Flower": 0.286, "Chicken's Egg": 0.048, "Deathbell": 0.048, "Elves Ear": 0.024, "Hagraven Feathers": 0.024, "Hanging Moss": 0.509, "Imp Stool": 0.183, "Juniper Berries": 0.024, "Large Antlers": 0.3, "Namira's Rot": 0.167, "Nightshade": 0.183, "Nirnroot": 0.032, "Purple Mountain Flower": 0.692, "Red Mountain Flower": 0.207, "Skeever Tail": 0.127, "Snowberries": 0.771, "Thistle Branch": 1.034, "Tundra Cotton": 0.254, "White Cap": 0.175 },
};

const INGREDIENTS = ["Abecean Longfin", "Ancestor Moth Wing", "Bear Claws", "Bleeding Crown", "Blisterwort", "Blue Dartwing", "Blue Mountain Flower", "Canis Root", "Charred Skeever Hide", "Chaurus Eggs", "Chicken's Egg", "Creep Cluster", "Deathbell", "Dragon's Tongue", "Elves Ear", "Fly Amanita", "Garlic", "Giant Lichen", "Glowing Mushroom", "Grass Pod", "Hagraven Feathers", "Hanging Moss", "Hawk's Egg", "Imp Stool", "Jazbay Grapes", "Juniper Berries", "Juvenile Mudcrab", "Large Antlers", "Lavender", "Luna Moth Wing", "Namira's Rot", "Nightshade", "Nirnroot", "Purple Mountain Flower", "Red Mountain Flower", "Salt Pile", "Scaly Pholiota", "Skeever Tail", "Slaughterfish Egg", "Snowberries", "Swamp Fungal Pod", "Thistle Branch", "Tundra Cotton", "White Cap", "Wild Grass Pod"];

// One canonical ingredient pair per potion (highest combined yield across all regions)
const POTIONS = {
  "Poison of Damage Health":              { "Deathbell": 1, "Red Mountain Flower": 1 },
  "Poison of Damage Magicka":             { "Hanging Moss": 1, "Namira's Rot": 1 },
  "Poison of Damage Magicka Regen":       { "Blue Mountain Flower": 1, "Hanging Moss": 1 },
  "Poison of Damage Stamina":             { "Blisterwort": 1, "Canis Root": 1 },
  "Poison of Damage Stamina Regen":       { "Creep Cluster": 1, "Juniper Berries": 1 },
  "Poison of Fear":                       { "Blue Dartwing": 1, "Namira's Rot": 1 },
  "Poison of Frenzy":                     { "Blisterwort": 1, "Fly Amanita": 1 },
  "Poison of Lingering Damage Health":    { "Imp Stool": 1, "Slaughterfish Egg": 1 },
  "Poison of Lingering Damage Magicka":   { "Purple Mountain Flower": 1, "Swamp Fungal Pod": 1 },
  "Poison of Lingering Damage Stamina":   { "Hawk's Egg": 1, "Nightshade": 1 },
  "Poison of Paralysis":                  { "Canis Root": 1, "Imp Stool": 1 },
  "Poison of Slow":                       { "Deathbell": 1, "Large Antlers": 1 },
  "Poison of Weakness to Fire":           { "Bleeding Crown": 1, "Juniper Berries": 1 },
  "Poison of Weakness to Frost":          { "Elves Ear": 1, "White Cap": 1 },
  "Poison of Weakness to Magic":          { "Creep Cluster": 1, "Jazbay Grapes": 1 },
  "Poison of Weakness to Poison":         { "Bleeding Crown": 1, "Deathbell": 1 },
  "Poison of Weakness to Shock":          { "Giant Lichen": 1, "Hagraven Feathers": 1 },
  "Potion of Cure Disease":               { "Charred Skeever Hide": 1, "Juvenile Mudcrab": 1 },
  "Potion of Fortify Alteration":         { "Grass Pod": 1, "Wild Grass Pod": 1 },
  "Potion of Fortify Barter":             { "Dragon's Tongue": 1, "Tundra Cotton": 1 },
  "Potion of Fortify Block":              { "Bleeding Crown": 1, "Tundra Cotton": 1 },
  "Potion of Fortify Carry Weight":       { "Creep Cluster": 1, "Juvenile Mudcrab": 1 },
  "Potion of Fortify Conjuration":        { "Blue Mountain Flower": 1, "Lavender": 1 },
  "Potion of Fortify Destruction":        { "Glowing Mushroom": 1, "Nightshade": 1 },
  "Potion of Fortify Enchanting":         { "Ancestor Moth Wing": 1, "Snowberries": 1 },
  "Potion of Fortify Health":             { "Glowing Mushroom": 1, "Hanging Moss": 1 },
  "Potion of Fortify Heavy Armor":        { "Thistle Branch": 1, "White Cap": 1 },
  "Potion of Fortify Illusion":           { "Dragon's Tongue": 1, "Scaly Pholiota": 1 },
  "Potion of Fortify Light Armor":        { "Luna Moth Wing": 1, "Skeever Tail": 1 },
  "Potion of Fortify Magicka":            { "Jazbay Grapes": 1, "Tundra Cotton": 1 },
  "Potion of Fortify Marksman":           { "Canis Root": 1, "Elves Ear": 1 },
  "Potion of Fortify One-handed":         { "Bear Claws": 1, "Hanging Moss": 1 },
  "Potion of Fortify Restoration":        { "Abecean Longfin": 1, "Salt Pile": 1 },
  "Potion of Fortify Smithing":           { "Blisterwort": 1, "Glowing Mushroom": 1 },
  "Potion of Fortify Sneak":              { "Abecean Longfin": 1, "Purple Mountain Flower": 1 },
  "Potion of Fortify Stamina":            { "Large Antlers": 1, "Lavender": 1 },
  "Potion of Fortify Two-handed":         { "Dragon's Tongue": 1, "Fly Amanita": 1 },
  "Potion of Invisibility":               { "Chaurus Eggs": 1, "Nirnroot": 1 },
  "Potion of Regenerate Health":          { "Juniper Berries": 1, "Namira's Rot": 1 },
  "Potion of Regenerate Magicka":         { "Garlic": 1, "Jazbay Grapes": 1 },
  "Potion of Regenerate Stamina":         { "Fly Amanita": 1, "Juvenile Mudcrab": 1 },
  "Potion of Resist Fire":                { "Dragon's Tongue": 1, "Snowberries": 1 },
  "Potion of Resist Frost":               { "Purple Mountain Flower": 1, "Snowberries": 1 },
  "Potion of Resist Magic":               { "Lavender": 1, "Tundra Cotton": 1 },
  "Potion of Resist Poison":              { "Thistle Branch": 1, "Wild Grass Pod": 1 },
  "Potion of Resist Shock":               { "Glowing Mushroom": 1, "Snowberries": 1 },
  "Potion of Restore Health":             { "Blue Mountain Flower": 1, "Imp Stool": 1 },
  "Potion of Restore Magicka":            { "Creep Cluster": 1, "Red Mountain Flower": 1 },
  "Potion of Restore Stamina":            { "Bear Claws": 1, "Purple Mountain Flower": 1 },
  "Potion of Waterbreathing":             { "Chicken's Egg": 1, "Hawk's Egg": 1 },
};

const BUILDS = {
  "Heavy Armor Warrior": { "Potion of Fortify Health": 4.0, "Potion of Fortify Heavy Armor": 3.0, "Potion of Fortify Block": 3.0, "Potion of Restore Health": 3.0, "Potion of Restore Stamina": 2.0, "Potion of Fortify One-handed": 2.0, "Potion of Fortify Two-handed": 1.0, "Poison of Damage Health": 2.0, "Poison of Paralysis": 2.0 },
  "Stealth Archer":      { "Potion of Fortify Marksman": 4.0, "Potion of Invisibility": 4.0, "Potion of Fortify Sneak": 3.0, "Poison of Damage Health": 3.0, "Poison of Slow": 2.0, "Potion of Restore Stamina": 2.0, "Potion of Fortify Light Armor": 1.0 },
  "Pure Mage":           { "Potion of Fortify Destruction": 4.0, "Potion of Fortify Magicka": 3.0, "Potion of Regenerate Magicka": 3.0, "Potion of Restore Magicka": 3.0, "Potion of Invisibility": 2.0, "Poison of Damage Health": 2.0, "Potion of Fortify Restoration": 1.0, "Potion of Fortify Conjuration": 1.0 },
  "Illusion Assassin":   { "Potion of Invisibility": 4.0, "Potion of Fortify Illusion": 4.0, "Potion of Fortify Sneak": 3.0, "Poison of Damage Health": 3.0, "Poison of Paralysis": 3.0, "Poison of Lingering Damage Health": 2.0, "Potion of Restore Health": 1.0 },
  "Paladin":             { "Potion of Restore Health": 4.0, "Potion of Fortify Heavy Armor": 3.0, "Potion of Fortify Block": 3.0, "Potion of Cure Disease": 3.0, "Potion of Fortify Restoration": 2.0, "Potion of Resist Magic": 2.0, "Potion of Fortify One-handed": 2.0 },
  "Necromancer":         { "Potion of Fortify Conjuration": 4.0, "Potion of Fortify Magicka": 3.0, "Potion of Regenerate Magicka": 3.0, "Poison of Damage Health": 3.0, "Poison of Frenzy": 2.0, "Potion of Fortify Destruction": 2.0, "Potion of Invisibility": 1.0 },
};

const BUILD_ICONS = {
  "Heavy Armor Warrior": "🛡️",
  "Stealth Archer":      "🏹",
  "Pure Mage":           "🔮",
  "Illusion Assassin":   "🌑",
  "Paladin":             "✨",
  "Necromancer":         "💀",
};

const REGION_COLORS = {
  "The Rift (Southeast)":           "#c2813a",
  "Hjaalmarch / The Pale (North)":  "#4a7a8a",
  "The Reach / Haafingar (West)":   "#8a5a8a",
  "Whiterun Hold (Central Plains)": "#c4a832",
  "Winterhold / Eastmarch (Northeast)": "#7a9ab8",
  "Falkreath (South)":              "#5a8a4a",
};

// ---------------------------------------------------------------------------
// LP Simplex solver (minimization, Ax ≤ b) — no external dependencies
// ---------------------------------------------------------------------------

function solveLP(c, A_ub, b_ub, n) {
  const EPS = 1e-9;
  const m = A_ub.length;
  const total = n + m;

  let tab = [];
  for (let i = 0; i < m; i++) {
    let row = [...A_ub[i]];
    for (let j = 0; j < m; j++) row.push(i === j ? 1 : 0);
    row.push(b_ub[i]);
    tab.push(row);
  }
  let obj = [...c];
  for (let j = 0; j < m; j++) obj.push(0);
  obj.push(0);
  tab.push(obj);

  const cols = total + 1;
  let basis = Array.from({ length: m }, (_, i) => n + i);

  for (let iter = 0; iter < 3000; iter++) {
    const objRow = tab[m];
    let pivCol = -1, minVal = -EPS;
    for (let j = 0; j < cols - 1; j++) {
      if (objRow[j] < minVal) { minVal = objRow[j]; pivCol = j; }
    }
    if (pivCol === -1) break;

    let pivRow = -1, minRatio = Infinity;
    for (let i = 0; i < m; i++) {
      if (tab[i][pivCol] > EPS) {
        const r = tab[i][cols - 1] / tab[i][pivCol];
        if (r < minRatio) { minRatio = r; pivRow = i; }
      }
    }
    if (pivRow === -1) break;

    basis[pivRow] = pivCol;
    const piv = tab[pivRow][pivCol];
    for (let j = 0; j < cols; j++) tab[pivRow][j] /= piv;
    for (let i = 0; i <= m; i++) {
      if (i !== pivRow && Math.abs(tab[i][pivCol]) > EPS) {
        const f = tab[i][pivCol];
        for (let j = 0; j < cols; j++) tab[i][j] -= f * tab[pivRow][j];
      }
    }
  }

  const x = new Array(total).fill(0);
  for (let i = 0; i < m; i++) if (basis[i] < total) x[basis[i]] = tab[i][cols - 1];
  return x.slice(0, n);
}

function optimize(buildWeights, timeBudget) {
  const regions = Object.keys(REGIONS);
  const potions = Object.keys(POTIONS).filter(p => (buildWeights[p] || 0) > 0);
  const R = regions.length, P = potions.length;

  const Y = regions.map(r => INGREDIENTS.map(ing => REGIONS[r][ing] || 0));
  const Rec = potions.map(p => INGREDIENTS.map(ing => POTIONS[p][ing] || 0));

  const n = R + P;
  const c = new Array(n).fill(0);
  potions.forEach((p, pi) => { c[R + pi] = -(buildWeights[p] || 0); });

  const A_ub = [], b_ub = [];

  // Time budget: Σ x_r ≤ T
  const tRow = new Array(n).fill(0);
  regions.forEach((_, ri) => { tRow[ri] = 1; });
  A_ub.push(tRow); b_ub.push(timeBudget);

  // Supply: z_p ≤ Σ x_r·y_{r,i}  for each ingredient i in recipe[p]
  potions.forEach((_, pi) => {
    INGREDIENTS.forEach((_, ii) => {
      if (Rec[pi][ii] > 0) {
        const row = new Array(n).fill(0);
        regions.forEach((_, ri) => { row[ri] = -Y[ri][ii]; });
        row[R + pi] = Rec[pi][ii];
        A_ub.push(row); b_ub.push(0);
      }
    });
  });

  const sol = solveLP(c, A_ub, b_ub, n);

  const regionHours = {};
  regions.forEach((r, ri) => { regionHours[r] = Math.max(0, sol[ri] || 0); });

  const potionBatches = {};
  potions.forEach((p, pi) => { potionBatches[p] = Math.max(0, sol[R + pi] || 0); });

  const ingredientTotals = {};
  INGREDIENTS.forEach((ing, ii) => {
    const total = regions.reduce((s, r, ri) => s + (regionHours[r] || 0) * Y[ri][ii], 0);
    if (total > 0.01) ingredientTotals[ing] = total;
  });

  const obj = potions.reduce((s, p, pi) => s + (buildWeights[p] || 0) * (sol[R + pi] || 0), 0);
  return { regionHours, potionBatches, ingredientTotals, objective: obj };
}

// ---------------------------------------------------------------------------
// UI
// ---------------------------------------------------------------------------

const BAR_MAX_W = 160;

function RegionBar({ region, hours, maxHours }) {
  const pct = maxHours > 0 ? hours / maxHours : 0;
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 7 }}>
      <div style={{ width: 200, fontSize: 12, color: "#a09080", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{region}</div>
      <div style={{ flex: 1, height: 10, background: "#1a1410", borderRadius: 5 }}>
        <div style={{ width: `${pct * 100}%`, height: "100%", background: REGION_COLORS[region] || "#c2813a", borderRadius: 5, transition: "width 0.3s" }} />
      </div>
      <div style={{ width: 50, textAlign: "right", fontSize: 12, color: "#e8c87a" }}>{hours.toFixed(1)} hr</div>
    </div>
  );
}

function PotionCard({ name, batches, recipe }) {
  const isPoison = name.startsWith("Poison");
  return (
    <div style={{ background: "#111213", border: `1px solid ${isPoison ? "#3a1a1a" : "#1a1a2a"}`, borderRadius: 6, padding: "10px 12px", marginBottom: 6 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <div>
          <div style={{ fontSize: 12, color: isPoison ? "#c87a7a" : "#b0d0e8", fontWeight: "bold" }}>{name}</div>
          <div style={{ fontSize: 10, color: "#5a4030", marginTop: 2 }}>{recipe.join(" + ")}</div>
        </div>
        <div style={{ fontSize: 20, fontWeight: "bold", color: "#e8c87a", marginLeft: 8 }}>{batches.toFixed(1)}</div>
      </div>
    </div>
  );
}

export default function SkyrimAlchemyOptimizer() {
  const [selectedBuild, setSelectedBuild] = useState("Stealth Archer");
  const [customWeights, setCustomWeights] = useState(null);
  const [timeBudget, setTimeBudget] = useState(20);
  const [result, setResult] = useState(null);
  const [tab, setTab] = useState("regions");
  const [mode, setMode] = useState("preset");

  const weights = mode === "custom" && customWeights ? customWeights : BUILDS[selectedBuild];

  useEffect(() => {
    if (mode === "custom" && !customWeights) {
      setCustomWeights({ ...BUILDS["Stealth Archer"] });
    }
  }, [mode]);

  useEffect(() => {
    const res = optimize(weights, timeBudget);
    setResult(res);
  }, [selectedBuild, timeBudget, customWeights, mode]);

  const regionEntries = result
    ? Object.entries(result.regionHours).filter(([, h]) => h > 0.01).sort((a, b) => b[1] - a[1])
    : [];

  const potionEntries = result
    ? Object.entries(result.potionBatches).filter(([, b]) => b > 0.01).sort((a, b) => b[1] - a[1])
    : [];

  const maxHours = regionEntries.length > 0 ? regionEntries[0][1] : 1;

  return (
    <div style={{ background: "#0d0e0f", color: "#d4b896", fontFamily: "'Georgia', 'Palatino Linotype', serif", borderRadius: 8, overflow: "hidden", border: "1px solid #2a1e12" }}>
      {/* Header */}
      <div style={{ background: "linear-gradient(180deg, #1a0e06 0%, #0d0e0f 100%)", borderBottom: "1px solid #3a2810", padding: "16px 20px 14px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <span style={{ fontSize: 26 }}>⚗️</span>
          <div>
            <div style={{ fontSize: 16, fontWeight: "bold", color: "#e8c87a", letterSpacing: 1 }}>Skyrim Alchemy Optimizer</div>
            <div style={{ fontSize: 10, color: "#6a5040", letterSpacing: 2, textTransform: "uppercase", marginTop: 2 }}>Linear Programming · Region Allocation · Data from UESP</div>
          </div>
        </div>
      </div>

      <div style={{ display: "flex", flexWrap: "wrap", minHeight: 500 }}>
        {/* Left Panel */}
        <div style={{ width: 260, minWidth: 220, background: "#0f1011", borderRight: "1px solid #1a1208", padding: "16px 14px", display: "flex", flexDirection: "column", gap: 18 }}>

          {/* Mode Toggle */}
          <div>
            <div style={{ fontSize: 9, color: "#5a4030", letterSpacing: 3, textTransform: "uppercase", marginBottom: 8 }}>Character Build</div>
            <div style={{ display: "flex", borderRadius: 4, overflow: "hidden", border: "1px solid #2a1a08", marginBottom: 10 }}>
              {["preset","custom"].map(m => (
                <button key={m} onClick={() => setMode(m)} style={{ flex: 1, padding: "6px 0", background: mode === m ? "#3a2010" : "transparent", color: mode === m ? "#e8c87a" : "#5a4030", border: "none", cursor: "pointer", fontSize: 10, letterSpacing: 2, textTransform: "uppercase", fontFamily: "inherit" }}>
                  {m}
                </button>
              ))}
            </div>

            {mode === "preset" ? (
              <div style={{ display: "flex", flexDirection: "column", gap: 5 }}>
                {Object.keys(BUILDS).map(b => (
                  <button key={b} onClick={() => setSelectedBuild(b)} style={{ padding: "8px 12px", borderRadius: 4, border: `1px solid ${selectedBuild === b ? "#c2813a" : "#2a1a08"}`, background: selectedBuild === b ? "rgba(194,129,58,0.10)" : "transparent", color: selectedBuild === b ? "#e8c87a" : "#8a7060", cursor: "pointer", fontSize: 12, textAlign: "left", fontFamily: "inherit" }}>
                    {BUILD_ICONS[b]} {b}
                  </button>
                ))}
              </div>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: 7, maxHeight: 300, overflowY: "auto" }}>
                {Object.keys(POTIONS).map(p => (
                  <div key={p}>
                    <div style={{ display: "flex", justifyContent: "space-between", fontSize: 10, color: "#8a7060", marginBottom: 2 }}>
                      <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", flex: 1 }}>{p.replace("Potion of ", "").replace("Poison of ", "☠ ")}</span>
                      <span style={{ color: "#c2813a", marginLeft: 6 }}>{((customWeights || {})[p] || 0).toFixed(1)}</span>
                    </div>
                    <input type="range" min={0} max={5} step={0.5}
                      value={(customWeights || {})[p] || 0}
                      onChange={e => setCustomWeights(prev => ({ ...(prev || {}), [p]: parseFloat(e.target.value) }))}
                      style={{ width: "100%", accentColor: "#c2813a", height: 4 }}
                    />
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Time Budget */}
          <div>
            <div style={{ fontSize: 9, color: "#5a4030", letterSpacing: 3, textTransform: "uppercase", marginBottom: 8 }}>Foraging Time Budget</div>
            <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
              <input type="range" min={5} max={50} step={1} value={timeBudget}
                onChange={e => setTimeBudget(Number(e.target.value))}
                style={{ flex: 1, accentColor: "#c2813a" }}
              />
              <span style={{ color: "#e8c87a", fontWeight: "bold", minWidth: 44, textAlign: "right", fontSize: 13 }}>{timeBudget} hrs</span>
            </div>
          </div>

          {/* Objective */}
          {result && (
            <div style={{ background: "rgba(194,129,58,0.07)", border: "1px solid #2a1a08", borderRadius: 6, padding: 12 }}>
              <div style={{ fontSize: 9, color: "#5a4030", letterSpacing: 3, textTransform: "uppercase", marginBottom: 4 }}>Weighted Score</div>
              <div style={{ fontSize: 32, fontWeight: "bold", color: "#e8c87a", lineHeight: 1 }}>{result.objective.toFixed(1)}</div>
              <div style={{ fontSize: 10, color: "#6a5040", marginTop: 3 }}>Σ weight × batches</div>
            </div>
          )}

          {/* Model info */}
          <div style={{ fontSize: 10, color: "#4a3020", lineHeight: 1.8, borderTop: "1px solid #1a1208", paddingTop: 12 }}>
            <div style={{ color: "#6a5040", marginBottom: 4, fontStyle: "italic" }}>LP formulation</div>
            max Σ w<sub>p</sub>·z<sub>p</sub><br />
            s.t. Σ x<sub>r</sub> ≤ T<br />
            &nbsp;&nbsp;&nbsp;&nbsp;z<sub>p</sub> ≤ Σ x<sub>r</sub>·y<sub>ri</sub><br />
            &nbsp;&nbsp;&nbsp;&nbsp;x<sub>r</sub>, z<sub>p</sub> ≥ 0
          </div>
        </div>

        {/* Right Panel */}
        <div style={{ flex: 1, minWidth: 280, display: "flex", flexDirection: "column" }}>
          {/* Tab Bar */}
          <div style={{ display: "flex", borderBottom: "1px solid #1a1208", background: "#0f1011" }}>
            {["regions","potions","ingredients"].map(t => (
              <button key={t} onClick={() => setTab(t)} style={{ padding: "10px 16px", background: tab === t ? "#0d0e0f" : "transparent", color: tab === t ? "#e8c87a" : "#5a4030", border: "none", borderBottom: tab === t ? "2px solid #c2813a" : "2px solid transparent", cursor: "pointer", fontSize: 11, letterSpacing: 1, textTransform: "capitalize", fontFamily: "inherit" }}>
                {t}
              </button>
            ))}
          </div>

          <div style={{ flex: 1, padding: "16px 18px", overflowY: "auto", maxHeight: 480 }}>
            {tab === "regions" && (
              <div>
                <div style={{ fontSize: 11, color: "#5a4030", marginBottom: 14, letterSpacing: 1 }}>
                  Optimal hours per region — bars proportional to allocation
                </div>
                {regionEntries.length === 0 && <div style={{ color: "#4a3020", fontSize: 12 }}>No allocation — set some potion weights</div>}
                {regionEntries.map(([region, hrs]) => (
                  <RegionBar key={region} region={region} hours={hrs} maxHours={maxHours} />
                ))}
                <div style={{ fontSize: 10, color: "#3a2010", marginTop: 12, borderTop: "1px solid #1a1208", paddingTop: 10 }}>
                  Total: {regionEntries.reduce((s, [, h]) => s + h, 0).toFixed(1)} / {timeBudget} hrs
                </div>
              </div>
            )}

            {tab === "potions" && (
              <div>
                <div style={{ fontSize: 11, color: "#5a4030", marginBottom: 14, letterSpacing: 1 }}>
                  Craftable batches — limited by bottleneck ingredient in each recipe
                </div>
                {potionEntries.length === 0 && <div style={{ color: "#4a3020", fontSize: 12 }}>No potions — set some weights</div>}
                {potionEntries.map(([name, batches]) => (
                  <PotionCard key={name} name={name} batches={batches} recipe={Object.keys(POTIONS[name] || {})} />
                ))}
              </div>
            )}

            {tab === "ingredients" && (
              <div>
                <div style={{ fontSize: 11, color: "#5a4030", marginBottom: 14, letterSpacing: 1 }}>
                  Total ingredient units collected across all regions
                </div>
                {result && Object.entries(result.ingredientTotals).sort((a, b) => b[1] - a[1]).map(([ing, total]) => {
                  const pct = total / (result.ingredientTotals[Object.keys(result.ingredientTotals)[0]] || 1);
                  return (
                    <div key={ing} style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
                      <div style={{ width: 160, fontSize: 11, color: "#907060", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{ing}</div>
                      <div style={{ flex: 1, height: 8, background: "#1a1410", borderRadius: 4 }}>
                        <div style={{ width: `${pct * 100}%`, height: "100%", background: ACCENT_COLOR, borderRadius: 4, transition: "width 0.3s" }} />
                      </div>
                      <div style={{ width: 42, textAlign: "right", fontSize: 11, color: "#c2813a" }}>{total.toFixed(1)}</div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

const ACCENT_COLOR = "#c2813a";

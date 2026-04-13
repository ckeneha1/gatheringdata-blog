import { useState, useEffect } from "react";

// ---------------------------------------------------------------------------
// Data — derived from UESP scrape via fetch_data.py + build_dataset.py
// Yield rates: spawn_count_in_region / max_spawn_count × 4.0 (scaled 0–4)
// ---------------------------------------------------------------------------

const REGIONS = {
  "The Rift (Southeast)": { "Beehive Husk": 4.0, "Bleeding Crown": 3.934, "Bone Meal": 1.455, "Charred Skeever Hide": 4.0, "Chaurus Eggs": 3.385, "Deathbell": 0.596, "Elves Ear": 1.244, "Fire Salts": 1.6, "Fly Amanita": 2.465, "Frost Salts": 3.333, "Giant's Toe": 1.333, "Glowing Mushroom": 4.0, "Hagraven Claw": 2.667, "Human Flesh": 4.0, "Imp Stool": 1.476, "Nightshade": 1.185, "Purple Mountain Flower": 4.0, "Red Mountain Flower": 4.0, "River Betty": 4.0, "Rock Warbler Egg": 0.0, "Salt Pile": 4.0, "Scaly Pholiota": 2.286, "Skeever Tail": 0.75, "Slaughterfish Egg": 2.4, "Slaughterfish Scales": 2.667, "Small Pearl": 4.0, "Spider Egg": 0.0, "Taproot": 2.0, "Troll Fat": 1.333, "Vampire Dust": 4.0, "Void Salts": 1.2, "Wheat": 1.486, "White Cap": 3.0 },
  "Hjaalmarch / The Pale (North)": { "Beehive Husk": 0.0, "Bleeding Crown": 4.0, "Bone Meal": 3.273, "Charred Skeever Hide": 3.556, "Chaurus Eggs": 3.077, "Deathbell": 4.0, "Elves Ear": 0.533, "Fire Salts": 4.0, "Fly Amanita": 2.586, "Frost Salts": 1.333, "Giant's Toe": 3.333, "Glowing Mushroom": 0.427, "Hagraven Claw": 3.333, "Human Flesh": 4.0, "Imp Stool": 4.0, "Nightshade": 4.0, "Purple Mountain Flower": 0.0, "Red Mountain Flower": 0.0, "River Betty": 0.0, "Rock Warbler Egg": 0.0, "Salt Pile": 0.0, "Scaly Pholiota": 2.286, "Skeever Tail": 3.0, "Slaughterfish Egg": 2.0, "Slaughterfish Scales": 0.0, "Small Pearl": 0.0, "Spider Egg": 1.28, "Taproot": 4.0, "Troll Fat": 2.667, "Vampire Dust": 4.0, "Void Salts": 0.0, "Wheat": 0.686, "White Cap": 4.0 },
  "The Reach / Haafingar (West)": { "Beehive Husk": 0.0, "Bleeding Crown": 1.443, "Bone Meal": 4.0, "Charred Skeever Hide": 0.0, "Chaurus Eggs": 0.0, "Deathbell": 0.482, "Elves Ear": 4.0, "Fire Salts": 1.6, "Fly Amanita": 4.0, "Frost Salts": 4.0, "Giant's Toe": 4.0, "Glowing Mushroom": 1.663, "Hagraven Claw": 4.0, "Human Flesh": 2.0, "Imp Stool": 1.286, "Nightshade": 2.074, "Purple Mountain Flower": 2.805, "Red Mountain Flower": 2.523, "River Betty": 0.0, "Rock Warbler Egg": 2.0, "Salt Pile": 0.0, "Scaly Pholiota": 0.0, "Skeever Tail": 2.75, "Slaughterfish Egg": 4.0, "Slaughterfish Scales": 4.0, "Small Pearl": 0.0, "Spider Egg": 4.0, "Taproot": 4.0, "Troll Fat": 4.0, "Vampire Dust": 0.0, "Void Salts": 4.0, "Wheat": 1.486, "White Cap": 1.867 },
  "Whiterun Hold (Central Plains)": { "Beehive Husk": 2.0, "Bleeding Crown": 1.508, "Bone Meal": 3.273, "Charred Skeever Hide": 1.333, "Chaurus Eggs": 3.077, "Deathbell": 0.369, "Elves Ear": 1.6, "Fire Salts": 0.0, "Fly Amanita": 0.0, "Frost Salts": 0.0, "Giant's Toe": 0.0, "Glowing Mushroom": 1.034, "Hagraven Claw": 0.0, "Human Flesh": 0.0, "Imp Stool": 0.905, "Nightshade": 2.963, "Purple Mountain Flower": 3.586, "Red Mountain Flower": 0.757, "River Betty": 0.0, "Rock Warbler Egg": 0.0, "Salt Pile": 0.696, "Scaly Pholiota": 4.0, "Skeever Tail": 2.0, "Slaughterfish Egg": 2.8, "Slaughterfish Scales": 0.0, "Small Pearl": 0.0, "Spider Egg": 1.12, "Taproot": 0.0, "Troll Fat": 1.333, "Vampire Dust": 2.0, "Void Salts": 0.8, "Wheat": 1.943, "White Cap": 1.333 },
  "Winterhold / Eastmarch (Northeast)": { "Beehive Husk": 0.0, "Bleeding Crown": 0.197, "Bone Meal": 0.0, "Charred Skeever Hide": 2.667, "Chaurus Eggs": 4.0, "Deathbell": 0.113, "Elves Ear": 0.533, "Fire Salts": 3.6, "Fly Amanita": 1.051, "Frost Salts": 1.333, "Giant's Toe": 1.333, "Glowing Mushroom": 1.079, "Hagraven Claw": 1.333, "Human Flesh": 4.0, "Imp Stool": 0.0, "Nightshade": 2.222, "Purple Mountain Flower": 1.885, "Red Mountain Flower": 2.126, "River Betty": 0.0, "Rock Warbler Egg": 1.6, "Salt Pile": 0.783, "Scaly Pholiota": 1.714, "Skeever Tail": 0.0, "Slaughterfish Egg": 2.8, "Slaughterfish Scales": 1.778, "Small Pearl": 4.0, "Spider Egg": 3.04, "Taproot": 2.0, "Troll Fat": 4.0, "Vampire Dust": 2.0, "Void Salts": 1.2, "Wheat": 4.0, "White Cap": 2.4 },
  "Falkreath (South)": { "Beehive Husk": 0.0, "Bleeding Crown": 0.0, "Bone Meal": 0.0, "Charred Skeever Hide": 0.0, "Chaurus Eggs": 0.0, "Deathbell": 0.17, "Elves Ear": 0.267, "Fire Salts": 1.2, "Fly Amanita": 0.0, "Frost Salts": 3.333, "Giant's Toe": 0.0, "Glowing Mushroom": 0.0, "Hagraven Claw": 4.0, "Human Flesh": 0.0, "Imp Stool": 1.095, "Nightshade": 3.407, "Purple Mountain Flower": 4.0, "Red Mountain Flower": 0.937, "River Betty": 4.0, "Rock Warbler Egg": 4.0, "Salt Pile": 0.0, "Scaly Pholiota": 0.0, "Skeever Tail": 4.0, "Slaughterfish Egg": 0.0, "Slaughterfish Scales": 2.667, "Small Pearl": 0.0, "Spider Egg": 2.08, "Taproot": 0.0, "Troll Fat": 1.333, "Vampire Dust": 0.0, "Void Salts": 0.0, "Wheat": 0.0, "White Cap": 1.467 },
};

const INGREDIENTS = ["Beehive Husk","Bleeding Crown","Bone Meal","Charred Skeever Hide","Chaurus Eggs","Deathbell","Elves Ear","Fire Salts","Fly Amanita","Frost Salts","Giant's Toe","Glowing Mushroom","Hagraven Claw","Human Flesh","Imp Stool","Nightshade","Purple Mountain Flower","Red Mountain Flower","River Betty","Rock Warbler Egg","Salt Pile","Scaly Pholiota","Skeever Tail","Slaughterfish Egg","Slaughterfish Scales","Small Pearl","Spider Egg","Taproot","Troll Fat","Vampire Dust","Void Salts","Wheat","White Cap"];

// One canonical ingredient pair per potion (highest combined yield across all regions)
const POTIONS = {
  "Poison of Damage Health":           { "Nightshade": 1, "Troll Fat": 1 },
  "Poison of Frenzy":                  { "Fly Amanita": 1, "Troll Fat": 1 },
  "Poison of Lingering Damage Health": { "Slaughterfish Egg": 1, "Slaughterfish Scales": 1 },
  "Poison of Paralysis":               { "Human Flesh": 1, "Imp Stool": 1 },
  "Poison of Slow":                    { "Deathbell": 1, "River Betty": 1 },
  "Potion of Cure Disease":            { "Charred Skeever Hide": 1, "Vampire Dust": 1 },
  "Potion of Fortify Block":           { "Bleeding Crown": 1, "Slaughterfish Scales": 1 },
  "Potion of Fortify Conjuration":     { "Bone Meal": 1, "Frost Salts": 1 },
  "Potion of Fortify Destruction":     { "Glowing Mushroom": 1, "Nightshade": 1 },
  "Potion of Fortify Health":          { "Giant's Toe": 1, "Wheat": 1 },
  "Potion of Fortify Heavy Armor":     { "Slaughterfish Scales": 1, "White Cap": 1 },
  "Potion of Fortify Illusion":        { "Scaly Pholiota": 1, "Taproot": 1 },
  "Potion of Fortify Light Armor":     { "Beehive Husk": 1, "Skeever Tail": 1 },
  "Potion of Fortify Magicka":         { "Red Mountain Flower": 1, "Void Salts": 1 },
  "Potion of Fortify Marksman":        { "Elves Ear": 1, "Spider Egg": 1 },
  "Potion of Fortify One-handed":      { "Rock Warbler Egg": 1, "Small Pearl": 1 },
  "Potion of Fortify Restoration":     { "Salt Pile": 1, "Small Pearl": 1 },
  "Potion of Fortify Sneak":           { "Human Flesh": 1, "Purple Mountain Flower": 1 },
  "Potion of Fortify Two-handed":      { "Fly Amanita": 1, "Troll Fat": 1 },
  "Potion of Invisibility":            { "Chaurus Eggs": 1, "Vampire Dust": 1 },
  "Potion of Regenerate Magicka":      { "Fire Salts": 1, "Taproot": 1 },
  "Potion of Resist Magic":            { "Bleeding Crown": 1, "Hagraven Claw": 1 },
  "Potion of Restore Health":          { "Charred Skeever Hide": 1, "Wheat": 1 },
  "Potion of Restore Magicka":         { "Human Flesh": 1, "White Cap": 1 },
  "Potion of Restore Stamina":         { "Charred Skeever Hide": 1, "Purple Mountain Flower": 1 },
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

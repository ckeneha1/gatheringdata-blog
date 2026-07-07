"""
Emit a standalone interactive 3-D scatter (Plotly.js) of the Tasker supply, so the
"2.5-D via colour" slide charts can be compared against a true 3-D object.

Axes:  X = invoice contribution (rolling %)   [low = top contributor]
       Y = close rate  OR  tasker-fault cancel rate  (toggle)
       Z = revenue contribution (rolling %)   [low = top contributor]

Colour is freed up (no longer needed for revenue): toggle it onto any single axis
to emphasise that trend, or onto the k-means clusters (matching the deck).

Output: tasker_3d_scatter.html  (single self-contained file; data embedded inline).
"""

import json
import numpy as np
import pandas as pd

DIR = "analysis/taskrabbit-elite-criteria"
N = 15000
df = pd.read_csv(f"{DIR}/taskers_clustered.csv")
us = df[df.region == "US"]
sub = us.sample(n=min(N, len(us)), random_state=7)

data = {
    "x":  [round(float(v), 1) for v in sub.rolling_percent_total_invoices],
    "z":  [round(float(v), 1) for v in sub.rolling_percent_total_revenue_cents],
    "yc": [round(float(v), 4) for v in sub.percent_of_bookings_invoiced],
    "yk": [round(float(v), 4) for v in sub.percent_of_bookings_tasker_canceled],
    "cn": [int(v) for v in sub.naive_k4],    # clusters for the close-rate feature set
    "cf": [int(v) for v in sub.floor_k4],    # clusters for the cancel-floor feature set
}
DATA_JSON = json.dumps(data, separators=(",", ":"))

HTML = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Tasker supply — 3-D scatter</title>
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js" charset="utf-8"></script>
<style>
  :root{ --cream:#FFFCE4; --green:#13301F; --green2:#1B5E20; --ink:#1A2E22;
         --muted:#6b7b70; }
  *{ box-sizing:border-box; }
  html,body{ margin:0; height:100%; background:var(--cream);
             font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif; color:var(--ink); }
  #app{ display:flex; flex-direction:column; height:100vh; }
  header{ padding:10px 16px 6px; }
  h1{ font-size:16px; margin:0 0 2px; font-weight:700; }
  .sub{ font-size:12px; color:var(--muted); margin:0; }
  #bar{ display:flex; flex-wrap:wrap; gap:16px 22px; align-items:center;
        padding:8px 16px 10px; border-bottom:1px solid #e7e3c4; }
  .grp{ display:flex; flex-direction:column; gap:4px; }
  .lbl{ font-size:10px; text-transform:uppercase; letter-spacing:.06em; color:var(--muted); font-weight:700; }
  .seg{ display:inline-flex; border:1px solid #cfd6c8; border-radius:8px; overflow:hidden; background:#fff; }
  .seg button{ border:0; background:#fff; color:var(--ink); font-size:12.5px; padding:6px 11px;
               cursor:pointer; border-left:1px solid #e5e9df; }
  .seg button:first-child{ border-left:0; }
  .seg button:hover{ background:#f3f6ef; }
  .seg button.on{ background:var(--green); color:#fff; }
  .sld{ display:flex; align-items:center; gap:7px; font-size:12px; color:var(--muted); }
  input[type=range]{ width:96px; accent-color:var(--green2); }
  #plot{ flex:1 1 auto; min-height:0; }
  .hint{ font-size:11px; color:var(--muted); }
  code{ background:#f0efd6; padding:1px 4px; border-radius:4px; font-size:11px; }
</style>
</head>
<body>
<div id="app">
  <header>
    <h1>Tasker supply — true 3-D scatter</h1>
    <p class="sub">X = invoice contribution &middot; Y = close rate / cancel rate &middot; Z = revenue contribution &nbsp;|&nbsp;
      <span class="hint">low rolling&nbsp;% = <b>top</b> contributor. Drag to rotate &middot; scroll to zoom &middot; or snap to a plane.</span></p>
  </header>
  <div id="bar">
    <div class="grp"><span class="lbl">Y axis / version</span>
      <div class="seg" id="segVer">
        <button data-v="close" class="on">Close rate</button>
        <button data-v="cancel">Tasker-fault cancels</button>
      </div></div>
    <div class="grp"><span class="lbl">Colour by</span>
      <div class="seg" id="segCol">
        <button data-c="cluster" class="on">K-clusters</button>
        <button data-c="x">X &middot; Invoice</button>
        <button data-c="y">Y &middot; Rate</button>
        <button data-c="z">Z &middot; Revenue</button>
      </div></div>
    <div class="grp"><span class="lbl">Snap view</span>
      <div class="seg" id="segView">
        <button data-view="yx">Y&ndash;X</button>
        <button data-view="yz">Y&ndash;Z</button>
        <button data-view="xz">X&ndash;Z</button>
        <button data-view="3d">3-D</button>
      </div></div>
    <div class="grp"><span class="lbl">Point size</span>
      <div class="sld"><input id="size" type="range" min="1" max="6" step="0.2" value="2.4"><span id="sizeV">2.4</span></div></div>
    <div class="grp"><span class="lbl">Opacity</span>
      <div class="sld"><input id="opac" type="range" min="0.1" max="1" step="0.05" value="0.72"><span id="opacV">0.72</span></div></div>
  </div>
  <div id="plot"></div>
</div>

<script>
const DATA = __DATA__;
const el = document.getElementById('plot');

const CLUSTER_COLORS = ['#3B6FB0','#E08A3C','#3FA07A','#C0504D'];   // 0..3, distinct
const CONT = [[0,'#2c115f'],[0.3,'#9e2f7f'],[0.6,'#e34e65'],[1,'#f98e52']]; // rocket-ish
const AX = { x:'Invoice contribution (rolling %)', z:'Revenue contribution (rolling %)' };

let state = { version:'close', color:'cluster', size:2.4, opacity:0.72 };

const CAMERAS = {
  yx: { eye:{x:0,   y:0,   z:2.5}, up:{x:0,y:1,z:0} },   // look down Z: X horiz, Y vert
  yz: { eye:{x:2.5, y:0,   z:0  }, up:{x:0,y:1,z:0} },   // look down X: Z horiz, Y vert
  xz: { eye:{x:0,   y:-2.5,z:0  }, up:{x:0,y:0,z:1} },   // look down Y: X horiz, Z vert
  '3d':{ eye:{x:1.7,y:1.35,z:1.5}, up:{x:0,y:1,z:0} }
};
let currentCamera = CAMERAS['3d'];

const yField   = () => state.version==='close' ? DATA.yc : DATA.yk;
const clustField= () => state.version==='close' ? DATA.cn : DATA.cf;
const yLabel   = () => state.version==='close' ? 'Close rate (% bookings invoiced)'
                                               : 'Tasker-fault cancel rate';
function hovertmpl(){
  return 'Invoice %{x:.0f}<br>'+ (state.version==='close'?'Close':'Cancel')
       + ' %{y:.2f}<br>Revenue %{z:.0f}<extra></extra>';
}

function buildTraces(){
  const y = yField();
  if(state.color==='cluster'){
    const cf = clustField(), groups = {};
    for(let i=0;i<cf.length;i++){ (groups[cf[i]] = groups[cf[i]]||[]).push(i); }
    return Object.keys(groups).sort().map(k=>{
      const idx = groups[k];
      return { type:'scatter3d', mode:'markers', name:'Cluster '+k,
        x: idx.map(i=>DATA.x[i]), y: idx.map(i=>y[i]), z: idx.map(i=>DATA.z[i]),
        marker:{ size:state.size, opacity:state.opacity,
                 color:CLUSTER_COLORS[k % CLUSTER_COLORS.length] },
        hovertemplate: hovertmpl() };
    });
  }
  const field = state.color==='x' ? DATA.x : state.color==='z' ? DATA.z : y;
  const title = state.color==='x' ? 'Invoice' : state.color==='z' ? 'Revenue' : 'Rate';
  return [{ type:'scatter3d', mode:'markers', name:'',
    x:DATA.x, y:y, z:DATA.z,
    marker:{ size:state.size, opacity:state.opacity, color:field, colorscale:CONT,
      showscale:true, colorbar:{ title:{text:title,side:'right'}, thickness:12, len:0.6, x:0.98 } },
    hovertemplate: hovertmpl() }];
}

function layout(){
  const pane = { backgroundcolor:'#ffffff', showbackground:true, gridcolor:'#e6e6e6',
                 zerolinecolor:'#cccccc', titlefont:{size:11}, tickfont:{size:9} };
  return {
    paper_bgcolor:'#FFFCE4', margin:{l:0,r:0,t:0,b:0}, showlegend: state.color==='cluster',
    legend:{ x:0.01, y:0.98, bgcolor:'rgba(255,252,228,0.7)', font:{size:11},
             itemsizing:'constant' },
    scene:{
      xaxis:Object.assign({title:AX.x, range:[0,100]}, pane),
      yaxis:Object.assign({title:yLabel(), range:[0,1]}, pane),
      zaxis:Object.assign({title:AX.z, range:[0,100]}, pane),
      aspectmode:'cube', camera:currentCamera
    }
  };
}

function render(){
  Plotly.react(el, buildTraces(), layout(),
    {responsive:true, displaylogo:false, modeBarButtonsToRemove:['resetCameraLastSave3d']});
}

// preserve user rotation across control changes
function attachRelayout(){
  el.on('plotly_relayout', e=>{ if(e && e['scene.camera']) currentCamera = e['scene.camera']; });
}

function wireSeg(id, key, after){
  document.querySelectorAll('#'+id+' button').forEach(b=>{
    b.addEventListener('click', ()=>{
      document.querySelectorAll('#'+id+' button').forEach(x=>x.classList.remove('on'));
      b.classList.add('on'); after(b); });
  });
}
wireSeg('segVer','v', b=>{ state.version=b.dataset.v; render(); });
wireSeg('segCol','c', b=>{ state.color=b.dataset.c; render(); });
document.querySelectorAll('#segView button').forEach(b=>{
  b.addEventListener('click', ()=>{ currentCamera = CAMERAS[b.dataset.view];
    Plotly.relayout(el, {'scene.camera':currentCamera}); });
});
const sz=document.getElementById('size'), op=document.getElementById('opac');
sz.addEventListener('input', ()=>{ state.size=+sz.value; document.getElementById('sizeV').textContent=sz.value; render(); });
op.addEventListener('input', ()=>{ state.opacity=+op.value; document.getElementById('opacV').textContent=op.value; render(); });

Plotly.newPlot(el, buildTraces(), layout(),
  {responsive:true, displaylogo:false}).then(attachRelayout);
</script>
</body>
</html>
"""

out = f"{DIR}/tasker_3d_scatter.html"
with open(out, "w") as f:
    f.write(HTML.replace("__DATA__", DATA_JSON))
print(f"wrote {out}  ({len(sub):,} points, {len(HTML)+len(DATA_JSON):,} bytes)")

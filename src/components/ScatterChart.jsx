import { useState, useEffect } from 'react';

const W = 680;
const H = 480;
const MARGIN = { top: 20, right: 30, bottom: 52, left: 62 };
const PW = W - MARGIN.left - MARGIN.right;
const PH = H - MARGIN.top - MARGIN.bottom;

const COLOR_MAP = {
  Blue: '#3b82c4',
  Red: '#d95f3b',
  Green: '#3a8a50',
  White: '#b8860b',
  Black: '#7c5cbf',
  Colorless: '#8c8c8c',
  Multicolor: '#c8932a',
};

function parseCSV(text) {
  const lines = text.trim().split('\n');
  const headers = lines[0].split(',').map((h) => h.trim());
  return lines.slice(1).map((line) => {
    const vals = line.split(',');
    const obj = {};
    headers.forEach((h, i) => {
      obj[h] = vals[i]?.trim() ?? '';
    });
    return obj;
  });
}

function x(v) {
  return (v / 100) * PW;
}
function y(v) {
  return PH - (v / 100) * PH;
}

const TICKS = [0, 25, 50, 75, 100];

export default function ScatterChart() {
  const [data, setData] = useState([]);
  const [filter, setFilter] = useState('');
  const [tooltip, setTooltip] = useState(null);

  useEffect(() => {
    fetch('/data/mtg-legacy-tournament-gap.csv')
      .then((r) => r.text())
      .then((text) => {
        const rows = parseCSV(text)
          .map((r) => ({
            name: r.card_name,
            x: parseFloat(r.pctrank_power),
            y: parseFloat(r.pctrank_prevalence_flat),
            color: r.color,
          }))
          .filter((r) => !isNaN(r.x) && !isNaN(r.y));
        setData(rows);
      });
  }, []);

  const q = filter.toLowerCase().trim();
  const matches = q ? data.filter((d) => d.name.toLowerCase().includes(q)) : [];

  return (
    <div>
      <div style={{ overflowX: 'auto' }}>
        <svg
          viewBox={`0 0 ${W} ${H}`}
          style={{
            width: '100%',
            maxWidth: W,
            display: 'block',
            background: '#f8f7f4',
            borderRadius: 10,
            border: '1px solid #e4e0d8',
          }}
        >
          <g transform={`translate(${MARGIN.left},${MARGIN.top})`}>
            {/* Grid */}
            {TICKS.map((v) => (
              <g key={v}>
                <line x1={x(v)} y1={0} x2={x(v)} y2={PH} stroke="#e2ddd6" strokeWidth={1} />
                <line x1={0} y1={y(v)} x2={PW} y2={y(v)} stroke="#e2ddd6" strokeWidth={1} />
                <text x={x(v)} y={PH + 18} textAnchor="middle" fontSize={11} fill="#999">
                  {v}
                </text>
                <text x={-10} y={y(v) + 4} textAnchor="end" fontSize={11} fill="#999">
                  {v}
                </text>
              </g>
            ))}

            {/* Diagonal reference */}
            <line
              x1={x(0)}
              y1={y(0)}
              x2={x(100)}
              y2={y(100)}
              stroke="#ccc"
              strokeWidth={1}
              strokeDasharray="5 4"
            />

            {/* Axis labels */}
            <text
              x={PW / 2}
              y={PH + 44}
              textAnchor="middle"
              fontSize={12}
              fill="#666"
            >
              Power score percentile
            </text>
            <text
              transform={`rotate(-90)`}
              x={-(PH / 2)}
              y={-48}
              textAnchor="middle"
              fontSize={12}
              fill="#666"
            >
              Prevalence percentile
            </text>

            {/* Points */}
            {data.map((d, i) => {
              const isMatch = q && d.name.toLowerCase().includes(q);
              const dimmed = q && !isMatch;
              const fill = COLOR_MAP[d.color] ?? '#888';
              return (
                <circle
                  key={i}
                  cx={x(d.x)}
                  cy={y(d.y)}
                  r={isMatch ? 6.5 : 3.5}
                  fill={fill}
                  opacity={dimmed ? 0.08 : isMatch ? 1 : 0.6}
                  stroke={isMatch ? '#1a1a1a' : 'none'}
                  strokeWidth={isMatch ? 1.5 : 0}
                  style={{ cursor: 'crosshair' }}
                  onMouseEnter={() => setTooltip(d)}
                  onMouseLeave={() => setTooltip(null)}
                />
              );
            })}

            {/* Tooltip */}
            {tooltip && (() => {
              const tx = x(tooltip.x);
              const ty = y(tooltip.y);
              const boxW = 172;
              const boxH = 56;
              const bx = tx + boxW + 12 > PW ? tx - boxW - 10 : tx + 10;
              const by = ty - boxH / 2 < 0 ? 2 : ty + boxH / 2 > PH ? PH - boxH - 2 : ty - boxH / 2;
              return (
                <g style={{ pointerEvents: 'none' }}>
                  <rect
                    x={bx}
                    y={by}
                    width={boxW}
                    height={boxH}
                    rx={5}
                    fill="white"
                    stroke="#d0ccc4"
                    strokeWidth={1}
                    style={{ filter: 'drop-shadow(0 1px 4px rgba(0,0,0,0.10))' }}
                  />
                  <text x={bx + 10} y={by + 18} fontSize={11} fontWeight="600" fill="#1a1a1a">
                    {tooltip.name.length > 22 ? tooltip.name.slice(0, 21) + '…' : tooltip.name}
                  </text>
                  <text x={bx + 10} y={by + 33} fontSize={10} fill="#555">
                    {`Power: ${tooltip.x.toFixed(1)}th pctile`}
                  </text>
                  <text x={bx + 10} y={by + 47} fontSize={10} fill="#555">
                    {`Prevalence: ${tooltip.y.toFixed(1)}th pctile`}
                  </text>
                </g>
              );
            })()}
          </g>
        </svg>
      </div>

      {/* Filter */}
      <div
        style={{
          marginTop: '0.9em',
          display: 'flex',
          alignItems: 'center',
          gap: '0.6em',
          flexWrap: 'wrap',
        }}
      >
        <label htmlFor="card-filter" style={{ fontSize: '0.85em', color: '#666' }}>
          Find a card:
        </label>
        <input
          id="card-filter"
          type="text"
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          placeholder="e.g. Force of Will"
          style={{
            border: '1px solid #ccc',
            borderRadius: 5,
            padding: '4px 10px',
            fontSize: '0.875em',
            width: 210,
            outline: 'none',
            background: '#fff',
          }}
        />
        {q && (
          <span style={{ fontSize: '0.8em', color: '#888' }}>
            {matches.length} match{matches.length !== 1 ? 'es' : ''}
          </span>
        )}
      </div>

      {/* Color legend */}
      <div
        style={{
          marginTop: '0.6em',
          display: 'flex',
          gap: '1em',
          flexWrap: 'wrap',
        }}
      >
        {Object.entries(COLOR_MAP).map(([label, fill]) => (
          <span
            key={label}
            style={{ display: 'flex', alignItems: 'center', gap: '0.3em', fontSize: '0.78em', color: '#555' }}
          >
            <svg width={10} height={10} style={{ flexShrink: 0 }}>
              <circle cx={5} cy={5} r={4} fill={fill} opacity={0.8} />
            </svg>
            {label}
          </span>
        ))}
      </div>
    </div>
  );
}

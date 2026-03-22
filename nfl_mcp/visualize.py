"""
Interactive HTML visualization generator for NFL MCP.

Generates self-contained HTML dashboards with inline SVG charts and
JavaScript interactivity — no external dependencies required.
Inspired by Claude's inline visual capabilities.
"""

import json
import html
from typing import Any


def generate_qb_dashboard(
    player_name: str,
    weekly_data: list[dict[str, Any]],
    season_data: list[dict[str, Any]],
    qb_comparison: list[dict[str, Any]],
    team_colors: dict[str, str],
    season: int = 2025,
) -> str:
    """Generate a fully interactive HTML dashboard for a QB's season.

    Args:
        player_name: Display name (e.g., "Caleb Williams").
        weekly_data: List of dicts with week, epa_play, cpoe, success_rate,
                     pass_yards, tds, ints, dropbacks, comp_pct.
        season_data: List of dicts with season-level aggregates.
        qb_comparison: List of dicts with name, epa_play, cpoe for all
                       qualifying QBs.
        team_colors: Dict with 'primary' and 'accent' hex colors.
        season: The season year being visualized.

    Returns:
        A self-contained HTML string.
    """
    primary = team_colors.get("primary", "#0B162A")
    accent = team_colors.get("accent", "#E64100")

    weekly_json = json.dumps(weekly_data)
    season_json = json.dumps(season_data)
    qb_json = json.dumps(qb_comparison)

    player_escaped = html.escape(player_name)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{player_escaped} — {season} Season Dashboard</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: #f8f9fa; color: #333; padding: 20px;
  }}
  .dashboard {{
    max-width: 1200px; margin: 0 auto;
  }}
  .header {{
    text-align: center; margin-bottom: 30px; padding: 24px;
    background: linear-gradient(135deg, {primary}, {primary}dd);
    border-radius: 16px; color: white;
  }}
  .header h1 {{ font-size: 28px; margin-bottom: 6px; }}
  .header p {{ opacity: 0.85; font-size: 15px; }}
  .kpi-row {{
    display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
    gap: 12px; margin-bottom: 24px;
  }}
  .kpi {{
    background: white; border-radius: 12px; padding: 16px; text-align: center;
    box-shadow: 0 1px 4px rgba(0,0,0,0.08); transition: transform 0.15s;
  }}
  .kpi:hover {{ transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.12); }}
  .kpi .value {{ font-size: 26px; font-weight: 700; color: {primary}; }}
  .kpi .label {{ font-size: 12px; color: #888; margin-top: 4px; text-transform: uppercase; letter-spacing: 0.5px; }}
  .kpi .change {{ font-size: 12px; margin-top: 2px; }}
  .change.pos {{ color: #16a34a; }} .change.neg {{ color: #dc2626; }}
  .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 24px; }}
  @media (max-width: 768px) {{ .grid {{ grid-template-columns: 1fr; }} }}
  .panel {{
    background: white; border-radius: 12px; padding: 20px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.08);
  }}
  .panel h3 {{
    font-size: 15px; color: {primary}; margin-bottom: 14px;
    padding-bottom: 8px; border-bottom: 2px solid {accent}44;
  }}
  .full-width {{ grid-column: 1 / -1; }}
  svg {{ width: 100%; height: auto; display: block; }}
  .tooltip {{
    position: fixed; pointer-events: none; background: {primary}f0;
    color: white; padding: 8px 12px; border-radius: 8px; font-size: 13px;
    line-height: 1.5; z-index: 999; white-space: nowrap;
    box-shadow: 0 4px 12px rgba(0,0,0,0.2); display: none;
  }}
  .bar {{ cursor: pointer; transition: opacity 0.15s; }}
  .bar:hover {{ opacity: 0.85; }}
  .dot {{ cursor: pointer; transition: r 0.15s; }}
  .dot:hover {{ r: 8; }}
  .toggle-row {{
    display: flex; gap: 8px; margin-bottom: 12px; flex-wrap: wrap;
  }}
  .toggle-btn {{
    padding: 5px 12px; border-radius: 6px; border: 1.5px solid #ddd;
    background: white; font-size: 12px; cursor: pointer; transition: all 0.15s;
  }}
  .toggle-btn.active {{ background: {primary}; color: white; border-color: {primary}; }}
  .summary-table {{
    width: 100%; border-collapse: collapse; font-size: 14px;
  }}
  .summary-table th {{
    text-align: left; padding: 10px 12px; background: {primary}0a;
    border-bottom: 2px solid {primary}22; font-weight: 600; color: {primary};
  }}
  .summary-table td {{
    padding: 8px 12px; border-bottom: 1px solid #eee;
  }}
  .summary-table tr:hover td {{ background: {accent}08; }}
  .legend {{ display: flex; gap: 16px; margin-top: 8px; font-size: 12px; color: #888; }}
  .legend-item {{ display: flex; align-items: center; gap: 4px; }}
  .legend-swatch {{ width: 12px; height: 12px; border-radius: 3px; }}
</style>
</head>
<body>
<div class="dashboard">
  <div class="header">
    <h1>{player_escaped}</h1>
    <p>{season} Season Interactive Dashboard &middot; Powered by nflverse + NFL MCP</p>
  </div>

  <div id="kpiRow" class="kpi-row"></div>

  <div class="grid">
    <div class="panel">
      <h3>EPA per Dropback by Week</h3>
      <div class="toggle-row">
        <button class="toggle-btn active" onclick="toggleRolling('epa',this)">Show Rolling Avg</button>
      </div>
      <div id="epaChart"></div>
      <div class="legend">
        <div class="legend-item"><div class="legend-swatch" style="background:{accent}"></div> Positive EPA</div>
        <div class="legend-item"><div class="legend-swatch" style="background:#aaa"></div> Negative EPA</div>
        <div class="legend-item"><div class="legend-swatch" style="background:{primary}"></div> 3-Game Rolling</div>
      </div>
    </div>
    <div class="panel">
      <h3>CPOE by Week</h3>
      <div class="toggle-row">
        <button class="toggle-btn active" onclick="toggleRolling('cpoe',this)">Show Rolling Avg</button>
      </div>
      <div id="cpoeChart"></div>
    </div>
    <div class="panel">
      <h3>Success Rate Trend</h3>
      <div class="toggle-row">
        <button class="toggle-btn active" onclick="toggleRolling('success',this)">Show Rolling Avg</button>
      </div>
      <div id="successChart"></div>
    </div>
    <div class="panel">
      <h3>Passing Yards, TDs &amp; INTs</h3>
      <div class="toggle-row">
        <button class="toggle-btn active" data-metric="yards" onclick="toggleVolume(this,'yards')">Yards</button>
        <button class="toggle-btn active" data-metric="tds" onclick="toggleVolume(this,'tds')">TDs</button>
        <button class="toggle-btn active" data-metric="ints" onclick="toggleVolume(this,'ints')">INTs</button>
      </div>
      <div id="volumeChart"></div>
    </div>
    <div class="panel full-width">
      <h3>2025 QB Landscape — CPOE vs EPA</h3>
      <p style="font-size:12px;color:#888;margin:-8px 0 12px;">Hover over dots to see QB names. Click to highlight.</p>
      <div id="scatterChart"></div>
    </div>
    <div class="panel full-width">
      <h3>Season Summary</h3>
      <div id="summaryTable"></div>
    </div>
  </div>
</div>

<div class="tooltip" id="tip"></div>

<script>
// ── Data ──
const weekly = {weekly_json};
const seasons = {season_json};
const qbComp = {qb_json};
const PRIMARY = "{primary}";
const ACCENT = "{accent}";
const PLAYER = "{player_escaped}";

// ── Utilities ──
const tip = document.getElementById('tip');
function showTip(evt, html) {{
  tip.innerHTML = html;
  tip.style.display = 'block';
  tip.style.left = (evt.clientX + 14) + 'px';
  tip.style.top = (evt.clientY - 10) + 'px';
}}
function hideTip() {{ tip.style.display = 'none'; }}
document.addEventListener('mousemove', e => {{
  if (tip.style.display === 'block') {{
    tip.style.left = (e.clientX + 14) + 'px';
    tip.style.top = (e.clientY - 10) + 'px';
  }}
}});

function rollingAvg(arr, w) {{
  return arr.map((_, i) => {{
    const start = Math.max(0, i - w + 1);
    const slice = arr.slice(start, i + 1);
    return slice.reduce((a, b) => a + b, 0) / slice.length;
  }});
}}

function fmt(v, d=2) {{ return v == null ? '—' : v.toFixed(d); }}
function pct(v) {{ return v == null ? '—' : (v * 100).toFixed(1) + '%'; }}

// ── KPI Row ──
function buildKPIs() {{
  const last = seasons[seasons.length - 1];
  const prev = seasons.length > 1 ? seasons[seasons.length - 2] : null;
  const items = [
    {{ label: 'EPA/Play', val: fmt(last.epa_play, 3), change: prev ? last.epa_play - prev.epa_play : null, fmt: v => v.toFixed(3) }},
    {{ label: 'CPOE', val: fmt(last.cpoe, 1), change: prev ? last.cpoe - prev.cpoe : null, fmt: v => v.toFixed(1) }},
    {{ label: 'Success Rate', val: pct(last.success_rate), change: prev ? (last.success_rate - prev.success_rate) : null, fmt: v => (v*100).toFixed(1) + '%' }},
    {{ label: 'Pass Yards', val: Math.round(last.pass_yards).toLocaleString(), change: prev ? last.pass_yards - prev.pass_yards : null, fmt: v => Math.round(v).toLocaleString() }},
    {{ label: 'TDs', val: Math.round(last.tds), change: prev ? last.tds - prev.tds : null, fmt: v => Math.round(v) }},
    {{ label: 'INTs', val: Math.round(last.ints), change: prev ? last.ints - prev.ints : null, fmt: v => Math.round(v), invert: true }},
    {{ label: 'Dropbacks', val: Math.round(last.dropbacks).toLocaleString(), change: null }},
  ];
  const row = document.getElementById('kpiRow');
  row.innerHTML = items.map(k => {{
    let changeHtml = '';
    if (k.change != null) {{
      const isGood = k.invert ? k.change < 0 : k.change > 0;
      const cls = isGood ? 'pos' : 'neg';
      const sign = k.change > 0 ? '+' : '';
      changeHtml = `<div class="change ${{cls}}">${{sign}}${{k.fmt(k.change)}} vs prev</div>`;
    }}
    return `<div class="kpi"><div class="value">${{k.val}}</div><div class="label">${{k.label}}</div>${{changeHtml}}</div>`;
  }}).join('');
}}

// ── Bar chart with rolling avg ──
const rollingState = {{ epa: true, cpoe: true, success: true }};
const volumeState = {{ yards: true, tds: true, ints: true }};

function barChart(containerId, data, key, opts) {{
  const W = 540, H = 220, pad = {{ t: 10, r: 20, b: 36, l: 50 }};
  const cw = W - pad.l - pad.r, ch = H - pad.t - pad.b;
  const weeks = data.map(d => d.week);
  const vals = data.map(d => d[key]);
  const rolling = rollingAvg(vals, 3);
  const mn = Math.min(0, ...vals) * 1.15;
  const mx = Math.max(0, ...vals) * 1.15;
  const range = mx - mn || 1;
  const barW = Math.max(8, cw / weeks.length - 6);

  const x = i => pad.l + (i + 0.5) * (cw / weeks.length);
  const y = v => pad.t + ch - ((v - mn) / range) * ch;
  const zeroY = y(0);

  let svg = `<svg viewBox="0 0 ${{W}} ${{H}}" xmlns="http://www.w3.org/2000/svg">`;

  // Grid lines
  const ticks = 5;
  for (let i = 0; i <= ticks; i++) {{
    const v = mn + (range * i / ticks);
    const yy = y(v);
    svg += `<line x1="${{pad.l}}" y1="${{yy}}" x2="${{W-pad.r}}" y2="${{yy}}" stroke="#e5e7eb" stroke-width="1"/>`;
    svg += `<text x="${{pad.l-6}}" y="${{yy+4}}" text-anchor="end" font-size="10" fill="#999">${{opts.fmtTick ? opts.fmtTick(v) : v.toFixed(2)}}</text>`;
  }}

  // Zero line
  svg += `<line x1="${{pad.l}}" y1="${{zeroY}}" x2="${{W-pad.r}}" y2="${{zeroY}}" stroke="#999" stroke-width="1" stroke-dasharray="4"/>`;

  // Bars
  vals.forEach((v, i) => {{
    const bx = x(i) - barW / 2;
    const barH = Math.abs(y(v) - zeroY);
    const by = v >= 0 ? y(v) : zeroY;
    const color = v >= 0 ? ACCENT : '#aaa';
    const tipHtml = `<b>Week ${{weeks[i]}}</b><br>${{opts.label}}: ${{opts.fmtVal ? opts.fmtVal(v) : v.toFixed(3)}}`;
    svg += `<rect class="bar" x="${{bx}}" y="${{by}}" width="${{barW}}" height="${{barH}}" rx="3" fill="${{color}}" opacity="0.75"
      onmouseenter="showTip(event,'${{tipHtml.replace(/'/g, "\\\\'")}}')" onmouseleave="hideTip()"/>`;
  }});

  // Rolling avg line
  const showRolling = rollingState[key];
  if (showRolling) {{
    const pts = rolling.map((v, i) => `${{x(i)}},${{y(v)}}`).join(' ');
    svg += `<polyline points="${{pts}}" fill="none" stroke="${{PRIMARY}}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" class="rolling-${{key}}"/>`;
    rolling.forEach((v, i) => {{
      svg += `<circle class="dot" cx="${{x(i)}}" cy="${{y(v)}}" r="4" fill="${{PRIMARY}}" stroke="white" stroke-width="1.5"
        onmouseenter="showTip(event,'<b>Week ${{weeks[i]}}</b><br>Rolling: ${{opts.fmtVal ? opts.fmtVal(v) : v.toFixed(3)}}')" onmouseleave="hideTip()"/>`;
    }});
  }}

  // X-axis labels
  weeks.forEach((w, i) => {{
    svg += `<text x="${{x(i)}}" y="${{H - 6}}" text-anchor="middle" font-size="11" fill="#666">W${{w}}</text>`;
  }});

  svg += '</svg>';
  document.getElementById(containerId).innerHTML = svg;
}}

function toggleRolling(key, btn) {{
  rollingState[key] = !rollingState[key];
  btn.classList.toggle('active');
  renderCharts();
}}

// ── Volume chart (yards + TDs + INTs) ──
function volumeChart() {{
  const W = 540, H = 220, pad = {{ t: 10, r: 50, b: 36, l: 50 }};
  const cw = W - pad.l - pad.r, ch = H - pad.t - pad.b;
  const weeks = weekly.map(d => d.week);
  const yards = weekly.map(d => d.pass_yards);
  const tds = weekly.map(d => d.tds);
  const ints = weekly.map(d => d.ints);

  const maxY = Math.max(...yards) * 1.1;
  const maxTD = Math.max(...tds, ...ints, 1) + 1;
  const barW = Math.max(8, cw / weeks.length - 6);
  const x = i => pad.l + (i + 0.5) * (cw / weeks.length);
  const yL = v => pad.t + ch - (v / maxY) * ch;
  const yR = v => pad.t + ch - (v / maxTD) * ch;

  let svg = `<svg viewBox="0 0 ${{W}} ${{H}}" xmlns="http://www.w3.org/2000/svg">`;

  // Grid
  for (let i = 0; i <= 4; i++) {{
    const v = (maxY * i / 4);
    const yy = yL(v);
    svg += `<line x1="${{pad.l}}" y1="${{yy}}" x2="${{W-pad.r}}" y2="${{yy}}" stroke="#e5e7eb"/>`;
    svg += `<text x="${{pad.l-6}}" y="${{yy+4}}" text-anchor="end" font-size="10" fill="#999">${{Math.round(v)}}</text>`;
  }}

  // Right axis labels
  for (let i = 0; i <= maxTD; i++) {{
    svg += `<text x="${{W-pad.r+6}}" y="${{yR(i)+4}}" font-size="10" fill="${{ACCENT}}">${{i}}</text>`;
  }}

  // Bars (yards)
  if (volumeState.yards) {{
    yards.forEach((v, i) => {{
      svg += `<rect class="bar" x="${{x(i)-barW/2}}" y="${{yL(v)}}" width="${{barW}}" height="${{ch - (yL(v)-pad.t)}}" rx="3"
        fill="${{PRIMARY}}" opacity="0.65"
        onmouseenter="showTip(event,'<b>Week ${{weeks[i]}}</b><br>Yards: ${{v}}')" onmouseleave="hideTip()"/>`;
    }});
  }}

  // TD line
  if (volumeState.tds) {{
    const pts = tds.map((v, i) => `${{x(i)}},${{yR(v)}}`).join(' ');
    svg += `<polyline points="${{pts}}" fill="none" stroke="${{ACCENT}}" stroke-width="2.5"/>`;
    tds.forEach((v, i) => {{
      svg += `<circle class="dot" cx="${{x(i)}}" cy="${{yR(v)}}" r="5" fill="${{ACCENT}}" stroke="white" stroke-width="1.5"
        onmouseenter="showTip(event,'<b>Week ${{weeks[i]}}</b><br>TDs: ${{v}}')" onmouseleave="hideTip()"/>`;
    }});
  }}

  // INT line
  if (volumeState.ints) {{
    const pts = ints.map((v, i) => `${{x(i)}},${{yR(v)}}`).join(' ');
    svg += `<polyline points="${{pts}}" fill="none" stroke="#dc2626" stroke-width="2" stroke-dasharray="6,3"/>`;
    ints.forEach((v, i) => {{
      svg += `<circle class="dot" cx="${{x(i)}}" cy="${{yR(v)}}" r="4" fill="#dc2626" stroke="white" stroke-width="1.5"
        onmouseenter="showTip(event,'<b>Week ${{weeks[i]}}</b><br>INTs: ${{v}}')" onmouseleave="hideTip()"/>`;
    }});
  }}

  weeks.forEach((w, i) => {{
    svg += `<text x="${{x(i)}}" y="${{H-6}}" text-anchor="middle" font-size="11" fill="#666">W${{w}}</text>`;
  }});

  svg += '</svg>';
  document.getElementById('volumeChart').innerHTML = svg;
}}

function toggleVolume(btn, key) {{
  volumeState[key] = !volumeState[key];
  btn.classList.toggle('active');
  volumeChart();
}}

// ── Scatter plot ──
function scatterChart() {{
  const W = 800, H = 400, pad = {{ t: 20, r: 30, b: 40, l: 55 }};
  const cw = W - pad.l - pad.r, ch = H - pad.t - pad.b;

  const allEpa = qbComp.map(q => q.epa_play);
  const allCpoe = qbComp.map(q => q.cpoe);
  const epaMin = Math.min(...allEpa) - 0.02, epaMax = Math.max(...allEpa) + 0.02;
  const cpoeMin = Math.min(...allCpoe) - 1, cpoeMax = Math.max(...allCpoe) + 1;
  const avgEpa = allEpa.reduce((a,b) => a+b, 0) / allEpa.length;
  const avgCpoe = allCpoe.reduce((a,b) => a+b, 0) / allCpoe.length;

  const x = v => pad.l + ((v - cpoeMin) / (cpoeMax - cpoeMin)) * cw;
  const y = v => pad.t + ch - ((v - epaMin) / (epaMax - epaMin)) * ch;

  let svg = `<svg viewBox="0 0 ${{W}} ${{H}}" xmlns="http://www.w3.org/2000/svg">`;

  // Quadrant shading
  svg += `<rect x="${{x(avgCpoe)}}" y="${{pad.t}}" width="${{W-pad.r-x(avgCpoe)}}" height="${{y(avgEpa)-pad.t}}" fill="#16a34a08"/>`;
  svg += `<rect x="${{pad.l}}" y="${{y(avgEpa)}}" width="${{x(avgCpoe)-pad.l}}" height="${{pad.t+ch-y(avgEpa)}}" fill="#dc262608"/>`;

  // Avg lines
  svg += `<line x1="${{pad.l}}" y1="${{y(avgEpa)}}" x2="${{W-pad.r}}" y2="${{y(avgEpa)}}" stroke="#ccc" stroke-dasharray="4"/>`;
  svg += `<line x1="${{x(avgCpoe)}}" y1="${{pad.t}}" x2="${{x(avgCpoe)}}" y2="${{pad.t+ch}}" stroke="#ccc" stroke-dasharray="4"/>`;

  // Quadrant labels
  svg += `<text x="${{W-pad.r-8}}" y="${{pad.t+16}}" text-anchor="end" font-size="11" fill="#16a34a" opacity="0.6">Elite</text>`;
  svg += `<text x="${{pad.l+8}}" y="${{pad.t+ch-8}}" font-size="11" fill="#dc2626" opacity="0.6">Struggling</text>`;

  // Axis labels
  svg += `<text x="${{pad.l + cw/2}}" y="${{H-4}}" text-anchor="middle" font-size="12" fill="#666">CPOE (%)</text>`;
  svg += `<text x="14" y="${{pad.t + ch/2}}" text-anchor="middle" font-size="12" fill="#666" transform="rotate(-90,14,${{pad.t+ch/2}})">EPA / Play</text>`;

  // Axis ticks
  for (let i = 0; i <= 5; i++) {{
    const v = cpoeMin + (cpoeMax - cpoeMin) * i / 5;
    svg += `<text x="${{x(v)}}" y="${{H-22}}" text-anchor="middle" font-size="10" fill="#999">${{v.toFixed(1)}}</text>`;
  }}
  for (let i = 0; i <= 5; i++) {{
    const v = epaMin + (epaMax - epaMin) * i / 5;
    svg += `<text x="${{pad.l-8}}" y="${{y(v)+4}}" text-anchor="end" font-size="10" fill="#999">${{v.toFixed(2)}}</text>`;
  }}

  // QB dots
  let highlighted = null;
  qbComp.forEach(q => {{
    const isTarget = q.name.includes(PLAYER.split(' ').pop()) || q.name === PLAYER;
    const cx = x(q.cpoe), cy = y(q.epa_play);
    const tipHtml = `<b>${{q.name}}</b><br>EPA/play: ${{q.epa_play.toFixed(3)}}<br>CPOE: ${{q.cpoe.toFixed(1)}}%`;

    if (isTarget) {{
      svg += `<circle cx="${{cx}}" cy="${{cy}}" r="10" fill="${{ACCENT}}" stroke="${{PRIMARY}}" stroke-width="2.5" class="dot"
        onmouseenter="showTip(event,'${{tipHtml.replace(/'/g, "\\\\'")}}')" onmouseleave="hideTip()"/>`;
      svg += `<text x="${{cx+14}}" y="${{cy-6}}" font-size="13" font-weight="700" fill="${{ACCENT}}">${{q.name}}</text>`;
    }} else {{
      svg += `<circle cx="${{cx}}" cy="${{cy}}" r="5" fill="#bbb" opacity="0.7" class="dot"
        onmouseenter="showTip(event,'${{tipHtml.replace(/'/g, "\\\\'")}}')" onmouseleave="hideTip()"/>`;
      svg += `<text x="${{cx+8}}" y="${{cy+3}}" font-size="9" fill="#888" opacity="0"
        onmouseenter="this.setAttribute('opacity','1')" onmouseleave="this.setAttribute('opacity','0')">${{q.name}}</text>`;
    }}
  }});

  svg += '</svg>';
  document.getElementById('scatterChart').innerHTML = svg;
}}

// ── Summary table ──
function summaryTable() {{
  if (seasons.length < 2) return;
  const s0 = seasons[seasons.length - 2], s1 = seasons[seasons.length - 1];
  const rows = [
    ['EPA / Play', fmt(s0.epa_play, 3), fmt(s1.epa_play, 3), s1.epa_play - s0.epa_play, v => (v>0?'+':'')+v.toFixed(3)],
    ['CPOE', fmt(s0.cpoe, 1), fmt(s1.cpoe, 1), s1.cpoe - s0.cpoe, v => (v>0?'+':'')+v.toFixed(1)],
    ['Success Rate', pct(s0.success_rate), pct(s1.success_rate), s1.success_rate - s0.success_rate, v => (v>0?'+':'')+(v*100).toFixed(1)+'%'],
    ['Passing Yards', Math.round(s0.pass_yards).toLocaleString(), Math.round(s1.pass_yards).toLocaleString(), s1.pass_yards - s0.pass_yards, v => (v>0?'+':'')+Math.round(v).toLocaleString()],
    ['Touchdowns', Math.round(s0.tds), Math.round(s1.tds), s1.tds - s0.tds, v => (v>0?'+':'')+Math.round(v)],
    ['Interceptions', Math.round(s0.ints), Math.round(s1.ints), s1.ints - s0.ints, v => (v>0?'+':'')+Math.round(v), true],
    ['Dropbacks', Math.round(s0.dropbacks).toLocaleString(), Math.round(s1.dropbacks).toLocaleString(), s1.dropbacks - s0.dropbacks, v => (v>0?'+':'')+Math.round(v).toLocaleString()],
  ];
  let html = `<table class="summary-table"><thead><tr><th>Metric</th><th>${{s0.season}}</th><th>${{s1.season}}</th><th>Change</th></tr></thead><tbody>`;
  rows.forEach(([label, v0, v1, diff, fmtFn, invert]) => {{
    const isGood = invert ? diff < 0 : diff > 0;
    const cls = diff === 0 ? '' : (isGood ? 'pos' : 'neg');
    html += `<tr><td><b>${{label}}</b></td><td>${{v0}}</td><td>${{v1}}</td><td class="change ${{cls}}">${{fmtFn(diff)}}</td></tr>`;
  }});
  html += '</tbody></table>';
  document.getElementById('summaryTable').innerHTML = html;
}}

// ── Render all ──
function renderCharts() {{
  barChart('epaChart', weekly, 'epa_play', {{ label: 'EPA/Play', fmtVal: v => v.toFixed(3), fmtTick: v => v.toFixed(2) }});
  barChart('cpoeChart', weekly, 'cpoe', {{ label: 'CPOE', fmtVal: v => v.toFixed(1) + '%', fmtTick: v => v.toFixed(1) }});
  barChart('successChart', weekly, 'success_rate', {{ label: 'Success Rate', fmtVal: v => (v*100).toFixed(1) + '%', fmtTick: v => (v*100).toFixed(0) + '%' }});
  volumeChart();
  scatterChart();
}}

buildKPIs();
renderCharts();
summaryTable();
</script>
</body>
</html>"""

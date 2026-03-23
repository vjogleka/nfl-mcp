"""
Interactive HTML visualization generator for NFL MCP.

Generates self-contained HTML dashboards with inline SVG charts and
JavaScript interactivity — no external dependencies required.
Inspired by Claude's inline visual capabilities.
"""

import json
import html as html_mod
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

    player_escaped = html_mod.escape(player_name)

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


def generate_qb_comparison_dashboard(
    title: str,
    qb_season_data: list[dict],
    qb_weekly_data: list[dict],
    qb_info: dict[str, dict],
    seasons: list[int],
) -> str:
    """Generate an interactive multi-QB comparison dashboard.

    Args:
        title: Dashboard title (e.g., "2024 Draft Class: Year 1 vs Year 2").
        qb_season_data: List of dicts with name, season, epa_play, cpoe,
                        success_rate, pass_yards, tds, ints, dropbacks.
        qb_weekly_data: List of dicts with name, season, week, epa_play,
                        cpoe, success_rate, pass_yards, tds, ints.
        qb_info: Dict mapping passer_player_name to {display_name, team,
                 primary, accent}.
        seasons: List of season years being compared (e.g., [2024, 2025]).

    Returns:
        Self-contained HTML string.
    """
    title_escaped = html_mod.escape(title)
    season_json = json.dumps(qb_season_data)
    weekly_json = json.dumps(qb_weekly_data)
    info_json = json.dumps(qb_info)
    seasons_json = json.dumps(seasons)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title_escaped}</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: #f8f9fa; color: #333; padding: 20px;
  }}
  .dashboard {{ max-width: 1300px; margin: 0 auto; }}
  .header {{
    text-align: center; margin-bottom: 28px; padding: 24px;
    background: linear-gradient(135deg, #1a1a2e, #16213e);
    border-radius: 16px; color: white;
  }}
  .header h1 {{ font-size: 26px; margin-bottom: 6px; }}
  .header p {{ opacity: 0.8; font-size: 14px; }}
  .qb-toggles {{
    display: flex; justify-content: center; gap: 10px; margin-bottom: 24px; flex-wrap: wrap;
  }}
  .qb-toggle {{
    padding: 8px 18px; border-radius: 10px; border: 2.5px solid; cursor: pointer;
    font-size: 13px; font-weight: 600; transition: all 0.15s; background: white;
  }}
  .qb-toggle.active {{ color: white; }}
  .qb-toggle:hover {{ transform: translateY(-1px); box-shadow: 0 3px 10px rgba(0,0,0,0.15); }}
  .grid {{
    display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 24px;
  }}
  @media (max-width: 800px) {{ .grid {{ grid-template-columns: 1fr; }} }}
  .panel {{
    background: white; border-radius: 12px; padding: 20px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.08);
  }}
  .panel h3 {{
    font-size: 15px; color: #1a1a2e; margin-bottom: 14px;
    padding-bottom: 8px; border-bottom: 2px solid #e5e7eb;
  }}
  .full-width {{ grid-column: 1 / -1; }}
  svg {{ width: 100%; height: auto; display: block; }}
  .tooltip {{
    position: fixed; pointer-events: none; background: #1a1a2ef0;
    color: white; padding: 8px 12px; border-radius: 8px; font-size: 13px;
    line-height: 1.5; z-index: 999; white-space: nowrap;
    box-shadow: 0 4px 12px rgba(0,0,0,0.2); display: none;
  }}
  .dot {{ cursor: pointer; transition: r 0.15s; }}
  .dot:hover {{ r: 8; }}
  .bar {{ cursor: pointer; transition: opacity 0.15s; }}
  .bar:hover {{ opacity: 0.9; }}
  .legend {{
    display: flex; gap: 14px; margin-top: 10px; font-size: 12px;
    color: #666; flex-wrap: wrap; justify-content: center;
  }}
  .legend-item {{ display: flex; align-items: center; gap: 5px; }}
  .legend-swatch {{ width: 14px; height: 14px; border-radius: 4px; }}
  .season-tabs {{
    display: flex; gap: 6px; margin-bottom: 10px;
  }}
  .season-tab {{
    padding: 4px 14px; border-radius: 6px; border: 1.5px solid #ddd;
    background: white; font-size: 12px; cursor: pointer; transition: all 0.15s;
  }}
  .season-tab.active {{ background: #1a1a2e; color: white; border-color: #1a1a2e; }}
  .comp-table {{
    width: 100%; border-collapse: collapse; font-size: 13px;
  }}
  .comp-table th {{
    text-align: left; padding: 10px 8px; background: #f1f5f9;
    border-bottom: 2px solid #e2e8f0; font-weight: 600; color: #1a1a2e;
    position: sticky; top: 0;
  }}
  .comp-table td {{
    padding: 8px; border-bottom: 1px solid #f1f5f9;
  }}
  .comp-table tr:hover td {{ background: #f8fafc; }}
  .rank-1 {{ color: #d97706; font-weight: 700; }}
  .rank-2 {{ color: #6b7280; font-weight: 600; }}
  .rank-3 {{ color: #92400e; font-weight: 600; }}
  .metric-selector {{
    display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 10px;
  }}
  .metric-btn {{
    padding: 4px 12px; border-radius: 6px; border: 1.5px solid #ddd;
    background: white; font-size: 12px; cursor: pointer; transition: all 0.15s;
  }}
  .metric-btn.active {{ background: #1a1a2e; color: white; border-color: #1a1a2e; }}
  .change-pos {{ color: #16a34a; font-weight: 600; }}
  .change-neg {{ color: #dc2626; font-weight: 600; }}
</style>
</head>
<body>
<div class="dashboard">
  <div class="header">
    <h1>{title_escaped}</h1>
    <p>Interactive comparison dashboard &middot; Powered by nflverse + NFL MCP</p>
  </div>

  <div id="qbToggles" class="qb-toggles"></div>

  <div class="grid">
    <div class="panel">
      <h3>EPA / Play — Season Comparison</h3>
      <div id="epaGrouped"></div>
    </div>
    <div class="panel">
      <h3>Success Rate — Season Comparison</h3>
      <div id="srGrouped"></div>
    </div>
    <div class="panel">
      <h3>CPOE — Season Comparison</h3>
      <div id="cpoeGrouped"></div>
    </div>
    <div class="panel">
      <h3>CPOE vs EPA Landscape</h3>
      <div class="season-tabs" id="scatterTabs"></div>
      <div id="scatterPlot"></div>
    </div>
    <div class="panel full-width">
      <h3>Weekly Trends</h3>
      <div class="metric-selector" id="weeklyMetricSelector"></div>
      <div class="season-tabs" id="weeklySeasonTabs"></div>
      <div id="weeklyTrend"></div>
      <div class="legend" id="weeklyLegend"></div>
    </div>
    <div class="panel full-width">
      <h3>Full Comparison Table</h3>
      <div id="compTable"></div>
    </div>
  </div>
</div>

<div class="tooltip" id="tip"></div>

<script>
const seasonData = {season_json};
const weeklyData = {weekly_json};
const qbInfo = {info_json};
const SEASONS = {seasons_json};
const qbNames = Object.keys(qbInfo);

// State
let activeQBs = new Set(qbNames);
let scatterSeason = SEASONS[SEASONS.length - 1];
let weeklyMetric = 'epa_play';
let weeklySeason = SEASONS[SEASONS.length - 1];

const tip = document.getElementById('tip');
function showTip(evt, h) {{
  tip.innerHTML = h; tip.style.display = 'block';
  tip.style.left = (evt.clientX+14)+'px'; tip.style.top = (evt.clientY-10)+'px';
}}
function hideTip() {{ tip.style.display = 'none'; }}
document.addEventListener('mousemove', e => {{
  if(tip.style.display==='block') {{
    tip.style.left=(e.clientX+14)+'px'; tip.style.top=(e.clientY-10)+'px';
  }}
}});

function fmt(v,d=2) {{ return v==null?'—':v.toFixed(d); }}
function pct(v) {{ return v==null?'—':(v*100).toFixed(1)+'%'; }}

// ── QB toggles ──
function buildToggles() {{
  const el = document.getElementById('qbToggles');
  el.innerHTML = qbNames.map(name => {{
    const info = qbInfo[name];
    const active = activeQBs.has(name);
    const bg = active ? info.primary : 'white';
    const fg = active ? 'white' : info.primary;
    return `<div class="qb-toggle ${{active?'active':''}}" style="border-color:${{info.primary}};background:${{bg}};color:${{fg}}" onclick="toggleQB('${{name}}')">${{info.display_name}} <span style="opacity:0.7;font-size:11px">(${{info.team}})</span></div>`;
  }}).join('');
}}

function toggleQB(name) {{
  if (activeQBs.has(name)) {{ if (activeQBs.size > 1) activeQBs.delete(name); }}
  else activeQBs.add(name);
  buildToggles(); renderAll();
}}

// ── Grouped bar chart (season comparison) ──
function groupedBar(containerId, metric, opts) {{
  const W = 540, H = 240, pad = {{ t: 15, r: 20, b: 50, l: 55 }};
  const cw = W - pad.l - pad.r, ch = H - pad.t - pad.b;
  const names = qbNames.filter(n => activeQBs.has(n));
  const nQBs = names.length, nSeasons = SEASONS.length;
  const groupW = cw / nQBs;
  const barW = Math.min(28, (groupW - 12) / nSeasons);

  let allVals = [];
  names.forEach(n => SEASONS.forEach(s => {{
    const d = seasonData.find(r => r.name === n && r.season === s);
    if (d) allVals.push(d[metric]);
  }}));

  const mn = Math.min(0, ...allVals) * 1.15;
  const mx = Math.max(0, ...allVals) * 1.15;
  const range = mx - mn || 1;
  const y = v => pad.t + ch - ((v - mn) / range) * ch;
  const zeroY = y(0);

  let svg = `<svg viewBox="0 0 ${{W}} ${{H}}" xmlns="http://www.w3.org/2000/svg">`;

  // Grid
  for (let i = 0; i <= 4; i++) {{
    const v = mn + range * i / 4;
    const yy = y(v);
    svg += `<line x1="${{pad.l}}" y1="${{yy}}" x2="${{W-pad.r}}" y2="${{yy}}" stroke="#e5e7eb"/>`;
    svg += `<text x="${{pad.l-6}}" y="${{yy+4}}" text-anchor="end" font-size="10" fill="#999">${{opts.fmtTick(v)}}</text>`;
  }}
  svg += `<line x1="${{pad.l}}" y1="${{zeroY}}" x2="${{W-pad.r}}" y2="${{zeroY}}" stroke="#999" stroke-dasharray="4"/>`;

  names.forEach((name, qi) => {{
    const info = qbInfo[name];
    const gx = pad.l + (qi + 0.5) * groupW;
    const colors = [info.primary, info.accent || '#888'];

    SEASONS.forEach((s, si) => {{
      const d = seasonData.find(r => r.name === name && r.season === s);
      if (!d) return;
      const v = d[metric];
      const bx = gx + (si - nSeasons/2) * (barW + 2);
      const barH = Math.abs(y(v) - zeroY);
      const by = v >= 0 ? y(v) : zeroY;
      const tipHtml = `<b>${{info.display_name}}</b> (${{s}})<br>${{opts.label}}: ${{opts.fmtVal(v)}}`;
      svg += `<rect class="bar" x="${{bx}}" y="${{by}}" width="${{barW}}" height="${{barH}}" rx="3"
        fill="${{colors[si % colors.length]}}" opacity="0.85"
        onmouseenter="showTip(event,'${{tipHtml.replace(/'/g,"\\\\'")}}')" onmouseleave="hideTip()"/>`;
      svg += `<text x="${{bx + barW/2}}" y="${{(v >= 0 ? by - 4 : by + barH + 12)}}" text-anchor="middle"
        font-size="9" font-weight="600" fill="${{colors[si % colors.length]}}">${{opts.fmtVal(v)}}</text>`;
    }});

    // QB name label
    const short = info.display_name.split(' ').pop();
    svg += `<text x="${{gx}}" y="${{H-6}}" text-anchor="middle" font-size="11" fill="#444" font-weight="600">${{short}}</text>`;
  }});

  svg += '</svg>';
  document.getElementById(containerId).innerHTML = svg;
}}

// ── Scatter plot (single season) ──
function buildScatterTabs() {{
  const el = document.getElementById('scatterTabs');
  el.innerHTML = SEASONS.map(s =>
    `<div class="season-tab ${{s===scatterSeason?'active':''}}" onclick="scatterSeason=${{s}};buildScatterTabs();scatter()">${{s}}</div>`
  ).join('');
}}

function scatter() {{
  const W = 540, H = 320, pad = {{ t: 20, r: 20, b: 40, l: 55 }};
  const cw = W - pad.l - pad.r, ch = H - pad.t - pad.b;

  const pts = seasonData.filter(d => d.season === scatterSeason && activeQBs.has(d.name));
  if (pts.length === 0) {{ document.getElementById('scatterPlot').innerHTML = '<p style="color:#999;text-align:center">No data</p>'; return; }}

  const allE = pts.map(p => p.epa_play), allC = pts.map(p => p.cpoe);
  const eMin = Math.min(...allE)-0.03, eMax = Math.max(...allE)+0.03;
  const cMin = Math.min(...allC)-1.5, cMax = Math.max(...allC)+1.5;
  const avgE = allE.reduce((a,b)=>a+b,0)/allE.length;
  const avgC = allC.reduce((a,b)=>a+b,0)/allC.length;

  const x = v => pad.l + ((v-cMin)/(cMax-cMin))*cw;
  const y = v => pad.t + ch - ((v-eMin)/(eMax-eMin))*ch;

  let svg = `<svg viewBox="0 0 ${{W}} ${{H}}" xmlns="http://www.w3.org/2000/svg">`;
  svg += `<line x1="${{pad.l}}" y1="${{y(avgE)}}" x2="${{W-pad.r}}" y2="${{y(avgE)}}" stroke="#ddd" stroke-dasharray="4"/>`;
  svg += `<line x1="${{x(avgC)}}" y1="${{pad.t}}" x2="${{x(avgC)}}" y2="${{pad.t+ch}}" stroke="#ddd" stroke-dasharray="4"/>`;

  // Axis labels
  svg += `<text x="${{pad.l+cw/2}}" y="${{H-4}}" text-anchor="middle" font-size="11" fill="#888">CPOE</text>`;
  svg += `<text x="12" y="${{pad.t+ch/2}}" text-anchor="middle" font-size="11" fill="#888" transform="rotate(-90,12,${{pad.t+ch/2}})">EPA/Play</text>`;

  for (let i=0;i<=4;i++) {{
    const v=cMin+(cMax-cMin)*i/4;
    svg+=`<text x="${{x(v)}}" y="${{H-20}}" text-anchor="middle" font-size="9" fill="#aaa">${{v.toFixed(1)}}</text>`;
  }}
  for (let i=0;i<=4;i++) {{
    const v=eMin+(eMax-eMin)*i/4;
    svg+=`<text x="${{pad.l-6}}" y="${{y(v)+3}}" text-anchor="end" font-size="9" fill="#aaa">${{v.toFixed(2)}}</text>`;
  }}

  pts.forEach(p => {{
    const info = qbInfo[p.name];
    const cx = x(p.cpoe), cy = y(p.epa_play);
    const tipHtml = `<b>${{info.display_name}}</b> (${{p.season}})<br>EPA: ${{p.epa_play.toFixed(3)}}<br>CPOE: ${{p.cpoe.toFixed(1)}}%<br>Success: ${{(p.success_rate*100).toFixed(1)}}%`;
    svg += `<circle cx="${{cx}}" cy="${{cy}}" r="8" fill="${{info.primary}}" stroke="white" stroke-width="2" class="dot"
      onmouseenter="showTip(event,'${{tipHtml.replace(/'/g,"\\\\'")}}')" onmouseleave="hideTip()"/>`;
    svg += `<text x="${{cx+12}}" y="${{cy+4}}" font-size="11" font-weight="600" fill="${{info.primary}}">${{info.display_name.split(' ').pop()}}</text>`;
  }});

  svg += '</svg>';
  document.getElementById('scatterPlot').innerHTML = svg;
}}

// ── Weekly trend lines (multi-QB, single metric) ──
const weeklyMetrics = [
  {{ key: 'epa_play', label: 'EPA/Play', fmt: v => v.toFixed(3), fmtTick: v => v.toFixed(2) }},
  {{ key: 'success_rate', label: 'Success Rate', fmt: v => (v*100).toFixed(1)+'%', fmtTick: v => (v*100).toFixed(0)+'%' }},
  {{ key: 'cpoe', label: 'CPOE', fmt: v => v.toFixed(1)+'%', fmtTick: v => v.toFixed(1) }},
  {{ key: 'pass_yards', label: 'Pass Yards', fmt: v => Math.round(v).toString(), fmtTick: v => Math.round(v).toString() }},
];

function buildWeeklyControls() {{
  document.getElementById('weeklyMetricSelector').innerHTML = weeklyMetrics.map(m =>
    `<div class="metric-btn ${{m.key===weeklyMetric?'active':''}}" onclick="weeklyMetric='${{m.key}}';buildWeeklyControls();weeklyTrend()">${{m.label}}</div>`
  ).join('');
  document.getElementById('weeklySeasonTabs').innerHTML = SEASONS.map(s =>
    `<div class="season-tab ${{s===weeklySeason?'active':''}}" onclick="weeklySeason=${{s}};buildWeeklyControls();weeklyTrend()">${{s}}</div>`
  ).join('');
}}

function weeklyTrend() {{
  const W = 900, H = 300, pad = {{ t: 15, r: 20, b: 40, l: 55 }};
  const cw = W - pad.l - pad.r, ch = H - pad.t - pad.b;
  const mInfo = weeklyMetrics.find(m => m.key === weeklyMetric);

  const names = qbNames.filter(n => activeQBs.has(n));
  const filtered = weeklyData.filter(d => d.season === weeklySeason && names.includes(d.name));
  if (filtered.length === 0) {{
    document.getElementById('weeklyTrend').innerHTML = '<p style="color:#999;text-align:center;padding:40px">No weekly data for this selection</p>';
    document.getElementById('weeklyLegend').innerHTML = '';
    return;
  }}

  const allWeeks = [...new Set(filtered.map(d => d.week))].sort((a,b) => a-b);
  const allVals = filtered.map(d => d[weeklyMetric]).filter(v => v != null);
  const mn = Math.min(0, ...allVals) * 1.15;
  const mx = Math.max(...allVals) * 1.15;
  const range = mx - mn || 1;

  const x = w => pad.l + ((allWeeks.indexOf(w)) / Math.max(1, allWeeks.length - 1)) * cw;
  const y = v => pad.t + ch - ((v - mn) / range) * ch;

  let svg = `<svg viewBox="0 0 ${{W}} ${{H}}" xmlns="http://www.w3.org/2000/svg">`;

  // Grid
  for (let i = 0; i <= 4; i++) {{
    const v = mn + range * i / 4;
    const yy = y(v);
    svg += `<line x1="${{pad.l}}" y1="${{yy}}" x2="${{W-pad.r}}" y2="${{yy}}" stroke="#e5e7eb"/>`;
    svg += `<text x="${{pad.l-6}}" y="${{yy+4}}" text-anchor="end" font-size="10" fill="#999">${{mInfo.fmtTick(v)}}</text>`;
  }}

  if (mn < 0) svg += `<line x1="${{pad.l}}" y1="${{y(0)}}" x2="${{W-pad.r}}" y2="${{y(0)}}" stroke="#bbb" stroke-dasharray="4"/>`;

  allWeeks.forEach(w => {{
    svg += `<text x="${{x(w)}}" y="${{H-8}}" text-anchor="middle" font-size="10" fill="#888">W${{w}}</text>`;
  }});

  // Lines per QB
  names.forEach(name => {{
    const info = qbInfo[name];
    const qbWeeks = filtered.filter(d => d.name === name).sort((a,b) => a.week - b.week);
    if (qbWeeks.length < 2) return;

    const pts = qbWeeks.map(d => `${{x(d.week)}},${{y(d[weeklyMetric])}}`).join(' ');
    svg += `<polyline points="${{pts}}" fill="none" stroke="${{info.primary}}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" opacity="0.85"/>`;

    qbWeeks.forEach(d => {{
      const tipHtml = `<b>${{info.display_name}}</b> — Week ${{d.week}}<br>${{mInfo.label}}: ${{mInfo.fmt(d[weeklyMetric])}}`;
      svg += `<circle class="dot" cx="${{x(d.week)}}" cy="${{y(d[weeklyMetric])}}" r="4.5" fill="${{info.primary}}" stroke="white" stroke-width="1.5"
        onmouseenter="showTip(event,'${{tipHtml.replace(/'/g,"\\\\'")}}')" onmouseleave="hideTip()"/>`;
    }});
  }});

  svg += '</svg>';
  document.getElementById('weeklyTrend').innerHTML = svg;

  // Legend
  document.getElementById('weeklyLegend').innerHTML = names.map(n => {{
    const info = qbInfo[n];
    return `<div class="legend-item"><div class="legend-swatch" style="background:${{info.primary}}"></div>${{info.display_name}}</div>`;
  }}).join('');
}}

// ── Comparison table ──
function compTable() {{
  const names = qbNames.filter(n => activeQBs.has(n));
  const metrics = [
    {{ key: 'epa_play', label: 'EPA/Play', fmt: v => fmt(v,3), higher: true }},
    {{ key: 'cpoe', label: 'CPOE', fmt: v => fmt(v,1), higher: true }},
    {{ key: 'success_rate', label: 'Success %', fmt: v => pct(v), higher: true }},
    {{ key: 'pass_yards', label: 'Yards', fmt: v => Math.round(v).toLocaleString(), higher: true }},
    {{ key: 'tds', label: 'TDs', fmt: v => Math.round(v), higher: true }},
    {{ key: 'ints', label: 'INTs', fmt: v => Math.round(v), higher: false }},
    {{ key: 'dropbacks', label: 'Dropbacks', fmt: v => Math.round(v).toLocaleString(), higher: null }},
  ];

  let html = '<table class="comp-table"><thead><tr><th>QB</th>';
  SEASONS.forEach(s => metrics.forEach(m => {{ html += `<th>${{m.label}}<br><span style="font-weight:400;font-size:11px;color:#888">${{s}}</span></th>`; }}));
  html += '<th>EPA &Delta;</th><th>CPOE &Delta;</th><th>SR &Delta;</th>';
  html += '</tr></thead><tbody>';

  names.forEach(name => {{
    const info = qbInfo[name];
    html += `<tr><td><b style="color:${{info.primary}}">${{info.display_name}}</b><br><span style="font-size:11px;color:#888">${{info.team}}</span></td>`;

    const byS = {{}};
    SEASONS.forEach(s => {{
      byS[s] = seasonData.find(r => r.name === name && r.season === s);
    }});

    SEASONS.forEach(s => {{
      const d = byS[s];
      metrics.forEach(m => {{
        html += `<td>${{d ? m.fmt(d[m.key]) : '—'}}</td>`;
      }});
    }});

    // Deltas
    if (SEASONS.length >= 2) {{
      const s0 = byS[SEASONS[0]], s1 = byS[SEASONS[1]];
      const deltas = [
        {{ key: 'epa_play', fmt: v => (v>0?'+':'')+v.toFixed(3), higher: true }},
        {{ key: 'cpoe', fmt: v => (v>0?'+':'')+v.toFixed(1), higher: true }},
        {{ key: 'success_rate', fmt: v => (v>0?'+':'')+(v*100).toFixed(1)+'%', higher: true }},
      ];
      deltas.forEach(dd => {{
        if (s0 && s1) {{
          const diff = s1[dd.key] - s0[dd.key];
          const cls = diff > 0 === dd.higher ? 'change-pos' : 'change-neg';
          html += `<td class="${{cls}}">${{dd.fmt(diff)}}</td>`;
        }} else {{
          html += '<td>—</td>';
        }}
      }});
    }}

    html += '</tr>';
  }});

  html += '</tbody></table>';
  document.getElementById('compTable').innerHTML = html;
}}

// ── Render ──
function renderAll() {{
  groupedBar('epaGrouped', 'epa_play', {{ label: 'EPA/Play', fmtVal: v => v.toFixed(3), fmtTick: v => v.toFixed(2) }});
  groupedBar('srGrouped', 'success_rate', {{ label: 'Success Rate', fmtVal: v => (v*100).toFixed(1)+'%', fmtTick: v => (v*100).toFixed(0)+'%' }});
  groupedBar('cpoeGrouped', 'cpoe', {{ label: 'CPOE', fmtVal: v => v.toFixed(1), fmtTick: v => v.toFixed(1) }});
  scatter();
  weeklyTrend();
  compTable();
}}

buildToggles();
buildScatterTabs();
buildWeeklyControls();
renderAll();
</script>
</body>
</html>"""

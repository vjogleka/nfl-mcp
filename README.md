# NFL MCP Server

An MCP (Model Context Protocol) server that lets you query NFL play-by-play data and statistics using natural language through Claude Code or any MCP-compatible client.

Powered by [nflfastR/nflverse](https://nflfastr.com/) data, including EPA, CPOE, WPA, and 80+ play-level metrics going back to 1999.

## What It Does

Ask questions like:
- "Which QBs had the best EPA per dropback in the red zone last season?"
- "How did the Bears' pass defense rank in 2024?"
- "Compare Caleb Williams and Jayden Daniels' rookie seasons"
- "Show me the most efficient offenses on early downs in neutral game script"
- "Visualize Drake Maye's 2025 season progression"
- "Compare the 2024 draft class QBs across their first two years"

The database covers **every play, player, and team** since 1999 — not just QBs. You can analyze receivers, rushers, team units, matchups, game scripts, and more.

Claude translates your question into SQL, runs it against the local database, and interprets the results. It can also generate **interactive HTML dashboards** with charts you can hover, click, and toggle — right from a natural language request.

## Architecture

```
You (plain English) → Claude Code → MCP Tools → SQLite (nflverse data) → Results / Visualizations
```

The server exposes 8 tools:

| Tool | Purpose |
|---|---|
| `nfl_query` | Execute SQL against the NFL database |
| `nfl_schema` | Discover table structures and column names |
| `nfl_glossary` | Look up metric definitions (EPA, CPOE, etc.) |
| `nfl_search_player` | Find player names and IDs |
| `nfl_team_lookup` | Resolve team names to abbreviations |
| `nfl_roster` | Get a team's roster by season and position |
| `nfl_visualize` | Generate an interactive single-QB season dashboard |
| `nfl_compare_qbs` | Generate a multi-QB comparison dashboard |

## Setup

### Prerequisites

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

### 1. Clone / copy the project

```bash
# Copy the nfl-mcp directory to wherever you keep projects
cp -r nfl-mcp ~/projects/nfl-mcp
cd ~/projects/nfl-mcp
```

### 2. Install dependencies

```bash
# With uv (recommended)
uv venv
source .venv/bin/activate
uv pip install -e .

# Or with pip
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

### 3. Build the database (one-time)

This downloads data from nflverse GitHub releases and loads it into a local SQLite database at `~/nfl-data/nfl.db`.

```bash
# Load 2020-2025 seasons (default)
python -m nfl_mcp --init

# Or specify seasons
python -m nfl_mcp --init --seasons "2015,2016,2017,2018,2019,2020,2021,2022,2023,2024,2025"

# Or just specific tables
python -m nfl_mcp --init --tables "pbp,rosters"
```

**Note:** The initial download takes 2-5 minutes depending on how many seasons you load. Each season's PBP data is ~50MB compressed. The resulting SQLite database will be ~500MB-1GB for 5 seasons.

### 4. Add to Claude Code

Add the MCP server to your Claude Code configuration:

```bash
claude mcp add nfl-stats -- python -m nfl_mcp
```

Or manually add to your Claude Code MCP config (`~/.claude/claude_desktop_config.json` or similar):

```json
{
  "mcpServers": {
    "nfl-stats": {
      "command": "python",
      "args": ["-m", "nfl_mcp"],
      "cwd": "/path/to/nfl-mcp",
      "env": {
        "NFL_MCP_DATA_DIR": "/Users/yourname/nfl-data"
      }
    }
  }
}
```

If using a virtual environment, point to the venv Python:

```json
{
  "mcpServers": {
    "nfl-stats": {
      "command": "/path/to/nfl-mcp/.venv/bin/python",
      "args": ["-m", "nfl_mcp"]
    }
  }
}
```

### 5. Use it

In Claude Code, just ask NFL questions:

```
> Which teams had the highest EPA/play on passing downs in 2024?

> How did Justin Jefferson's target share change week over week last season?

> Show me red zone efficiency by team for the 2024 regular season
```

## Interactive Visualizations

The server can generate self-contained HTML dashboards with interactive SVG charts — no external dependencies, just open in a browser.

### Via MCP (ask Claude naturally)

When using Claude with the NFL MCP connected, just ask:

```
> Visualize Caleb Williams' 2025 season

> Compare Caleb Williams, Drake Maye, Jayden Daniels, Michael Penix,
  and Bo Nix across 2024 and 2025
```

Claude calls `nfl_visualize` or `nfl_compare_qbs` and returns HTML that you can save and open in your browser.

### Via CLI (standalone)

You can also generate dashboards directly from the command line:

```bash
# Single QB dashboard
python generate_dashboard.py
python generate_dashboard.py --player P.Mahomes --team KC --name "Patrick Mahomes"
python generate_dashboard.py --player J.Hurts --season 2024 --output hurts_2024.html

# Multi-QB comparison
python generate_comparison.py
python generate_comparison.py --players P.Mahomes J.Allen L.Jackson \
                              --names "Patrick Mahomes" "Josh Allen" "Lamar Jackson" \
                              --seasons 2023,2024,2025

# Then open in your browser
open draft_class_2024_comparison.html
```

### What's in the dashboards

**Single QB (`nfl_visualize` / `generate_dashboard.py`):**
- KPI cards with year-over-year changes
- EPA/play, CPOE, and success rate by week with toggleable 3-game rolling averages
- Passing yards, TDs, and INTs volume chart
- QB landscape scatter plot (CPOE vs EPA, all qualifying QBs)
- Season comparison summary table

**Multi-QB (`nfl_compare_qbs` / `generate_comparison.py`):**
- QB toggle buttons (click to show/hide players) with team colors
- Grouped bar charts comparing EPA, CPOE, and success rate by season
- CPOE vs EPA scatter with season toggle
- Weekly trend lines with metric and season selectors
- Full comparison table with color-coded year-over-year deltas

All charts include hover tooltips, and the HTML files are fully self-contained (~30-50KB each) — no internet connection or dependencies needed to view them.

### Note on scope

The dedicated visualization tools (`nfl_visualize`, `nfl_compare_qbs`) currently focus on QB analysis. For other positions and team-level analysis, use `nfl_query` to pull the data — Claude can help you interpret the results in tables and text. Additional visualization tools for team rankings, WR/RB comparisons, and matchup analysis are on the roadmap.

## Configuration

Environment variables:

| Variable | Default | Description |
|---|---|---|
| `NFL_MCP_DATA_DIR` | `~/nfl-data/` | Directory for cached data and database |
| `NFL_MCP_DB_PATH` | `~/nfl-data/nfl.db` | Path to SQLite database |
| `NFL_MCP_SEASONS` | `2020,2021,2022,2023,2024,2025` | Comma-separated seasons to load |

## Updating Data

During the NFL season, nflverse updates data nightly. To refresh:

```bash
# Rebuild just the current season's PBP
python -m nfl_mcp --init --seasons "2025" --tables "pbp,player_stats,seasonal_stats"

# Or rebuild everything
python -m nfl_mcp --init
```

## Database Tables

| Table | Rows | Description |
|---|---|---|
| `pbp` | 1.5M+ | One row per play with 80+ columns: EPA, WPA, CPOE, player IDs, game context, drive/series info (1999-present) |
| `player_stats` | — | Per-player, per-week stats: completions, attempts, yards, TDs, targets, receptions, rushing, receiving |
| `seasonal_stats` | — | Per-player, per-season totals for the same metrics |
| `rosters` | — | Player metadata: full name, position, height, weight, college, jersey number, years of experience |
| `schedules` | — | Game-level data: teams, final scores, spreads, over/unders, weather, stadium, roof type |
| `teams` | 32 | Team colors, logos, divisions, conferences (for visualization styling) |

### What you can query

The data supports analysis across **all positions and team units**, not just QBs:

- **QBs**: EPA/play, CPOE, success rate, air yards, pressure rate
- **WRs/TEs**: Targets, receptions, YAC, receiving EPA, route efficiency
- **RBs**: Rushing EPA, yards before/after contact, success rate by down
- **Team offense/defense**: Unit-level EPA, success rate, explosiveness
- **Game script**: Performance by win probability, score differential, quarter
- **Situational**: Red zone, 3rd down, 2-minute drill, no-huddle, shotgun
- **Historical**: Any season back to 1999, cross-era comparisons

## Key Metrics

| Metric | Column | Description |
|---|---|---|
| EPA | `epa` | Expected Points Added per play |
| CPOE | `cpoe` | Completion % Over Expected |
| WPA | `wpa` | Win Probability Added |
| Success Rate | `success` | Binary: EPA > 0 |
| Win Probability | `wp` | Pre-play win probability |
| Completion Prob | `cp` | Model-estimated completion probability |

## Common Query Patterns

```sql
-- QB EPA/play leaders (min 200 dropbacks)
SELECT passer_player_name, AVG(epa) as epa_play, COUNT(*) as plays
FROM pbp
WHERE season = 2024 AND season_type = 'REG' AND pass = 1
  AND passer_player_name IS NOT NULL
GROUP BY passer_player_name HAVING COUNT(*) >= 200
ORDER BY epa_play DESC

-- WR receiving EPA leaders
SELECT receiver_player_name, AVG(epa) as epa_target,
  COUNT(*) as targets, SUM(complete_pass) as receptions
FROM pbp
WHERE season = 2024 AND season_type = 'REG' AND pass = 1
  AND receiver_player_name IS NOT NULL
GROUP BY receiver_player_name HAVING COUNT(*) >= 60
ORDER BY epa_target DESC

-- Team offensive efficiency
SELECT posteam, AVG(epa) as epa_play, AVG(success) as success_rate
FROM pbp
WHERE season = 2024 AND season_type = 'REG' AND (pass = 1 OR rush = 1)
GROUP BY posteam
ORDER BY epa_play DESC

-- Team defensive EPA (lower = better)
SELECT defteam, AVG(epa) as epa_allowed, AVG(success) as opp_success
FROM pbp
WHERE season = 2024 AND season_type = 'REG' AND (pass = 1 OR rush = 1)
GROUP BY defteam
ORDER BY epa_allowed ASC

-- Red zone TD rate by team
SELECT posteam,
  SUM(CASE WHEN touchdown = 1 THEN 1 ELSE 0 END) * 1.0 / COUNT(*) as td_rate,
  COUNT(*) as plays
FROM pbp
WHERE season = 2024 AND season_type = 'REG'
  AND yardline_100 <= 20 AND (pass = 1 OR rush = 1)
GROUP BY posteam
ORDER BY td_rate DESC

-- RB rushing efficiency (min 100 carries)
SELECT rusher_player_name, AVG(epa) as epa_rush,
  AVG(success) as success_rate, COUNT(*) as carries
FROM pbp
WHERE season = 2024 AND season_type = 'REG' AND rush = 1
  AND rusher_player_name IS NOT NULL
GROUP BY rusher_player_name HAVING COUNT(*) >= 100
ORDER BY epa_rush DESC
```

## License

MIT. NFL data is provided by [nflverse](https://github.com/nflverse) under their terms of use.

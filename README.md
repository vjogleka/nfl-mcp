# NFL MCP Server

An MCP (Model Context Protocol) server that lets you query NFL play-by-play data and statistics using natural language through Claude Code or any MCP-compatible client.

Powered by [nflfastR/nflverse](https://nflfastr.com/) data, including EPA, CPOE, WPA, and 80+ play-level metrics going back to 1999.

## What It Does

Ask questions like:
- "Which QBs had the best EPA per dropback in the red zone last season?"
- "How did the Bears' pass defense rank in 2024?"
- "Compare Caleb Williams and Jayden Daniels' rookie seasons"
- "Show me the most efficient offenses on early downs in neutral game script"

Claude translates your question into SQL, runs it against the local database, and interprets the results.

## Architecture

```
You (plain English) → Claude Code → MCP Tools → SQLite (nflverse data) → Results
```

The server exposes 5 tools:

| Tool | Purpose |
|---|---|
| `nfl_query` | Execute SQL against the NFL database |
| `nfl_schema` | Discover table structures and column names |
| `nfl_glossary` | Look up metric definitions (EPA, CPOE, etc.) |
| `nfl_search_player` | Find player names and IDs |
| `nfl_team_lookup` | Resolve team names to abbreviations |

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

### `pbp` - Play-by-Play
The core table. One row per play with 80+ columns including EPA, WPA, CPOE, player names, game context, and drive/series info. Going back to 1999.

### `player_stats` - Weekly Player Stats
Per-player, per-week aggregated stats (completions, attempts, yards, TDs, etc.).

### `seasonal_stats` - Season Player Stats
Per-player, per-season aggregated stats.

### `rosters` - Team Rosters
Player metadata: full name, position, height, weight, college, jersey number, etc.

### `schedules` - Game Schedules
Game-level data: teams, scores, spreads, over/unders, weather, stadium info.

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
-- EPA/play leaders (QBs, min 200 dropbacks)
SELECT passer_player_name, AVG(epa) as epa_play, COUNT(*) as plays
FROM pbp
WHERE season = 2024 AND season_type = 'REG' AND pass = 1
  AND passer_player_name IS NOT NULL
GROUP BY passer_player_name
HAVING COUNT(*) >= 200
ORDER BY epa_play DESC

-- Team offensive efficiency
SELECT posteam, AVG(epa) as epa_play, AVG(success) as success_rate
FROM pbp
WHERE season = 2024 AND season_type = 'REG' AND (pass = 1 OR rush = 1)
GROUP BY posteam
ORDER BY epa_play DESC

-- Red zone TD rate
SELECT posteam,
  SUM(CASE WHEN touchdown = 1 THEN 1 ELSE 0 END) * 1.0 / COUNT(*) as td_rate,
  COUNT(*) as plays
FROM pbp
WHERE season = 2024 AND season_type = 'REG'
  AND yardline_100 <= 20 AND (pass = 1 OR rush = 1)
GROUP BY posteam
ORDER BY td_rate DESC
```

## License

MIT. NFL data is provided by [nflverse](https://github.com/nflverse) under their terms of use.

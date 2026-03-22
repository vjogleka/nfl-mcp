"""
NFL MCP Server

An MCP server that exposes NFL play-by-play and stats data from nflfastR/nflverse
through natural-language-friendly tools. Backed by a local SQLite database.

Usage:
    # First time: build the database
    python -m nfl_mcp.server --init

    # Run as MCP server (stdio transport for Claude Code)
    python -m nfl_mcp.server
"""

import argparse
import json
import logging
import sys
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional

from mcp.server.fastmcp import FastMCP, Context
from pydantic import BaseModel, Field, ConfigDict

from nfl_mcp.data import build_database, db_exists, get_db_path, get_seasons
from nfl_mcp.glossary import get_glossary_text, resolve_team, TEAM_ALIASES, GLOSSARY
from nfl_mcp.query_engine import QueryEngine
from nfl_mcp.visualize import generate_qb_dashboard, generate_qb_comparison_dashboard

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Lifespan: connect to DB on startup, close on shutdown
# ---------------------------------------------------------------------------

@dataclass
class AppState:
    engine: QueryEngine


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppState]:
    """Initialize database connection on startup."""
    db_path = get_db_path()

    if not db_exists(db_path):
        logger.error(
            f"Database not found at {db_path}. "
            "Run 'python -m nfl_mcp.server --init' to build it first."
        )
        raise RuntimeError(
            f"NFL database not found at {db_path}. "
            "Run 'python -m nfl_mcp.server --init' to build it."
        )

    engine = QueryEngine(db_path)
    engine.connect()
    logger.info("NFL MCP server ready")

    try:
        yield AppState(engine=engine)
    finally:
        engine.close()


# ---------------------------------------------------------------------------
# Server definition
# ---------------------------------------------------------------------------

mcp = FastMCP(
    "nfl_mcp",
    dependencies=["nfl_data_py", "pandas"],
    lifespan=app_lifespan,
)


# ---------------------------------------------------------------------------
# Input models
# ---------------------------------------------------------------------------

class ResponseFormat(str, Enum):
    MARKDOWN = "markdown"
    JSON = "json"


class NflQueryInput(BaseModel):
    """Input for executing a SQL query against the NFL database."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    sql: str = Field(
        ...,
        description=(
            "A SELECT SQL query to run against the NFL database. "
            "Only SELECT queries are allowed. "
            "Available tables: pbp (play-by-play), player_stats (weekly), "
            "seasonal_stats (season totals), rosters, schedules, teams (colors/logos/divisions). "
            "Use the nfl_schema tool first to see column names."
        ),
        min_length=5,
        max_length=5000,
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for readable tables, 'json' for raw data.",
    )


class NflSearchPlayerInput(BaseModel):
    """Input for searching players by name."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    name: str = Field(
        ...,
        description=(
            "Player name to search for. Supports partial matches. "
            "Examples: 'Mahomes', 'Justin Jefferson', 'J.Herbert'"
        ),
        min_length=2,
        max_length=100,
    )
    position: Optional[str] = Field(
        default=None,
        description="Optional position filter: QB, RB, WR, TE, etc.",
    )
    season: Optional[int] = Field(
        default=None,
        description="Optional season filter (e.g., 2024).",
        ge=1999,
        le=2026,
    )


class NflTeamLookupInput(BaseModel):
    """Input for resolving a team name."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    team: str = Field(
        ...,
        description=(
            "Team name, city, or abbreviation to look up. "
            "Examples: 'Bears', 'Kansas City', 'SF', 'niners'"
        ),
        min_length=2,
        max_length=50,
    )


class NflGlossaryInput(BaseModel):
    """Input for looking up a metric definition."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    term: Optional[str] = Field(
        default=None,
        description=(
            "Specific metric to look up (e.g., 'epa', 'cpoe', 'wpa'). "
            "Leave empty to get the full glossary."
        ),
    )


class NflRosterInput(BaseModel):
    """Input for fetching a team roster."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    team: str = Field(
        ...,
        description=(
            "Team abbreviation, name, city, or nickname. "
            "Examples: 'KC', 'Chiefs', 'Kansas City'. "
            "Use nfl_team_lookup first if unsure of the abbreviation."
        ),
        min_length=2,
        max_length=50,
    )
    season: Optional[int] = Field(
        default=None,
        description="Season year (e.g., 2024). Defaults to the most recent season available.",
        ge=1999,
        le=2026,
    )
    position: Optional[str] = Field(
        default=None,
        description="Optional position filter: QB, RB, WR, TE, OL, DL, LB, CB, S, K, P, etc.",
    )


class NflSchemaInput(BaseModel):
    """Input for getting database schema info."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    table: Optional[str] = Field(
        default=None,
        description=(
            "Specific table to describe: 'pbp', 'player_stats', "
            "'seasonal_stats', 'rosters', 'schedules', or 'teams'. "
            "Leave empty to get all tables."
        ),
    )
    sample_column: Optional[str] = Field(
        default=None,
        description=(
            "If provided along with a table, show distinct sample values "
            "for this column (useful for understanding enums like play_type, position)."
        ),
    )


class NflVisualizeInput(BaseModel):
    """Input for generating an interactive QB dashboard."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    player_name: str = Field(
        ...,
        description=(
            "QB name as it appears in passer_player_name (e.g., 'C.Williams', "
            "'P.Mahomes', 'J.Hurts'). Use nfl_search_player first if unsure."
        ),
        min_length=2,
        max_length=100,
    )
    display_name: Optional[str] = Field(
        default=None,
        description="Human-friendly display name (e.g., 'Caleb Williams'). Defaults to player_name.",
    )
    team: Optional[str] = Field(
        default=None,
        description="Team abbreviation for colors (e.g., 'CHI'). Auto-detected if omitted.",
    )
    season: int = Field(
        default=2025,
        description="Season to visualize.",
        ge=2006,
        le=2026,
    )
    min_dropbacks: int = Field(
        default=200,
        description="Minimum dropbacks for QB comparison scatter plot.",
        ge=50,
        le=600,
    )


class NflCompareQBsInput(BaseModel):
    """Input for generating a multi-QB comparison dashboard."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    players: list[str] = Field(
        ...,
        description=(
            "List of passer_player_name values to compare "
            "(e.g., ['C.Williams', 'D.Maye', 'J.Daniels']). "
            "Use nfl_search_player first if unsure of exact names."
        ),
        min_length=2,
        max_length=10,
    )
    display_names: Optional[list[str]] = Field(
        default=None,
        description=(
            "Optional list of human-friendly display names, same order as players. "
            "E.g., ['Caleb Williams', 'Drake Maye', 'Jayden Daniels']."
        ),
    )
    seasons: list[int] = Field(
        default=[2024, 2025],
        description="List of seasons to compare (e.g., [2024, 2025]).",
    )
    title: Optional[str] = Field(
        default=None,
        description="Dashboard title. Auto-generated if omitted.",
    )


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@mcp.tool(
    name="nfl_query",
    annotations={
        "title": "Query NFL Database",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def nfl_query(params: NflQueryInput, ctx: Context) -> str:
    """Execute a SQL query against the NFL play-by-play and stats database.

    This is the primary tool for answering NFL analytics questions. The database
    contains nflfastR/nflverse data including play-by-play (with EPA, WPA, CPOE),
    weekly and seasonal player stats, rosters, and schedules.

    Only SELECT queries are allowed. Use nfl_schema to discover table structures
    and nfl_glossary to understand metric definitions.

    Common query patterns:
    - EPA/play by team: SELECT posteam, AVG(epa) FROM pbp WHERE pass=1 AND season=2024 GROUP BY posteam
    - QB stats: SELECT passer_player_name, AVG(cpoe), AVG(epa) FROM pbp WHERE pass=1 GROUP BY passer_player_name
    - Red zone: Filter with yardline_100 <= 20
    - Neutral game script: Filter with wp BETWEEN 0.20 AND 0.80
    - Regular season only: Filter with season_type='REG'

    Args:
        params: NflQueryInput with sql query and optional response format.

    Returns:
        Query results formatted as markdown table or JSON.
    """
    state: AppState = ctx.request_context.lifespan_state
    engine = state.engine

    results = engine.execute_query(params.sql)

    if params.response_format == ResponseFormat.JSON:
        return engine.format_results_json(results)
    return engine.format_results_markdown(results)


@mcp.tool(
    name="nfl_schema",
    annotations={
        "title": "Get NFL Database Schema",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def nfl_schema(params: NflSchemaInput, ctx: Context) -> str:
    """Get the schema of the NFL database tables, including column names and types.

    Use this tool FIRST before writing queries to understand what columns are
    available. You can also request sample values for a specific column to
    understand what values it contains (e.g., what are the possible play_type values).

    Available tables:
    - pbp: Play-by-play data with EPA, WPA, CPOE, and 80+ columns per play (1999-present)
    - player_stats: Weekly player statistics (passing, rushing, receiving)
    - seasonal_stats: Full-season aggregated player statistics
    - rosters: Player rosters with position, height, weight, college, etc.
    - schedules: Game schedules with scores, spreads, and weather
    - teams: Team metadata with colors, logos, divisions, and conferences

    Args:
        params: NflSchemaInput with optional table name and sample column.

    Returns:
        Schema description with column names, types, and row counts.
    """
    state: AppState = ctx.request_context.lifespan_state
    engine = state.engine

    if params.table and params.sample_column:
        values = engine.get_sample_values(params.table, params.sample_column)
        return (
            f"Sample values for `{params.sample_column}` in `{params.table}`:\n"
            f"{json.dumps(values, default=str)}"
        )

    if params.table:
        columns = engine.get_table_columns(params.table)
        count_result = engine.execute_query(f"SELECT count(*) as cnt FROM [{params.table}]")
        count = count_result["rows"][0]["cnt"] if count_result["rows"] else 0
        return (
            f"TABLE: {params.table} ({count:,} rows)\n"
            f"Columns ({len(columns)}):\n"
            + "\n".join(f"  - {c}" for c in columns)
        )

    return engine.get_schema()


@mcp.tool(
    name="nfl_glossary",
    annotations={
        "title": "NFL Analytics Glossary",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def nfl_glossary(params: NflGlossaryInput) -> str:
    """Look up definitions of NFL analytics metrics and columns.

    Returns explanations of key metrics like EPA, CPOE, WPA, success rate,
    and important column conventions (pass vs rush flags, player name formats, etc.).

    Use this to understand what metrics mean and how to use them correctly
    in queries.

    Args:
        params: NflGlossaryInput with optional specific term.

    Returns:
        Metric definition(s) with usage guidance.
    """
    if params.term:
        key = params.term.lower().strip()
        if key in GLOSSARY:
            info = GLOSSARY[key]
            return (
                f"## {info['name']} (`{key}`)\n\n"
                f"{info['description']}\n\n"
                f"**Usage:** {info['usage']}\n"
                f"**Available from:** {info['available_from']} season"
            )
        # Fuzzy match
        matches = [k for k in GLOSSARY if key in k or k in key]
        if matches:
            return (
                f"Term '{key}' not found exactly. Did you mean one of: "
                + ", ".join(f"`{m}`" for m in matches)
                + "?\n\nUse nfl_glossary without a term to see all definitions."
            )
        return (
            f"Term '{key}' not found in glossary. "
            f"Available terms: {', '.join(sorted(GLOSSARY.keys()))}"
        )

    return get_glossary_text()


@mcp.tool(
    name="nfl_search_player",
    annotations={
        "title": "Search NFL Players",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def nfl_search_player(params: NflSearchPlayerInput, ctx: Context) -> str:
    """Search for NFL players by name, with optional position and season filters.

    Useful for finding exact player name spellings and IDs before running
    more detailed queries. Searches across rosters and player stats.

    Args:
        params: NflSearchPlayerInput with name, optional position and season.

    Returns:
        Matching players with their team, position, and seasons active.
    """
    state: AppState = ctx.request_context.lifespan_state
    engine = state.engine

    # Try rosters first (has most detail)
    conditions = [f"player_name LIKE '%{params.name}%'"]
    if params.position:
        conditions.append(f"position = '{params.position.upper()}'")
    if params.season:
        conditions.append(f"season = {params.season}")

    where = " AND ".join(conditions)
    sql = (
        f"SELECT DISTINCT player_name, position, team, season "
        f"FROM rosters WHERE {where} "
        f"ORDER BY season DESC, player_name LIMIT 30"
    )

    results = engine.execute_query(sql)

    if results["row_count"] == 0:
        # Fall back to player_stats table
        conditions_ps = [f"player_name LIKE '%{params.name}%'"]
        if params.season:
            conditions_ps.append(f"season = {params.season}")
        where_ps = " AND ".join(conditions_ps)
        sql_ps = (
            f"SELECT DISTINCT player_name, position, recent_team, season "
            f"FROM player_stats WHERE {where_ps} "
            f"ORDER BY season DESC, player_name LIMIT 30"
        )
        results = engine.execute_query(sql_ps)

    if results["row_count"] == 0:
        return f"No players found matching '{params.name}'. Try a shorter search term."

    return engine.format_results_markdown(results)


@mcp.tool(
    name="nfl_team_lookup",
    annotations={
        "title": "Resolve NFL Team Name",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def nfl_team_lookup(params: NflTeamLookupInput) -> str:
    """Resolve a team name, city, or nickname to the nflverse team abbreviation.

    Use this to find the correct abbreviation before querying. Handles
    common aliases like 'Bears' -> 'CHI', 'niners' -> 'SF', etc.
    Also handles historical names (e.g., 'Redskins' -> 'WAS', 'Oakland' -> 'LV').

    Args:
        params: NflTeamLookupInput with team name to resolve.

    Returns:
        The nflverse team abbreviation, or suggestions if not found.
    """
    abbr = resolve_team(params.team)
    if abbr:
        return f"**{params.team}** → `{abbr}`\n\nUse `{abbr}` in queries (e.g., `posteam = '{abbr}'`)."

    # Try partial match
    query_lower = params.team.lower()
    matches = [
        (alias, code) for alias, code in TEAM_ALIASES.items()
        if query_lower in alias
    ]
    if matches:
        unique_teams = list(set((code, alias) for alias, code in matches))
        suggestions = "\n".join(f"  - '{alias}' → `{code}`" for code, alias in unique_teams[:5])
        return f"Didn't find exact match for '{params.team}'. Possible matches:\n{suggestions}"

    return (
        f"Team '{params.team}' not recognized. "
        "Try a team city, nickname, or abbreviation (e.g., 'CHI', 'Bears', 'Chicago')."
    )


@mcp.tool(
    name="nfl_roster",
    annotations={
        "title": "Get NFL Team Roster",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def nfl_roster(params: NflRosterInput, ctx: Context) -> str:
    """Get the roster for an NFL team, with optional season and position filters.

    Returns player names, positions, jersey numbers, height, weight, college,
    age, and years of experience. Useful for answering questions like:
    - "Who is on the Chiefs roster?"
    - "Show me all the QBs on the Bears in 2024"
    - "What college did the Packers' wide receivers attend?"

    Args:
        params: NflRosterInput with team, optional season and position.

    Returns:
        Team roster formatted as a markdown table.
    """
    state: AppState = ctx.request_context.lifespan_state
    engine = state.engine

    # Resolve team name to abbreviation
    abbr = resolve_team(params.team)
    if not abbr:
        return (
            f"Could not resolve team '{params.team}'. "
            "Use nfl_team_lookup to find the correct abbreviation."
        )

    # Determine season: use provided or find the latest available
    if params.season:
        season = params.season
    else:
        latest = engine.execute_query(
            "SELECT MAX(season) as max_season FROM rosters"
        )
        if latest["rows"]:
            season = latest["rows"][0]["max_season"]
        else:
            return "No roster data available in the database."

    conditions = [f"team = '{abbr}'", f"season = {season}"]
    if params.position:
        conditions.append(f"position = '{params.position.upper()}'")

    where = " AND ".join(conditions)
    sql = (
        f"SELECT player_name, position, jersey_number, height, weight, "
        f"college, birth_date, years_exp, status "
        f"FROM rosters WHERE {where} "
        f"ORDER BY position, player_name LIMIT 200"
    )

    results = engine.execute_query(sql)

    if results["row_count"] == 0:
        msg = f"No roster entries found for {abbr} in {season}"
        if params.position:
            msg += f" at position {params.position.upper()}"
        msg += ". The roster data may not be available for this season."
        return msg

    header = f"## {abbr} Roster — {season}"
    if params.position:
        header += f" ({params.position.upper()})"
    header += f"\n\n"

    return header + engine.format_results_markdown(results)


@mcp.tool(
    name="nfl_visualize",
    annotations={
        "title": "Generate Interactive QB Dashboard",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def nfl_visualize(params: NflVisualizeInput, ctx: Context) -> str:
    """Generate an interactive HTML dashboard for a QB's season performance.

    Creates a self-contained HTML page with inline SVG charts and JavaScript
    interactivity. The dashboard includes:
    - KPI cards with year-over-year changes
    - EPA/play, CPOE, and success rate by week (with toggleable rolling averages)
    - Passing yards, TDs, and INTs volume chart
    - QB landscape scatter plot (CPOE vs EPA)
    - Season comparison summary table

    All charts have hover tooltips and interactive toggle buttons. The HTML
    file requires no external dependencies — just open in a browser.

    Args:
        params: NflVisualizeInput with player name, season, and options.

    Returns:
        The generated HTML content as a string.
    """
    state: AppState = ctx.request_context.lifespan_state
    engine = state.engine

    pname = params.player_name
    season = params.season
    display = params.display_name or pname

    # Detect team if not provided
    team_abbr = params.team
    if not team_abbr:
        team_result = engine.execute_query(
            f"SELECT posteam FROM pbp WHERE passer_player_name = '{pname}' "
            f"AND season = {season} AND posteam IS NOT NULL LIMIT 1"
        )
        if team_result["rows"]:
            team_abbr = team_result["rows"][0]["posteam"]

    # Fetch team colors
    primary, accent = "#333333", "#e64100"
    if team_abbr:
        tc = engine.execute_query(
            f"SELECT team_color, team_color2 FROM teams WHERE team_abbr = '{team_abbr}'"
        )
        if tc["rows"]:
            primary = tc["rows"][0].get("team_color") or primary
            accent = tc["rows"][0].get("team_color2") or accent

    # Prepend '#' if missing
    if primary and not primary.startswith("#"):
        primary = "#" + primary
    if accent and not accent.startswith("#"):
        accent = "#" + accent

    # Weekly stats
    weekly_result = engine.execute_query(f"""
        SELECT week,
               COUNT(*) as dropbacks,
               AVG(qb_epa) as epa_play,
               AVG(cpoe) as cpoe,
               AVG(success) as success_rate,
               AVG(CASE WHEN complete_pass=1 THEN 1.0 ELSE 0.0 END) as comp_pct,
               SUM(passing_yards) as pass_yards,
               SUM(touchdown) as tds,
               SUM(interception) as ints
        FROM pbp
        WHERE passer_player_name = '{pname}' AND pass = 1
              AND season = {season} AND season_type = 'REG'
              AND qb_epa IS NOT NULL
        GROUP BY week ORDER BY week
    """)

    if weekly_result["row_count"] == 0:
        return f"No data found for {pname} in {season}. Check the player name with nfl_search_player."

    weekly_data = weekly_result["rows"]

    # Season comparison (all seasons for this player)
    season_result = engine.execute_query(f"""
        SELECT season,
               COUNT(*) as dropbacks,
               AVG(qb_epa) as epa_play,
               AVG(cpoe) as cpoe,
               AVG(success) as success_rate,
               SUM(passing_yards) as pass_yards,
               SUM(touchdown) as tds,
               SUM(interception) as ints
        FROM pbp
        WHERE passer_player_name = '{pname}' AND pass = 1
              AND season_type = 'REG' AND qb_epa IS NOT NULL
        GROUP BY season ORDER BY season
    """)
    season_data = season_result["rows"]

    # QB comparison scatter
    qb_result = engine.execute_query(f"""
        SELECT passer_player_name as name,
               COUNT(*) as dropbacks,
               AVG(qb_epa) as epa_play,
               AVG(cpoe) as cpoe
        FROM pbp
        WHERE pass = 1 AND season = {season} AND season_type = 'REG'
              AND qb_epa IS NOT NULL AND passer_player_name IS NOT NULL
        GROUP BY passer_player_name
        HAVING COUNT(*) >= {params.min_dropbacks}
        ORDER BY epa_play DESC
    """)
    qb_comparison = qb_result["rows"]

    html = generate_qb_dashboard(
        player_name=display,
        weekly_data=weekly_data,
        season_data=season_data,
        qb_comparison=qb_comparison,
        team_colors={"primary": primary, "accent": accent},
        season=season,
    )

    return html


@mcp.tool(
    name="nfl_compare_qbs",
    annotations={
        "title": "Compare Multiple QBs",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def nfl_compare_qbs(params: NflCompareQBsInput, ctx: Context) -> str:
    """Generate an interactive comparison dashboard for multiple QBs across seasons.

    Creates a self-contained HTML page comparing 2-10 QBs side by side with:
    - Grouped bar charts for EPA/play, CPOE, and success rate by season
    - CPOE vs EPA scatter plot with season toggle
    - Weekly trend lines with metric and season selectors
    - Full comparison table with year-over-year deltas
    - QB toggle buttons to show/hide individual players

    All charts have hover tooltips. Each QB uses their team's colors.

    Args:
        params: NflCompareQBsInput with player names, seasons, and options.

    Returns:
        The generated HTML content as a string.
    """
    state: AppState = ctx.request_context.lifespan_state
    engine = state.engine

    players = params.players
    seasons = sorted(params.seasons)
    display_names = params.display_names or players

    if len(display_names) != len(players):
        display_names = players

    # Build QB info with team colors
    qb_info = {}
    for i, pname in enumerate(players):
        # Detect team from most recent season
        team_abbr = None
        for s in reversed(seasons):
            tr = engine.execute_query(
                f"SELECT posteam FROM pbp WHERE passer_player_name = '{pname}' "
                f"AND season = {s} AND posteam IS NOT NULL LIMIT 1"
            )
            if tr["rows"]:
                team_abbr = tr["rows"][0]["posteam"]
                break

        primary, accent = "#555555", "#999999"
        if team_abbr:
            tc = engine.execute_query(
                f"SELECT team_color, team_color2 FROM teams WHERE team_abbr = '{team_abbr}'"
            )
            if tc["rows"]:
                primary = tc["rows"][0].get("team_color") or primary
                accent = tc["rows"][0].get("team_color2") or accent

        if primary and not primary.startswith("#"):
            primary = "#" + primary
        if accent and not accent.startswith("#"):
            accent = "#" + accent

        qb_info[pname] = {
            "display_name": display_names[i],
            "team": team_abbr or "?",
            "primary": primary,
            "accent": accent,
        }

    # Season-level data
    placeholders = ",".join(f"'{p}'" for p in players)
    season_list = ",".join(str(s) for s in seasons)

    season_result = engine.execute_query(f"""
        SELECT passer_player_name as name, season,
               COUNT(*) as dropbacks,
               AVG(qb_epa) as epa_play,
               AVG(cpoe) as cpoe,
               AVG(success) as success_rate,
               SUM(passing_yards) as pass_yards,
               SUM(touchdown) as tds,
               SUM(interception) as ints
        FROM pbp
        WHERE passer_player_name IN ({placeholders})
              AND pass = 1 AND season IN ({season_list})
              AND season_type = 'REG' AND qb_epa IS NOT NULL
        GROUP BY passer_player_name, season
        ORDER BY passer_player_name, season
    """)

    if season_result["row_count"] == 0:
        return "No data found for these players/seasons. Check names with nfl_search_player."

    # Weekly data
    weekly_result = engine.execute_query(f"""
        SELECT passer_player_name as name, season, week,
               AVG(qb_epa) as epa_play,
               AVG(cpoe) as cpoe,
               AVG(success) as success_rate,
               SUM(passing_yards) as pass_yards,
               SUM(touchdown) as tds,
               SUM(interception) as ints
        FROM pbp
        WHERE passer_player_name IN ({placeholders})
              AND pass = 1 AND season IN ({season_list})
              AND season_type = 'REG' AND qb_epa IS NOT NULL
        GROUP BY passer_player_name, season, week
        ORDER BY passer_player_name, season, week
    """)

    title = params.title or f"QB Comparison: {', '.join(display_names)} ({' vs '.join(str(s) for s in seasons)})"

    html = generate_qb_comparison_dashboard(
        title=title,
        qb_season_data=season_result["rows"],
        qb_weekly_data=weekly_result["rows"],
        qb_info=qb_info,
        seasons=seasons,
    )

    return html


# ---------------------------------------------------------------------------
# Resources (static context for Claude)
# ---------------------------------------------------------------------------

@mcp.resource("nfl://glossary")
def glossary_resource() -> str:
    """Full NFL analytics glossary for reference."""
    return get_glossary_text()


@mcp.resource("nfl://query-tips")
def query_tips_resource() -> str:
    """Tips and common patterns for querying the NFL database."""
    return """# NFL Query Tips

## Filtering Plays
- Regular season only: `season_type = 'REG'`
- Pass plays (dropbacks): `pass = 1` (includes sacks + scrambles)
- Rush plays (designed runs): `rush = 1`
- Exclude garbage time: `wp BETWEEN 0.10 AND 0.90`
- Neutral game script: `wp BETWEEN 0.20 AND 0.80`
- Red zone: `yardline_100 <= 20`
- Early downs: `down IN (1, 2)`
- Only real plays: `pass = 1 OR rush = 1` (excludes penalties, timeouts, etc.)
- Exclude nulls: `epa IS NOT NULL AND posteam IS NOT NULL`

## Common Aggregations
- EPA/play: `AVG(epa)`
- Success rate: `AVG(success)`
- Pass rate: `AVG(pass)` (when filtering to pass=1 OR rush=1)
- CPOE: `AVG(cpoe)` (only on pass plays with cpoe IS NOT NULL)

## Player Name Formats
- PBP table: `passer_player_name` = 'P.Mahomes' (first initial + last name)
- Player stats table: `player_name` = 'Patrick Mahomes' (full name)
- Use `nfl_search_player` to find exact name spellings

## Team Abbreviations
- Use `nfl_team_lookup` to resolve team names to abbreviations
- Use `posteam` for offense, `defteam` for defense in PBP table
- Use `recent_team` in player_stats table

## Table Relationships
- PBP ↔ Rosters: Join on passer_player_id = gsis_id (or similar)
- PBP ↔ Schedules: Join on game_id
- Player Stats ↔ Rosters: Join on player_id / gsis_id + season

## Roster Queries
- Use the `nfl_roster` tool for quick team roster lookups
- For custom roster queries, the rosters table has: player_name, position,
  jersey_number, height, weight, college, birth_date, years_exp, status, team, season

## Team Metadata (for visualizations)
- The `teams` table has: team_abbr, team_name, team_color, team_color2,
  team_logo_wikipedia, team_logo_espn, team_division, team_conference
- Join to PBP: `JOIN teams ON pbp.posteam = teams.team_abbr`
- Useful for coloring charts by team or grouping by division/conference

## QB-Specific Metrics
- `qb_epa`: Like EPA but gives QBs credit only up to the fumble spot on
  completed passes with fumbles lost (fairer QB evaluation)
- CPOE vs EPA/play scatter plots are a classic QB evaluation chart
"""


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="NFL MCP Server")
    parser.add_argument(
        "--init",
        action="store_true",
        help="Initialize/rebuild the NFL database (downloads data from nflverse)",
    )
    parser.add_argument(
        "--seasons",
        type=str,
        default=None,
        help="Comma-separated list of seasons to load (e.g., '2022,2023,2024')",
    )
    parser.add_argument(
        "--tables",
        type=str,
        default=None,
        help="Comma-separated list of tables to build (e.g., 'pbp,rosters')",
    )
    parser.add_argument(
        "--db-path",
        type=str,
        default=None,
        help=f"Path to SQLite database (default: {get_db_path()})",
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        stream=sys.stderr,  # MCP stdio servers must not log to stdout
    )

    if args.init:
        seasons = [int(s.strip()) for s in args.seasons.split(",")] if args.seasons else get_seasons()
        tables = [t.strip() for t in args.tables.split(",")] if args.tables else None
        db_path = Path(args.db_path) if args.db_path else get_db_path()

        print(f"Building NFL database at {db_path}", file=sys.stderr)
        print(f"Seasons: {seasons}", file=sys.stderr)
        print(f"Tables: {tables or 'all'}", file=sys.stderr)

        build_database(db_path=db_path, seasons=seasons, tables=tables)
        print("Done! Database is ready.", file=sys.stderr)
        return

    # Run the MCP server (stdio transport for Claude Code)
    mcp.run()


if __name__ == "__main__":
    main()

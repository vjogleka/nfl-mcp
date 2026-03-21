"""
Data loader for nflverse NFL data.

Downloads play-by-play, player stats, rosters, and schedules from nflverse
GitHub releases and loads them into a local SQLite database for fast querying.
"""

import logging
import os
import sqlite3
from pathlib import Path

import nfl_data_py as nfl
import pandas as pd

logger = logging.getLogger(__name__)

# Default data directory: ~/nfl-data/
DEFAULT_DATA_DIR = Path.home() / "nfl-data"
DEFAULT_DB_PATH = DEFAULT_DATA_DIR / "nfl.db"

# Seasons to load by default (adjust as needed)
DEFAULT_SEASONS = list(range(2020, 2026))

# Key PBP columns to keep (the full dataset has 300+ columns; we keep the most useful ones)
PBP_COLUMNS = [
    # Game context
    "game_id", "season", "season_type", "week", "game_date",
    "posteam", "defteam", "home_team", "away_team",
    "posteam_type", "side_of_field", "yardline_100",
    # Play identifiers
    "play_id", "play_type", "desc",
    # Situation
    "down", "ydstogo", "qtr", "quarter_seconds_remaining",
    "half_seconds_remaining", "game_seconds_remaining",
    "game_half", "goal_to_go",
    # Score state
    "score_differential", "posteam_score", "defteam_score",
    "posteam_score_post", "defteam_score_post",
    # Outcomes
    "yards_gained", "air_yards", "yards_after_catch",
    "first_down", "touchdown", "interception", "fumble", "sack",
    "complete_pass", "incomplete_pass", "pass_attempt",
    "rush_attempt", "penalty", "penalty_yards",
    # nflfastR model fields
    "epa", "qb_epa", "wp", "wpa", "cpoe", "cp",
    "success",
    "xyac_epa", "xyac_mean_yardage",
    # Play type flags (nflfastR-computed)
    "pass", "rush", "special_teams_play", "qb_kneel", "qb_spike",
    "two_point_attempt", "extra_point_attempt", "field_goal_attempt",
    "punt_attempt", "kickoff_attempt",
    # Player fields
    "passer_player_name", "passer_player_id",
    "receiver_player_name", "receiver_player_id",
    "rusher_player_name", "rusher_player_id",
    "lateral_receiver_player_name",
    "fantasy_player_name", "fantasy_player_id",
    # Team context
    "home_score", "away_score",
    "result", "total", "spread_line", "total_line",
    "roof", "surface", "temp", "wind",
    # Drive info
    "fixed_drive", "fixed_drive_result",
    "drive_play_count", "drive_time_of_possession",
    # Series info
    "series", "series_success", "series_result",
    # Passing detail
    "passing_yards", "receiving_yards", "rushing_yards",
    "pass_location", "pass_length",
    "shotgun", "no_huddle", "qb_scramble", "qb_dropback",
    # Return fields
    "return_yards",
    # Misc
    "passer", "rusher", "receiver",
    "name",
    "no_score_prob", "opp_fg_prob", "opp_safety_prob",
    "opp_td_prob", "fg_prob", "safety_prob", "td_prob",
]


def get_data_dir() -> Path:
    """Get data directory from env var or default."""
    data_dir = Path(os.environ.get("NFL_MCP_DATA_DIR", str(DEFAULT_DATA_DIR)))
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def get_db_path() -> Path:
    """Get database path from env var or default."""
    db_env = os.environ.get("NFL_MCP_DB_PATH")
    if db_env:
        return Path(db_env)
    return get_data_dir() / "nfl.db"


def get_seasons() -> list[int]:
    """Get seasons to load from env var or default."""
    seasons_env = os.environ.get("NFL_MCP_SEASONS")
    if seasons_env:
        return [int(s.strip()) for s in seasons_env.split(",")]
    return DEFAULT_SEASONS


def _filter_columns(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """Keep only columns that exist in the DataFrame."""
    existing = [c for c in columns if c in df.columns]
    return df[existing]


def load_pbp(seasons: list[int]) -> pd.DataFrame:
    """Download play-by-play data for given seasons."""
    logger.info(f"Downloading play-by-play data for seasons: {seasons}")
    pbp = nfl.import_pbp_data(seasons, downcast=True, cache=False)
    pbp = _filter_columns(pbp, PBP_COLUMNS)
    logger.info(f"Loaded {len(pbp):,} plays across {len(seasons)} seasons")
    return pbp


def load_player_stats(seasons: list[int]) -> pd.DataFrame:
    """Download weekly player stats."""
    logger.info(f"Downloading weekly player stats for seasons: {seasons}")
    stats = nfl.import_weekly_data(seasons, downcast=True)
    logger.info(f"Loaded {len(stats):,} player-week rows")
    return stats


def load_seasonal_stats(seasons: list[int]) -> pd.DataFrame:
    """Download seasonal player stats."""
    logger.info(f"Downloading seasonal player stats for seasons: {seasons}")
    stats = nfl.import_seasonal_data(seasons, downcast=True)
    logger.info(f"Loaded {len(stats):,} player-season rows")
    return stats


def load_rosters(seasons: list[int]) -> pd.DataFrame:
    """Download roster data."""
    logger.info(f"Downloading rosters for seasons: {seasons}")
    rosters = nfl.import_rosters(seasons)
    logger.info(f"Loaded {len(rosters):,} roster entries")
    return rosters


def load_schedules(seasons: list[int]) -> pd.DataFrame:
    """Download schedule data."""
    logger.info(f"Downloading schedules for seasons: {seasons}")
    schedules = nfl.import_schedules(seasons)
    logger.info(f"Loaded {len(schedules):,} games")
    return schedules


def load_teams() -> pd.DataFrame:
    """Download team descriptions (colors, logos, divisions, conferences)."""
    logger.info("Downloading team descriptions")
    teams = nfl.import_team_desc()
    logger.info(f"Loaded {len(teams):,} teams")
    return teams


def build_database(
    db_path: Path | None = None,
    seasons: list[int] | None = None,
    tables: list[str] | None = None,
) -> Path:
    """
    Build (or rebuild) the SQLite database with nflverse data.

    Args:
        db_path: Path to the SQLite database file.
        seasons: List of seasons to load.
        tables: Which tables to build. Defaults to all.
                 Options: 'pbp', 'player_stats', 'seasonal_stats', 'rosters', 'schedules'

    Returns:
        Path to the created database.
    """
    db_path = db_path or get_db_path()
    seasons = seasons or get_seasons()
    tables = tables or ["pbp", "player_stats", "seasonal_stats", "rosters", "schedules", "teams"]

    db_path.parent.mkdir(parents=True, exist_ok=True)
    logger.info(f"Building database at {db_path} for seasons {seasons}")

    conn = sqlite3.connect(str(db_path))

    try:
        if "pbp" in tables:
            pbp = load_pbp(seasons)
            pbp.to_sql("pbp", conn, if_exists="replace", index=False)
            logger.info("Wrote pbp table")

        if "player_stats" in tables:
            player_stats = load_player_stats(seasons)
            player_stats.to_sql("player_stats", conn, if_exists="replace", index=False)
            logger.info("Wrote player_stats table")

        if "seasonal_stats" in tables:
            seasonal_stats = load_seasonal_stats(seasons)
            seasonal_stats.to_sql("seasonal_stats", conn, if_exists="replace", index=False)
            logger.info("Wrote seasonal_stats table")

        if "rosters" in tables:
            rosters = load_rosters(seasons)
            rosters.to_sql("rosters", conn, if_exists="replace", index=False)
            logger.info("Wrote rosters table")

        if "schedules" in tables:
            schedules = load_schedules(seasons)
            schedules.to_sql("schedules", conn, if_exists="replace", index=False)
            logger.info("Wrote schedules table")

        if "teams" in tables:
            teams = load_teams()
            teams.to_sql("teams", conn, if_exists="replace", index=False)
            logger.info("Wrote teams table")

        # Create indexes for common query patterns
        _create_indexes(conn)

        conn.execute("ANALYZE")
        conn.commit()

    finally:
        conn.close()

    db_size_mb = db_path.stat().st_size / (1024 * 1024)
    logger.info(f"Database built successfully: {db_path} ({db_size_mb:.1f} MB)")
    return db_path


def _create_indexes(conn: sqlite3.Connection) -> None:
    """Create indexes for fast querying."""
    indexes = [
        # PBP indexes
        "CREATE INDEX IF NOT EXISTS idx_pbp_season ON pbp(season)",
        "CREATE INDEX IF NOT EXISTS idx_pbp_posteam ON pbp(posteam)",
        "CREATE INDEX IF NOT EXISTS idx_pbp_defteam ON pbp(defteam)",
        "CREATE INDEX IF NOT EXISTS idx_pbp_passer ON pbp(passer_player_name)",
        "CREATE INDEX IF NOT EXISTS idx_pbp_rusher ON pbp(rusher_player_name)",
        "CREATE INDEX IF NOT EXISTS idx_pbp_receiver ON pbp(receiver_player_name)",
        "CREATE INDEX IF NOT EXISTS idx_pbp_play_type ON pbp(play_type)",
        "CREATE INDEX IF NOT EXISTS idx_pbp_season_posteam ON pbp(season, posteam)",
        "CREATE INDEX IF NOT EXISTS idx_pbp_game_id ON pbp(game_id)",
        "CREATE INDEX IF NOT EXISTS idx_pbp_week ON pbp(season, week)",
        # Player stats indexes
        "CREATE INDEX IF NOT EXISTS idx_ps_player ON player_stats(player_name)",
        "CREATE INDEX IF NOT EXISTS idx_ps_season ON player_stats(season)",
        "CREATE INDEX IF NOT EXISTS idx_ps_team ON player_stats(recent_team)",
        # Seasonal stats indexes
        "CREATE INDEX IF NOT EXISTS idx_ss_player ON seasonal_stats(player_name)",
        "CREATE INDEX IF NOT EXISTS idx_ss_season ON seasonal_stats(season)",
        # Roster indexes
        "CREATE INDEX IF NOT EXISTS idx_roster_team ON rosters(team)",
        "CREATE INDEX IF NOT EXISTS idx_roster_season ON rosters(season)",
        "CREATE INDEX IF NOT EXISTS idx_roster_name ON rosters(player_name)",
        "CREATE INDEX IF NOT EXISTS idx_roster_position ON rosters(position)",
        # Schedule indexes
        "CREATE INDEX IF NOT EXISTS idx_sched_season ON schedules(season)",
        "CREATE INDEX IF NOT EXISTS idx_sched_week ON schedules(season, week)",
        "CREATE INDEX IF NOT EXISTS idx_sched_home ON schedules(home_team)",
        "CREATE INDEX IF NOT EXISTS idx_sched_away ON schedules(away_team)",
        # Team indexes
        "CREATE INDEX IF NOT EXISTS idx_teams_abbr ON teams(team_abbr)",
    ]
    for idx_sql in indexes:
        try:
            conn.execute(idx_sql)
        except sqlite3.OperationalError:
            # Column might not exist in this dataset version
            pass
    logger.info("Created database indexes")


def db_exists(db_path: Path | None = None) -> bool:
    """Check if database exists and has data."""
    db_path = db_path or get_db_path()
    if not db_path.exists():
        return False
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.execute("SELECT count(*) FROM pbp LIMIT 1")
        count = cursor.fetchone()[0]
        conn.close()
        return count > 0
    except Exception:
        return False

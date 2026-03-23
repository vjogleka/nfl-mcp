#!/usr/bin/env python3
"""
Generate an interactive HTML dashboard for any QB.

Usage:
    python generate_dashboard.py                          # Caleb Williams (default)
    python generate_dashboard.py --player P.Mahomes --team KC --name "Patrick Mahomes"
    python generate_dashboard.py --player J.Hurts --season 2024
"""

import argparse
import sqlite3
import sys
from pathlib import Path

from nfl_mcp.visualize import generate_qb_dashboard

DB_PATH = Path.home() / "nfl-data" / "nfl.db"


def main():
    parser = argparse.ArgumentParser(description="Generate interactive QB dashboard")
    parser.add_argument("--player", default="C.Williams", help="passer_player_name (e.g., C.Williams)")
    parser.add_argument("--name", default=None, help="Display name (e.g., 'Caleb Williams')")
    parser.add_argument("--team", default=None, help="Team abbreviation for colors (e.g., CHI)")
    parser.add_argument("--season", type=int, default=2025, help="Season year")
    parser.add_argument("--min-dropbacks", type=int, default=200, help="Min dropbacks for QB comparison")
    parser.add_argument("--output", default=None, help="Output HTML file path")
    parser.add_argument("--db", default=str(DB_PATH), help=f"Database path (default: {DB_PATH})")
    args = parser.parse_args()

    db = Path(args.db)
    if not db.exists():
        print(f"Database not found at {db}. Run 'python -m nfl_mcp.server --init' first.", file=sys.stderr)
        sys.exit(1)

    conn = sqlite3.connect(str(db))
    conn.row_factory = sqlite3.Row

    pname = args.player
    season = args.season
    display = args.name or pname

    # Detect team
    team_abbr = args.team
    if not team_abbr:
        row = conn.execute(
            "SELECT posteam FROM pbp WHERE passer_player_name = ? AND season = ? AND posteam IS NOT NULL LIMIT 1",
            (pname, season),
        ).fetchone()
        if row:
            team_abbr = row["posteam"]

    # Team colors
    primary, accent = "#333333", "#e64100"
    if team_abbr:
        tc = conn.execute("SELECT team_color, team_color2 FROM teams WHERE team_abbr = ?", (team_abbr,)).fetchone()
        if tc:
            primary = tc["team_color"] or primary
            accent = tc["team_color2"] or accent
    if not primary.startswith("#"):
        primary = "#" + primary
    if not accent.startswith("#"):
        accent = "#" + accent

    # Weekly stats
    weekly = [dict(r) for r in conn.execute("""
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
        WHERE passer_player_name = ? AND pass = 1
              AND season = ? AND season_type = 'REG'
              AND qb_epa IS NOT NULL
        GROUP BY week ORDER BY week
    """, (pname, season)).fetchall()]

    if not weekly:
        print(f"No data for {pname} in {season}.", file=sys.stderr)
        sys.exit(1)

    # Season comparison
    season_data = [dict(r) for r in conn.execute("""
        SELECT season,
               COUNT(*) as dropbacks,
               AVG(qb_epa) as epa_play,
               AVG(cpoe) as cpoe,
               AVG(success) as success_rate,
               SUM(passing_yards) as pass_yards,
               SUM(touchdown) as tds,
               SUM(interception) as ints
        FROM pbp
        WHERE passer_player_name = ? AND pass = 1
              AND season_type = 'REG' AND qb_epa IS NOT NULL
        GROUP BY season ORDER BY season
    """, (pname,)).fetchall()]

    # QB landscape
    qb_comp = [dict(r) for r in conn.execute("""
        SELECT passer_player_name as name,
               COUNT(*) as dropbacks,
               AVG(qb_epa) as epa_play,
               AVG(cpoe) as cpoe
        FROM pbp
        WHERE pass = 1 AND season = ? AND season_type = 'REG'
              AND qb_epa IS NOT NULL AND passer_player_name IS NOT NULL
        GROUP BY passer_player_name
        HAVING COUNT(*) >= ?
        ORDER BY epa_play DESC
    """, (season, args.min_dropbacks)).fetchall()]

    conn.close()

    html = generate_qb_dashboard(
        player_name=display,
        weekly_data=weekly,
        season_data=season_data,
        qb_comparison=qb_comp,
        team_colors={"primary": primary, "accent": accent},
        season=season,
    )

    output_path = args.output or f"{pname.replace('.', '_').lower()}_{season}_dashboard.html"
    Path(output_path).write_text(html)
    print(f"Dashboard saved to {output_path}")


if __name__ == "__main__":
    main()

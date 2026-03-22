#!/usr/bin/env python3
"""
Generate an interactive multi-QB comparison dashboard.

Usage:
    python generate_comparison.py
    python generate_comparison.py --players P.Mahomes J.Allen L.Jackson --seasons 2023,2024,2025
"""

import argparse
import sqlite3
import sys
from pathlib import Path

from nfl_mcp.visualize import generate_qb_comparison_dashboard

DB_PATH = Path.home() / "nfl-data" / "nfl.db"

# Default: 2024 draft class QBs
DEFAULT_PLAYERS = [
    ("C.Williams", "Caleb Williams"),
    ("D.Maye", "Drake Maye"),
    ("J.Daniels", "Jayden Daniels"),
    ("M.Penix", "Michael Penix"),
    ("B.Nix", "Bo Nix"),
]


def main():
    parser = argparse.ArgumentParser(description="Generate multi-QB comparison dashboard")
    parser.add_argument("--players", nargs="+", default=None,
                        help="passer_player_names (e.g., C.Williams D.Maye)")
    parser.add_argument("--names", nargs="+", default=None,
                        help="Display names in same order as --players")
    parser.add_argument("--seasons", default="2024,2025",
                        help="Comma-separated seasons (e.g., 2024,2025)")
    parser.add_argument("--title", default=None, help="Dashboard title")
    parser.add_argument("--output", default=None, help="Output HTML path")
    parser.add_argument("--db", default=str(DB_PATH), help=f"Database path")
    args = parser.parse_args()

    db = Path(args.db)
    if not db.exists():
        print(f"Database not found at {db}.", file=sys.stderr)
        sys.exit(1)

    conn = sqlite3.connect(str(db))
    conn.row_factory = sqlite3.Row

    if args.players:
        players = args.players
        display_names = args.names or players
    else:
        players = [p[0] for p in DEFAULT_PLAYERS]
        display_names = [p[1] for p in DEFAULT_PLAYERS]

    seasons = sorted(int(s) for s in args.seasons.split(","))

    # Build QB info
    qb_info = {}
    for i, pname in enumerate(players):
        team_abbr = None
        for s in reversed(seasons):
            r = conn.execute(
                "SELECT posteam FROM pbp WHERE passer_player_name=? AND season=? AND posteam IS NOT NULL LIMIT 1",
                (pname, s),
            ).fetchone()
            if r:
                team_abbr = r["posteam"]
                break

        primary, accent = "#555555", "#999999"
        if team_abbr:
            tc = conn.execute("SELECT team_color, team_color2 FROM teams WHERE team_abbr=?", (team_abbr,)).fetchone()
            if tc:
                primary = tc["team_color"] or primary
                accent = tc["team_color2"] or accent
        if not primary.startswith("#"):
            primary = "#" + primary
        if not accent.startswith("#"):
            accent = "#" + accent

        qb_info[pname] = {
            "display_name": display_names[i] if i < len(display_names) else pname,
            "team": team_abbr or "?",
            "primary": primary,
            "accent": accent,
        }

    placeholders = ",".join("?" for _ in players)
    season_placeholders = ",".join("?" for _ in seasons)

    # Season-level data
    season_data = [dict(r) for r in conn.execute(f"""
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
              AND pass = 1 AND season IN ({season_placeholders})
              AND season_type = 'REG' AND qb_epa IS NOT NULL
        GROUP BY passer_player_name, season
        ORDER BY passer_player_name, season
    """, players + seasons).fetchall()]

    # Weekly data
    weekly_data = [dict(r) for r in conn.execute(f"""
        SELECT passer_player_name as name, season, week,
               AVG(qb_epa) as epa_play,
               AVG(cpoe) as cpoe,
               AVG(success) as success_rate,
               SUM(passing_yards) as pass_yards,
               SUM(touchdown) as tds,
               SUM(interception) as ints
        FROM pbp
        WHERE passer_player_name IN ({placeholders})
              AND pass = 1 AND season IN ({season_placeholders})
              AND season_type = 'REG' AND qb_epa IS NOT NULL
        GROUP BY passer_player_name, season, week
        ORDER BY passer_player_name, season, week
    """, players + seasons).fetchall()]

    conn.close()

    title = args.title or f"2024 Draft Class: {' vs '.join(str(s) for s in seasons)}"

    html = generate_qb_comparison_dashboard(
        title=title,
        qb_season_data=season_data,
        qb_weekly_data=weekly_data,
        qb_info=qb_info,
        seasons=seasons,
    )

    output_path = args.output or "draft_class_2024_comparison.html"
    Path(output_path).write_text(html)
    print(f"Dashboard saved to {output_path}")


if __name__ == "__main__":
    main()

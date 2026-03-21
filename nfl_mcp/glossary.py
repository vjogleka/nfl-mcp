"""
NFL analytics glossary.

Provides definitions for key metrics and terms used in nflfastR data,
so Claude can interpret results correctly and explain them to users.
"""

GLOSSARY = {
    # Core metrics
    "epa": {
        "name": "Expected Points Added (EPA)",
        "description": (
            "The change in expected points on a given play. Positive EPA means "
            "the offense gained value; negative EPA means they lost value. "
            "EPA accounts for down, distance, field position, and score. "
            "It is the single most important play-level metric in modern NFL analytics."
        ),
        "usage": "Higher EPA/play = better performance. League average is ~0.00.",
        "available_from": 1999,
    },
    "qb_epa": {
        "name": "QB-Adjusted EPA",
        "description": (
            "Like EPA but adjusted for QB evaluation. On completed passes where "
            "the receiver fumbles, standard EPA charges the full play outcome to "
            "the passer. qb_epa instead gives the QB credit only up to the spot "
            "of the fumble, which is fairer for QB evaluation."
        ),
        "usage": "Use AVG(qb_epa) instead of AVG(epa) for QB-specific analysis.",
        "available_from": 1999,
    },
    "wpa": {
        "name": "Win Probability Added (WPA)",
        "description": (
            "The change in win probability on a given play. More context-dependent "
            "than EPA because it factors in score, time remaining, and timeouts."
        ),
        "usage": "Useful for identifying clutch/high-leverage plays.",
        "available_from": 1999,
    },
    "wp": {
        "name": "Win Probability (WP)",
        "description": (
            "The estimated probability that the possession team wins the game "
            "at the start of a given play. Ranges from 0 to 1."
        ),
        "usage": "Filter by wp BETWEEN 0.20 AND 0.80 for 'neutral game script'.",
        "available_from": 1999,
    },
    "cpoe": {
        "name": "Completion Percentage Over Expected (CPOE)",
        "description": (
            "The difference between a quarterback's actual completion percentage "
            "and their expected completion percentage based on factors like air yards, "
            "pass location, and defensive coverage. Positive CPOE = better than expected."
        ),
        "usage": "One of the best QB accuracy metrics. +2% CPOE is solid, +5% is elite.",
        "available_from": 2006,
    },
    "cp": {
        "name": "Completion Probability (CP)",
        "description": (
            "The nflfastR model's estimated probability that a pass will be completed, "
            "based on air yards, pass location, and other factors."
        ),
        "usage": "Used to calculate CPOE (actual completion % minus CP).",
        "available_from": 2006,
    },
    "success": {
        "name": "Success Rate",
        "description": (
            "A binary indicator (1/0) for whether a play was 'successful'. "
            "Defined as EPA > 0. On 1st down, gaining 40%+ of yards to go; "
            "on 2nd down, gaining 60%+; on 3rd/4th, converting."
        ),
        "usage": "Aggregate as AVG(success) for team/player success rate.",
        "available_from": 1999,
    },
    "xyac_epa": {
        "name": "Expected Yards After Catch EPA",
        "description": (
            "The expected EPA from yards after the catch, based on the nflfastR model. "
            "Helps separate QB contribution from receiver YAC ability."
        ),
        "usage": "Compare to actual EPA to assess receiver YAC contribution.",
        "available_from": 2006,
    },

    # Play type flags
    "pass": {
        "name": "Pass Play Flag",
        "description": (
            "nflfastR-computed flag (1/0) for pass plays. Includes sacks and scrambles "
            "(since those are dropbacks). This is DIFFERENT from play_type='pass'."
        ),
        "usage": "Use pass=1 to filter dropbacks. Use rush=1 for designed runs.",
        "available_from": 1999,
    },
    "rush": {
        "name": "Rush Play Flag",
        "description": (
            "nflfastR-computed flag (1/0) for designed rush plays. Does NOT include "
            "scrambles (those have pass=1, qb_scramble=1)."
        ),
        "usage": "Use rush=1 to filter designed runs.",
        "available_from": 1999,
    },
    "qb_dropback": {
        "name": "QB Dropback",
        "description": (
            "Flag for all plays where the QB dropped back to pass, including "
            "sacks, scrambles, and actual pass attempts."
        ),
        "usage": "Alternative to pass=1; semantically the same in most cases.",
        "available_from": 1999,
    },

    # Common filters
    "season_type": {
        "name": "Season Type",
        "description": "Either 'REG' for regular season or 'POST' for playoffs.",
        "usage": "Most analyses filter to season_type='REG'.",
        "available_from": 1999,
    },
    "down": {
        "name": "Down",
        "description": "The down number (1-4). NULL on kickoffs, extra points, etc.",
        "usage": "down IN (1,2) for 'early downs'. down IN (3,4) for 'late downs'.",
        "available_from": 1999,
    },
    "yardline_100": {
        "name": "Yardline (from opponent end zone)",
        "description": (
            "Numeric distance from the opponent's end zone. 0 = opponent end zone, "
            "100 = own end zone. The red zone is yardline_100 <= 20."
        ),
        "usage": "Filter yardline_100 <= 20 for red zone analysis.",
        "available_from": 1999,
    },
    "shotgun": {
        "name": "Shotgun Formation",
        "description": "Flag (1/0) for whether the play was run from shotgun.",
        "usage": "shotgun=1 to filter shotgun plays.",
        "available_from": 1999,
    },
    "no_huddle": {
        "name": "No Huddle",
        "description": "Flag (1/0) for whether the offense ran a no-huddle play.",
        "usage": "no_huddle=1 to filter hurry-up plays.",
        "available_from": 1999,
    },

    # Player columns
    "passer_player_name": {
        "name": "Passer Name",
        "description": (
            "Name of the passer on pass plays. Format: 'First Initial.Last Name' "
            "(e.g., 'P.Mahomes'). Filled on all dropbacks including sacks/scrambles."
        ),
        "usage": "Use for QB-level aggregations. Join with rosters for full names.",
        "available_from": 1999,
    },
    "name": {
        "name": "Primary Player Name",
        "description": (
            "nflfastR convenience field: equals passer on pass plays, rusher on rush plays. "
            "Think of it as 'the primary player involved in the play'."
        ),
        "usage": "Quick way to get the main player without checking play type.",
        "available_from": 1999,
    },

    # Drive and series
    "fixed_drive": {
        "name": "Drive Number (fixed)",
        "description": (
            "nflfastR-corrected drive number. Use this instead of the raw NFL drive field, "
            "which has known bugs."
        ),
        "usage": "Group by game_id, fixed_drive for drive-level analysis.",
        "available_from": 1999,
    },
    "fixed_drive_result": {
        "name": "Drive Result (fixed)",
        "description": (
            "How the drive ended: 'Touchdown', 'Field goal', 'Punt', 'Turnover', "
            "'Turnover on downs', 'End of half', 'Opp touchdown', 'Safety', etc."
        ),
        "usage": "Use to analyze red zone efficiency, drive outcomes, etc.",
        "available_from": 1999,
    },
    "series_success": {
        "name": "Series Success",
        "description": (
            "Whether a series (set of downs) resulted in a new first down or touchdown. "
            "Binary 1/0."
        ),
        "usage": "AVG(series_success) gives first-down conversion rate.",
        "available_from": 1999,
    },
}

# Team abbreviation mappings (common aliases -> nflverse abbreviation)
TEAM_ALIASES = {
    # Common names
    "bears": "CHI", "chicago": "CHI", "chicago bears": "CHI",
    "packers": "GB", "green bay": "GB", "green bay packers": "GB",
    "chiefs": "KC", "kansas city": "KC", "kansas city chiefs": "KC",
    "eagles": "PHI", "philadelphia": "PHI", "philadelphia eagles": "PHI",
    "bills": "BUF", "buffalo": "BUF", "buffalo bills": "BUF",
    "cowboys": "DAL", "dallas": "DAL", "dallas cowboys": "DAL",
    "49ers": "SF", "niners": "SF", "san francisco": "SF", "san francisco 49ers": "SF",
    "ravens": "BAL", "baltimore": "BAL", "baltimore ravens": "BAL",
    "bengals": "CIN", "cincinnati": "CIN", "cincinnati bengals": "CIN",
    "lions": "DET", "detroit": "DET", "detroit lions": "DET",
    "dolphins": "MIA", "miami": "MIA", "miami dolphins": "MIA",
    "vikings": "MIN", "minnesota": "MIN", "minnesota vikings": "MIN",
    "patriots": "NE", "new england": "NE", "new england patriots": "NE",
    "saints": "NO", "new orleans": "NO", "new orleans saints": "NO",
    "giants": "NYG", "ny giants": "NYG", "new york giants": "NYG",
    "jets": "NYJ", "ny jets": "NYJ", "new york jets": "NYJ",
    "raiders": "LV", "las vegas": "LV", "las vegas raiders": "LV",
    "steelers": "PIT", "pittsburgh": "PIT", "pittsburgh steelers": "PIT",
    "chargers": "LAC", "la chargers": "LAC", "los angeles chargers": "LAC",
    "rams": "LA", "la rams": "LA", "los angeles rams": "LA",
    "seahawks": "SEA", "seattle": "SEA", "seattle seahawks": "SEA",
    "cardinals": "ARI", "arizona": "ARI", "arizona cardinals": "ARI",
    "falcons": "ATL", "atlanta": "ATL", "atlanta falcons": "ATL",
    "panthers": "CAR", "carolina": "CAR", "carolina panthers": "CAR",
    "browns": "CLE", "cleveland": "CLE", "cleveland browns": "CLE",
    "broncos": "DEN", "denver": "DEN", "denver broncos": "DEN",
    "texans": "HOU", "houston": "HOU", "houston texans": "HOU",
    "colts": "IND", "indianapolis": "IND", "indianapolis colts": "IND",
    "jaguars": "JAX", "jacksonville": "JAX", "jacksonville jaguars": "JAX",
    "titans": "TEN", "tennessee": "TEN", "tennessee titans": "TEN",
    "commanders": "WAS", "washington": "WAS", "washington commanders": "WAS",
    "buccaneers": "TB", "bucs": "TB", "tampa bay": "TB", "tampa bay buccaneers": "TB",
    # Historical
    "redskins": "WAS", "washington redskins": "WAS",
    "football team": "WAS", "washington football team": "WAS",
    "oakland": "LV", "oakland raiders": "LV",
    "san diego": "LAC", "san diego chargers": "LAC",
    "st. louis": "LA", "st. louis rams": "LA",
}


def get_glossary_text() -> str:
    """Return the full glossary as formatted text for Claude's context."""
    parts = ["# NFL Analytics Glossary\n"]
    for key, info in GLOSSARY.items():
        parts.append(f"## {info['name']} (`{key}`)")
        parts.append(info["description"])
        parts.append(f"**Usage:** {info['usage']}")
        parts.append(f"**Available from:** {info['available_from']} season\n")
    return "\n".join(parts)


def resolve_team(name: str) -> str | None:
    """Resolve a team name/alias to the nflverse abbreviation."""
    name_lower = name.strip().lower()
    # Direct abbreviation match
    if name_lower.upper() in {v for v in TEAM_ALIASES.values()}:
        return name_lower.upper()
    return TEAM_ALIASES.get(name_lower)

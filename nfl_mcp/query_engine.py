"""
Query engine for the NFL MCP server.

Provides safe SQL execution, schema introspection, and helper queries
against the local nflverse SQLite database.
"""

import json
import logging
import re
import sqlite3
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Maximum rows to return from a single query
MAX_ROWS = 200

# SQL keywords that indicate write operations (blocked)
WRITE_KEYWORDS = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|REPLACE|ATTACH|DETACH|VACUUM|REINDEX)\b",
    re.IGNORECASE,
)


class QueryEngine:
    """Safe, read-only query engine for the NFL SQLite database."""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._conn: sqlite3.Connection | None = None

    def connect(self) -> None:
        """Open a read-only connection to the database."""
        uri = f"file:{self.db_path}?mode=ro"
        self._conn = sqlite3.connect(uri, uri=True, timeout=30)
        self._conn.row_factory = sqlite3.Row
        # Set a busy timeout and limit query execution time
        self._conn.execute("PRAGMA busy_timeout = 5000")
        logger.info(f"Connected to database (read-only): {self.db_path}")

    def close(self) -> None:
        """Close the database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None

    @property
    def conn(self) -> sqlite3.Connection:
        if self._conn is None:
            raise RuntimeError("Database not connected. Call connect() first.")
        return self._conn

    def get_schema(self) -> str:
        """
        Return a human-readable schema description of all tables,
        including column names, types, and row counts.
        """
        tables = self.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()

        schema_parts = []
        for (table_name,) in tables:
            # Get row count
            count = self.conn.execute(f"SELECT count(*) FROM [{table_name}]").fetchone()[0]

            # Get column info
            columns = self.conn.execute(f"PRAGMA table_info([{table_name}])").fetchall()
            col_descriptions = []
            for col in columns:
                col_name = col["name"]
                col_type = col["type"] or "TEXT"
                col_descriptions.append(f"  - {col_name} ({col_type})")

            schema_parts.append(
                f"TABLE: {table_name} ({count:,} rows)\n" + "\n".join(col_descriptions)
            )

        return "\n\n".join(schema_parts)

    def get_table_columns(self, table_name: str) -> list[str]:
        """Get column names for a given table."""
        columns = self.conn.execute(f"PRAGMA table_info([{table_name}])").fetchall()
        return [col["name"] for col in columns]

    def get_sample_values(self, table_name: str, column_name: str, limit: int = 20) -> list[Any]:
        """Get distinct sample values for a column (useful for understanding enums)."""
        try:
            rows = self.conn.execute(
                f"SELECT DISTINCT [{column_name}] FROM [{table_name}] "
                f"WHERE [{column_name}] IS NOT NULL "
                f"ORDER BY [{column_name}] LIMIT ?",
                (limit,),
            ).fetchall()
            return [row[0] for row in rows]
        except sqlite3.OperationalError:
            return []

    def execute_query(self, sql: str, params: tuple = ()) -> dict[str, Any]:
        """
        Execute a read-only SQL query and return results as a dict.

        Args:
            sql: SQL query to execute (must be SELECT only).
            params: Query parameters for safe binding.

        Returns:
            Dict with 'columns', 'rows', 'row_count', and 'truncated' keys.
        """
        # Safety check: block any write operations
        if WRITE_KEYWORDS.search(sql):
            return {
                "error": "Only SELECT queries are allowed. Write operations are blocked.",
                "columns": [],
                "rows": [],
                "row_count": 0,
                "truncated": False,
            }

        # Strip trailing semicolons and whitespace
        sql = sql.strip().rstrip(";")

        # Add LIMIT if not already present
        if not re.search(r"\bLIMIT\b", sql, re.IGNORECASE):
            sql = f"{sql} LIMIT {MAX_ROWS}"

        try:
            cursor = self.conn.execute(sql, params)
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            rows = cursor.fetchall()

            # Convert sqlite3.Row objects to plain dicts
            row_dicts = [dict(row) for row in rows]
            truncated = len(row_dicts) >= MAX_ROWS

            return {
                "columns": columns,
                "rows": row_dicts,
                "row_count": len(row_dicts),
                "truncated": truncated,
            }

        except sqlite3.OperationalError as e:
            return {
                "error": f"SQL error: {str(e)}",
                "columns": [],
                "rows": [],
                "row_count": 0,
                "truncated": False,
            }
        except Exception as e:
            return {
                "error": f"Unexpected error: {type(e).__name__}: {str(e)}",
                "columns": [],
                "rows": [],
                "row_count": 0,
                "truncated": False,
            }

    def format_results_markdown(self, results: dict[str, Any], max_display: int = 50) -> str:
        """Format query results as a readable markdown table."""
        if "error" in results and results["error"]:
            return f"**Error:** {results['error']}"

        if results["row_count"] == 0:
            return "No results found."

        columns = results["columns"]
        rows = results["rows"][:max_display]

        # Build markdown table
        header = "| " + " | ".join(str(c) for c in columns) + " |"
        separator = "| " + " | ".join("---" for _ in columns) + " |"
        body_lines = []
        for row in rows:
            vals = []
            for c in columns:
                v = row.get(c, "")
                if v is None:
                    vals.append("")
                elif isinstance(v, float):
                    vals.append(f"{v:.3f}")
                else:
                    vals.append(str(v))
            body_lines.append("| " + " | ".join(vals) + " |")

        table = "\n".join([header, separator] + body_lines)

        footer_parts = [f"**{results['row_count']} rows returned.**"]
        if results.get("truncated"):
            footer_parts.append(f"(Results truncated to {MAX_ROWS} rows. Add a LIMIT clause for more control.)")
        if results["row_count"] > max_display:
            footer_parts.append(f"(Showing first {max_display} of {results['row_count']} rows.)")

        return table + "\n\n" + " ".join(footer_parts)

    def format_results_json(self, results: dict[str, Any]) -> str:
        """Format query results as JSON."""
        return json.dumps(results, indent=2, default=str)

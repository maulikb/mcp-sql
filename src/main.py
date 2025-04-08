import os
import sys
import sqlite3
import logging
import asyncio
import csv
from contextlib import closing
from pathlib import Path
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
import mcp.server.stdio
from typing import Any

# Reconfigure UnicodeEncodeError prone default (i.e., windows-1252) to utf-8
if sys.platform == "win32" and os.environ.get('PYTHONIOENCODING') is None:
    sys.stdin.reconfigure(encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

# Configure logging
logger = logging.getLogger('mcp_sqlite_server')
logging.basicConfig(level=logging.DEBUG)
logger.info("Starting MCP SQLite Server")

class SqliteDatabase:
    def __init__(self, db_path: str):
        self.db_path = str(Path(db_path).expanduser())
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_database()

    def _init_database(self):
        """Initialize connection to the SQLite database"""
        logger.debug("Initializing database connection")
        with closing(sqlite3.connect(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            conn.close()

    def import_csv_to_table(self, csv_path: str, table_name: str):
        """Import a CSV file into a SQLite table"""
        if not Path(csv_path).is_file():
            logger.warning(f"CSV file not found: {csv_path}. Using default dataset: data/youtube_2025_dataset.csv")
            csv_path = "data/youtube_2025_dataset.csv"
            if not Path(csv_path).is_file():
                logger.error(f"Default dataset not found: {csv_path}")
                raise FileNotFoundError(f"Default dataset not found: {csv_path}")

        logger.debug(f"Importing CSV file {csv_path} into table {table_name}")
        try:
            with closing(sqlite3.connect(self.db_path)) as conn:
                with closing(conn.cursor()) as cursor:
                    with open(csv_path, newline='', encoding='utf-8') as csvfile:
                        reader = csv.reader(csvfile)
                        headers = next(reader)
                        # Escape column names with double quotes
                        escaped_headers = [f'"{header}"' for header in headers]
                        cursor.execute(
                            f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(f'{header} TEXT' for header in escaped_headers)})"
                        )
                        for row in reader:
                            cursor.execute(
                                f"INSERT INTO {table_name} VALUES ({', '.join('?' for _ in row)})", row
                            )
                        conn.commit()
                        logger.debug(f"CSV file {csv_path} imported successfully")
        except Exception as e:
            logger.error(f"Error importing CSV: {e}")
            raise

    def execute_query(self, query: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """Execute a SQL query and return results as a list of dictionaries"""
        logger.debug(f"Executing query: {query}")
        try:
            with closing(sqlite3.connect(self.db_path)) as conn:
                conn.row_factory = sqlite3.Row
                with closing(conn.cursor()) as cursor:
                    if params:
                        cursor.execute(query, params)
                    else:
                        cursor.execute(query)

                    if query.strip().upper().startswith(('INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'ALTER')):
                        conn.commit()
                        affected = cursor.rowcount
                        logger.debug(f"Write query affected {affected} rows")
                        return [{"affected_rows": affected}]

                    results = [dict(row) for row in cursor.fetchall()]
                    logger.debug(f"Read query returned {len(results)} rows")
                    return results
        except Exception as e:
            logger.error(f"Database error executing query: {e}")
            raise

async def main(db_path: str, csv_path: str, table_name: str):
    logger.info(f"Starting SQLite MCP Server with DB path: {db_path}")

    db = SqliteDatabase(db_path)

    # Check if the CSV file exists, otherwise use the default dataset
    if not Path(csv_path).is_file():
        logger.warning(f"CSV file not found: {csv_path}. Using default dataset: data/youtube_2025_dataset.csv")
        csv_path = "data/youtube_2025_dataset.csv"

    db.import_csv_to_table(csv_path, table_name)
    server = Server("sqlite-manager")

    # Register handlers
    logger.debug("Registering handlers")

    @server.list_tools()
    async def handle_list_tools() -> list[types.Tool]:
        """List available tools"""
        return [
            types.Tool(
                name="upload_csv",
                description="Upload a new CSV file and convert it into a table",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "csv_path": {"type": "string", "description": "Path to the CSV file to upload"},
                        "table_name": {"type": "string", "description": "Name of the table to create"},
                    },
                    "required": ["csv_path", "table_name"],
                },
            ),
            types.Tool(
                name="read_query",
                description="Execute a SELECT query on the SQLite database",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "SELECT SQL query to execute"},
                    },
                    "required": ["query"],
                },
            ),
            types.Tool(
                name="write_query",
                description="Execute an INSERT, UPDATE, or DELETE query on the SQLite database",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "SQL query to execute"},
                    },
                    "required": ["query"],
                },
            ),
            types.Tool(
                name="list_tables",
                description="List all tables in the SQLite database",
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
            ),
            types.Tool(
                name="describe_table",
                description="Get the schema information for a specific table",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "table_name": {"type": "string", "description": "Name of the table to describe"},
                    },
                    "required": ["table_name"],
                },
            ),
        ]

    @server.call_tool()
    async def handle_call_tool(
        name: str, arguments: dict[str, Any] | None
    ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        """Handle tool execution requests"""
        try:
            if name == "upload_csv":
                if not arguments or "csv_path" not in arguments or "table_name" not in arguments:
                    raise ValueError("Missing csv_path or table_name argument")
                csv_path = arguments["csv_path"]
                table_name = arguments["table_name"]
                db.import_csv_to_table(csv_path, table_name)
                return [types.TextContent(type="text", text=f"CSV file {csv_path} uploaded and converted to table {table_name}")]

            if name == "list_tables":
                results = db.execute_query(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
                return [types.TextContent(type="text", text=str(results))]

            elif name == "describe_table":
                if not arguments or "table_name" not in arguments:
                    raise ValueError("Missing table_name argument")
                results = db.execute_query(
                    f"PRAGMA table_info({arguments['table_name']})"
                )
                return [types.TextContent(type="text", text=str(results))]

            if not arguments:
                raise ValueError("Missing arguments")

            if name == "read_query":
                if not arguments["query"].strip().upper().startswith("SELECT"):
                    raise ValueError("Only SELECT queries are allowed for read_query")
                results = db.execute_query(arguments["query"])
                return [types.TextContent(type="text", text=str(results))]

            elif name == "write_query":
                if arguments["query"].strip().upper().startswith("SELECT"):
                    raise ValueError("SELECT queries are not allowed for write_query")
                results = db.execute_query(arguments["query"])
                return [types.TextContent(type="text", text=str(results))]

            else:
                raise ValueError(f"Unknown tool: {name}")

        except sqlite3.Error as e:
            return [types.TextContent(type="text", text=f"Database error: {str(e)}")]
        except Exception as e:
            return [types.TextContent(type="text", text=f"Error: {str(e)}")]

    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        logger.info("Server running with stdio transport")
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="sqlite",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    db_path = os.getenv("DATABASE_PATH", "database/new_created_db.db")
    csv_path = os.getenv("CSV_PATH", "data/input.csv")
    table_name = os.getenv("TABLE_NAME", "imported_table")

    asyncio.run(main(db_path, csv_path, table_name))
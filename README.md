<<<<<<< HEAD
# MCP SQLite Server

This project demonstrates the use of an SQLite database with the Model Context Protocol (MCP). It allows users to upload CSV files, convert them into database tables, and perform SQL queries (SELECT, CRUD operations, etc.).

## Prerequisites

- Python 3.11 or higher
- `uv` CLI tool (for managing the virtual environment and running the server)

## Setup Instructions

### Step 1: Initialize the Project with `uv`

1. Open a terminal and navigate to the directory where you want to set up the project.
2. Run the following commands to initialize the project:
   ```bash
   uv init {{project_folder_name}}
   cd {{project_folder_name}}
   uv venv
   source .venv/bin/activate
   ```

### Step 2: Install Dependencies

1. Clone the repository into the initialized project folder:
   ```bash
   git clone https://github.com/your-repo/mcp-dbms.git .
   ```
2. Install the required Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Step 3: Configure `claude_desktop_config.json`

1. Locate the `claude_desktop_config.json` file in your system.
2. Add the following configuration to the file:
   ```json
   {
       "mcpServers": {
           "sqlite": {
               "command": "uv",
               "args": [
                   "--directory",
                   "absolute_path_to/mcp_server",
                   "run",
                   "src/main.py",
                   "--db-path",
                   "path_to_db"
               ]
           }
       }
   }
   ```
   Replace:
   - `absolute_path_to/mcp_server` with the absolute path to the `mcp-dbms` project folder.
   - `path_to_db` with the path to the SQLite database file (e.g., `database/new_created_db.db`).

### Step 4: Run the Server

1. Start the MCP SQLite server:
   ```bash
   uv run src/main.py --db-path database/new_created_db.db
   ```

2. The server will start and listen for requests.

### Features

- **Upload CSV**: Upload a CSV file and convert it into a database table.
- **Execute Queries**: Perform SQL queries (SELECT, INSERT, UPDATE, DELETE, etc.).
- **List Tables**: View all tables in the database.
- **Describe Table**: Get schema information for a specific table.

### Default Dataset

If no CSV file is uploaded, the server will use the default dataset located at `data/youtube_2025_dataset.csv`.

### Notes

- Ensure that the `data` folder contains the default dataset (`youtube_2025_dataset.csv`) if no CSV file is provided.
- The SQLite database file will be created at the path specified in the `--db-path` argument.

### Troubleshooting

- **FileNotFoundError**: Ensure the CSV file exists or the default dataset is available in the `data` folder.
- **SQLite Syntax Errors**: Ensure column names in the CSV file do not conflict with SQLite reserved keywords.

### License

This project is licensed under the MIT License. See the `LICENSE` file for details.
=======
# mcp-sql
It uses mcp architecture to generate dbms operations from simple text
>>>>>>> 2f1d4e25cf07addef050c4c5e91daa04eb07d392

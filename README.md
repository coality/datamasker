<<<<<<< HEAD
# datamasker

You are a senior software developer specialized in PowerShell, SQL Server, and data security.

Your task is to generate a GENERIC, ROBUST PowerShell script that generates a SQL Server data-masking script from a JSON configuration file.

=====================
GENERAL CONTEXT
=====================

The goal is to mask sensitive data in SQL Server databases (HOMO / TEST environments).

The masking process MUST follow this architecture:

1. A JSON file explicitly defines:
   - schema name
   - table name
   - column name to mask
   - column used for ordering (orderBy)
2. A PowerShell script:
   - reads the JSON
   - validates the rules against SQL Server metadata
   - generates a SQL script (masking.sql)
3. The SQL execution is performed later using sqlcmd.
   PowerShell MUST NOT execute SQL UPDATE statements directly.

PowerShell is only responsible for VALIDATION and SQL SCRIPT GENERATION.

=====================
SECURITY RULES (MANDATORY)
=====================

- A column MUST NEVER be masked if it:
  - is a PRIMARY KEY
  - is part of a FOREIGN KEY (incoming or outgoing)
  - has a UNIQUE constraint
  - is a computed column

- If any rule violates one of the above constraints:
  - the script MUST stop execution
  - display a clear error message
  - NOT generate masking.sql

- No automatic guessing is allowed.
  Only tables and columns explicitly defined in the JSON are processed.

=====================
JSON FORMAT TO SUPPORT
=====================

Example JSON file:

=======
# Datamasker

SQL Server Data Masking Script Generator for HOMO/TEST environments.

## Objective

Datamasker generates SQL Server data masking scripts from JSON configuration files. It validates masking rules against SQL Server metadata and produces an auditable `masking.sql` script that can be reviewed and executed manually.

**Important**: Python never executes UPDATE statements directly. SQL script execution is always a separate, manual operational step.

## General Workflow

1. Create the DPAPI-encrypted password file (one-time setup)
2. Create the functional configuration file (masking rules)
3. Create the technical configuration file (connection settings)
4. Run the generator: `python -m app.cli generate --config sample.masking.json --connection sample.connection.json --output masking.sql`
5. Review the generated `masking.sql`
6. Execute `masking.sql` manually via sqlcmd or another SQL Server tool

## Configuration File Architecture

```
datamasker/
  app/                      # Application source code
    cli.py                  # Command-line interface
    config_loader.py        # Functional configuration loader
    connection_loader.py    # Technical configuration loader
    models.py               # Data models (dataclasses)
    exceptions.py           # Custom exceptions
    sqlserver_metadata.py   # SQL Server metadata queries
    validator.py            # Rule validation against metadata
    sql_generator.py        # SQL script generation
    secret_store.py         # DPAPI encryption/decryption
  tests/                    # Unit tests
  secrets/                  # Directory for encrypted password files (not committed)
  sample.masking.json       # Sample functional configuration
  sample.connection.json    # Sample technical configuration
  requirements.txt          # Python dependencies
```

## Prerequisites

- Python 3.11 or later
- Windows Server (for DPAPI support)
- ODBC Driver 17 for SQL Server
- SQL Server instance for validation (read-only access to system catalogs is sufficient)

## Installation

### Create Virtual Environment (Windows)

```cmd
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### Linux/macOS Virtual Environment

```cmd
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Note**: DPAPI support is only available on Windows. On Linux/macOS, the application can generate SQL scripts but cannot decrypt DPAPI-encrypted passwords.

### Installing Dependencies

```cmd
pip install pyodbc pytest
```

## Functional Configuration

The functional configuration file (`sample.masking.json`) defines which columns to mask:

```json
{
  "global": {
    "maskingFormat": "<{column}_{counter}>",
    "padLength": 4
  },
  "maskingRules": [
    {
      "schema": "dbo",
      "table": "Personnel",
      "column": "LastName",
      "orderBy": "PersonID"
    }
  ]
}
```

**Fields**:
- `global.maskingFormat`: Template for mask values. Must contain `<{column}>` placeholder.
- `global.padLength`: Zero-padding length for the counter (must be strictly positive integer).
- `maskingRules`: Array of rules. Each rule requires: `schema`, `table`, `column`, `orderBy`.

## Technical Configuration

The technical configuration file (`sample.connection.json`) defines database connection:

```json
{
  "server": "SQL01",
  "database": "MyDb",
  "username": "masking_user",
  "passwordFile": "secrets/sql-password.dpapi"
}
```

**Fields**:
- `server`: SQL Server host name or IP address.
- `database`: Target database name.
- `username`: SQL Server login name.
- `passwordFile`: Path to the DPAPI-encrypted password file.

**Important**: This file contains no clear-text password. The actual password is stored separately in the DPAPI file.

## Secure Password Handling with DPAPI

### What is DPAPI?

DPAPI (Data Protection API) is a Windows cryptographic API that protects data using the current user account or machine credentials. When you encrypt a password with DPAPI:

- The encrypted data can only be decrypted by the same Windows user account on the same machine.
- The encryption is transparent - no manual key management is required.
- If you copy the encrypted file to another machine or user account, decryption will fail.

### How DPAPI Works in This Project

1. **Encryption** (`encrypt-password` command): Takes a plain-text password, encrypts it with DPAPI using the current Windows user context, and writes the encrypted bytes to a file.

2. **Decryption** (during `generate` command): Reads the encrypted file, calls DPAPI to decrypt using the same user context, and returns the password in memory only.

3. **Security Guarantee**: The password never exists in clear text on disk. Even if someone gains access to the encrypted file and the machine, they cannot decrypt it without the original user credentials.

### Limitations

- DPAPI encryption is bound to the Windows account that performed the encryption.
- Moving the encrypted file to another machine or user account will make it unreadable.
- If the Windows user password is changed, DPAPI may fail to decrypt existing files.
- On Windows Server, if the server is joined to a domain, DPAPI may be subject to domain security policies.

## Creating the DPAPI Password File

### Step-by-Step Instructions

1. **Ensure you are on the target Windows server** (or an account that will run Datamasker).

2. **Create the secrets directory**:
   ```cmd
   mkdir secrets
   ```

3. **Generate the encrypted password file**:
   ```cmd
   python -m app.cli encrypt-password --output secrets/sql-password.dpapi
   ```
   
   When prompted, enter the SQL Server password. The password is encrypted immediately and stored in the file. It is never displayed or logged.

4. **Verify the file was created**:
   ```cmd
   dir secrets\sql-password.dpapi
   ```

5. **Protect the secrets directory with NTFS permissions** (see next section).

### Example Output

```
Enter SQL Server password: ********
SUCCESS: Password encrypted and saved to 'secrets\sql-password.dpapi'
NOTE: This file is encrypted with DPAPI and can only be decrypted
      by the same Windows user account on the same machine.
```

## Protecting Secrets with NTFS ACLs

### Recommended Permissions

The `secrets` directory should be accessible only by the account that runs Datamasker:

```cmd
icacls secrets /inheritance:r
icacls secrets /grant:r "DOMAIN\Username:RX"
icacls secrets /grant:r "DOMAIN\Username:(OI)(CI)W"
```

Where `DOMAIN\Username` is the account that runs the masking process.

### Verification

Check current permissions:
```cmd
icacls secrets
```

Expected output should show only the authorized user with access.

## Command-Line Usage

### Encrypt Password (DPAPI)

```cmd
python -m app.cli encrypt-password --output secrets/sql-password.dpapi
```

Interactive: Prompts for password without echo.

### Generate Masking Script

```cmd
python -m app.cli generate --config sample.masking.json --connection sample.connection.json --output masking.sql
```

### All Options

```
datamasker [-h] {encrypt-password,generate}

encrypt-password:
  --output, -o    Output file for encrypted password

generate:
  --config, -c    Functional configuration JSON file
  --connection, -cn  Technical configuration JSON file
  --output, -o    Output path for generated SQL script
```

## Example Generation Command

```cmd
python -m app.cli generate --config sample.masking.json --connection sample.connection.json --output masking.sql
```

If successful:
```
SUCCESS: masking.sql generated at 'masking.sql'
NOTE: Review the generated SQL script before executing it manually.
      SQL execution is NOT automatic. Use sqlcmd or another tool to run it.
```

If validation fails:
```
ERROR: Validation failed. The following rules cannot be processed:
  - Column 'dbo.Personnel.PersonID' is a PRIMARY KEY and cannot be masked

No masking.sql file has been generated.
```

## Generated File

The generator produces `masking.sql` with SQL UPDATE statements:

```sql
-- ===============================================
-- MASKING RULE
-- Schema: dbo
-- Table: Personnel
-- Column: LastName
-- orderBy: PersonID
-- Generated by: Datamasker
-- ===============================================
WITH cte AS (
    SELECT PersonID, ROW_NUMBER() OVER (ORDER BY PersonID) AS rn
    FROM dbo.Personnel
)
UPDATE cte
SET LastName = '<LASTNAME_' + RIGHT('0000' + CAST(rn AS VARCHAR), 4) + '>';
GO
```

## Security Rules

A column **cannot be masked** if it is:
- A PRIMARY KEY
- A FOREIGN KEY (source or target)
- Under a UNIQUE constraint
- A computed column

If any rule violates these constraints, the generator stops and reports the error. No `masking.sql` is created.

## Error Handling

| Exit Code | Meaning |
|-----------|---------|
| 0 | Success |
| 1 | Error (configuration, validation, secret, or execution error) |

All errors are written to stderr with clear messages. Passwords never appear in error messages or logs.

## Running Tests

```cmd
pytest tests/
```

Run with verbose output:
```cmd
pytest tests/ -v
```

Run specific test file:
```cmd
pytest tests/test_config_loader.py -v
```

## Project Structure

```
datamasker/
  app/
    __init__.py              # Package init
    cli.py                   # CLI entry point
    config_loader.py         # Functional config loader
    connection_loader.py    # Technical config loader
    models.py                # Dataclasses
    exceptions.py            # Custom exceptions
    sqlserver_metadata.py    # SQL Server catalog queries
    validator.py             # Rule validation
    sql_generator.py         # SQL generation
    secret_store.py          # DPAPI operations
  tests/
    test_*.py                # Unit tests
  secrets/                   # DPAPI password files (not in git)
  sample.masking.json        # Example functional config
  sample.connection.json     # Example technical config
  requirements.txt           # Dependencies
  README.md                  # This file
```

## Known Limitations

1. **DPAPI is Windows-only**: Password encryption and decryption only work on Windows with the same user account.

2. **No SQL execution**: Python never executes UPDATE statements. All masking must be applied manually.

3. **Validation requires read access**: The generator needs SELECT permission on system catalogs (`sys.tables`, `sys.columns`, `sys.foreign_keys`, etc.).

4. **Deterministic but not random**: Masking values are deterministic based on `ROW_NUMBER()` and `orderBy` column. This is intentional for reproducibility.

5. **No rollback script**: The generator does not create rollback scripts. Backups should be taken before execution.

## Operational Best Practices

1. **Never store clear-text passwords** in configuration files or scripts.

2. **Protect the secrets directory** with NTFS ACLs. Only the service account should have access.

3. **Review masking.sql before execution**. Verify the UPDATE statements target the correct columns.

4. **Test on a non-production environment first**. Validate the generated SQL in a test database.

5. **Take a database backup before applying masking**. The masking is irreversible without backups.

6. **Document the masking process**. Keep records of which environments have been masked and when.

## Manual Execution of masking.sql via sqlcmd

**Important**: Python never executes the masking UPDATE statements. The SQL script must be executed manually by an operator.

### Basic Execution

```cmd
sqlcmd -S SQL01 -d MyDb -U masking_user -i masking.sql
```

This command:
- `-S SQL01`: Connects to SQL01 server
- `-d MyDb`: Uses MyDb database
- `-U masking_user`: Authenticates with SQL login (password will be prompted)
- `-i masking.sql`: Executes the masking script from file

### With Password (Not Recommended)

```cmd
sqlcmd -S SQL01 -d MyDb -U masking_user -P MyPassword -i masking.sql
```

**Warning**: Using `-P` exposes the password in clear text on the command line. This is visible in:
- Process lists (`wmic process get commandline`)
- Log files
- Shell history

Prefer using `-U` without `-P` and entering the password when prompted, or use Windows Authentication (`-E`) if available.

### Windows Authentication

If the SQL Server supports Windows Authentication and the current user has access:

```cmd
sqlcmd -S SQL01 -d MyDb -E -i masking.sql
```

### Verify Before Execution

To review the script without executing:

```cmd
type masking.sql
```

Or open `masking.sql` in a text editor before running.

### Dry Run (What-If)

To see what would be updated without making changes (SQL Server Management Studio):

1. In SSMS, open `masking.sql`
2. Click "Analyze" to check for syntax errors
3. Use `SET STATISTICS IO ON` and `SET STATISTICS TIME ON` before running
4. Review the number of rows affected

## Complete End-to-End Workflow Example

### 1. Set Up Environment

```cmd
git clone <repository>
cd datamasker
python -m venv venv
venv\Scripts\activate
pip install pyodbc pytest
```

### 2. Create Secrets Directory and Encrypt Password

```cmd
mkdir secrets
python -m app.cli encrypt-password --output secrets/sql-password.dpapi
Enter SQL Server password: MySecretPassword123
SUCCESS: Password encrypted and saved to 'secrets\sql-password.dpapi'
```

### 3. Create Functional Configuration

Create `config.masking.json`:

```json
>>>>>>> 8fe964e (Add skeleton files)
{
  "global": {
    "maskingFormat": "<{column}_{counter}>",
    "padLength": 4
  },
  "maskingRules": [
    {
      "schema": "dbo",
      "table": "Personnel",
      "column": "LastName",
      "orderBy": "PersonID"
    },
    {
      "schema": "dbo",
      "table": "Personnel",
      "column": "FirstName",
      "orderBy": "PersonID"
    }
  ]
}
<<<<<<< HEAD

=====================
MASKING LOGIC
=====================

Each masking rule must generate a deterministic, stable value using ROW_NUMBER().

Masked values must follow this format:

<ColumnName_0001>
<ColumnName_0002>

The counter must:
- be incremental
- be deterministic
- be ordered by the column "orderBy"
- be zero-padded based on padLength

=====================
SQL TEMPLATE TO GENERATE (STRICT)
=====================

For each rule, generate an independent SQL block exactly like this:

WITH cte AS (
    SELECT
        PersonID,
        ROW_NUMBER() OVER (ORDER BY PersonID) AS rn
    FROM dbo.Personnel
)
UPDATE cte
SET LastName =
    '<LastName_' 
    + RIGHT('0000' + CAST(rn AS VARCHAR), 4)
    + '>';
GO

=====================
SQL SERVER VALIDATIONS (MANDATORY)
=====================

Before generating SQL, the PowerShell script MUST validate using SQL Server system catalogs:

- table exists
- column to mask exists
- orderBy column exists
- masked column is NOT:
  - primary key
  - foreign key
  - unique
  - computed

System views to use:
- sys.tables
- sys.schemas
- sys.columns
- sys.indexes
- sys.index_columns
- sys.foreign_keys

=====================
OUTPUT REQUIREMENTS
=====================

The PowerShell script must generate a file named:

masking.sql

The SQL file must:
- contain ONLY SQL code
- be fully readable and auditable
- include comments indicating:
  - schema
  - table
  - column being masked
  - origin of the rule (JSON)

=====================
CODE QUALITY REQUIREMENTS
=====================

The PowerShell code must be:
- clean
- well commented
- structured into functions
- readable by operations teams
- production ready
- generic (works for any SQL Server database)

=====================
FINAL GOAL
=====================

Produce ONE PowerShell script that:
- is generic and reusable
- does NOT contain application-specific logic
- relies ONLY on JSON configuration
- safely generates SQL Server masking scripts
- never masks keys or constrained columns

Deliver ONLY the PowerShell code.
=======
```

### 4. Create Technical Configuration

Create `config.connection.json`:

```json
{
  "server": "SQL01",
  "database": "MyDb",
  "username": "masking_user",
  "passwordFile": "secrets/sql-password.dpapi"
}
```

### 5. Generate Masking Script

```cmd
python -m app.cli generate --config config.masking.json --connection config.connection.json --output masking.sql
SUCCESS: masking.sql generated at 'masking.sql'
NOTE: Review the generated SQL script before executing it manually.
```

### 6. Review the Generated Script

```cmd
type masking.sql
```

Verify:
- Schema and table names are correct
- Columns to mask are correct
- No unintended changes
- Comments match expectations

### 7. Execute Manually

```cmd
sqlcmd -S SQL01 -d MyDb -U masking_user -i masking.sql
Password: MySecretPassword123

(affected rows displayed)
```

### 8. Verify Masking Applied

```cmd
sqlcmd -S SQL01 -d MyDb -U masking_user -Q "SELECT TOP 10 LastName FROM dbo.Personnel"
Password: MySecretPassword123

LastName
--------
<LASTNAME_0001>
<LASTNAME_0002>
...
```

## Security Summary

| Concern | How Datamasker Addresses It |
|---------|----------------------------|
| Password storage | DPAPI-encrypted, Windows user-bound |
| Clear-text passwords | Never stored on disk |
| Password in logs | Never logged or displayed |
| Password in memory | Decrypted only when needed, not stored |
| Connection string | Built per-request, not logged |
| Secrets in git | `secrets/` directory in `.gitignore` |
| NTFS protection | README documents required ACLs |
| SQL injection | Generated SQL uses parameterized patterns |

## Troubleshooting

### "DPAPI decryption failed: The secret may have been encrypted on a different Windows account"

The encrypted password file was created by a different Windows user or on a different machine. Re-create the password file using the correct account.

### "Schema 'X' does not exist in the database"

Verify the schema name in your functional configuration matches the database exactly. Default is usually `dbo`.

### "Column 'X' is a PRIMARY KEY and cannot be masked"

This is a safety check. Primary keys should never be masked in a HOMO/TEST environment. If you need to mask this column, redesign your approach.

### "Failed to connect to SQL Server"

Check:
- Server name is correct
- SQL Server is running
- Network connectivity from the machine running Datamasker
- Firewall allows connection to SQL Server port (default 1433)
- Username/password credentials are valid

### "No modules named 'pyodbc'"

Install dependencies:
```cmd
pip install pyodbc
```
>>>>>>> 8fe964e (Add skeleton files)

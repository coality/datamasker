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

## PowerShell Wrapper

A production-ready PowerShell wrapper script is provided for Windows environments. The wrapper orchestrates the Python CLI and adds support for scheduled execution, confirmation prompts, and dry-run validation.

**File**: `scripts/datamasker.ps1`

### PowerShell Wrapper Features

- **Direct Python invocation**: Calls the virtualenv Python executable directly without interactive activation
- **Parameter-driven actions**: EncryptPassword, TestConnection, GenerateSql, ExecuteSql, FullRun
- **Automation support**: NoConfirm and DryRun switches for scripted/scheduled usage
- **Clear operational messages**: Timestamped INFO/WARN/ERROR/SUCCESS messages
- **Exit codes**: 0 for success, 1 for errors, 2 for invalid parameter combinations

### Invoking the VirtualEnv Python

The wrapper calls `.venv\Scripts\python.exe` directly:

```powershell
& $PythonExe -m app.cli <command>
```

This avoids interactive shell activation and is suitable for non-interactive Task Scheduler scenarios.

### PowerShell Parameters

| Parameter | Required | Description |
|-----------|----------|-------------|
| `-Action` | Yes | Operation: EncryptPassword, TestConnection, GenerateSql, ExecuteSql, FullRun |
| `-Config` | For GenerateSql, FullRun | Path to functional masking configuration JSON |
| `-Connection` | For TestConnection, GenerateSql, ExecuteSql, FullRun | Path to technical connection configuration JSON |
| `-SqlFile` | No | Output/input path for masking.sql (default: .\masking.sql) |
| `-ProjectRoot` | No | Datamasker project root (default: script parent directory) |
| `-PythonExe` | No | Python executable path (default: .\.venv\Scripts\python.exe) |
| `-NoConfirm` | No | Suppress confirmation prompts for automation |
| `-DryRun` | No | Validate but skip actual SQL execution |
| `-LogFile` | No | Optional log file path |

### PowerShell Action Details

#### EncryptPassword

Prompts for the SQL Server password (without echo) and calls the Python CLI `encrypt-password` command to create the DPAPI-encrypted password file. The password is never displayed.

```powershell
.\scripts\datamasker.ps1 -Action EncryptPassword
```

#### TestConnection

Validates the connection JSON, checks the DPAPI password file exists, and calls the Python CLI `test-connection` command. Does not generate or execute SQL.

```powershell
.\scripts\datamasker.ps1 -Action TestConnection -Connection ".\sample.connection.json"
```

#### GenerateSql

Validates inputs, calls the Python CLI `generate` command, and produces `masking.sql`. Does not execute SQL.

```powershell
.\scripts\datamasker.ps1 -Action GenerateSql -Config ".\sample.masking.json" -Connection ".\sample.connection.json"
```

#### ExecuteSql

Executes an existing `masking.sql` through sqlcmd. Prompts for confirmation unless `-NoConfirm` is provided.

```powershell
.\scripts\datamasker.ps1 -Action ExecuteSql -Connection ".\sample.connection.json" -SqlFile ".\masking.sql"
.\scripts\datamasker.ps1 -Action ExecuteSql -Connection ".\sample.connection.json" -SqlFile ".\masking.sql" -NoConfirm
```

#### FullRun

Performs the complete end-to-end workflow:

1. Validates environment
2. Tests connection
3. Generates masking.sql
4. Executes masking.sql via sqlcmd

```powershell
.\scripts\datamasker.ps1 -Action FullRun -Config ".\sample.masking.json" -Connection ".\sample.connection.json"
```

#### DryRun Mode

With `-DryRun`, FullRun and ExecuteSql validate everything and generate SQL but skip actual sqlcmd execution:

```powershell
.\scripts\datamasker.ps1 -Action FullRun -Config ".\sample.masking.json" -Connection ".\sample.connection.json" -DryRun
```

This shows what would be executed without making database changes.

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
  scripts/
    datamasker.ps1          # PowerShell wrapper
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
    "maskingFormat": "MASKED_{column}_{counter}",
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
- `global.maskingFormat`: Template for mask values. Supports `{column}` and `{counter}` placeholders (e.g. `MASKED_{column}_{counter}`).
- `global.padLength`: Zero-padding length for the counter (must be strictly positive integer).
- `maskingRules`: Array of rules. Each rule requires: `schema`, `table`, `column`, `orderBy`.

## Technical Configuration

The technical configuration file (`sample.connection.json`) defines database connection:

```json
{
  "server": "SQL01",
  "username": "masking_user",
  "passwordFile": "secrets/sql-password.dpapi",
  "databases": ["MyDb", "MyDb2", "MyDb3"]
}
```

**Fields**:
- `server`: SQL Server host name or IP address.
- `username`: SQL Server login name.
- `passwordFile`: Path to the DPAPI-encrypted password file.
- `databases`: Array of database names to process.

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

### Using the PowerShell Wrapper

```powershell
.\scripts\datamasker.ps1 -Action EncryptPassword
```

### Step-by-Step Instructions (Manual)

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

## Command-Line Usage (Python CLI)

### Encrypt Password (DPAPI)

```cmd
python -m app.cli encrypt-password --output secrets/sql-password.dpapi
```

Interactive: Prompts for password without echo.

### Generate Masking Script

```cmd
python -m app.cli generate --config sample.masking.json --connection sample.connection.json --output masking.sql
```

### Test Connection

```cmd
python -m app.cli test-connection --connection sample.connection.json
```

Verifies connectivity to the SQL Server without generating any SQL script. Useful to validate credentials and network connectivity before running `generate`.

### All Options

```
datamasker [-h] {encrypt-password,generate,test-connection}

encrypt-password:
  --output, -o    Output file for encrypted password

generate:
  --config, -c    Functional configuration JSON file
  --connection, -cn  Technical configuration JSON file
  --output, -o    Output path for generated SQL script

test-connection:
  --connection, -cn  Technical configuration JSON file
```

## PowerShell Wrapper Examples

### Encrypt Password

```powershell
.\scripts\datamasker.ps1 -Action EncryptPassword
```

Prompts for password, encrypts with DPAPI, saves to `secrets\sql-password.dpapi`.

### Test Connection

```powershell
.\scripts\datamasker.ps1 -Action TestConnection -Connection ".\sample.connection.json"
```

Validates the connection file and DPAPI password file, tests SQL Server connectivity.

### Generate SQL

```powershell
.\scripts\datamasker.ps1 -Action GenerateSql -Config ".\sample.masking.json" -Connection ".\sample.connection.json"
```

Generates `masking.sql` without executing it.

### Execute SQL (with confirmation)

```powershell
.\scripts\datamasker.ps1 -Action ExecuteSql -Connection ".\sample.connection.json" -SqlFile ".\masking.sql"
```

Prompts for SQL Server password and executes `masking.sql` via sqlcmd.

### Full Run

```powershell
.\scripts\datamasker.ps1 -Action FullRun -Config ".\sample.masking.json" -Connection ".\sample.connection.json"
```

Tests connection, generates SQL, and executes it (with confirmation).

### Full Run with NoConfirm

```powershell
.\scripts\datamasker.ps1 -Action FullRun -Config ".\sample.masking.json" -Connection ".\sample.connection.json" -NoConfirm
```

Full run without prompts. Suitable for automation and scripting.

### Full Run with DryRun

```powershell
.\scripts\datamasker.ps1 -Action FullRun -Config ".\sample.masking.json" -Connection ".\sample.connection.json" -DryRun
```

Validates everything and generates SQL but skips sqlcmd execution. Shows what would be executed.

## Windows Task Scheduler Usage

The PowerShell wrapper is designed for non-interactive scheduled execution.

### Scheduler Example

```
powershell.exe -ExecutionPolicy Bypass -File "C:\tools\datamasker\scripts\datamasker.ps1" -Action FullRun -Config "C:\tools\datamasker\sample.masking.json" -Connection "C:\tools\datamasker\sample.connection.json" -SqlFile "C:\tools\datamasker\masking.sql" -NoConfirm
```

This command:
- `-ExecutionPolicy Bypass`: Allows script execution without changing system policy
- `-File`: Specifies the wrapper script path
- `-Action FullRun`: Performs complete workflow
- `-Config` and `-Connection`: Paths to configuration files
- `-SqlFile`: Output/input SQL file path
- `-NoConfirm`: Skips interactive prompts (required for scheduled tasks)

### DPAPI and Scheduled Tasks

DPAPI decryption depends on the Windows account context. The encrypted password file must have been generated by the same Windows user account that runs the scheduled task. If the task runs under a service account, generate the DPAPI file using that same account first.

### Scheduled Task Configuration Best Practices

1. Create the DPAPI password file while logged in as the service account
2. Use a dedicated service account with minimal permissions
3. Set the working directory to the Datamasker project root
4. Use `-NoConfirm` for fully automated execution
5. Redirect output to a log file using `-LogFile`

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
| 2 | Invalid parameter combination |

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
  scripts/
    datamasker.ps1           # PowerShell wrapper
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

2. **No SQL execution**: Python never executes UPDATE statements. All masking must be applied manually or via PowerShell wrapper with explicit ExecuteSql or FullRun action.

3. **Validation requires read access**: The generator needs SELECT permission on system catalogs (`sys.tables`, `sys.columns`, `sys.foreign_keys`, etc.).

4. **Deterministic but not random**: Masking values are deterministic based on `ROW_NUMBER()` and `orderBy` column. This is intentional for reproducibility.

5. **No rollback script**: The generator does not create rollback scripts. Backups should be taken before execution.

6. **sqlcmd credential handling**: The PowerShell wrapper does not pass passwords to sqlcmd on the command line. Use SQL authentication with `-U` and password prompt, or prefer Windows Authentication (`-E`). Using `-P MyPassword` exposes the password in process listings and logs.

## Operational Best Practices

1. **Never store clear-text passwords** in configuration files or scripts.

2. **Protect the secrets directory** with NTFS ACLs. Only the service account should have access.

3. **Review masking.sql before execution**. Verify the UPDATE statements target the correct columns.

4. **Test on a non-production environment first**. Validate the generated SQL in a test database.

5. **Take a database backup before applying masking**. The masking is irreversible without backups.

6. **Document the masking process**. Keep records of which environments have been masked and when.

7. **Use DryRun before FullRun** to validate the workflow without making database changes.

8. **Use consistent account context** for DPAPI encryption and scheduled task execution.

## Complete End-to-End Workflow Examples

### Using PowerShell Wrapper

#### 1. Set Up Environment

```cmd
git clone <repository>
cd datamasker
python -m venv venv
venv\Scripts\activate
pip install pyodbc pytest
```

#### 2. Encrypt Password

```powershell
.\scripts\datamasker.ps1 -Action EncryptPassword
Enter SQL Server password: MySecretPassword123
SUCCESS: Password encrypted and saved to 'secrets\sql-password.dpapi'
```

#### 3. Run Full Workflow (with confirmation)

```powershell
.\scripts\datamasker.ps1 -Action FullRun -Config ".\sample.masking.json" -Connection ".\sample.connection.json"
```

#### 4. Run Full Workflow (no prompts)

```powershell
.\scripts\datamasker.ps1 -Action FullRun -Config ".\sample.masking.json" -Connection ".\sample.connection.json" -NoConfirm
```

#### 5. Dry Run First

```powershell
.\scripts\datamasker.ps1 -Action FullRun -Config ".\sample.masking.json" -Connection ".\sample.connection.json" -DryRun
```

### Using Python CLI Directly

#### 1. Set Up Environment

```cmd
git clone <repository>
cd datamasker
python -m venv venv
venv\Scripts\activate
pip install pyodbc pytest
```

#### 2. Create Secrets Directory and Encrypt Password

```cmd
mkdir secrets
python -m app.cli encrypt-password --output secrets/sql-password.dpapi
Enter SQL Server password: MySecretPassword123
SUCCESS: Password encrypted and saved to 'secrets\sql-password.dpapi'
```

#### 3. Create Functional Configuration

Create `config.masking.json`:

```json
{
  "global": {
    "maskingFormat": "MASKED_{column}_{counter}",
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
```

#### 4. Create Technical Configuration

Create `config.connection.json`:

```json
{
  "server": "SQL01",
  "username": "masking_user",
  "passwordFile": "secrets/sql-password.dpapi",
  "databases": ["MyDb", "MyDb2", "MyDb3"]
}
```

#### 5. Generate Masking Script

```cmd
python -m app.cli generate --config config.masking.json --connection config.connection.json --output masking.sql
SUCCESS: masking.sql generated at 'masking.sql'
NOTE: Review the generated SQL script before executing it manually.
```

#### 6. Review the Generated Script

```cmd
type masking.sql
```

Verify:
- Schema and table names are correct
- Columns to mask are correct
- No unintended changes
- Comments match expectations

#### 7. Execute Manually

```cmd
sqlcmd -S SQL01 -d MyDb -U masking_user -i masking.sql
Password: MySecretPassword123

(affected rows displayed)
```

#### 8. Verify Masking Applied

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
| SQL execution | Separated from generation; requires explicit action |

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

### PowerShell script fails with "cannot be loaded because running scripts is disabled"

Use `-ExecutionPolicy Bypass` when invoking PowerShell:
```cmd
powershell.exe -ExecutionPolicy Bypass -File ".\scripts\datamasker.ps1" -Action EncryptPassword
```

### sqlcmd is not recognized

Ensure SQL Server command-line tools are installed and `sqlcmd` is available in PATH. You can download the [SQL Server command-line tools](https://docs.microsoft.com/en-us/sql/tools/sqlcmd-utility) if needed.

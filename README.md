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

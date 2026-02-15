# OPSIGHT

Follow these steps to set up the environment and initialize the database for the **OPSIGHT** project.

---

## 1. Environment Configuration
Before running the initialization script, you must set the `DATABASE_URL` environment variable in **PowerShell**. This allows the application to connect to your PostgreSQL instance.

**Run the following command in your terminal:**
```powershell
$env:DATABASE_URL="postgresql+psycopg2://postgres:PASS@localhost:5432/OPSIGHT"

```

> [!IMPORTANT]
> Replace `PASS` with your actual PostgreSQL password before running the command.

---

## 2. Database Initialization

Once the environment variable is active, use the Python module to create the necessary database schema:

```powershell
python -m db.init_db

```

---

## 3. Seed Shift Definitions

After the tables are successfully created, you must populate the `shift_definitions` table. This project utilizes a 6-hour shift rotation logic.

**Execute this SQL command in your database tool (e.g., pgAdmin or psql):**

```sql
INSERT INTO shift_definitions (shift_id, shift_name, duration_hours)
VALUES
  (1, 'DAY', 6),
  (2, 'NIGHT', 6)
ON CONFLICT (shift_id) DO NOTHING;

```

### Shift Logic Overview

| Shift ID | Shift Name | Duration (Hours) |
| --- | --- | --- |
| 1 | DAY | 6 |
| 2 | NIGHT | 6 |

---

## Troubleshooting

If the connection fails, verify that:

1. PostgreSQL is running on `localhost:5432`.
2. The database `OPSIGHT` has been created.
3. Your credentials in the `DATABASE_URL` are correct.

```
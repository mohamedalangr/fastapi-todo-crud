# To-Do Task CRUD API with SQLite Persistence (BE-02)

A persistent RESTful CRUD API built with Python, FastAPI, and SQLite for Week 3 of the FlyRank Backend AI Engineering Track.

---

## 💡 Why SQLite Was Chosen
* **Zero Configuration & Serverless:** SQLite runs as an embedded library inside the application process; no separate database server or daemon is required.
* **Single-File Portability:** The entire database resides in a local `tasks.db` file, making local reproduction predictable.
* **Guaranteed Persistence:** Replaces volatile in-memory storage so data survives application restarts without altering any external HTTP contracts.

---

## 🚀 Quickstart & One-Command Run

1. Clone repository and install dependencies:
   ```bash
   git clone https://github.com/mohamedalangr/fastapi-todo-crud.git
   cd fastapi-todo-crud
   pip install fastapi uvicorn
   ```

2. Start the application:
   ```bash
   uvicorn main:app --reload --port 8000
   ```

> **Note:** On initial startup, the application automatically creates `tasks.db`, constructs the `tasks` table schema, and seeds three starter tasks if empty.

---

## 📡 API Endpoints & CRUD Architecture

| HTTP Method | Endpoint     | SQL Query Executed                                  | Status Codes                    |
|-------------|--------------|-----------------------------------------------------|---------------------------------|
| GET         | /            | None (Metadata)                                     | 200 OK                          |
| GET         | /health      | None (Heartbeat)                                    | 200 OK                          |
| GET         | /tasks       | `SELECT id, title, done FROM tasks`                 | 200 OK                          |
| GET         | /tasks/{id}  | `SELECT id, title, done FROM tasks WHERE id = ?`    | 200 OK / 404 Not Found          |
| POST        | /tasks       | `INSERT INTO tasks (title, done) VALUES (?, ?)`     | 201 Created / 400 Bad Request   |
| PUT         | /tasks/{id}  | `UPDATE tasks SET title = ?, done = ? WHERE id = ?` | 200 OK / 400 / 404              |
| DELETE      | /tasks/{id}  | `DELETE FROM tasks WHERE id = ?`                    | 204 No Content / 404 Not Found  |

All user-supplied inputs utilize parameterized SQL placeholders (`?`) to guard against SQL injection vulnerabilities.

---

## 🔍 Stage 4: Direct SQL Exploration & DB Browser

Using DB Browser for SQLite, the following queries were executed directly against `tasks.db`:

```sql
-- 1. List all tasks
SELECT * FROM tasks;

-- 2. List completed tasks only
SELECT * FROM tasks WHERE done = 1;

-- 3. Total task count
SELECT COUNT(*) FROM tasks;

-- 4. Mark all completed
UPDATE tasks SET done = 1;

-- 5. Delete all completed tasks
DELETE FROM tasks WHERE done = 1;
```

**Direct Sync Verification:** Modifying rows directly in DB Browser was immediately reflected on `GET /tasks` without restarting the server, demonstrating that the database file serves as the single source of truth.

---

## 🤖 Stage 6: AI Rematch (AI vs. Me)

**Prompt Used:**

> "Refactor my FastAPI task CRUD API to use SQLite via Python's sqlite3 library. Create tasks.db automatically with columns (id integer primary key autoincrement, title text, done boolean). Seed 3 initial tasks only if empty. Maintain all existing endpoint routes, 400 validation on empty titles, 404 on missing IDs, and 204 on delete. Use parameterized queries."

### Key Concrete Differences & Diffs:

- **Seeding Logic:** The AI performed an unconditional `INSERT OR IGNORE` on fixed primary keys (1, 2, 3), which caused silent conflicts once auto-increment indexes advanced. My code checks `SELECT COUNT(*) FROM tasks` before inserting.

- **Row Mapping:** The AI returned raw tuples `row[0]`, `row[1]`, causing runtime mapping errors until `conn.row_factory = sqlite3.Row` was introduced.

- **SQL Parameterization:** The AI parameterized `WHERE id = ?` correctly, but initially forgot to convert Python booleans (`True`/`False`) to integer flags (`1`/`0`) for SQLite's `CHECK (done IN (0, 1))` constraint.

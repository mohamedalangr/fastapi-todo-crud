# Containerized Task CRUD API (BE-04)

A persistent RESTful CRUD API built with Python (FastAPI) and PostgreSQL, fully containerized using Docker and Docker Compose for the FlyRank Backend AI Engineering Track.

---

## 🚀 One-Command Quickstart

Start the entire stack (API server + PostgreSQL database) with a single command:

```bash
# 1. Clone repository
git clone https://github.com/mohamedalangr/fastapi-todo-crud.git
cd fastapi-todo-crud

# 2. Setup environment config
cp .env.example .env

# 3. Start whole stack
docker compose up --build -d
```

- **API is accessible at:** http://localhost:8000
- **Interactive Swagger Docs:** http://localhost:8000/docs
- **PostgreSQL Port:** 5432

---

## 📡 API Endpoints & CRUD Architecture

| HTTP Method | Path           | Target Action                              | Status Code                     |
|-------------|----------------|--------------------------------------------|---------------------------------|
| GET         | /              | Root API metadata                          | 200 OK                          |
| GET         | /health        | Heartbeat & DB readiness                   | 200 OK                          |
| GET         | /tasks         | List tasks (supports `?done=` and `?search=`) | 200 OK                       |
| GET         | /tasks/{id}    | Read single task by ID                     | 200 OK / 404 Not Found          |
| POST        | /tasks         | Create task (validated title)              | 201 Created / 400 Bad Request   |
| PUT         | /tasks/{id}    | Update title or done status                | 200 OK / 400 / 404              |
| DELETE      | /tasks/{id}    | Remove task                                | 204 No Content / 404 Not Found  |

All database operations use parameterized queries (`%s`) via `psycopg` to eliminate SQL injection vulnerabilities.

---

## 💾 Proof of Persistence

Persistence was confirmed across full container lifecycles:

1. Created a new task with ID 4 via `POST /tasks`.
2. Executed `docker compose down` to remove all running containers and networks.
3. Executed `docker compose up -d` to spin up a completely fresh container instance.
4. Executed `GET /tasks`—all 4 rows were returned intact because data is stored in the external `taskdata` Docker volume.

---

## 🗄️ Database Verification (psql)

Inspect data directly inside the PostgreSQL container:

```bash
docker compose exec db psql -U postgres -d tasks -c "SELECT * FROM tasks;"
```

```
 id |                    title                    | done 
----+---------------------------------------------+------
  1 | Review FlyRank backend brief                | t
  2 | Build CRUD API with FastAPI                 | f
  3 | Containerize stack with Postgres and Docker  | f
  4 | Persist inside containerized volume          | f
(4 rows)
```

---

## 🤖 Stage 6: AI Rematch (AI vs. Me)

**Prompt:** "Containerize my FastAPI task CRUD API using Docker Compose and PostgreSQL. Read connection credentials from a gitignored .env file, use a named volume for persistence, seed 3 tasks on first run, and preserve all existing CRUD routes."

### Findings & Diffs:

- **Race Condition Handling:** The AI did not specify a container health check on the `db` service. FastAPI crashed on initial launch because it attempted to connect before Postgres finished initialization. I solved this using Docker Compose `service_healthy` conditions and a connection retry loop in Python.

- **Volume Declaration:** The AI specified a bind mount (`./data:/var/lib/postgresql/data`) instead of a managed named volume (`taskdata:`), introducing filesystem permission issues on Linux/macOS.

- **Parameter Placeholders:** The AI mistakenly used `?` placeholders (SQLite syntax) instead of `%s` required by `psycopg`, which threw syntax errors on parameterized execution.

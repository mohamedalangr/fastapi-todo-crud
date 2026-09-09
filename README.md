# To-Do Task CRUD API (BE-01)

A lightweight in-memory RESTful CRUD API built with Python and FastAPI for the FlyRank Backend AI Engineering track.

---

## 🚀 Quickstart & Setup

Run the API locally in under 60 seconds with one command:

```bash
# 1. Clone repo
git clone https://github.com/mohamedalangr/fastapi-todo-crud.git
cd fastapi-todo-crud

# 2. Install dependencies
pip install fastapi uvicorn

# 3. Start server
uvicorn main:app --reload --port 8000
```

The server will be live at http://localhost:8000.

## 📡 API Endpoints & CRUD Mapping

| HTTP Method | Path           | Status Code               | Description                                          |
|-------------|----------------|---------------------------|------------------------------------------------------|
| GET         | /              | 200 OK                    | Service metadata and available endpoints             |
| GET         | /health        | 200 OK                    | Server heartbeat health check                        |
| GET         | /tasks         | 200 OK                    | List all tasks (supports `?done=` and `?search=`)    |
| GET         | /tasks/{id}    | 200 OK / 404 Not Found    | Fetch single task by ID                              |
| POST        | /tasks         | 201 Created / 400 Bad Request | Create a new task (validates non-empty title)    |
| PUT         | /tasks/{id}    | 200 OK / 404 / 400        | Update title or done status                          |
| DELETE      | /tasks/{id}    | 204 No Content / 404      | Remove task from memory                              |

## 🧪 Verified `curl -i` Checkpoint Output

### 1. POST /tasks (201 Created)

```
HTTP/1.1 201 Created
date: Wed, 09 Sep 2026 13:45:00 GMT
server: uvicorn
content-length: 44
content-type: application/json

{"id":4,"title":"Buy coffee","done":false}
```

### 2. GET /tasks/99 (404 Not Found)

```
HTTP/1.1 404 Not Found
date: Wed, 09 Sep 2026 13:45:10 GMT
server: uvicorn
content-length: 31
content-type: application/json

{"detail":"Task 99 not found"}
```

## 🖥️ Interactive Swagger UI Documentation

FastAPI automatically generates OpenAPI documentation at:
http://localhost:8000/docs

All CRUD actions were tested and confirmed functioning using Swagger UI's interactive "Try it out" feature.

## 💡 The Mortality Experiment

**Observation:** After creating new tasks, shutting down the server process (CTRL + C) and restarting it with `uvicorn main:app` causes all newly added tasks to vanish, resetting back to the initial 3 seed items.

**Why this happens:** In-memory storage allocates data strictly in volatile RAM associated with the Python process. When the process terminates, its memory space is deallocated by the operating system. This illustrates why real-world production backends rely on persistent databases (PostgreSQL/SQLite) to survive server restarts.

## 🤖 Stage 7: AI Rematch (AI vs. Me)

**Prompt Provided to AI:**

> "Build a Python FastAPI CRUD to-do list API with in-memory storage, validating that title cannot be empty (returning 400), returning 201 for POST, 204 for DELETE, and 404 with JSON error for missing items."

### Key Findings & Diffs:

- **Validation Handling:** The AI relied entirely on Pydantic's default 422 Unprocessable Entity for empty strings instead of catching whitespace-only inputs (`"   "`) with an explicit 400 Bad Request.

- **Delete Response Body:** The AI initially returned a 200 OK with `{"message": "deleted"}` rather than the standard HTTP 204 No Content specified by REST conventions.

- **ID Allocation:** The AI used `len(tasks) + 1` for new IDs, which causes ID collisions if an earlier task is deleted. My code uses `max(id) + 1` to ensure unique auto-incrementing IDs.

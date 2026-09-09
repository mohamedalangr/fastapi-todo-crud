import sqlite3
from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

DB_FILE = "tasks.db"

# --- Database Helper Functions & Initialization ---


def get_db_connection():
    """Returns a SQLite connection with Row factory enabled for dictionary-like access."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initializes the database table and seeds starter tasks if empty."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # Stage 0: Create table if missing
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                done BOOLEAN NOT NULL CHECK (done IN (0, 1))
            )
        """
        )

        # Check if table already has rows to prevent duplicate seeding on restarts
        cursor.execute("SELECT COUNT(*) FROM tasks")
        count = cursor.fetchone()[0]

        if count == 0:
            initial_tasks = [
                ("Review FlyRank backend brief", 1),
                ("Build CRUD API with FastAPI", 0),
                ("Inspect interactive Swagger docs", 0),
            ]
            cursor.executemany(
                "INSERT INTO tasks (title, done) VALUES (?, ?)", initial_tasks
            )
        conn.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initializes SQLite schema and single seed pass on startup
    init_db()
    yield


app = FastAPI(
    title="Task API (SQLite Backed)",
    version="2.0",
    description="A persistent SQLite CRUD API for task management.",
    lifespan=lifespan,
)

# --- Pydantic Data Models (Identical Contract to BE-01) ---


class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, description="Task title cannot be empty")


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(
        None,
        min_length=1,
        description="Updated title (cannot be empty if supplied)",
    )
    done: Optional[bool] = Field(None, description="Task status flag")


class TaskResponse(BaseModel):
    id: int
    title: str
    done: bool


# --- Endpoints ---


# Stage 1: Root & Health Check
@app.get("/", tags=["General"], summary="API Root metadata")
def read_root():
    return {
        "name": "Task API",
        "version": "2.0",
        "storage": "SQLite (tasks.db)",
        "endpoints": ["/tasks", "/tasks/{id}", "/health", "/docs"],
    }


@app.get("/health", tags=["General"], summary="Health check endpoint")
def health_check():
    return {"status": "ok"}


# Stage 1: Read Endpoints
@app.get(
    "/tasks",
    response_model=List[TaskResponse],
    tags=["Tasks"],
    summary="List all tasks",
)
def get_tasks(done: Optional[bool] = None, search: Optional[str] = None):
    query = "SELECT id, title, done FROM tasks WHERE 1=1"
    params = []

    if done is not None:
        query += " AND done = ?"
        params.append(1 if done else 0)

    if search:
        query += " AND title LIKE ?"
        params.append(f"%{search}%")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [
            {"id": row["id"], "title": row["title"], "done": bool(row["done"])}
            for row in rows
        ]


@app.get(
    "/tasks/{task_id}",
    response_model=TaskResponse,
    tags=["Tasks"],
    summary="Get single task by ID",
)
def get_task(task_id: int):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # Parameterized query protects against SQL injection
        cursor.execute(
            "SELECT id, title, done FROM tasks WHERE id = ?", (task_id,)
        )
        row = cursor.fetchone()

        if row is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found",
            )
        return {
            "id": row["id"],
            "title": row["title"],
            "done": bool(row["done"]),
        }


# Stage 2: Create Endpoint with SQL Insert & Validation
@app.post(
    "/tasks",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Tasks"],
    summary="Create new task",
)
def create_task(payload: TaskCreate):
    title = payload.title.strip()
    if not title:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Title cannot be empty or whitespace only",
        )

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO tasks (title, done) VALUES (?, ?)", (title, 0)
        )
        conn.commit()
        new_id = cursor.lastrowid

    return {"id": new_id, "title": title, "done": False}


# Stage 3: Update & Delete Endpoints with SQL
@app.put(
    "/tasks/{task_id}",
    response_model=TaskResponse,
    tags=["Tasks"],
    summary="Update an existing task",
)
def update_task(task_id: int, payload: TaskUpdate):
    if payload.title is None and payload.done is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Request body must contain 'title' or 'done'",
        )

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, title, done FROM tasks WHERE id = ?", (task_id,))
        existing = cursor.fetchone()

        if existing is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found",
            )

        new_title = existing["title"]
        new_done = existing["done"]

        if payload.title is not None:
            stripped = payload.title.strip()
            if not stripped:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Title cannot be empty",
                )
            new_title = stripped

        if payload.done is not None:
            new_done = 1 if payload.done else 0

        cursor.execute(
            "UPDATE tasks SET title = ?, done = ? WHERE id = ?",
            (new_title, new_done, task_id),
        )
        conn.commit()

    return {"id": task_id, "title": new_title, "done": bool(new_done)}


@app.delete(
    "/tasks/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Tasks"],
    summary="Delete a task",
)
def delete_task(task_id: int):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM tasks WHERE id = ?", (task_id,))
        existing = cursor.fetchone()

        if existing is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found",
            )

        cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()

    return None

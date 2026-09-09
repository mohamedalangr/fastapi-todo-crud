from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, List

app = FastAPI(
    title="Task API",
    version="1.0",
    description="A lightweight in-memory CRUD API for to-do task management."
)

# --- Pydantic Data Models ---

class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, description="Task title cannot be empty")

class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, description="Updated title (cannot be empty if supplied)")
    done: Optional[bool] = Field(None, description="Task status flag")

class TaskResponse(BaseModel):
    id: int
    title: str
    done: bool

# --- In-Memory Storage ---
# Note: Data lives in memory and resets on server restart (Mortality Experiment)
tasks_db: List[dict] = [
    {"id": 1, "title": "Review FlyRank backend brief", "done": True},
    {"id": 2, "title": "Build CRUD API with FastAPI", "done": False},
    {"id": 3, "title": "Inspect interactive Swagger docs", "done": False}
]

# Helper function to find a task by ID
def find_task_index(task_id: int):
    for index, task in enumerate(tasks_db):
        if task["id"] == task_id:
            return index
    return None

# --- Endpoints ---

# Stage 1: Root & Health Check
@app.get("/", tags=["General"], summary="API Root metadata")
def read_root():
    return {
        "name": "Task API",
        "version": "1.0",
        "endpoints": ["/tasks", "/tasks/{id}", "/health", "/docs"]
    }

@app.get("/health", tags=["General"], summary="Health check endpoint")
def health_check():
    return {"status": "ok"}

# Stage 2: Read Endpoints
@app.get("/tasks", response_model=List[TaskResponse], tags=["Tasks"], summary="List all tasks")
def get_tasks(done: Optional[bool] = None, search: Optional[str] = None):
    results = tasks_db
    if done is not None:
        results = [t for t in results if t["done"] == done]
    if search:
        results = [t for t in results if search.lower() in t["title"].lower()]
    return results

@app.get("/tasks/{task_id}", response_model=TaskResponse, tags=["Tasks"], summary="Get single task by ID")
def get_task(task_id: int):
    idx = find_task_index(task_id)
    if idx is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found"
        )
    return tasks_db[idx]

# Stage 3: Create Endpoint with Validation
@app.post("/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED, tags=["Tasks"], summary="Create new task")
def create_task(payload: TaskCreate):
    title = payload.title.strip()
    if not title:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Title cannot be empty or whitespace only"
        )
    next_id = max([t["id"] for t in tasks_db], default=0) + 1
    new_task = {
        "id": next_id,
        "title": title,
        "done": False
    }
    tasks_db.append(new_task)
    return new_task

# Stage 4: Update & Delete Endpoints
@app.put("/tasks/{task_id}", response_model=TaskResponse, tags=["Tasks"], summary="Update an existing task")
def update_task(task_id: int, payload: TaskUpdate):
    idx = find_task_index(task_id)
    if idx is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found"
        )
    if payload.title is None and payload.done is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Request body must contain 'title' or 'done'"
        )
    if payload.title is not None:
        title = payload.title.strip()
        if not title:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Title cannot be empty"
            )
        tasks_db[idx]["title"] = title
    if payload.done is not None:
        tasks_db[idx]["done"] = payload.done
    return tasks_db[idx]

@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Tasks"], summary="Delete a task")
def delete_task(task_id: int):
    idx = find_task_index(task_id)
    if idx is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found"
        )
    tasks_db.pop(idx)
    return None

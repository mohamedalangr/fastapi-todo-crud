import os
from contextlib import asynccontextmanager
from typing import List, Optional
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from repository import PostgresTaskRepository

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:dev@localhost:5432/tasks")
repo = PostgresTaskRepository(DATABASE_URL)

@asynccontextmanager
async def lifespan(app: FastAPI):
    repo.init_schema()
    yield

app = FastAPI(
    title="Task API (Containerized PostgreSQL)",
    version="3.0",
    description="Full CRUD API backed by a PostgreSQL container managed via Docker Compose.",
    lifespan=lifespan
)

class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, description="Task title cannot be empty")

class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1)
    done: Optional[bool] = Field(None)

class TaskResponse(BaseModel):
    id: int
    title: str
    done: bool

@app.get("/", tags=["General"])
def read_root():
    return {
        "name": "Task API",
        "version": "3.0",
        "storage": "PostgreSQL in Docker",
        "endpoints": ["/tasks", "/tasks/{id}", "/health", "/docs"]
    }

@app.get("/health", tags=["General"])
def health_check():
    return {"status": "ok", "db": "connected"}

@app.get("/tasks", response_model=List[TaskResponse], tags=["Tasks"])
def get_tasks(done: Optional[bool] = None, search: Optional[str] = None):
    return repo.list_all(done=done, search=search)

@app.get("/tasks/{task_id}", response_model=TaskResponse, tags=["Tasks"])
def get_task(task_id: int):
    task = repo.get_by_id(task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task

@app.post("/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED, tags=["Tasks"])
def create_task(payload: TaskCreate):
    title = payload.title.strip()
    if not title:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Title cannot be empty")
    return repo.create(title=title)

@app.put("/tasks/{task_id}", response_model=TaskResponse, tags=["Tasks"])
def update_task(task_id: int, payload: TaskUpdate):
    if payload.title is None and payload.done is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Provide title or done")
    if payload.title is not None and not payload.title.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Title cannot be empty")
    
    updated = repo.update(task_id, payload.title.strip() if payload.title else None, payload.done)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return updated

@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Tasks"])
def delete_task(task_id: int):
    success = repo.delete(task_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return None

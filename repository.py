import os
import time
from typing import List, Optional
import psycopg
from psycopg.rows import dict_row

class PostgresTaskRepository:
    def __init__(self, db_url: str):
        self.db_url = db_url

    def get_connection(self):
        # Allow retry on startup while container database initializes
        for _ in range(10):
            try:
                conn = psycopg.connect(self.db_url, row_factory=dict_row)
                return conn
            except psycopg.OperationalError:
                time.sleep(1)
        return psycopg.connect(self.db_url, row_factory=dict_row)

    def init_schema(self):
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                # Stage 1: Create tasks table if not exists
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS tasks (
                        id SERIAL PRIMARY KEY,
                        title TEXT NOT NULL,
                        done BOOLEAN NOT NULL DEFAULT FALSE
                    );
                """)
                
                # Check row count to seed only once on first run
                cur.execute("SELECT COUNT(*) AS count FROM tasks;")
                row = cur.fetchone()
                if row["count"] == 0:
                    seed_tasks = [
                        ("Review FlyRank backend brief", True),
                        ("Build CRUD API with FastAPI", False),
                        ("Containerize stack with Postgres and Docker", False)
                    ]
                    cur.executemany(
                        "INSERT INTO tasks (title, done) VALUES (%s, %s);",
                        seed_tasks
                    )
            conn.commit()

    def list_all(self, done: Optional[bool] = None, search: Optional[str] = None) -> List[dict]:
        query = "SELECT id, title, done FROM tasks WHERE 1=1"
        params = []
        if done is not None:
            query += " AND done = %s"
            params.append(done)
        if search:
            query += " AND title ILIKE %s"
            params.append(f"%{search}%")
        query += " ORDER BY id ASC;"

        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                return cur.fetchall()

    def get_by_id(self, task_id: int) -> Optional[dict]:
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id, title, done FROM tasks WHERE id = %s;", (task_id,))
                return cur.fetchone()

    def create(self, title: str) -> dict:
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO tasks (title, done) VALUES (%s, %s) RETURNING id, title, done;",
                    (title, False)
                )
                new_task = cur.fetchone()
            conn.commit()
            return new_task

    def update(self, task_id: int, title: Optional[str], done: Optional[bool]) -> Optional[dict]:
        existing = self.get_by_id(task_id)
        if not existing:
            return None

        new_title = title if title is not None else existing["title"]
        new_done = done if done is not None else existing["done"]

        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE tasks SET title = %s, done = %s WHERE id = %s RETURNING id, title, done;",
                    (new_title, new_done, task_id)
                )
                updated = cur.fetchone()
            conn.commit()
            return updated

    def delete(self, task_id: int) -> bool:
        existing = self.get_by_id(task_id)
        if not existing:
            return False

        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM tasks WHERE id = %s;", (task_id,))
            conn.commit()
            return True

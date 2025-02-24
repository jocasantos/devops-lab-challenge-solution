import uvicorn
import os
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import mysql.connector

# Load environment variables from .env file
load_dotenv()

# MySQL RDS Configuration
MYSQL_CONFIG = {
    "host": os.getenv("MYSQL_HOST"),         # Your MySQL host (RDS endpoint)
    "port": os.getenv("MYSQL_PORT", 3306),   # Default MySQL port is 3306
    "database": os.getenv("MYSQL_DB"),       # Your database name
    "user": os.getenv("MYSQL_USER"),         # Your MySQL username
    "password": os.getenv("MYSQL_PASSWORD"), # Your MySQL password
}

# Database Connection Helper
def get_connection():
    try:
        return mysql.connector.connect(**MYSQL_CONFIG)
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None

app = FastAPI()

# Configure CORSMiddleware to allow all origins (disable CORS for development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # This allows all origins (use '*' for development only)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define the Task model
class Task(BaseModel):
    title: str
    description: str

# Create a table for tasks (You can run this once outside of the app)
@app.on_event("startup")
def create_tasks_table():
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Tasks (
                ID int NOT NULL PRIMARY KEY AUTO_INCREMENT,
                Title varchar(255),
                Description TEXT
            );
        """)
        conn.commit()
        print("✅ Table `Tasks` is ready!")
    except Exception as e:
        print(f"❌ Error creating table: {e}")
    finally:
        if conn and conn.is_connected():
            conn.close()

# List all tasks
@app.get("/api/tasks")
def get_tasks():
    conn = get_connection()  # Open the connection
    if conn is None:
        return {"error": "Could not connect to the database."}

    tasks = []
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Tasks")
        for row in cursor.fetchall():
            task = {
                "ID": row[0],
                "Title": row[1],
                "Description": row[2]
            }
            tasks.append(task)
    except Exception as e:
        return {"error": str(e)}
    finally:
        if conn.is_connected():
            conn.close()  # Ensure connection is closed after use
    
    return tasks

# Retrieve a single task by ID
@app.get("/api/tasks/{task_id}")
def get_task(task_id: int):
    conn = get_connection()  # Open the connection
    if conn is None:
        return {"error": "Could not connect to the database."}

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Tasks WHERE ID = %s", (task_id,))
        row = cursor.fetchone()
        if row:
            task = {
                "ID": row[0],
                "Title": row[1],
                "Description": row[2]
            }
            return task
        return {"message": "Task not found"}
    except Exception as e:
        return {"error": str(e)}
    finally:
        if conn.is_connected():
            conn.close()  # Ensure connection is closed after use

# Create a new task
@app.post("/api/tasks")
def create_task(task: Task):
    conn = get_connection()  # Open the connection
    if conn is None:
        return {"error": "Could not connect to the database."}

    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO Tasks (Title, Description) VALUES (%s, %s)", (task.title, task.description))
        conn.commit()
    except Exception as e:
        return {"error": str(e)}
    finally:
        if conn.is_connected():
            conn.close()  # Ensure connection is closed after use
    
    return task

# Update an existing task by ID
@app.put("/tasks/{task_id}")
def update_task(task_id: int, updated_task: Task):
    conn = get_connection()  # Open the connection
    if conn is None:
        return {"error": "Could not connect to the database."}

    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE Tasks SET Title = %s, Description = %s WHERE ID = %s", 
                       (updated_task.title, updated_task.description, task_id))
        conn.commit()
        return {"message": "Task updated"}
    except Exception as e:
        return {"error": str(e)}
    finally:
        if conn.is_connected():
            conn.close()  # Ensure connection is closed after use

# Delete a task by ID
@app.delete("/api/tasks/{task_id}")
def delete_task(task_id: int):
    conn = get_connection()  # Open the connection
    if conn is None:
        return {"error": "Could not connect to the database."}

    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Tasks WHERE ID = %s", (task_id,))
        conn.commit()
        return {"message": "Task deleted"}
    except Exception as e:
        return {"error": str(e)}
    finally:
        if conn.is_connected():
            conn.close()  # Ensure connection is closed after use

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

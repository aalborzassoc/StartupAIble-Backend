import os
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from supabase import create_client, Client
from celery import Celery

# 1. Explicitly find the .env file in the same folder as this script
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

# 2. Get environment variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
REDIS_URL = os.getenv("REDIS_URL")

# Debug print to confirm they are loaded
print(f"--- DEBUG ---")
print(f"Supabase URL loaded: {bool(SUPABASE_URL)}")
print(f"Supabase Key loaded: {bool(SUPABASE_KEY)}")
print(f"Redis URL loaded: {bool(REDIS_URL)}")
print(f"-------------")

# 3. Initialize Supabase
if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Supabase URL and Key are required. Check your .env file.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# 4. Initialize Celery
celery_app = Celery("parsaice_tasks", broker=REDIS_URL, backend=REDIS_URL)

# 5. Initialize FastAPI
app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class ProjectCreate(BaseModel):
    name: str
    business_idea: str
    target_audience: str
    user_id: str

# Routes
@app.get("/")
def read_root():
    return {"message": "ParsAIce API is running!"}

@app.get("/api/projects")
def get_all_projects(user_id: str):
    # Only fetch projects where the user_id matches
    response = supabase.table("projects").select("id, name, status, created_at").eq("user_id", user_id).order("created_at", desc=True).execute()
    return response.data

@app.get("/api/projects/{project_id}")
def get_project(project_id: str):
    response = supabase.table("projects").select("*").eq("id", project_id).single().execute()
    return response.data

@app.post("/api/projects")
def create_project(project: ProjectCreate):
    # Create project in database with user_id
    db_response = supabase.table("projects").insert({
        "user_id": project.user_id,
        "name": project.name,
        "business_idea": project.business_idea,
        "target_audience": project.target_audience,
        "status": "generating"
    }).execute()
    
    project_id = db_response.data[0]["id"]
    
    # Queue the Celery task with user_id
    celery_app.send_task(
        "backend.worker.generate_landing_page_task",
        args=[project_id, project.business_idea, project.target_audience, project.user_id]
    )
    
    return {"project_id": project_id, "status": "generating"}
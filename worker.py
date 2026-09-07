import os
from pathlib import Path
from dotenv import load_dotenv
from celery import Celery
from supabase import create_client, Client
from backend.ai_router import run_ai_agent

# 1. Explicitly find the .env file
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

# 2. Get environment variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
REDIS_URL = os.getenv("REDIS_URL")

# 3. Initialize Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# 4. Initialize Celery
celery_app = Celery("parsaice_tasks", broker=REDIS_URL, backend=REDIS_URL)

@celery_app.task(bind=True, max_retries=3)
def generate_landing_page_task(self, project_id: str, business_idea: str, target_audience: str, user_id: str):
    try:
        print(f"Starting ParsAIce agents for project {project_id}...")
        
        # 1. PLANNER AGENT
        planner_prompt = f"Create a high-converting landing page structure for: {business_idea}. Target audience: {target_audience}."
        planner_result = run_ai_agent(planner_prompt, "Conversion Rate Optimization Expert")
        print("Planner finished.")
        
        # 2. CRITIC AGENT
        critic_prompt = f"Critique this plan for weaknesses and suggest 3 improvements: {planner_result['content']}"
        critic_result = run_ai_agent(critic_prompt, "Senior Product Critic")
        print("Critic finished.")
        
        # 3. BUILDER AGENT
        builder_prompt = f"Create a complete, production-ready HTML landing page based on this plan: {planner_result['content']}. Apply these improvements: {critic_result['content']}. IMPORTANT: Use standard HTML5 with Tailwind CSS via CDN (<script src='https://cdn.tailwindcss.com'></script>). Do NOT use React, JSX, or Next.js. Generate semantic HTML with sections for Hero, Features, Pricing, Testimonials, and Footer. Make it fully responsive and visually stunning. Output ONLY the raw HTML code, no markdown fences or explanations."
        builder_result = run_ai_agent(builder_prompt, "Senior Frontend Engineer")
        print("Builder finished.")
        
        # 4. Update Database
        supabase.table("projects").update({
            "status": "ready_for_review",
            "generated_code": builder_result["content"],
            "user_id": user_id
        }).eq("id", project_id).execute()
        
        print("Project saved to database!")
        return "Success"
        
    except Exception as exc:
        print(f"Task failed: {exc}")
        raise self.retry(exc=exc, countdown=30)
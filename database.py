import os
from pathlib import Path
from supabase import create_client, Client
from dotenv import load_dotenv

# Explicitly load .env from the backend directory
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

# Get environment variables
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

# Initialize Supabase client
supabase: Client = create_client(url, key)
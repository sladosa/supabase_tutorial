from dotenv import load_dotenv
load_dotenv()  # Učitaj varijable iz .env datoteke

import os

from supabase import create_client

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

supabase = create_client(url, key)

users_email: str ="sasasladoljev59@gmail.com"
users_password: str = "sasa1234"
user = supabase.auth.sign_up({ "email": users_email, "password": users_password })
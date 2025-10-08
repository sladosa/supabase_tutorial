from dotenv import load_dotenv
load_dotenv()  # Učitaj varijable iz .env datoteke

import os

from supabase import create_client

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

supabase = create_client(url, key)

#data = supabase.table("todos").select("id,name").execute()
data = supabase.table("todos").insert({"name":"Todo 3"}).execute()
#data = supabase.table("todos").update({"name": "Todo_2!"}).eq("id", 2).execute()
#data = supabase.table("todos").delete().eq("id", 2).execute()
#data = supabase.table("todos").select("*").execute()
#print(data)
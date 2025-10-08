import streamlit as st
from dotenv import load_dotenv
import os
from supabase import create_client
import json
import datetime
import sys
import time
import uuid

# Učitaj varijable iz .env datoteke
load_dotenv()

# Konekcija na Supabase
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase = create_client(url, key)

st.title('Event Entry - Supabase Edition')

# **GUMB ZA UGAŠAVANJE APLIKACIJE**
col1, col2 = st.columns([1, 4])
with col1:
    if st.button("🔴 Ugasi App", type="primary"):
        st.success("Aplikacija se gasi... Zatvorite tab ručno.")
        time.sleep(5)
        sys.exit(0)

# Funkcija za ispravak auto-increment sekvenci
def fix_sequences():
    """Automatski ispravi sve auto-increment sekvence u bazi"""
    try:
        # Lista tablica s auto-increment ID poljima
        tables = ['event', 'category', 'area']
        
        for table in tables:
            try:
                # Dohvati trenutni maksimalni ID
                max_id_result = supabase.rpc('get_max_id', {'table_name': table}).execute()
                if max_id_result.data:
                    max_id = max_id_result.data
                    # Postavi sekvencu na sljedeći broj
                    supabase.rpc('fix_sequence', {
                        'table_name': table, 
                        'new_val': max_id + 1
                    }).execute()
            except:
                # Ako RPC funkcije ne postoje, preskačemo
                continue
                
    except Exception as e:
        st.warning(f"Napomena: Nije moguće automatski ispraviti sekvence: {str(e)}")

# Pokušaj automatski ispraviti sekvence na početku
if 'sequences_fixed' not in st.session_state:
    fix_sequences()
    st.session_state.sequences_fixed = True

# Dodaj unique key za svaki session kako bi izbjegli duplikate
if 'session_id' not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())[:8]

try:
    # 1. Dohvati sve area
    areas_response = supabase.table("area").select("id, name").order("name").execute()
    areas = areas_response.data
    area_dict = {area['name']: area['id'] for area in areas}
    
    if not areas:
        st.error("Nema dostupnih područja u bazi.")
        st.stop()
    
    # 2. Drop-down za Area
    area_name = st.selectbox("Choose Area", list(area_dict.keys()), 
                            key=f"area_{st.session_state.session_id}")
    
    # 3. Dohvati kategorije za odabranu area
    categories_response = supabase.table("category").select("id, name").eq("area_id", area_dict[area_name]).order("name").execute()
    categories = categories_response.data
    cat_dict = {cat['name']: cat['id'] for cat in categories}
    
    if not categories:
        st.warning(f"Nema dostupnih kategorija za područje '{area_name}'.")
        st.stop()
    
    # 4. Drop-down za Category
    category_name = st.selectbox("Choose Category", list(cat_dict.keys()),
                                key=f"category_{st.session_state.session_id}")
    
    # 5. Unos komentara i dodatnog podatka
    comment = st.text_input("Comment", key=f"comment_{st.session_state.session_id}")
    json_str = st.text_input("Optional JSON Data (e.g. {\"duration\":45})",
                           key=f"json_{st.session_state.session_id}")
    
    # 6. Datum događaja
    occurred_at = st.date_input("Datum događaja", datetime.date.today(),
                               key=f"date_{st.session_state.session_id}")
    
    # 7. Submit gumb
    if st.button("Save Event", key=f"save_{st.session_state.session_id}"):
        try:
            # Pripremi JSON podatke
            json_data = None
            if json_str.strip():
                try:
                    json_data = json.loads(json_str)
                except json.JSONDecodeError:
                    st.error("Neispravni JSON format!")
                    st.stop()
            
            # Definiraj event_data BEZ ID polja
            event_data = {
                "category_id": cat_dict[category_name],
                "occurred_at": occurred_at.isoformat(),
            }
            
            # Dodaj ostala polja samo ako nisu prazna
            if comment and comment.strip():
                event_data["comment"] = comment.strip()
            
            if json_data is not None:
                event_data["data"] = json_data
            
            # Alternativni pristup - koristi upsert umjesto insert
            result = supabase.table("event").upsert(event_data, 
                                                   on_conflict="id").execute()
            
            if not result.data:
                # Ako upsert ne radi, pokušaj s običnim insertom
                result = supabase.table("event").insert(event_data).execute()
            
            if result.data and len(result.data) > 0:
                event_id = result.data[0]['id']
                st.success(f"Event uspješno spremljen s ID: {event_id}")
                
                # Prikaži spremljene podatke
                with st.expander("Spremljeni podaci", expanded=True):
                    st.json({
                        "ID": event_id,
                        "Area": area_name,
                        "Category": category_name,
                        "Comment": comment or "N/A",
                        "Date": occurred_at.isoformat(),
                        "Data": json_data or "N/A"
                    })
                
                # Generiraj novi session ID za sljedeći unos
                st.session_state.session_id = str(uuid.uuid4())[:8]
                
                # Prikaži gumb za ponovni unos
                if st.button("Unesi novi event"):
                    st.rerun()
                    
            else:
                st.error("Dogodila se greška pri spremanju - nema povratnih podataka.")
                
        except Exception as e:
            error_msg = str(e).lower()
            if "duplicate key" in error_msg or "violates unique constraint" in error_msg:
                st.error("Greška: Pokušaj duplikatnog unosa. Molimo pokušajte ponovno.")
                st.info("Savjet: Ako se greška ponavlja, kontaktirajte administratora za ispravak baze.")
            else:
                st.error(f"Greška pri spremanju: {str(e)}")
            
            # Debugging informacije
            with st.expander("Debugging informacije"):
                st.write(f"Event data: {event_data}")
                st.write(f"Session ID: {st.session_state.session_id}")
    
       # 9. Alat za ispravak sekvenci (za administratore)

except Exception as e:
    st.error(f"Greška pri povezivanju s bazom: {str(e)}")
    st.write("Provjeri jesu li SUPABASE_URL i SUPABASE_KEY pravilno postavljeni u .env datoteci.")
    
    # Dodaj savjete za rješavanje
    st.info("""
    **Mogući uzroci:**
    - Neispravne Supabase kredencijale u .env datoteci
    - Mrežni problemi
    - Problemi s auto-increment sekvencama u bazi
    
    **Za rješavanje sekvenci:**
    Pokreni sljedeći SQL u Supabase SQL editoru:
    ```
    SELECT setval(pg_get_serial_sequence('event', 'id'), COALESCE(MAX(id), 1)) FROM event;
    ```
    """)

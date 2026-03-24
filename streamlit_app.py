import streamlit as st
from groq import Groq
from supabase import create_client
import uuid

# --- 1. DATABASE & AI SETUP ---
SUPABASE_URL = "https://tehvjosqerimjsomzfrs.supabase.co"
SUPABASE_KEY = "sb_publishable_VxRDPe0E8-u3lMeyCsN7RA_ajjKQ_zb"
GROQ_KEY = "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"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
client = Groq(api_key=GROQ_KEY)

st.set_page_config(page_title="Permanent AI", layout="wide")

# --- 2. SESSION & SIDEBAR ---
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

with st.sidebar:
    st.title("📂 Saved Chats")
    
    if st.button("➕ New Chat", use_container_width=True):
        st.session_state.session_id = str(uuid.uuid4())
        st.rerun()

    st.divider()

    # --- UNDO BUTTON (The "Edit" Fix) ---
    if st.button("↩️ Undo Last Turn", use_container_width=True):
        try:
            # Fetch the two most recent messages for this chat
            res = supabase.table("chat_history").select("id").eq("session_id", st.session_state.session_id).order("created_at", desc=True).limit(2).execute()
            if res.data:
                ids_to_delete = [item['id'] for item in res.data]
                for record_id in ids_to_delete:
                    supabase.table("chat_history").delete().eq("id", record_id).execute()
                st.toast("Last turn deleted!")
                st.rerun()
        except:
            st.error("Nothing to undo.")

    st.divider()
    
    # Fetch list of unique chats from database
    try:
        res = supabase.table("chat_history").select("session_id").execute()
        if res.data:
            unique_sessions = sorted(list(set([item['session_id'] for item in res.data])))
            for s_id in unique_sessions:
                label = f"💬 {s_id[:8]}..."
                if s_id == st.session_state.session_id:
                    label = f"✨ {s_id[:8]} (Active)"
                if st.button(label, key=s_id, use_container_width=True):
                    st.session_state.session_id = s_id
                    st.rerun()
    except:
        st.write("Start typing to save!")

# --- 3. LOAD CHAT FROM DATABASE ---
st.title(f"🤖 Chat ID: {st.session_state.session_id[:8]}")

def load_messages(s_id):
    try:
        res = supabase.table("chat_history").select("*").eq("session_id", s_id).order("created_at").execute()
        return [{"role": r["role"], "content": r["content"]} for r in res.data]
    except:
        return []

messages = load_messages(st.session_state.session_id)

for m in messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# --- 4. CHAT & SAVE ---
if prompt := st.chat_input("Type here..."):
    # Save User Message to DB
    supabase.table("chat_history").insert({"session_id": st.session_state.session_id, "role": "user", "content": prompt}).execute()
    
    with st.chat_message("user"):
        st.markdown(prompt)

    # CRITICAL STABILITY FIX: 
    # Only send the last 6 messages to stay under the 12k Token Per Minute limit.
    # This keeps each 'request' light enough so you don't hit the 60s wait.
    memory_window = messages[-6:] if len(messages) > 6 else messages
    
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=memory_window + [{"role": "user", "content": prompt}]
        )
        ans = response.choices[0].message.content
        
        # Save AI Response to DB
        supabase.table("chat_history").insert({"session_id": st.session_state.session_id, "role": "assistant", "content": ans}).execute()
        
        with st.chat_message("assistant"):
            st.markdown(ans)
            
    except Exception as e:
        st.error("The 'minute' limit was hit. Wait 60s and type '.' to retry. If this keeps happening, click 'New Chat'.")

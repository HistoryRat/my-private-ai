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

    # --- UNDO BUTTON ---
    if st.button("↩️ Undo Last Turn", use_container_width=True):
        try:
            res = supabase.table("chat_history").select("id").eq("session_id", st.session_state.session_id).order("created_at", desc=True).limit(2).execute()
            if res.data:
                for record in res.data:
                    supabase.table("chat_history").delete().eq("id", record['id']).execute()
                st.toast("Last turn deleted!")
                st.rerun()
        except:
            st.error("Nothing to undo.")

    st.divider()
    
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

# We fetch ONLY the messages for the CURRENT session
def load_messages(s_id):
    try:
        res = supabase.table("chat_history").select("role, content").eq("session_id", s_id).order("created_at", desc=False).execute()
        return res.data if res.data else []
    except:
        return []

# Force a clean load
current_chat_history = load_messages(st.session_state.session_id)

for m in current_chat_history:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# --- 4. CHAT & SAVE ---
if prompt := st.chat_input("Type here..."):
    # 1. Show user message instantly
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Save User Message to DB
    supabase.table("chat_history").insert({"session_id": st.session_state.session_id, "role": "user", "content": prompt}).execute()
    
    # 3. Trim memory to the bone (Last 4 messages only)
    # This keeps the request size tiny
    short_memory = current_chat_history[-4:] if len(current_chat_history) > 4 else current_chat_history
    
    try:
        # 4. Get AI Response
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant", 
            messages=short_memory + [{"role": "user", "content": prompt}]
        )
        ans = response.choices[0].message.content
        
        # 5. Save AI Response to DB
        supabase.table("chat_history").insert({"session_id": st.session_state.session_id, "role": "assistant", "content": ans}).execute()
        
        # 6. Show AI response
        with st.chat_message("assistant"):
            st.markdown(ans)
            
    except Exception as e:
        st.error(f"Rate Limit? Something is up with Groq. Wait 30s. Error: {e}")

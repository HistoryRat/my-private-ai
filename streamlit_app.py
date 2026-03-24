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
    if st.button("➕ New Chat"):
        st.session_state.session_id = str(uuid.uuid4())
        st.rerun()
    
    # Fetch list of unique chats from database
    try:
        res = supabase.table("chat_history").select("session_id").execute()
        if res.data:
            unique_sessions = sorted(list(set([item['session_id'] for item in res.data])))
            for s_id in unique_sessions:
                if st.button(f"💬 {s_id[:8]}...", key=s_id):
                    st.session_state.session_id = s_id
                    st.rerun()
    except Exception as e:
        st.write("Start typing to save your first chat!")

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
    # Save User Message to DB immediately
    supabase.table("chat_history").insert({"session_id": st.session_state.session_id, "role": "user", "content": prompt}).execute()
    
    with st.chat_message("user"):
        st.markdown(prompt)

    # FIXED: Only send the last 10 messages to Groq to prevent RateLimitErrors
    # This keeps the 'weight' of the request low (under 12k tokens)
    memory_window = messages[-10:] if len(messages) > 10 else messages
    
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
        st.error("The 'minute' limit was hit. Please wait 60 seconds and type '.' to refresh.")

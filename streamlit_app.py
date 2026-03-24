import streamlit as st
from groq import Groq
from supabase import create_client
import uuid

# --- 1. DATABASE & AI SETUP ---
# Replace these with the keys from your Supabase dashboard
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
        unique_sessions = list(set([item['session_id'] for item in res.data]))
        for s_id in unique_sessions:
            if st.button(f"💬 {s_id[:8]}...", key=s_id):
                st.session_state.session_id = s_id
                st.rerun()
    except:
        st.write("First chat? Start typing to save!")

# --- 3. LOAD CHAT FROM DATABASE ---
st.title(f"🤖 Chat ID: {st.session_state.session_id[:8]}")

def load_messages(s_id):
    res = supabase.table("chat_history").select("*").eq("session_id", s_id).order("created_at").execute()
    return [{"role": r["role"], "content": r["content"]} for r in res.data]

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

    # Get AI Response
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages + [{"role": "user", "content": prompt}]
    )
    ans = response.choices[0].message.content
    
    # Save AI Response to DB
    supabase.table("chat_history").insert({"session_id": st.session_state.session_id, "role": "assistant", "content": ans}).execute()
    with st.chat_message("assistant"):
        st.markdown(ans)

import streamlit as st
from groq import Groq
import os
import json
from datetime import datetime

st.set_page_config(page_title="My Private AI", layout="wide")

# --- 1. SETUP THE BRAIN ---
client = Groq(api_key="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")

# --- 2. MULTI-CHAT STORAGE ---
# All chats will be stored in a folder called 'chats'
if not os.path.exists("chats"):
    os.makedirs("chats")

def get_chat_list():
    files = os.listdir("chats")
    return sorted([f.replace(".json", "") for f in files if f.endswith(".json")], reverse=True)

def load_chat(chat_id):
    path = f"chats/{chat_id}.json"
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return []

def save_chat(chat_id, messages):
    with open(f"chats/{chat_id}.json", "w") as f:
        json.dump(messages, f)

# --- 3. SIDEBAR NAVIGATION ---
with st.sidebar:
    st.title("📂 Conversations")
    if st.button("➕ New Chat", use_container_width=True):
        # Create a unique ID based on timestamp
        new_id = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        st.session_state.current_chat = new_id
        st.session_state.messages = []
        st.rerun()

    st.divider()
    
    # List existing chats
    chats = get_chat_list()
    for chat in chats:
        # Show the date/time as a button
        if st.button(f"💬 {chat}", key=chat, use_container_width=True):
            st.session_state.current_chat = chat
            st.session_state.messages = load_chat(chat)
            st.rerun()

# --- 4. MAIN CHAT AREA ---
if "current_chat" not in st.session_state:
    # Default to a new chat if none selected
    st.session_state.current_chat = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    st.session_state.messages = []

st.title(f"🤖 Chat: {st.session_state.current_chat}")

# Display current messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 5. INPUT LOGIC ---
if prompt := st.chat_input("Type something..."):
    # Add User Message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Get AI Response
    with st.chat_message("assistant"):
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
        )
        full_response = response.choices[0].message.content
        st.markdown(full_response)
    
    st.session_state.messages.append({"role": "assistant", "content": full_response})
    
    # SAVE to the specific file for this chat
    save_chat(st.session_state.current_chat, st.session_state.messages)

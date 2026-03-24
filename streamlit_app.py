import streamlit as st
from groq import Groq
import os

st.set_page_config(page_title="My Private AI", layout="centered")

# --- 1. SETUP THE BRAIN ---
client = Groq(api_key="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")

# --- 2. SETUP PERMANENT STORAGE ---
DB_FILE = "chat_history.txt"

def load_history():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            return [eval(line) for line in f.readlines()]
    return []

def save_message(role, content):
    with open(DB_FILE, "a") as f:
        f.write(str({"role": role, "content": content}) + "\n")

# --- 3. LOAD CHATS ---
if "messages" not in st.session_state:
    st.session_state.messages = load_history()

st.title("🤖 Private AI")

# Display the history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 4. CHAT LOGIC ---
if prompt := st.chat_input("What's up?"):
    # Save User Message
    st.session_state.messages.append({"role": "user", "content": prompt})
    save_message("user", prompt)
    with st.chat_message("user"):
        st.markdown(prompt)

    # Get & Save AI Response
    with st.chat_message("assistant"):
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
        )
        full_response = response.choices[0].message.content
        st.markdown(full_response)
    
    st.session_state.messages.append({"role": "assistant", "content": full_response})
    save_message("assistant", full_response)

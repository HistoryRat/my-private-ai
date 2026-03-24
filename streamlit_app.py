import streamlit as st
from groq import Groq
import os

# --- PAGE CONFIG ---
st.set_page_config(page_title="Personal AI", layout="centered")
st.title("🤖 Private AI (No Limits)")

# --- BRAIN (GROQ API) ---
# I put your key here so it works immediately.
client = Groq(api_key="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")

# --- MEMORY (HISTORY) ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display old messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- INPUT ---
if prompt := st.chat_input("Type here..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        # This tells Groq to think
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
        )
        msg = response.choices[0].message.content
        st.markdown(msg)
    
    st.session_state.messages.append({"role": "assistant", "content": msg})

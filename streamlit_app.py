import streamlit as st
from query import ask

st.set_page_config(page_title="RAG-Based SAP Assistant", layout="wide")

st.title("SAP RAG Assistant")

# Chat history storage
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display previous messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Input box
if prompt := st.chat_input("Ask about SAP tutorial..."):
    
    # Show user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Get response from your RAG system
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            answer = ask(prompt)
            st.markdown(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})

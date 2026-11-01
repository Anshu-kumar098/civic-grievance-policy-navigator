import sys
import os
import streamlit as st
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../problem_2_policy_rag')))

import requests
import uuid
from langchain_core.messages import HumanMessage, AIMessage
from backend_rag.ai_service_rag import chatbot, retrieve_all_threads, ingest_pdf

st.set_page_config(page_title="LangGraph Tool & RAG Chatbot", page_icon="🤖", layout="wide")

# 1. Initialize Thread ID in Session State
if "thread_id" not in st.session_state:
    st.session_state["thread_id"] = str(uuid.uuid4())

# 2. Sidebar Navigation & PDF Uploader
# 1. Custom Name Input in Sidebar for New Chats
st.sidebar.title("💬 Chat Sessions")
st.sidebar.markdown("### 🔑 API Key Configuration")
user_api_key = st.sidebar.text_input(
    "Enter your Gemini API Key (Optional)", 
    type="password",
    key="navigator_api_key",
    help="Leave blank to use the default demo API key."
)

# Flexible validation check
if user_api_key and user_api_key.strip():
    key_clean = user_api_key.strip()
    if key_clean.startswith("sk-"):
        st.sidebar.error("❌ Invalid Key! You entered an OpenAI key (`sk-...`). Please enter a Google Gemini key.")
    elif len(key_clean) < 25:
        st.sidebar.error("❌ Key seems too short. Please enter a valid API key.")
    else:
        st.sidebar.success("✅ Custom Gemini Key Loaded!")
        os.environ["GOOGLE_API_KEY"] = key_clean
# Allow user to type a friendly name before starting a new chat
new_chat_name = st.sidebar.text_input("New Chat Title:", placeholder="e.g., Leave Policy Review")
if st.sidebar.button("➕ Create Chat", type="primary"):
    if new_chat_name.strip():
        # Use user-provided friendly name as the thread_id
        st.session_state["thread_id"] = new_chat_name.strip()
        st.rerun()
    else:
        st.sidebar.warning("Please enter a valid chat name.")

st.sidebar.markdown("---")
st.sidebar.subheader("📄 Upload PDF for RAG")

uploaded_file = st.sidebar.file_uploader("Upload a PDF document", type=["pdf"])

if uploaded_file is not None:
    if st.session_state.get("last_uploaded_file") != uploaded_file.name:
        with st.spinner("Processing & indexing PDF..."):
            try:
                file_bytes = uploaded_file.getvalue()
                # Call backend ingestion function with the current thread_id
                result = ingest_pdf(file_bytes, thread_id=st.session_state["thread_id"])
                st.session_state["last_uploaded_file"] = uploaded_file.name
                st.sidebar.success(f"Indexed {result.get('chunks', 0)} chunks from {result.get('filename')}!")
            except Exception as e:
                st.sidebar.error(f"Ingestion failed: {e}")

st.sidebar.markdown("---")
st.sidebar.markdown("### Past Conversations")
if st.sidebar.button("🗑️ Clear All History", type="secondary"):
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../chatbot.db'))
    try:
        import sqlite3
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all existing tables in the database dynamically
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        # Drop or clear each table safely
        for table_name in tables:
            t = table_name[0]
            if t != 'sqlite_sequence':
                cursor.execute(f"DELETE FROM {t};")
                
        conn.commit()
        conn.close()
        
        st.sidebar.success("History cleared successfully!")
        st.session_state["thread_id"] = "Default_Chat"
        st.rerun()
    except Exception as e:
        st.sidebar.error(f"Error clearing history: {e}")
try:
    existing_threads = retrieve_all_threads()
except Exception:
    existing_threads = []

for tid in existing_threads:
    if st.sidebar.button(f"🧵 {tid[:12]}...", key=tid):
        st.session_state["thread_id"] = tid
        st.rerun()

# 3. Main Chat Interface
CONFIG = {"configurable": {"thread_id": st.session_state["thread_id"]}}

st.title("🤖 LangGraph Tool & RAG Assistant")
st.caption("Ask general questions, search the web, calculate math, or query your uploaded PDF!")

# Helper to extract clean plain text from messages and history blocks
def extract_text(content):
    if isinstance(content, list):
        text_accumulator = ""
        for block in content:
            if isinstance(block, dict) and "text" in block:
                text_accumulator += block["text"]
            elif isinstance(block, str):
                text_accumulator += block
        return text_accumulator
    return str(content)

# Load and render message history from SQLite checkpointer state
try:
    state_snapshot = chatbot.get_state(CONFIG)
    messages = state_snapshot.values.get("messages", []) if state_snapshot and state_snapshot.values else []
except Exception:
    messages = []

for msg in messages:
    if isinstance(msg, HumanMessage):
        with st.chat_message("user"):
            st.markdown(extract_text(msg.content))
    elif isinstance(msg, AIMessage) and msg.content:
        with st.chat_message("assistant"):
            st.markdown(extract_text(msg.content))

# 4. Handle User Input & Stream Response
user_input = st.chat_input("Type your message here...")

if user_input:
    # Display user message immediately
    with st.chat_message("user"):
        st.markdown(user_input)

    # Stream the assistant response cleanly from LangGraph backend
    with st.chat_message("assistant"):
        def stream_ai_response():
            for message_chunk, metadata in chatbot.stream(
                {"messages": [HumanMessage(content=user_input)]},
                config=CONFIG,
                stream_mode="messages"
            ):
                if isinstance(message_chunk, AIMessage) and message_chunk.content:
                    content = message_chunk.content
                    if isinstance(content, list):
                        for block in content:
                            if isinstance(block, dict) and "text" in block:
                                yield block["text"]
                            elif isinstance(block, str):
                                yield block
                    elif isinstance(content, str):
                        yield content

        st.write_stream(stream_ai_response())
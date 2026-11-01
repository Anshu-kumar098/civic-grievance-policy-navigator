import os
import sqlite3
import requests
import tempfile
from dotenv import load_dotenv
from typing import TypedDict, Annotated, Any, Dict, Optional
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.tools import tool
from langchain_community.document_loaders import PyPDFLoader
from duckduckgo_search import DDGS
from langchain_community.vectorstores import FAISS

# Force the database to live strictly inside backend_rag/
DB_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(DB_DIR, "chatbot.db")
memory = SqliteSaver.from_conn_string(DB_PATH)
load_dotenv()

# 1. LLM Setup
API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

if not API_KEY:
    raise ValueError("GEMINI_API_KEY is not set in environment variables.")

llm = ChatGoogleGenerativeAI(
    model=MODEL_NAME,
    google_api_key=API_KEY,
    temperature=0.3,
    max_retries=5  # Automatically retries on 503/server overload errors
)
_THREAD_RETRIEVERS: Dict[str, Any] = {}
_THREAD_METADATA: Dict[str, dict] = {}

_LAST_GLOBAL_RETRIEVER = None

def _get_retriever(thread_id: Optional[str]):
    """Fetch the retriever for a thread if available, with a global fallback."""
    global _LAST_GLOBAL_RETRIEVER
    if thread_id and thread_id in _THREAD_RETRIEVERS:
        return _THREAD_RETRIEVERS[thread_id]
    if _THREAD_RETRIEVERS:
        return list(_THREAD_RETRIEVERS.values())[-1]
    return _LAST_GLOBAL_RETRIEVER


def ingest_pdf(file_bytes: bytes, thread_id: str, filename: Optional[str] = None) -> dict:
    """
    Build a FAISS retriever for the uploaded PDF and store it for the thread.

    Returns a summary dict that can be surfaced in the UI.
    """
    if not file_bytes:
        raise ValueError("No bytes received for ingestion.")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
        temp_file.write(file_bytes)
        temp_path = temp_file.name

    try:
        loader = PyPDFLoader(temp_path)
        docs = loader.load()

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, chunk_overlap=200, separators=["\n\n", "\n", " ", ""]
        )
        chunks = splitter.split_documents(docs)
        # Load embedding model name from .env with a secure fallback
        EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL", "gemini-embedding-001")

        # Initialize Google Generative AI Embeddings
        embeddings = GoogleGenerativeAIEmbeddings(model=EMBEDDING_MODEL_NAME)

        vector_store = FAISS.from_documents(chunks, embeddings)
        retriever = vector_store.as_retriever(
            search_type="similarity", search_kwargs={"k": 4}
        )
        global _LAST_GLOBAL_RETRIEVER
        _THREAD_RETRIEVERS[str(thread_id)] = retriever
        _LAST_GLOBAL_RETRIEVER = retriever
        _THREAD_METADATA[str(thread_id)] = {
            "filename": filename or os.path.basename(temp_path),
            "documents": len(docs),
            "chunks": len(chunks),
        }

        return {
            "filename": filename or os.path.basename(temp_path),
            "documents": len(docs),
            "chunks": len(chunks),
        }
    finally:
        # The FAISS store keeps copies of the text, so the temp file is safe to remove.
        try:
            os.remove(temp_path)
        except OSError:
            pass
# 2. Tools Setup


@tool
def search_web(query: str) -> str:
    """Search the web for up-to-date information, news, resources, and website URLs.
    Use this when the user asks for links, URLs, documentation, or recent web content."""
    try:
        results = list(DDGS().text(query, max_results=4))
        if not results:
            return "No web results found."
        
        output = []
        for r in results:
            output.append(f"Title: {r['title']}\nURL: {r['href']}\nSnippet: {r['body']}\n")
        return "\n---\n".join(output)
    except Exception as e:
        return f"Search error: {str(e)}"
@tool
def rag_tool(query: str, thread_id: Optional[str] = None) -> dict:
    """
    Retrieve relevant information from the uploaded PDF for this chat thread.
    Always include the thread_id when calling this tool.
    """
    retriever = _get_retriever(thread_id)
    if retriever is None:
        return {
            "error": "No document indexed for this chat. Upload a PDF first.",
            "query": query,
        }

    result = retriever.invoke(query)
    context = [doc.page_content for doc in result]
    metadata = [doc.metadata for doc in result]

    return {
        "query": query,
        "context": context,
        "metadata": metadata,
        "source_file": _THREAD_METADATA.get(str(thread_id), {}).get("filename"),
    }    

# Register both tools
tools = [ search_web,rag_tool]
llm_with_tools = llm.bind_tools(tools)

# 3. State Definition
class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

# 4. Graph Nodes
def chat_node(state: ChatState):
    messages = state["messages"]
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}

tool_node = ToolNode(tools)

# 5. Checkpointer
conn = sqlite3.connect(database="chatbot.db", check_same_thread=False)
checkpointer = SqliteSaver(conn=conn)
# 6. Graph Construction
graph = StateGraph(ChatState)

# Step A: Add BOTH nodes first
graph.add_node("chat_node", chat_node)
graph.add_node("tools", tool_node)

# Step B: Define entry point and edges
graph.add_edge(START, "chat_node")

# Conditional edge from chat_node (routes to 'tools' if tool calls exist, or END otherwise)
graph.add_conditional_edges(
    "chat_node",
    tools_condition,
    {"tools": "tools", END: END}
)

# Return edge back from tools to chat_node
graph.add_edge("tools", "chat_node")

# Compile graph with the checkpointer
chatbot = graph.compile(checkpointer=checkpointer)
# 7. Helper
def retrieve_all_threads():
    all_threads = set()
    for checkpoint in checkpointer.list(None):
        all_threads.add(checkpoint.config["configurable"]["thread_id"])
    return list(all_threads)

if __name__ == "__main__":
    config = {"configurable": {"thread_id": "test-search-thread"}}
    out = chatbot.invoke({"messages": [HumanMessage(content="Find the official Python documentation URL")]}, config=config)
    print(out["messages"][-1].content)



 ###  [Live Prototype Link](https://civic-grievance-policy-navigator.onrender.com)
 Unified AI Assistant Workspace

A multi-module AI application combining a Multimodal Civic Grievance Reporter and an Agentic Policy Navigator RAG Assistant, powered by LangChain, LangGraph, Streamlit, Flask, and Google Gemini 3.8 Flash.

 Project Overview

This workspace provides a centralized, dual-application suite designed to process complex multimodal user inputs and domain-specific documents:

1.  Civic Grievance Reporter (Problem 1)

Multimodal Ingestion: Accepts images/documents, user description text.

Automated Processing: Analyzes public infrastructure complaints, auto-detects administrative authority levels, translates voice notes, and formats official administrative letters.

PDF Generation: Generates official complaint PDFs complete with formatted typography and embedded timestamp details via ReportLab.

Decoupled Backend: Communicates seamlessly through a Flask REST API backend (ai.service.py).

2. 💬 Policy Navigator RAG (Problem 2)

Agentic RAG Assistant: State-driven conversational engine built with LangGraph and SQLite checkpointing (SqliteSaver).

Document Search & Indexing: Ingests policy PDF documents, splits content using recursive text splitters, and creates FAISS vector indexes dynamically.

Web Research Integration: Integrates DuckDuckGo web search tools for real-time external knowledge retrieval when documents lack coverage.

Session & Thread Management: Allows creation, persistence, and navigation of multiple independent chat sessions directly from the sidebar.

 Tech Stack & Architecture

Frontend: Streamlit (Multi-page App Dashboard with custom CSS and instant navigation)

Backend Framework: Flask (REST API running on port 8000 for Grievance Redressal Pipeline)

AI Orchestration: LangChain, LangGraph, Google Gemini 2.5 Flash (ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings)

Vector Store & Indexing: FAISS, PyPDF Loader, Recursive Character Text Splitter

Database / Checkpointing: SQLite (chatbot.db for thread state persistence)

PDF Engine: ReportLab

Audio Processing: audio-recorder-streamlit

 Dynamic API Key Management & Real-time Validation

To prevent shared quota exhaustion during evaluator testing, both workspace modules feature real-time sidebar API key validation:

Flexible Gemini Key Support: Accepts standard Google Cloud and Google AI Studio API key formats (AIza..., AQ..., etc., minimum 25 characters).

Instant UI Feedback: Displays real-time sidebar indicators:

❌ Error State: Flags OpenAI keys (sk-...) or under-length inputs.

✅ Success State: Confirms valid custom key loading into request headers/environment variables.

ℹ️ Default State: Gracefully falls back to pre-configured .env demo keys when empty.

Header & Session Propagation:

Problem 1 (Flask): Transmits custom key via HTTP request headers (X-Gemini-Api-Key).

Problem 2 (LangGraph): Dynamically updates session environment (os.environ["GOOGLE_API_KEY"]).

 Quick Start & Local Setup

1. Prerequisites

Python 3.10+

git

2. Clone Repository

git clone https://github.com/Anshu-kumar098/civic-grievance-policy-navigator.git
cd civic-grievance-policy-navigator


3. Set Up Environment & Install Dependencies

Create and activate a virtual environment:

python -m venv venv

# On Windows (PowerShell):
.\venv\Scripts\Activate.ps1

# On macOS/Linux:
source venv/bin/activate


Install all required packages from requirements.txt:

pip install -r requirements.txt


4. Configure Environment Variables (Optional)

Create a .env file in your backend directories or root folder:

GOOGLE_API_KEY=your_default_gemini_api_key_here
GEMINI_MODEL=gemini-3.8-flash


💻 Running the Applications

Step 1: Launch Backend Service (Problem 1)

Open Terminal 1 and start the Flask server:

cd problem_1_civic_grievance/backend
python ai.service.py


Backend server will run at http://localhost:8000

Step 2: Launch Streamlit Workspace Dashboard

Open Terminal 2 and start the main dashboard:

streamlit run app.py


Streamlit frontend will launch automatically at http://localhost:8501

📂 Complete Project Structure

project/
├── app.py                            # Centralized Multi-App Dashboard Landing Page
├── .gitignore                        # Privacy filter (excludes .env & SQLite databases)
├── requirements.txt                  # Consolidated Python dependencies
├── README.md                         # Project documentation
├── pages/
│   ├── 1_Civic_Grievance.py          # UI for Problem 1: Civic Grievance Reporter
│   └── 2_Policy_Navigator.py         # UI for Problem 2: Policy Navigator RAG Assistant
├── problem_1_civic_grievance/
│   └── backend/
│       ├── ai.service.py              # Flask REST API for Multimodal Processing
│       └── .env                       # Backend environment configuration
└── problem_2_policy_rag/
    └── backend_rag/
        ├── ai_service_rag.py         # LangGraph Agent, SQLite Checkpoints & Vector Indexing
        └── .env                       # Backend environment configuration


🛡️ Privacy & Security

The repository is configured with strict .gitignore rules to safeguard environment keys and user session data:

Keeps private API key configs (.env) out of Git tracking.

Prevents binary SQLite databases (*.db, *.db-wal, *.db-shm) and Python bytecode (__pycache__/) from committing.

📜 License

Distributed under the MIT License.

import streamlit as st

# 1. Page Configuration
st.set_page_config(
    page_title="Unified AI Assistant Workspace",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Custom CSS for Professional UI Styling
st.markdown("""
<style>
    /* Metric / Container Styling */
    .card-container {
        border: 1px solid rgba(250, 250, 250, 0.1);
        border-radius: 12px;
        padding: 24px;
        background-color: rgba(255, 255, 255, 0.03);
        margin-bottom: 20px;
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .card-container:hover {
        border-color: #4AF6C3;
        transform: translateY(-2px);
    }
    .badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .badge-blue { background-color: rgba(66, 133, 244, 0.2); color: #4285F4; }
    .badge-green { background-color: rgba(52, 168, 83, 0.2); color: #34A853; }
</style>
""", unsafe_allow_html=True)

# 3. Header Section
st.title("⚡ Unified AI Assistant Dashboard")
st.caption("Centralized AI Portal • Select a specialized workspace module below or navigate using the sidebar.")

st.markdown("---")

# 4. Applications Grid Layout
col1, col2 = st.columns(2, gap="medium")

with col1:
    st.markdown('<span class="badge badge-blue">Multimodal Processing</span>', unsafe_allow_html=True)
    st.subheader("🏛️ Civic Grievance Reporter")
    st.write(
        "Analyze public infrastructure photos, document uploads, or voice recordings in local languages. "
        "Automatically generates legally persuasive, formatted official administrative complaint letters."
    )
    
    st.markdown("**Key Capabilities:**")
    st.markdown("• Multimodal visual & audio input analysis\n• Department auto-detection & routing\n• Exportable PDF complaint letters")
    
    if st.button("Open Grievance Reporter ➔", key="btn_p1", use_container_width=True, type="primary"):
        st.switch_page("pages/1_Civic_Grievance.py")

with col2:
    st.markdown('<span class="badge badge-green">LangGraph + RAG</span>', unsafe_allow_html=True)
    st.subheader("💬 Policy Navigator RAG")
    st.write(
        "Upload complex policy PDFs and interact with an agentic RAG assistant powered by LangGraph. "
        "Includes web search, persistent thread history, and interactive document indexing."
    )
    
    st.markdown("**Key Capabilities:**")
    st.markdown("• Vector indexing with SQLite checkpointing\n• Web-augmented research tool integration\n• Thread management & session restore")
    
    if st.button("Open Policy Navigator ➔", key="btn_p2", use_container_width=True, type="primary"):
        st.switch_page("pages/2_Policy_Navigator.py")

st.markdown("---")

# 5. Dashboard System Info Banner
with st.sidebar:
    st.markdown("### 📌 Workspace Quick Info")
    st.info(
        "**Navigation Tip:** Use the buttons above or the left sidebar menu to switch between workspace applications seamlessly."
    )
    st.markdown("---")
    st.caption("Engineered with Streamlit, LangGraph & Google Gemini API")
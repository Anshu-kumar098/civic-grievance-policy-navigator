import sys
import os

# Add problem 1 backend path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../problem_1_civic_grievance')))

# Place your Problem 1 UI components and backend logic here
import streamlit as st
import requests
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from audio_recorder_streamlit import audio_recorder

st.set_page_config(page_title="Civic Grievance Reporter", page_icon="🏙️", layout="centered")
# --- Sidebar API Key Input & Flexible Validation ---
st.sidebar.markdown("### 🔑 API Key Configuration")
user_api_key = st.sidebar.text_input(
    "Enter your Gemini API Key (Optional)", 
    type="password",
    key="civic_api_key",
    help="Leave blank to use default demo key."
)

is_key_valid = True
active_key = ""

if user_api_key and user_api_key.strip():
    key_clean = user_api_key.strip()
    if key_clean.startswith("sk-"):
        st.sidebar.error("❌ Invalid Key! You entered an OpenAI key (`sk-...`). Please enter a Google Gemini key.")
        is_key_valid = False
    elif len(key_clean) < 25:
        st.sidebar.error("❌ Key seems too short. Please enter a valid API key.")
        is_key_valid = False
    else:
        st.sidebar.success("✅ Custom Gemini Key Loaded!")
st.title("🏙️ Multimodal Civic Grievance Reporter")
st.write("Upload a photo/document or record a voice note describing the civic issue in your local language (e.g., Hindi or English).")

# Helper function to generate PDF bytes
def create_pdf(letter_text):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=54, leftMargin=54, topMargin=54, bottomMargin=54)
    story = []
    
    styles = getSampleStyleSheet()
    normal_style = ParagraphStyle(
        'OfficialLetter',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10.5,
        leading=15,
        textColor='black'
    )
    
    paragraphs = letter_text.split('\n')
    for p in paragraphs:
        if p.strip() == "":
            story.append(Spacer(1, 10))
        else:
            story.append(Paragraph(p.replace('\n', '<br/>'), normal_style))
            story.append(Spacer(1, 4))
            
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

# Input Form UI
with st.form(key="grievance_form"):
    authority_level = st.selectbox(
        "Select Authority / Jurisdiction Level:",
        [
            "Auto-Detect Authority (AI Recommended)",
            "Local Municipal Corporation / City Board",
            "State Government Department (PWD, Electricity, Water)",
            "Central / National Ministry (NHAI, Railways, Central Authority)"
        ]
    )

    user_text = st.text_area(
        "Citizen Notes & Location Details (Optional):",
        placeholder="e.g., Large waterlogged pothole near Central Market Crossing, MG Road, Ward 12."
    )

    uploaded_file = st.file_uploader(
        "Upload Image or Document Reference:",
        type=["jpg", "jpeg", "png", "webp", "pdf"]
    )

    st.markdown("---")
    st.markdown("🎙️ **Or Record Voice Note (Supports Hindi, English, etc.):**")
    audio_bytes = audio_recorder(text="Click to record voice note", recording_color="#e8b62c", neutral_color="#6aa36f", icon_size="2x")

    submit_button = st.form_submit_button("Generate Complaint Letter", type="primary")

# Processing logic after form submission
if submit_button:
    if not uploaded_file and not user_text.strip() and not audio_bytes:
        st.warning("⚠️ Please provide at least an image/document, text description, or voice recording.")
    else:
        with st.spinner("Analyzing upload, voice notes, and drafting official complaint letter..."):
            try:
                files = {}
                data = {
                    "text": user_text,
                    "authority_level": authority_level
                }

                if uploaded_file:
                    files["image"] = (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)

                if audio_bytes:
                    files["audio"] = ("voice_note.wav", audio_bytes, "audio/wav")

                if not is_key_valid:
                    st.error("❌ Cannot submit: Please fix or remove the invalid API key in the sidebar.")
                else:
                    backend_url = "http://localhost:8000/api/civic-grievance"
                
                # Prepare headers to send valid user API key
                headers = {}
                if active_key:
                    headers["Gemini-Api-Key"] = active_key
                
                response = requests.post(backend_url, data=data, files=files if files else None, headers=headers)
                if response.status_code == 200:
                    result = response.json()
                    complaint_letter = result.get("complaint_letter", "")

                    st.success("✅ Complaint Letter Generated Successfully!")

                    # 1. Preview on screen
                    st.markdown("### 📄 Formal Official Complaint Letter")
                    st.text_area("Official Text", value=complaint_letter, height=450)

                    # 2. PDF Download Button
                    pdf_bytes = create_pdf(complaint_letter)
                    st.download_button(
                        label="📥 Download Complaint Letter (PDF)",
                        data=pdf_bytes,
                        file_name="Civic_Grievance_Complaint_Letter.pdf",
                        mime="application/pdf"
                    )
                else:
                    try:
                        err_msg = response.json().get("error", "Unknown error occurred")
                    except Exception:
                        err_msg = response.text
                    st.error(f"❌ Backend Error: {err_msg}")

            except requests.exceptions.ConnectionError:
                st.error("❌ Could not connect to the backend server. Make sure your Flask backend (`ai.service.py`) is running on port 8000!")
            except Exception as e:
                st.error(f"❌ An error occurred: {str(e)}")
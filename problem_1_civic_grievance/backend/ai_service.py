import os
import base64
import streamlit as st
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

load_dotenv()


safety_settings = {
    "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_LOW_AND_ABOVE",
    "HARM_CATEGORY_HATE_SPEECH": "BLOCK_LOW_AND_ABOVE",
    "HARM_CATEGORY_HARASSMENT": "BLOCK_LOW_AND_ABOVE",
    "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_LOW_AND_ABOVE",
}

app = Flask(__name__)
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
@app.route("/api/civic-grievance", methods=["POST"])
def civic_grievance_reporter():
    try:
        # Extract API key from header sent by frontend
        request_api_key = request.headers.get("Gemini-Api-Key")
        api_key = request_api_key.strip() if request_api_key and request_api_key.strip() else os.getenv("GEMINI_API_KEY")

        if not api_key:
            return jsonify({"error": "No valid Gemini API key found"}), 400

        # Initialize LLM dynamically for this request
        llm = ChatGoogleGenerativeAI(
            model=os.getenv("GEMINI_MODEL", "gemini-3.8-flash"),
            google_api_key=api_key,
            temperature=0.3,
            safety_settings=safety_settings
        )
        # ... rest of your backend logic
        user_text = request.form.get("text", "")
        authority_level = request.form.get("authority_level", "Auto-Detect Authority (AI Recommended)")
        uploaded_file = request.files.get("image")  # Image or PDF


        if not uploaded_file and not user_text:
            return jsonify({"error": "Please provide an image/document, text description, or recorded voice note."}), 400

        prompt_instruction = (
            "You are an expert administrative legal assistant and civic grievance specialist.\n"
            "Your objective is to draft an authoritative, formal, and legally persuasive complaint letter based on the provided image/document, citizen notes.\n"
            "Note: If the voice recording is in Hindi or another language, accurately transcribe, translate, and integrate its details into the official English complaint letter.\n\n"
            
            "STEP 1: RELEVANCE & SAFETY CHECK\n"
            "Analyze all inputs carefully. Determine if they relate to a genuine public infrastructure/civic issue.\n"
            "IF THE CONTENT IS IRRELEVANT (e.g., personal selfies, pets, memes, indoors, or unrelated items):\n"
            "Note: Screenshots of road damage, potholes, cave-ins, or utility issues MUST be accepted even if they contain UI overlays or image borders.\n"
            "Respond ONLY with: ERROR_IRRELEVANT_CONTENT\n\n"
            
            "STEP 2: CRITICAL FORMATTING & TONE RULES:\n"
            "1. Plain Text Only: Do NOT use any Markdown formatting syntax (such as **, *, or #).\n"
            "2. Official Tone: Use formal administrative terminology.\n"
            "3. No Ambiguity: State facts, location details, visual evidence, and risks clearly.\n\n"

            "JURISDICTION & ROUTING LOGIC:\n"
            "- Local Municipal Corporation / City Board -> Municipal Commissioner / Executive Officer.\n"
            "- State Government Department (PWD, Electricity, Water) -> Engineer-in-Chief / Principal Secretary.\n"
            "- Central / National Ministry (NHAI, Railways) -> Regional Officer / Project Director.\n\n"

            "LETTER STRUCTURE TO FOLLOW STAGE-BY-STAGE:\n"
            "1. RECIPIENT HEADER: Complete designation, department, office, city, state, pin code placeholder.\n"
            "2. DATE: Format strictly as: Date: [Insert Submission Date]\n"
            "3. SUBJECT LINE: Starting with 'GRIEVANCE REGARDING:' highlighting location and hazard.\n"
            "4. SALUTATION: 'Respected Sir/Madam,'\n"
            "5. OPENING PARAGRAPH: State primary issue with exact geographical markers.\n"
            "6. EVIDENCE & OBSERVATIONS (Numbered List):\n"
            "   - Detail 1: Physical dimensions or visual evidence from image/text.\n"
            "   - Detail 2: Traffic or structural impact.\n"
            "   - Detail 3: Public safety hazard.\n"
            "7. SPECIFIC DEMANDS / ACTION ITEMS (Numbered List):\n"
            "   - Demand immediate temporary safety measures.\n"
            "   - Demand technical inspection within 48 hours.\n"
            "   - Demand permanent repair/resurfacing.\n"
            "8. CLOSING & SIGN-OFF: Professional closing with complainant placeholders.\n"
        )

        message_content = [
            prompt_instruction,
            f"Selected Authority Preference: {authority_level}",
            f"Citizen's Text Description: {user_text if user_text else 'None provided.'}"
        ]

        # Handle Image or PDF Attachment
        if uploaded_file:
            file_bytes = uploaded_file.read()
            encoded_file = base64.b64encode(file_bytes).decode("utf-8")
            mime_type = uploaded_file.mimetype or "application/octet-stream"
            message_content.append({
                "type": "image_url",
                "image_url": f"data:{mime_type};base64,{encoded_file}"
            })

        # Handle Audio Recording Attachment (supports wav/mp3 from audiorecorder)
        message = HumanMessage(content=message_content)
        response = llm.invoke([message])
        
        if isinstance(response.content, list):
            complaint_letter = "".join([item.get("text", "") if isinstance(item, dict) else str(item) for item in response.content]).strip()
        else:
            complaint_letter = str(response.content).strip()

        if "ERROR_IRRELEVANT_CONTENT" in complaint_letter:
            return jsonify({
                "error": "The uploaded files or  note do not appear to show a public civic issue. Please provide valid details."
            }), 400

        return jsonify({
            "status": "success",
            "model_used": MODEL_NAME,
            "complaint_letter": complaint_letter
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
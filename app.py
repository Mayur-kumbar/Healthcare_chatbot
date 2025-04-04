from flask import Flask, request, jsonify, render_template
import google.generativeai as genai
import os
from dotenv import load_dotenv
import threading

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'default-secret-key')

# Gemini API Configuration
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("Missing GEMINI_API_KEY. Please check your .env file.")

genai.configure(api_key=api_key)

# Preferred AI Models
preferred_models = [
    "gemini-2.5-pro-exp-03-25",
    "gemini-1.5-pro",
    "gemini-1.5-pro-latest",
    "gemini-1.5-flash-latest"
]

# Fetch Available Models
try:
    available_models = [model.name.replace("models/", "") for model in genai.list_models()]
    model_name = next((m for m in preferred_models if m in available_models), None)

    if not model_name:
        raise ValueError("No valid Gemini model found. Check API access.")

    print(f"✅ Using model: {model_name}")  # Debugging output

except Exception as e:
    raise RuntimeError(f"❌ Error fetching models: {e}")

# AI Agent Prompt Format
diagnosis_agent = """
You are a **Medical AI Assistant** specializing in preliminary diagnostics.  
Your role is to provide **accurate and relevant medical insights** based on symptoms and medical history.  

### **Instructions:**
- Analyze the provided **symptoms** and **medical history** carefully.
- Structure your response into **four key sections**:
    1. **Primary Diagnosis:** Identify the most likely condition.
    2. **Possible Causes:** Explain potential causes of the condition.
    3. **Recommended Tests:** Suggest medical tests that can confirm the diagnosis.
    4. **Treatment & Lifestyle Changes:** Provide guidance on medication, home remedies, and lifestyle improvements.

- Keep responses **clear, concise, and medically sound**.
- Use **bold** for important terms and format your response professionally.
"""

def get_ai_response(prompt):
    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt)
        return response.text.strip() if response and hasattr(response, "text") else "No information available."
    except Exception as e:
        return f"❌ Error: {str(e)}"

# Multi-Agent Diagnosis Function
def multi_agent_diagnosis(symptoms, history, results):
    """Runs AI agents simultaneously using threading."""

    prompts = {
        "Diagnosis": f"""
        {diagnosis_agent}
        **Patient Symptoms:** {symptoms}  
        **Medical History:** {history}  
        """,
        
        "Causes": f"""
        You are a **Medical Cause Identifier**.  
        Your task is to identify possible causes based on:  
        - **Symptoms:** {symptoms}  
        - **Medical History:** {history}  
        
        - List **the top 3-5 possible causes** in a **bullet-point format**.
        - Use **bold text** for key medical terms.
        """,

        "Tests": f"""
        You are a **Medical Test Advisor**.  
        Your role is to recommend **necessary diagnostic tests** based on:  
        - **Symptoms:** {symptoms}  
        - **Medical History:** {history}  
        
        Provide:  
        1. **Test Name** - **Purpose**  
        2. Only include tests **relevant to the case**.
        """,

        "Treatment": f"""
        You are a **Medical Treatment Expert**.  
        Based on the given symptoms and history, suggest:  
        - **Key Medications** (if applicable).  
        - **Home Remedies & Lifestyle Changes** (concise & actionable).  
        - **Precautions** to consider.  

        Keep your response **clear, structured, and evidence-based**.
        """
    }

    def process_agent(agent, prompt):
        results[agent] = get_ai_response(prompt)

    threads = []
    for agent, prompt in prompts.items():
        thread = threading.Thread(target=process_agent, args=(agent, prompt))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()  # Wait for all agents to complete

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/diagnose', methods=['POST'])
def diagnose():
    data = request.json
    symptoms = data.get("symptoms", "").strip()
    history = data.get("history", "").strip()

    if not symptoms:
        return jsonify({"error": "No symptoms provided"}), 400
    if not history:
        return jsonify({"error": "No medical history provided"}), 400

    results = {}
    multi_agent_diagnosis(symptoms, history, results)

    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True)

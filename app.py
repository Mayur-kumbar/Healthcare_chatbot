from flask import Flask, request, jsonify, render_template
import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'default-secret-key')

# Gemini API Client Configuration
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("Missing GEMINI_API_KEY. Please check your .env file.")

genai.configure(api_key=api_key)

# Check available models
try:
    available_models = [model.name.replace("models/", "") for model in genai.list_models()]
    print("Available Models from API:", available_models)  # Debugging output

    # Preferred models in order
    preferred_models = [
        "gemini-2.5-pro-exp-03-25",
        "gemini-1.5-pro",
        "gemini-1.5-pro-latest",
        "gemini-1.5-flash-latest"
    ]

    # Select the first available preferred model
    model_name = next((m for m in preferred_models if m in available_models), None)

    if not model_name:
        raise ValueError("No valid Gemini model found. Check API access.")

    print(f"✅ Using model: {model_name}")  # Debugging output

except Exception as e:
    raise RuntimeError(f"❌ Error fetching models: {e}")

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/diagnose', methods=['POST'])
def diagnose():
    data = request.json
    symptoms = data.get("symptoms", "").strip()
    
    if not symptoms:
        return jsonify({"error": "No symptoms provided"}), 400
    
    prompt = f"""
    A patient presents with the following symptoms: {symptoms}. 
    Provide a structured diagnosis including:
    1. Possible Diagnosis
    2. Possible Causes
    3. Recommended Tests
    4. Suggested Treatments
    Format the response with each section separated by a newline.
    """

    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt)

        diagnosis_text = response.text if response and hasattr(response, "text") else "No diagnosis available."

        # Splitting response into sections
        diagnosis_sections = diagnosis_text.split("\n\n")

        structured_response = {
            "diagnosis": diagnosis_sections[0] if len(diagnosis_sections) > 0 else "Not Available",
            "possible_causes": diagnosis_sections[1] if len(diagnosis_sections) > 1 else "Not Available",
            "recommended_tests": diagnosis_sections[2] if len(diagnosis_sections) > 2 else "Not Available",
            "treatment_suggestions": diagnosis_sections[3] if len(diagnosis_sections) > 3 else "Not Available"
        }

    except Exception as e:
        return jsonify({"error": f"Failed to generate diagnosis: {str(e)}"}), 500

    return jsonify(structured_response)

if __name__ == '__main__':
    app.run(debug=True)

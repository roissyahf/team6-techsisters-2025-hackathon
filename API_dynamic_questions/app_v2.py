from flask import Flask, request, jsonify
import os
from dotenv import load_dotenv
from openai import OpenAI
from typing import List, Literal, Dict, Any
from pydantic import BaseModel, Field, ValidationError

# === 1. Define Strict JSON Schema using Pydantic (for Validation and Generation) ===

class QuestionOptions(BaseModel):
    """Defines the four ordinal answer options."""
    A: str = Field(description="Highest alignment score (e.g., Always/Strongly Agree).")
    B: str = Field(description="Medium-High alignment score (e.g., Often/Agree).")
    C: str = Field(description="Medium-Low alignment score (e.g., Sometimes/Neutral).")
    D: str = Field(description="Lowest alignment score (e.g., Rarely/Disagree).")

class DynamicQuestion(BaseModel):
    """Defines the structure for a single assessment question."""
    competency: Literal["A", "B", "C", "D", "E", "F"] = Field(
        description="The primary skill category (A-F) this question assesses. Must be one of A, B, C, D, E, or F."
    )
    competency_name: str = Field(description="The full name of the competency.")
    question_text: str = Field(description="The non-technical, behavioral question text, personalized to the user's persona and focused on their area of interest.")
    options: QuestionOptions

class DynamicAssessment(BaseModel):
    """The root object containing the assessment result."""
    user_context_summary: str = Field(description="A 3-5 word summary of the user's synthesized persona and main interest.")
    questions: List[DynamicQuestion] = Field(
        min_items=6, 
        max_items=6, 
        description="A list containing exactly 6 dynamic questions, each targeting one competency."
    )

# --- 2. Initialize Flask App and Client ---
app = Flask(__name__)
load_dotenv()

# Check for API key and initialize client
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("Warning: OPENAI_API_KEY environment variable not set.")
    pass

client = OpenAI(api_key=api_key)

# --- 3. Step 1: Persona Builder (Refined for User JSON Structure) ---
def build_user_persona(user_profile_json: Dict[str, Any]) -> Dict[str, str]:
    """
    Extracts and cleans all relevant inputs from the nested user_profile JSON 
    into a simple dictionary, and identifies the Primary_Interest_Field for focus.
    """
    
    # Safely access the nested 'responses' dictionary
    responses = user_profile_json.get("user_profile", {}).get("responses", {})
    DEFAULT_ANSWER = "unknown or not provided" # Neutral default constant

    def safe_extract(key: str, default: str = DEFAULT_ANSWER) -> str:
        """Safely extracts the 'answer' from the nested response, cleaning up extra text."""
        # Access the dictionary responses[key]['answer']
        answer = responses.get(key, {}).get("answer", default)
        
        # Remove parenthetical descriptions and convert to lowercase for clean prompting
        return answer.split('(')[0].strip().lower()

    # Explicitly retrieve all 10 answers (Q1 to Q10) from the dynamic input
    situation = safe_extract("Q1_current_status")
    familiarity = safe_extract("Q2_tech_familiarity")
    tech_experience = safe_extract("Q3_tech_experience")
    
    # Q4 MUST be present and valid, based on the user's guarantee.
    interest_area = safe_extract("Q4_interest_area") 
    
    motivation = safe_extract("Q5_motivation")
    skill_level = safe_extract("Q6_skill_level")
    project_experience = safe_extract("Q7_project_experience")
    learning_preference = safe_extract("Q8_learning_preference")
    time_commitment = safe_extract("Q9_time_commitment")
    goal = safe_extract("Q10_goal")

    # Map raw user interest string to the 6 fixed categories (Code & Name)
    interest_map = {
        # System constants defining the mapping
        "building and coding software or apps": "A: Logical & Structured Thinking",
        "working with data and insights": "B: Data & Analytical Insight",
        "designing visuals or user experiences": "C: Creative & User-Centricity",
        "managing systems or ensuring cybersecurity": "D: Systemic & Risk Management",
        "coordinating teams or managing projects": "E: Communication & Stakeholder",
        "creating content or writing documentation": "F: Content & Language Fluency"
    }

    # --- VALIDATION: Ensure Q4 is valid and mapped ---
    if interest_area == DEFAULT_ANSWER:
        # This occurs if Q4_interest_area is completely missing from the input JSON
        raise ValueError("Q4_interest_area is missing from input, violating frontend data guarantee.")

    # Determine the primary category for the Focused Depth Assessment
    primary_category = interest_map.get(interest_area)
    
    if primary_category is None:
        # This occurs if the Q4 answer exists but doesn't match a recognized category key
        raise ValueError(f"Q4_interest_area answer '{interest_area}' is not a recognized mapping to an A-F category. Please check frontend mapping keys.")
    # --- END VALIDATION ---
    
    # Consolidate relevant data for the LLM prompt
    persona_data = {
        "Situation": situation,
        "Familiarity": familiarity,
        "Skill_Level": skill_level,
        "Time": time_commitment,
        "Goal": goal,
        "Primary_Interest_Field": primary_category,
        "Raw_Interest": interest_area
    }
    
    return persona_data

# --- 4. Step 2: LLM Dynamic Question Generator (with Schema) ---
def generate_dynamic_questions(persona_data: Dict[str, str], num_questions=6) -> Dict[str, Any]:
    """Generates dynamic questions using GPT-4o-mini with Pydantic schema."""
    
    # 4.1 Define the primary focus and competencies
    primary_focus = persona_data["Primary_Interest_Field"]
    
    # The categories must be included in the prompt for the LLM to choose from
    competency_map = {
        "A": "Logical & Structured Thinking (SW/Dev)",
        "B": "Data & Analytical Insight (Data/ML)",
        "C": "Creative & User-Centricity (Design/UX)",
        "D": "Systemic & Risk Management (Infra/Security)",
        "E": "Communication & Stakeholder (Management/PM)",
        "F": "Content & Language Fluency (Technical Writing/Digital)"
    }

    # 4.2 Define the System Prompt
    system_prompt = f"""
    You are an expert behavioral analyst and career coach. 
    You generate EXACTLY 6 close-ended, non-technical behavioral questions — one for each competency A-F.
    Your output MUST be a STRICT JSON object following the schema you were given:
    - DynamicAssessment
    - DynamicQuestion
    - QuestionOptions
    Do NOT include markdown, explanations, or commentary.
    Only produce raw JSON.
    
    =====================
    CRITICAL INSTRUCTIONS
    =====================
    1. Each question MUST be a realistic behavioral scenario describing an everyday situation 
    (e.g., organizing tasks, solving problems, making decisions, communicating).
    
    2. Each answer option A-D MUST be a short *behavioral micro-profile*:  
    • 1-2 natural-language sentences  
    • Describing HOW the user behaves  
    • Not generic labels like “Agree/Disagree”  
    • NOT abstract traits  
    • NOT one-word adjectives  
    • NOT generic Likert scale labels (Strongly Agree, Agree, etc.)
    
    3. The 4 answer options MUST reflect descending alignment with the competency:
    A = strong alignment  
    B = moderate-high alignment  
    C = moderate-low alignment  
    D = weak alignment
    
    4. Each option MUST function as meaningful semantic text for TF-IDF.  
    Options MUST describe actual actions, habits, or preferences.
    
    Example of GOOD option:
    “I usually break tasks into steps and track my progress with notes or digital tools.”
    
    Example of BAD option (NOT allowed):  
    “Agree”  
    “Strongly agree”  
    “Often”  
    “Sometimes I plan things”  
    “I am organized”
    
    5. Each question MUST correspond to exactly one competency:
    A - Logical & Structured Thinking  
    B - Data & Analytical Insight  
    C - Creative & User-Centricity  
    D - Systemic & Risk Management  
    E - Communication & Stakeholder  
    F - Content & Language Fluency
    
    6. The question for the user's declared primary interest ('{persona_data['Raw_Interest']}') must be more detailed and more probing than the others.
    
    7. Absolutely NO technical references (e.g., Python, SQL, UX design tools).
    
    8. Your final JSON MUST pass the provided Pydantic validation.
    Produce ONLY valid JSON.
    """

    system_prompt += """
    =====================
    STRICT JSON FORMAT
    =====================
    Your final output MUST be a valid JSON object matching this EXACT structure:
    {
        "user_context_summary": "string",
        "questions": [
            {
                "competency": "A|B|C|D|E|F",
                "competency_name": "string",
                "question_text": "string",
                "options": {
                    "A": "string",
                    "B": "string",
                    "C": "string",
                    "D": "string"
                    }
            }
                    ]
    }
    
    REMINDERS:
    - "user_context_summary" MUST always be present.
    - "user_context_summary" MUST be a 3-5 word micro-persona phrase.
    It must combine the user's experience level, motivation or mindset, 
    and primary interest field. It MUST feel descriptive and human, not generic.
    
    Examples of GOOD summaries:
    • “enthusiastic beginner exploring UX”
    • “motivated career shifter into data”
    • “detail-driven learner pursuing software”
    • “creative thinker exploring content tech”
    
    Examples NOT allowed:
    • “beginner”
    • “tech learner”
    • “student interested in design”
    • “job seeker”
    
    - Output MUST NOT contain markdown.
    - Output MUST NOT include commentary.
    - Produce ONLY valid JSON.

    Produce ONLY that JSON object as your final output.
    """

    # 4.3 Define the User Prompt
    user_prompt = f"""
    USER FULL PERSONA:
    - Current Status: {persona_data['Situation']}
    - Tech Familiarity: {persona_data['Familiarity']}
    - Skill Level: {persona_data['Skill_Level']}
    - Weekly Time Commitment: {persona_data['Time']}
    - Main Goal: {persona_data['Goal']}
    - Primary Interest Area: {persona_data['Raw_Interest']}
    - Primary Competency Focus: {persona_data['Primary_Interest_Field']}

    Generate the 6 required questions now.
    """
    
    # 4.4 Make the API Call
    try:
        response = client.responses.create(
            model="gpt-4o-mini",
            temperature=0.7, 
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )
        
        raw_content = response.output_text
        print("RAW MODEL OUTPUT:\n", raw_content)

        # 4.5 Runtime Schema Validation (Pydantic Model Validation)
        validated_data = DynamicAssessment.model_validate_json(raw_content)
        return validated_data.model_dump()
        
    except ValidationError as e:
        # Pydantic validation failed (LLM returned malformed JSON or invalid data types)
        print(f"Validation Error: {e.errors()}")
        return {"error": "LLM failed schema validation. Retrying or falling back recommended.", "detail": str(e.errors())}
    except Exception as e:
        # API errors, network issues, etc.
        return {"error": f"API or processing error: {e}"}

# --- 5. API Endpoint ---
@app.route("/", methods=["GET"])
def index():
    return "Model Service is Running", 200

@app.route("/generate_dynamic_questions", methods=["POST"])
def api_generate_dynamic_questions():
    if not api_key:
        return jsonify({"error": "OpenAI API Key not configured."}), 500
        
    try:
        user_base_json = request.get_json()
        if not user_base_json:
            return jsonify({"error": "Missing or invalid JSON payload"}), 400

        # Build persona data based on user's provided structure
        persona_data = build_user_persona(user_base_json)
        
        # Generate questions
        output = generate_dynamic_questions(persona_data)
        
        # Check for errors returned by the generator function itself
        if "error" in output:
            # Return LLM/Validation errors as 500
            return jsonify(output), 500

        # The output is already a validated dictionary
        return jsonify(output), 200

    except Exception as e:
        # Catch unexpected errors during request processing
        return jsonify({"error": str(e)}), 500
        
# --- 6. Run Flask App ---
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7070, debug=True)
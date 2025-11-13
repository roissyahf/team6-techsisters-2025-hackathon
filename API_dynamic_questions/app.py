from flask import Flask, request, jsonify
import json
import os
from dotenv import load_dotenv
from openai import OpenAI
from datetime import datetime

# === Initialize Flask App ===
app = Flask(__name__)

# === Initialize OpenAI Client ===
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# === Step 1: Persona Builder ===
def build_user_persona(user_profile_json):
    responses = user_profile_json["user_profile"]["responses"]

    # Extract fields safely
    situation = responses.get("Q1_current_status", {}).get("answer", "Unknown status")
    familiarity = responses.get("Q2_tech_familiarity", {}).get("answer", "Unknown familiarity")
    tech_experience = responses.get("Q3_tech_experience", {}).get("code") != "NO_EXP"
    interest_area = responses.get("Q4_interest_area", {}).get("answer", "general interest in tech")
    motivation = responses.get("Q5_motivation", {}).get("answer", "self-improvement")
    skill_level = responses.get("Q6_skill_level", {}).get("answer", "beginner level")
    project_experience = responses.get("Q7_project_experience", {}).get("code") != "NO_PROJ"
    learning_style = responses.get("Q8_learning_preference", {}).get("answer", "various online sources")
    time = responses.get("Q9_time_commitment", {}).get("answer", "a few hours")
    goal = responses.get("Q10_goal", {}).get("answer", "explore tech careers")

    persona = (
        f"The user is currently a {situation.lower()}, "
        f"with {familiarity.lower()} familiarity with technology. "
        f"They have {'no' if not tech_experience else 'some'} prior exposure to tech or related training. "
        f"Their main area of interest is {interest_area.lower()}. "
        f"They are mainly motivated by {motivation.lower()}, "
        f"and currently identify as {skill_level.lower()}. "
        f"They {'have not yet' if not project_experience else 'have previously'} completed any tech projects. "
        f"They prefer learning through {learning_style.lower()}, "
        f"can dedicate about {time.lower()} per week to learning, "
        f"and their current goal is to {goal.lower()}."
    )

    return persona.strip()


# === Step 2: LLM Dynamic Question Generator ===
def generate_dynamic_questions(user_base_json, num_questions=6):
    competencies = {
        "A": "Logical & Structured Thinking",
        "B": "Data & Analytical Insight",
        "C": "Creative & User-Centricity",
        "D": "Systemic & Risk Management",
        "E": "Communication & Stakeholder",
        "F": "Content & Language Fluency"
    }

    persona_summary = build_user_persona(user_base_json)

    system_prompt = f"""
    You are an expert AI career coach helping a beginner (non-technical person)
    discover their natural strengths to recommend a suitable tech career path.

    You must create {num_questions} personalized, **close-ended personality questions** — each probing one of
    the six universal competencies below:

    {json.dumps(competencies, indent=2)}

    Rules:
    - Tone: warm, simple, and non-technical.
    - Each question must relate naturally to the user's persona.
    - Each question probes ONE competency only.
    - Each question must have exactly 4 answer options (A-D) forming an ordinal scale.
    - The 4 options must represent strength or intensity of alignment with the question, for example:
        A. Strongly agree / Always
        B. Often / Agree
        C. Sometimes / Neutral
        D. Rarely / Disagree
    - The meaning of each option should allow consistent scoring:
        A → 1.0  
        B → 0.75  
        C → 0.5  
        D → 0.25
    - Avoid open-ended or subjective responses.
    - Output format (strict JSON):
      {{
        "user_context_summary": "short summary of persona",
        "questions": [
          {{
            "competency": "A",
            "competency_name": "Logical & Structured Thinking",
            "question_text": "...",
            "options": {{
              "A": "...",
              "B": "...",
              "C": "...",
              "D": "..."
            }}
          }}
        ]
      }}
    """

    user_prompt = f"""
    USER PERSONA SUMMARY:
    {persona_summary}

    Generate exactly {num_questions} close-ended questions that measure their natural alignment
    to the competencies A-F. Make it sound conversational, encouraging, and personal.
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.8,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        response_format={"type": "json_object"}
    )

    # Parse response safely
    try:
        content = response.choices[0].message.content
        result = json.loads(content)
        return result
    except Exception as e:
        return {
            "error": str(e),
            "raw_output": response.choices[0].message.content
        }


# === Step 3: API Endpoint ===
@app.route("/", methods=["GET"])
def index():
    return "Model Service is Running", 200

@app.route("/generate_dynamic_questions", methods=["POST"])
def api_generate_dynamic_questions():
    try:
        user_base_json = request.get_json()
        if not user_base_json:
            return jsonify({"error": "Missing or invalid JSON payload"}), 400

        output = generate_dynamic_questions(user_base_json)
        return jsonify(output), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# === Step 4: Run Flask App ===
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7070, debug=True)
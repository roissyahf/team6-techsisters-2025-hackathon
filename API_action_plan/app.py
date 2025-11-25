from flask import Flask, request, jsonify
from openai import OpenAI
from datetime import datetime
import os
from dotenv import load_dotenv
import json
from pydantic import BaseModel, Field
from typing import List, Optional

# Import processing helper
from services.processing import process_inputs, ActionPlanRequest

app = Flask(__name__)
load_dotenv()

# Check for API key and initialize client
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("Warning: OPENAI_API_KEY environment variable not set.")
client = OpenAI(api_key=api_key)
MODEL_NAME = "gpt-4o-mini"

# Test API connection
try:
    test_response = client.models.list()
    print("OpenAI API connection successful")
except Exception as e:
    print(f"OpenAI API connection failed: {e}")

# System prompt
SYSTEM_PROMPT = """
You are an expert career coach and curriculum designer who creates concise, optimistic, and realistic 6-month learning roadmaps for women entering tech.

Your responsibilities:
1. Always output STRICTLY VALID JSON matching the provided schema.
2. Tone MUST be encouraging, concise, supportive.
3. You MUST respect the user's weekly commitment hours and map learning pace accordingly.
4. You MUST use provided course_recommendations exactly as-is. Do NOT invent new metadata for them.
5. If course_recommendations is empty, you MAY propose generic, verifiable resource categories but clearly mark them as "suggested".
6. Milestones must sum to ~24 weeks (6 months), adjusted for user pace.
7. Include realistic project ideas aligned with the selected role.
8. Avoid hallucinations. If unsure, be conservative.

Temperature guidance: 0.8 for creativity but maintain structure.

You MUST generate output ONLY as JSON following this schema:
{
  "plan_meta": {
    "target_role": "string",
    "start_date": "YYYY-MM-DD or null",
    "estimated_completion": "string",
    "weekly_commitment": "string",
    "generated_at": "ISO timestamp"
  },
  "milestones": [
    {
      "milestone_number": 1,
      "title": "string",
      "duration_weeks": "integer",
      "description": "string",
      "learning_objectives": ["string"],
      "recommended_courses": [
        {
          "name": "string",
          "platform": "string or null",
          "duration_weeks": "integer or null",
          "skill_focus": ["string"],
          "difficulty": "string or null"
        }
      ],
      "projects": [
        {
          "project_name": "string",
          "description": "string",
          "skills_practiced": ["string"]
        }
      ]
    }
  ],
  "success_metrics": {
    "technical_skills": ["string"],
    "soft_skills": ["string"],
    "portfolio_items": ["string"]
  },
  "next_steps": ["string"]
}
"""


class RawInput(BaseModel):
    persona_json: dict = Field(...)
    selected_role_json: dict = Field(...)
    course_recommendations_json: Optional[List[dict]] = Field(default_factory=list)


def build_user_prompt(payload: ActionPlanRequest) -> str:
    persona_dict = payload.persona.model_dump()
    persona_summary = f"User is {persona_dict['Q1_current_status']}, familiarity: {persona_dict['Q2_tech_familiarity']}, motivation: {persona_dict['Q5_motivation']}, skill level: {persona_dict['Q6_skill_level']}, weekly commitment: {persona_dict['Q9_time_commitment']}."

    # Serialize role and courses
    role_json = payload.selected_role.model_dump_json() if payload.selected_role else "{}"
    courses_json = json.dumps([c.model_dump() for c in payload.course_recommendations], indent=2)
    constraints_json = payload.constraints.model_dump_json() if payload.constraints else "null"

    prompt = f"""
Generate a 6-month targeted action learning plan.

### USER PERSONA
{json.dumps(persona_dict, indent=2)}

Persona summary: {persona_summary}

### SELECTED ROLE
{role_json}

### COURSE RECOMMENDATIONS (use ONLY as given)
{courses_json}

### PARAMETERS
Weekly commitment: {payload.weekly_commitment}
Preferred learning format: {payload.preferred_learning_format}
Start date: {payload.start_date}
Constraints: {constraints_json}

Instructions:
1. Follow the JSON schema strictly.
2. Use course recommendations directly. If empty, add "suggested" placeholders.
3. Map weekly commitment to milestone pacing.
4. Produce 3-5 milestones, total ≈ 24 weeks.
5. Include realistic project ideas for the selected role.
6. Tone: encouraging.
7. Output JSON only, no explanations.
"""
    return prompt


def call_llm(system_prompt: str, user_prompt: str) -> str:
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            temperature=0.8,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )

        # Extract the response text
        llm_raw = response.choices[0].message.content

        if not llm_raw or llm_raw.strip() == "":
            print("LLM RESPONSE OBJECT:", response)
            raise ValueError("Empty LLM output")

        print("✓ LLM response received successfully")
        return llm_raw

    except Exception as e:
        print("✗ LLM ERROR:", e)
        print("Error type:", type(e).__name__)
        raise RuntimeError(f"LLM call failed: {e}")


@app.post("/generate-action-plan")
def generate_plan():
    try:
        data = request.json

        # Validate incoming raw blobs
        raw = RawInput(**data)
        persona_json = raw.persona_json
        selected_role_json = raw.selected_role_json
        course_recommendations_json = raw.course_recommendations_json

        # processing_input will validate, flatten and return ActionPlanRequest
        payload: ActionPlanRequest = process_inputs(persona_json, selected_role_json, course_recommendations_json)

        system_prompt = SYSTEM_PROMPT
        user_prompt = build_user_prompt(payload)

        print("→ Calling LLM...")
        llm_output = call_llm(system_prompt, user_prompt)

        print("→ Parsing LLM response...")
        # Clean potential markdown code blocks
        llm_output_clean = llm_output.strip()
        if llm_output_clean.startswith("```json"):
            llm_output_clean = llm_output_clean[7:]
        if llm_output_clean.startswith("```"):
            llm_output_clean = llm_output_clean[3:]
        if llm_output_clean.endswith("```"):
            llm_output_clean = llm_output_clean[:-3]
        llm_output_clean = llm_output_clean.strip()

        parsed = json.loads(llm_output_clean)
        parsed["plan_meta"]["generated_at"] = datetime.utcnow().isoformat()
        parsed["plan_meta"]["start_date"] = parsed["plan_meta"].get("start_date") or None
        parsed["plan_meta"]["weekly_commitment"] = payload.weekly_commitment

        print("✓ Action plan generated successfully")
        return jsonify(parsed), 200

    except json.JSONDecodeError as e:
        print("JSON Parse Error:", e)
        print("LLM Output was:", llm_output if 'llm_output' in locals() else "Not available")
        return jsonify({
            "error": f"JSON parsing failed: {str(e)}",
            "debug_note": "The LLM did not return valid JSON. Check the raw output above in server logs."
        }), 400
    except Exception as e:
        print("✗ General Error:", e)
        print("Error type:", type(e).__name__)
        return jsonify({
            "error": str(e),
            "debug_note": "Ensure the LLM returned valid JSON. Check OPENAI_API_KEY and network connectivity."
        }), 400


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9000, debug=True)
import openai
import json
from dotenv import load_dotenv
import os

# Initialize client
load_dotenv()
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# Parse the base questions response to get user persona
def build_user_persona(user_profile_json):
    """
    Build a short natural-language summary (persona) from user's base question responses.
    This will be passed to the LLM to generate dynamic questions.
    """
    responses = user_profile_json["user_profile"]["responses"]

    # Extract fields safely
    situation = responses["Q1_current_status"]["answer"]
    familiarity = responses["Q2_tech_familiarity"]["answer"]
    tech_experience = responses["Q3_tech_experience"]["code"] != "NO_EXP"
    interest_area = responses["Q4_interest_area"]["answer"]
    motivation = responses["Q5_motivation"]["answer"]
    skill_level = responses["Q6_skill_level"]["answer"]
    project_experience = responses["Q7_project_experience"]["code"] != "NO_PROJ"
    learning_style = responses["Q8_learning_preference"]["answer"]
    time = responses["Q9_time_commitment"]["answer"]
    goal = responses["Q10_goal"]["answer"]

    # Construct persona summary
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

    # Shorten or clean style
    persona = persona.replace(" .", ".").replace("  ", " ")

    return persona



# Main function to generate the dynamic questions from Open AI LLM
def generate_dynamic_questions(user_base_answers, num_questions=6):
    """
    Generate 4-6 personalized, close-ended personality based assessment questions for tech-role discovery to measure one competency (A-F) at a time.
    
    Args:
        user_base_answers (dict): User responses to the 10 base questions.
        num_questions (int): Number of questions to generate (4-6 recommended).
        
    Returns:
        list[dict]: List of questions, each with options and mapped competency.
    """

    # Prepare user context summary for the LLM
    user_context = json.dumps(user_base_answers, ensure_ascii=False, indent=2)

    # Define the competency framework
    competencies = {
        "A": "Logical & Structured Thinking",
        "B": "Data & Analytical Insight",
        "C": "Creative & User-Centricity",
        "D": "Systemic & Risk Management",
        "E": "Communication & Stakeholder",
        "F": "Content & Language Fluency"
    }

    system_prompt = f"""
    You are an expert AI career coach helping a beginner (non-technical person)
    discover their natural strengths to recommend a suitable tech career path.

    You will receive the user's base answers and must create {num_questions} 
    personalized, **close-ended personality questions** — each probing one of
    the six universal competencies below:

    {json.dumps(competencies, indent=2)}

    Rules:
    - The tone should be warm, encouraging, and non-technical.
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
    - Avoid free-text, open-ended, or qualitative answers.
    - Output should be strictly in JSON list format:
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
    Here are the user's base answers:
    {user_context}

    Based on these, generate exactly {num_questions} close-ended questions that measure their natural alignment
    to the competencies A-F. Try to balance coverage — one per category. Make it sound conversational, encouraging, and personal.
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.8,
        response_format={"type": "json_object"}
    )

    # Parse JSON from LLM response safely
    try:
        content = response.choices[0].message.content
        questions = json.loads(content)
        return questions
    except Exception as e:
        print("Failed to parse LLM output:", e)
        print("Raw output:", response.choices[0].message.content)
        return []
    



# Call the function
user_profile_json_path = "data/sample_base_questions_response.json"
try:
    with open(user_profile_json_path, 'r') as file:
        user_profile_json = json.load(file)
    print("JSON data successfully loaded:")
    print(user_profile_json)
    print(f"Type of loaded data: {type(user_profile_json)}")
except FileNotFoundError:
    print(f"Error: The file '{user_profile_json_path}' was not found.")
except json.JSONDecodeError:
    print(f"Error: Could not decode JSON from '{user_profile_json_path}'. Check file format.")
except Exception as e:
    print(f"An unexpected error occurred: {e}")

user_base_answers = build_user_persona(user_profile_json)
print(user_base_answers)
questions = generate_dynamic_questions(user_base_answers, num_questions=6)
print(json.dumps(questions, indent=2))
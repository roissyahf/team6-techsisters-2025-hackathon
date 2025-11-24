import json

def load_base_responses(base_json):
    """
    Extracts the 'responses' block from the base questions JSON.
    Supports the exact structure in sample.json, sample_1.json, sample_2.json etc.
    """
    return base_json["user_profile"]["responses"]


def map_base_to_features(responses):
    """
    Convert base questions answers into numerical feature scores (0–5 scale).
    Only uses the information from sample_X.json files you uploaded.
    """

    features = {
        "interest_tech": 0,
        "experience_level": 0,
        "learning_commitment": 0,
        "motivation_career": 0,
        "motivation_flexibility": 0,
        "motivation_money": 0,
        "preference_data": 0,
        "preference_building": 0,
        "preference_design": 0,
        "preference_management": 0,
        "preference_content": 0
    }

    # Q1 - current status
    q1 = responses["Q1_current_status"]["answer"]
    if q1 in ["Working Professional (Tech)", "Career Switcher"]:
        features["experience_level"] += 3
    elif q1 in ["Working Professional (Non-Tech)", "Student"]:
        features["experience_level"] += 2
    elif q1 == "Job Seeker":
        features["experience_level"] += 1

    # Q2 - tech familiarity
    q2 = responses["Q2_tech_familiarity"]["answer"]
    mapping_q2 = {
        "Not at all": 0,
        "Somewhat familiar": 2,
        "Comfortable": 3,
        "Very comfortable": 4
    }
    features["experience_level"] += mapping_q2.get(q2, 0)

    # Q3 - previous tech experience
    q3 = responses["Q3_tech_experience"]["answer"]
    if q3 == "Yes":
        features["experience_level"] += 2

    # Q4 - interest area
    q4 = responses["Q4_interest_area"]["answer"].lower()
    if "data" in q4:
        features["preference_data"] = 4
    if "coding" in q4 or "software" in q4 or "building" in q4:
        features["preference_building"] = 4
    if "design" in q4 or "ui" in q4 or "ux" in q4:
        features["preference_design"] = 4
    if "managing" in q4 or "project" in q4:
        features["preference_management"] = 4
    if "content" in q4 or "writing" in q4:
        features["preference_content"] = 4

    # Q5 - motivation
    q5 = responses["Q5_motivation"]["answer"]
    if "Career advancement" in q5:
        features["motivation_career"] = 4
    if "Flexibility / Remote work" in q5:
        features["motivation_flexibility"] = 4
    if "Financial growth" in q5:
        features["motivation_money"] = 4
    if "Impact" in q5 or "Innovation" in q5 or "Curiosity" in q5:
        features["motivation_career"] = max(3, features["motivation_career"])

    # Q9 - time commitment
    q9 = responses["Q9_time_commitment"]["answer"]
    if "Less" in q9:
        features["learning_commitment"] = 1
    elif "3-6" in q9 or "3–6" in q9:
        features["learning_commitment"] = 3
    elif "7-10" in q9:
        features["learning_commitment"] = 4
    elif "10" in q9:
        features["learning_commitment"] = 5

    # Clip values to range [0, 5]
    for key in features:
        features[key] = float(min(5, max(0, features[key])))

    return features


def map_technical_to_skills(technical_answers):
    """
    Convert your 5 technical questions into numeric skill values.
    technical_answers example:
    {
      "T1_programming": 4,
      "T2_problem_solving": 3,
      "T3_debugging": 2,
      ...
    }
    """
    skills = {
        "programming": 0,
        "problem_solving": 0,
        "debugging": 0,
        "system_understanding": 0,
        "tools_familiarity": 0
    }

    for qid, value in technical_answers.items():
        if qid.startswith("T") and "_" in qid:
            skill_key = qid.split("_", 1)[1]
            skills[skill_key] = float(value)

    return skills


def build_user_scores(base_json, technical_answers):
    """
    MAIN FUNCTION:
    base_json + technical_answers → unified user_scores dictionary.
    """
    responses = load_base_responses(base_json)
    base_features = map_base_to_features(responses)
    tech_skills = map_technical_to_skills(technical_answers)

    user_scores = {}
    user_scores.update(base_features)
    user_scores.update(tech_skills)

    return user_scores

import json
import numpy as np
import pickle
from typing import Dict, Any, List, Tuple
from pathlib import Path

# --- Configuration & Path Setup ---
BASE_DIR = Path(__file__).resolve().parents[2]
STATIC_DATA_PATH = BASE_DIR / "static_data"
PICKLE_PATH = BASE_DIR / "pickle_file"

print("BASE_DIR:", BASE_DIR)
print("STATIC_DATA_PATH:", STATIC_DATA_PATH)
print("PICKLE_PATH:", PICKLE_PATH)

# --- 1. Singleton Model and Data Loading (Runs ONLY ONCE on import) ---
try:
    with open(STATIC_DATA_PATH / "roles.json", 'r') as f:
        ROLES = json.load(f)
    with open(STATIC_DATA_PATH / "constraints.json", 'r') as f:
        CONSTRAINTS = json.load(f)
    
    VECTORIZER = pickle.load(open(PICKLE_PATH / "tfidf.pkl", "rb"))
    ROLE_IDS, ROLE_TFIDF_MATRIX = pickle.load(open(PICKLE_PATH / "role_tfidf_matrix.pkl", "rb"))
    
    # Static data for hybrid scoring weight
    WEIGHT_WSM = 0.6
    WEIGHT_TFIDF = 0.4
    
    print("✅ Recommender Engine: All models and static data loaded successfully.")

except Exception as e:
    print(f"FATAL ERROR: Could not load required model assets. {e}")
    raise RuntimeError("Recommender Engine initialization failed.")


# =====================================================================
# --- 2. Processing Helper Functions (Data Transformation) ---
# Renamed to start with _ to signify internal use only
# =====================================================================

def _build_pesona_flags(data: Dict[str, Any]) -> Dict[str, bool]:
    """Calculates persona flags based on base questions response answers."""
    responses = data.get('user_profile', {}).get('responses', {})
    q6_answer = responses.get('Q6_skill_level', {}).get('answer', '')
    is_beginner = q6_answer == "Beginner (I have little or no practical experience)"
    q9_answer = responses.get('Q9_time_commitment', {}).get('answer', '')
    is_low_time = q9_answer == "Less than 3 hours"
    q1_answer = responses.get('Q1_current_status', {}).get('answer', '')
    is_career_break = q1_answer == "Career Switcher"
    q5_answer = responses.get('Q5_motivation', {}).get('answer', '')
    is_remote_only = q5_answer == "Flexibility / Remote work"
    return {
        "beginner": is_beginner,
        "low_time": is_low_time,
        "remote_only": is_remote_only,
        "career_break": is_career_break
    }

def _build_user_persona_summary(user_profile_json: Dict[str, Any]) -> str:
    """Use base Q1, Q4, Q6, Q9 to Build user persona summary."""
    responses = user_profile_json.get("user_profile", {}).get("responses", {})
    situation = responses.get("Q1_current_status", {}).get("answer", "Unknown status")
    interest_area = responses.get("Q4_interest_area", {}).get("answer", "general interest in tech")
    skill_level = responses.get("Q6_skill_level", {}).get("answer", "beginner level")
    time = responses.get("Q9_time_commitment", {}).get("answer", "a few hours")
    persona_summary = (
        f"The user is currently a {situation.lower()}, "
        f"interested in {interest_area.lower()}, "
        f"identifying as {skill_level.lower()}, "
        f"and can dedicate about {time.lower()} per week to learning."
    )
    return persona_summary.strip()

def _simplify_response_structure(data: Dict[str, Any]) -> Dict[str, Any]:
    """Transforms the dynamic answers JSON into a simplified structure."""
    raw_responses: List[Dict[str, Any]] = data.get("user_profile", {}).get("responses", [])
    simplified_answers = []
    for resp in raw_responses:
        competency = resp["competency"]
        answer = resp["selected_answer"]
        simplified_answers.append({
            "competency": competency,
            "selected_option": answer["option_key"],
            "option_text": answer["answer_text"] 
        })
    return {"dynamic_answers": simplified_answers}


def _build_dynamic_text(persona_summary: str, simplified_data: Dict[str, Any]) -> str:
    """Concatenates a persona summary with all chosen option_texts."""
    answer_texts = [
        str(a["option_text"]).strip() 
        for a in simplified_data.get("dynamic_answers", []) 
        if "option_text" in a and str(a["option_text"]).strip()
    ]
    cleaned_texts = [t.rstrip('.').rstrip(' ').strip() for t in answer_texts]
    joined_answers = ". ".join(cleaned_texts)
    persona_part = persona_summary.rstrip(".").strip() + "."
    if joined_answers:
        final_document = f"{persona_part} {joined_answers}."
    else:
        final_document = persona_part
    return final_document.strip()

def _mapping_competency_scores(data: Dict[str, Any]) -> Tuple[float, ...]:
    """Directly converts dynamic competency answers to the ordered aptitude vector."""
    responses = data.get('user_profile', {}).get('responses', {})
    option_weights = {'A': 1.0, 'B': 0.75, 'C': 0.5, 'D': 0.25}
    COMPETENCIES = ['A', 'B', 'C', 'D', 'E', 'F']
    raw_scores: Dict[str, float] = {comp: 0.0 for comp in COMPETENCIES}
    
    for r in responses:
        comp = r.get('competency')
        opt = r.get('selected_answer', {}).get('option_key') 
        weight = option_weights.get(opt, 0.0) 
        if comp in raw_scores:
            raw_scores[comp] = weight

    return tuple(raw_scores[comp] for comp in COMPETENCIES)


# =====================================================================
# --- 3. Modeling Helper Functions (Inference) ---
# =====================================================================

def _compute_wsm_score(user_vector, role_weights):
    """Calculates Weighted Scoring Model score."""
    w = np.array([
        role_weights["A_logic"],
        role_weights["B_data"],
        role_weights["C_creative"],
        role_weights["D_communication"],
        role_weights["E_empowerment"],
        role_weights["F_execution"],
    ])
    u = np.array(user_vector)
    return float(np.dot(u, w) / (np.linalg.norm(u) * np.linalg.norm(w) + 1e-9))

def _apply_constraints(base_persona, role):
    """Multiplies score based on user persona flags and role tags (Penalty/Bonus)."""
    factor = 1.0
    for key in base_persona:
        if key not in CONSTRAINTS:
            continue
        rule = CONSTRAINTS[key]
        role_value = role["tags"].get(rule.get("tag_key", "skill_level"))
        if "penalty" in rule and role_value in rule["applies_to"]:
            factor *= rule["penalty"]
        if "bonus" in rule and role_value in rule["applies_to"]:
            factor *= rule["bonus"]
    return factor

def _compute_similarity(user_text):
    """Calculates TF-IDF Cosine Similarity."""
    user_vec = VECTORIZER.transform([user_text])
    sims = (ROLE_TFIDF_MATRIX @ user_vec.T).toarray().flatten()
    return sims

# =====================================================================
# --- 4. Main Public Entry Point ---
# =====================================================================

def get_recommendations(base_persona_data: Dict[str, Any], dynamic_questions_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Main entry point for the API. Processes raw data and generates recommendations.
    
    Args:
        base_persona_data: JSON data for base questions (Q1, Q4, Q6, Q9).
        dynamic_questions_data: JSON data for dynamic competency answers (A-F).
        
    Returns:
        A list of dictionaries for the top recommended roles.
    """
    
    # 1. Processing (Feature Engineering)
    
    # Base Persona
    base_persona = _build_pesona_flags(base_persona_data)
    persona_summary = _build_user_persona_summary(base_persona_data)
    
    # Dynamic Answers
    simplify_dynamic_response = _simplify_response_structure(dynamic_questions_data)
    dynamic_text = _build_dynamic_text(persona_summary, simplify_dynamic_response)
    user_vector = _mapping_competency_scores(dynamic_questions_data) # aptitude_vector

    # 2. Model Inference (Scoring)
    
    # Get all TF-IDF scores in one go
    tfidf_scores = _compute_similarity(dynamic_text)
    
    results = []
    
    for i, role in enumerate(ROLES):
        # WSM Score
        wsm_score = _compute_wsm_score(user_vector, role["weights"])
        
        # Apply Constraints/Penalty/Bonus
        factor = _apply_constraints(base_persona, role)
        wsm_adj = wsm_score * factor
        
        # TF-IDF Score
        tfidf_score = float(tfidf_scores[i])
        
        # Final hybrid score: 0.6 * WSM_adj + 0.4 * TFIDF
        final_score = (WEIGHT_WSM * wsm_adj) + (WEIGHT_TFIDF * tfidf_score)
        
        results.append({
            "role_id": role["role_id"],
            "role_name": role["role_name"],
            "score": final_score
        })

    # 3. Final Output
    ranked = sorted(results, key=lambda x: x["score"], reverse=True)
    
    return ranked[:10]
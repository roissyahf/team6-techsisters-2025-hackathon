import numpy as np
import json
from typing import Dict, Any, List, Union
from pathlib import Path
from services.rec_explanation import generate_tech_rec_explanation

# -------------------------
# Loader (used by app.py)
# -------------------------
def load_json_data(filepath: Union[str, Path]) -> Dict[str, Any]:
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


# -------------------------
# WSM scoring
# -------------------------
def compute_wsm_score(user_vector, role_weights):
    w = np.array([
        role_weights["A_logic"],
        role_weights["B_data"],
        role_weights["C_creative"],
        role_weights["D_systemic"],
        role_weights["E_communication"],
        role_weights["F_execution"],
    ])
    u = np.array(user_vector)

    return float(np.dot(u, w) / (np.linalg.norm(u) * np.linalg.norm(w) + 1e-9))


# -------------------------
# Role constraints matching
# -------------------------
def match_user_to_role_constraints(user_constraints: Dict[str, Any], role_constraints: Dict[str, Any]) -> float:
    score = 1.0

    if "time_commitment" in user_constraints:
        if user_constraints["time_commitment"] not in role_constraints.get("time_commitment", []):
            score *= 0.78

    if "work_preference" in user_constraints:
        if user_constraints["work_preference"] not in role_constraints.get("work_preference", []):
            score *= 0.88

    if "skill_level" in user_constraints:
        if user_constraints["skill_level"] not in role_constraints.get("skill_level", []):
            score *= 0.72

    if user_constraints.get("career_break"):
        if not role_constraints.get("career_break_friendly", False):
            score *= 0.75

    return float(score)


# -------------------------
# Persona modifiers
# -------------------------
def apply_persona_modifiers(wsm_score, persona_flags: Dict[str, bool], role: Dict[str, Any]) -> float:

    multiplier = 1.0
    tags = role.get("tags", {}) or role.get("constraints", {})

    def _get_tag_as_lower_str(tag_key: str, default: str = "") -> str:
        value = tags.get(tag_key, default)
        if isinstance(value, list) and value:
            value = value[0]
        return str(value).lower()

    skill_level_tag = _get_tag_as_lower_str("skill_level")
    if persona_flags.get("beginner") and skill_level_tag not in ["beginner", "beginner_friendly", "intermediate"]:
        multiplier *= 0.60

    time_commitment_tag = _get_tag_as_lower_str("time_commitment")
    if persona_flags.get("low_time") and time_commitment_tag not in ["less than 3 hours", "3-6 hour", "3-6 hours", "3 to 6 hours"]:
        multiplier *= 0.68

    if persona_flags.get("remote_only"):
        work_mode = tags.get("remote", tags.get("work_preference", ""))
        if isinstance(work_mode, list) and work_mode:
            work_mode = work_mode[0]
        work_mode = str(work_mode).lower()
        if "remote" not in work_mode:
            multiplier *= 0.70

    if persona_flags.get("career_break") and not tags.get("career_break_friendly", False):
        multiplier *= 0.75

    return float(wsm_score * multiplier)


# -------------------------
# Final score combining WSM + TF-IDF
# -------------------------
def compute_final_role_score(user_vector, role, persona_flags, user_constraints, tfidf_score):
    wsm = compute_wsm_score(user_vector, role["weights"])
    role_constraints = role.get("constraints") or role.get("tags") or {}
    constraint_factor = match_user_to_role_constraints(user_constraints, role_constraints)

    wsm *= constraint_factor
    wsm = apply_persona_modifiers(wsm, persona_flags, role)

    return float(0.6 * wsm + 0.4 * tfidf_score)


# -------------------------
# TF-IDF similarity
# -------------------------
def compute_similarity(user_text: str, vectorizer, role_tfidf_matrix):
    user_vec = vectorizer.transform([user_text])
    sims = (role_tfidf_matrix @ user_vec.T).toarray().flatten()
    return sims


# -------------------------
# MAIN recommendation function (used by Flask)
# -------------------------
def recommend(final_payload: Dict[str, Any],
              roles: List[Dict[str, Any]],
              vectorizer,
              role_ids,
              role_tfidf_matrix) -> List[Dict[str, Any]]:

    user_vector = final_payload["aptitude_vector"]
    persona_flags = final_payload["persona_flags"]
    persona_summary = final_payload.get("persona_summary", "").lower()

    # Build user constraints
    user_constraints = {
        "career_break": persona_flags.get("career_break", False)
    }

    # Time commitment
    for option in ["less than 3 hours", "3-6 hours", "7-10 hours", "10+ hours"]:
        if option in persona_summary:
            user_constraints["time_commitment"] = option
            break

    # Skill level
    for s in ["beginner", "intermediate", "expert"]:
        if s in persona_summary:
            user_constraints["skill_level"] = s
            break

    # Work preference
    if "remote" in persona_summary or persona_flags.get("remote_only"):
        user_constraints["work_preference"] = "remote"

    # Compute tf-idf similarity
    text = final_payload["dynamic_text"]
    tfidf_scores = compute_similarity(text, vectorizer, role_tfidf_matrix)

    results = []
    for i, role in enumerate(roles):
        wsm_score = compute_wsm_score(user_vector, role["weights"])
        final_score = compute_final_role_score(
            user_vector,
            role,
            persona_flags,
            user_constraints,
            float(tfidf_scores[i])
        )

        # --- NEW: Build role_meta for explanation ---
        role_meta = {
            "role_name": role["role_name"],
            "weight_vector": {
                "A": role["weights"]["A_logic"],
                "B": role["weights"]["B_data"],
                "C": role["weights"]["C_creative"],
                "D": role["weights"]["D_systemic"],
                "E": role["weights"]["E_communication"],
                "F": role["weights"]["F_execution"]
            }
        }

        # --- NEW: Generate explanation ---
        explanation = generate_tech_rec_explanation(
            role_id=role["role_id"],
            role_meta=role_meta,
            wsm_score=wsm_score,
            tfidf_similarity=float(tfidf_scores[i]),
            final_score=final_score,
            user_aptitude_vector={
                "A": user_vector[0],
                "B": user_vector[1],
                "C": user_vector[2],
                "D": user_vector[3],
                "E": user_vector[4],
                "F": user_vector[5],
            },
            user_constraints_flags={
                "beginner_penalty_applied": persona_flags.get("beginner", False),
                "time_penalty_applied": persona_flags.get("low_time", False),
                "career_switch_bonus": persona_flags.get("career_break", False)
            }
        )

        results.append({
            "role_id": role["role_id"],
            "role_name": role["role_name"],
            "score": final_score,
            "tfidf": float(tfidf_scores[i]),
            "explanation": explanation
        })

    # Return top 3 (adjust as needed)
    return sorted(results, key=lambda x: x["score"], reverse=True)[:3]

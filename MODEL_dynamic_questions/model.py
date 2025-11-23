# modeling.py
import json
import numpy as np
import pickle
import argparse
from typing import Dict, Any, List

def load_json_data(filepath: str) -> Dict[str, Any]:
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


# -------------------------
# Unified scoring helpers
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


def match_user_to_role_constraints(user_constraints: Dict[str, Any], role_constraints: Dict[str, Any]) -> float:
    score = 1.0
    # TIME COMMITMENT mismatch -> penalty
    if "time_commitment" in user_constraints:
        if user_constraints["time_commitment"] not in role_constraints.get("time_commitment", []):
            score *= 0.78
    # WORK PREFERENCE mismatch (remote/onsite/hybrid)
    if "work_preference" in user_constraints:
        if user_constraints["work_preference"] not in role_constraints.get("work_preference", []):
            score *= 0.88
    # SKILL LEVEL mismatch
    if "skill_level" in user_constraints:
        if user_constraints["skill_level"] not in role_constraints.get("skill_level", []):
            score *= 0.72
    # CAREER BREAK: prefer roles flagged friendly
    if user_constraints.get("career_break"):
        if not role_constraints.get("career_break_friendly", False):
            score *= 0.75
    return float(score)


def apply_persona_modifiers(wsm_score, persona_flags: Dict[str, bool], role: Dict[str, Any]) -> float:
    multiplier = 1.0
    tags = role.get("tags", {}) or role.get("constraints", {})

    # Helper function to safely get a tag value as a lowercased string
    # It handles cases where tags are a single string, a list of strings, or missing (defaulting to "")
    def _get_tag_as_lower_str(tag_key: str, default: str = "") -> str:
        value = tags.get(tag_key, default)
        
        # 1. Handle if the value is a list (e.g., ['beginner']) and take the first element
        if isinstance(value, list) and value:
            value = value[0]
            
        # 2. Ensure it's treated as a string (handling None, bools, etc.) and then convert to lowercase
        return str(value).lower()

    # --- 1. Beginner vs. Skill Level ---
    skill_level_tag = _get_tag_as_lower_str("skill_level")
    if persona_flags.get("beginner") and skill_level_tag not in ["beginner", "beginner_friendly", "intermediate"]:
        multiplier *= 0.60

    # --- 2. Low Time vs. Time Commitment ---
    time_commitment_tag = _get_tag_as_lower_str("time_commitment")
    if persona_flags.get("low_time") and time_commitment_tag not in ["less than 3 hours", "3-6 hour", "3-6 hours", "3 to 6 hours"]:
        multiplier *= 0.68

    # --- 3. Remote Only vs. Work Preference ---
    if persona_flags.get("remote_only"):
        # Retrieve either the 'remote' or 'work_preference' tag value
        work_mode = tags.get("remote", tags.get("work_preference", ""))
        
        # Apply the same list-to-string and lowercasing logic
        if isinstance(work_mode, list) and work_mode:
            work_mode = work_mode[0]
            
        work_mode = str(work_mode).lower()

        if "remote" not in work_mode:
            multiplier *= 0.70

    # --- 4. Career Break ---
    if persona_flags.get("career_break") and not tags.get("career_break_friendly", False):
        multiplier *= 0.75

    return float(wsm_score * multiplier)


def compute_final_role_score(user_vector, role, persona_flags, user_constraints, tfidf_score):
    wsm = compute_wsm_score(user_vector, role["weights"])
    role_constraints = role.get("constraints") or role.get("tags") or {}
    constraint_factor = match_user_to_role_constraints(user_constraints, role_constraints)
    wsm *= constraint_factor
    wsm = apply_persona_modifiers(wsm, persona_flags, role)
    final_score = 0.6 * wsm + 0.4 * tfidf_score
    return float(final_score)


# -------------------------
# TF-IDF similarity
# -------------------------
def compute_similarity(user_text: str, vectorizer, role_tfidf_matrix):
    user_vec = vectorizer.transform([user_text])
    sims = (role_tfidf_matrix @ user_vec.T).toarray().flatten()
    return sims


# -------------------------
# Main recommendation function
# -------------------------
def recommend(final_payload: Dict[str, Any], roles: List[Dict[str, Any]], vectorizer, role_ids, role_tfidf_matrix) -> List[Dict[str, Any]]:
    user_vector = final_payload["aptitude_vector"]
    persona_flags = final_payload["persona_flags"]
    # Build user_constraints from persona_summary + flags
    # Expect the final_payload to carry fields used by constraints (using persona_flags + parsed persona_summary)
    persona_summary = final_payload.get("persona_summary","").lower()
    # Derive user constraints simple mapping
    user_constraints = {
        "time_commitment": None,
        "work_preference": None,
        "skill_level": None,
        "career_break": persona_flags.get("career_break", False)
    }
    # find time commitment phrase in persona_summary
    for option in ["less than 3 hours", "3-6 hours", "3-6 hours", "7-10 hours", "10+ hours", "10+"]:
        if option in persona_summary:
            user_constraints["time_commitment"] = option
            break
    # skill level
    for s in ["beginner", "intermediate", "expert"]:
        if s in persona_summary:
            user_constraints["skill_level"] = s
            break
    # remote preference
    if "remote" in persona_summary or persona_flags.get("remote_only"):
        user_constraints["work_preference"] = "remote"
    # compute tfidf
    text = final_payload["dynamic_text"]
    tfidf_scores = compute_similarity(text, vectorizer, role_tfidf_matrix)
    results = []
    for i, role in enumerate(roles):
        tfidf_score = float(tfidf_scores[i])
        final_score = compute_final_role_score(
            user_vector=user_vector,
            role=role,
            persona_flags=persona_flags,
            user_constraints=user_constraints,
            tfidf_score=tfidf_score
        )
        results.append({
            "role_id": role["role_id"],
            "role_name": role["role_name"],
            "score": final_score,
            "tfidf": tfidf_score
        })
    ranked = sorted(results, key=lambda x: x["score"], reverse=True)
    return ranked[:10]

# -------------------------
# CLI and main
# -------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run hybrid recommendation model using final payload.")
    parser.add_argument('--final_payload', required=True, help="Path to final payload JSON")
    parser.add_argument('--roles', default="static_data/roles_upd.json", help="Path to roles JSON (weights + tags/constraints)")
    parser.add_argument('--descriptions', default="static_data/descriptions_upd.json", help="Path to tech roles descriptions JSON")
    parser.add_argument('--tfidf', default="pickle_file/tfidf_upd.pkl", help="Path to TF-IDF vectorizer pickle")
    parser.add_argument('--matrix', default="pickle_file/role_tfidf_matrix_upd.pkl", help="Path to role tfidf matrix pickle (tuple: role_ids, matrix)")
    args = parser.parse_args()

    final_payload = load_json_data(args.final_payload)
    roles = load_json_data(args.roles)
    descriptions = load_json_data(args.descriptions)

    # Load TF-IDF resources
    with open(args.tfidf, 'rb') as f:
        vectorizer = pickle.load(f)
    with open(args.matrix, 'rb') as f:
        role_ids, role_tfidf_matrix = pickle.load(f)

    # Ensure roles order aligns with role_ids. If not, re-order roles to match role_ids
    roles_by_id = {r["role_id"]: r for r in roles}
    ordered_roles = []
    for rid in role_ids:
        if rid in roles_by_id:
            ordered_roles.append(roles_by_id[rid])
        else:
            print(f"Warning: role_id {rid} not found in roles json; alignment may be off.")
            ordered_roles.append({"role_id": rid, "role_name": rid, "weights": {"A_logic":0,"B_data":0,"C_creative":0,"D_systemic":0,"E_communication":0,"F_execution":0}, "tags": {}, "constraints": {}})

    top_roles = recommend(final_payload, ordered_roles, vectorizer, role_ids, role_tfidf_matrix)

    print("\n==================== TOP 10 ROLES ====================")
    for idx, r in enumerate(top_roles, 1):
        print(f"{idx}. {r['role_name']}  | Final Score: {r['score']:.4f} | TF-IDF Score: {r['tfidf']:.6f}")
    print("======================================================")
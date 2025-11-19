# recommend tech roles based on user profile and text input

import json
import numpy as np
import pickle
import argparse

# -------------------------
# Load static data at startup
# -------------------------
roles_path = "static_data/roles.json"
descriptions_path = "static_data/descriptions.json"
constraints_path = "static_data/constraints.json"

with open(roles_path) as f: #
    ROLES = json.load(f)

with open(constraints_path) as f:
    CONSTRAINTS = json.load(f)

# TF-IDF resources
VECTORIZER = pickle.load(open("pickle_file/tfidf.pkl", "rb"))
ROLE_IDS, ROLE_TFIDF_MATRIX = pickle.load(open("pickle_file/role_tfidf_matrix.pkl", "rb"))


# -------------------------
# Compute WSM score
# -------------------------

def compute_wsm_score(user_vector, role_weights):
    """
    user_vector: list of 6 floats (0-1 normalized)
    role_weights: dict of 6 floats (A-F weights)
    """
    w = np.array([
        role_weights["A_logic"],
        role_weights["B_data"],
        role_weights["C_creative"],
        role_weights["D_communication"],
        role_weights["E_empowerment"],
        role_weights["F_execution"],
    ])

    u = np.array(user_vector)

    # Dot product, normalized
    return float(np.dot(u, w) / (np.linalg.norm(u) * np.linalg.norm(w) + 1e-9))


# -------------------------
# Constraint logic
# -------------------------
def apply_constraints(base_persona, role):
    """Multiply score depending on user persona and role tags."""
    factor = 1.0

    for key in base_persona:
        if key not in CONSTRAINTS:
            continue

        rule = CONSTRAINTS[key]

        # Has tag? 
        if "tag_key" in rule:
            role_value = role["tags"].get(rule["tag_key"])
        else:
            role_value = role["tags"].get("skill_level")

        # Check penalty
        if "penalty" in rule and role_value in rule["applies_to"]:
            factor *= rule["penalty"]

        # Check bonus
        if "bonus" in rule and role_value in rule["applies_to"]:
            factor *= rule["bonus"]

    return factor


# -------------------------
# TF-IDF similarity
# -------------------------
def compute_similarity(user_text):
    user_vec = VECTORIZER.transform([user_text])
    sims = (ROLE_TFIDF_MATRIX @ user_vec.T).toarray().flatten()
    return sims  # raw similarity scores


# -------------------------
# Main recommendation endpoint
# -------------------------

def recommend(final_payload_path: str):
    """
    Generates tech role recommendations based on the user's final payload.
    
    Args:
        final_payload_path: Path to the JSON file containing the processed user data.
    """
    
    # Load the final payload file specified by the argument
    with open(final_payload_path) as f:
        data = json.load(f)

    user_vector = data["aptitude_vector"]      # 6 floats
    base_persona = data["persona_flags"]       # dict of persona flags
    dynamic_text = data["dynamic_text"]        # Combined text for similarity

    tfidf_scores = compute_similarity(dynamic_text)

    results = []

    for i, role in enumerate(ROLES):
        role_id = role["role_id"]

        # WSM score
        wsm_score = compute_wsm_score(user_vector, role["weights"])

        # Persona penalty/bonus
        factor = apply_constraints(base_persona, role)
        wsm_adj = wsm_score * factor

        # TF-IDF score
        tfidf_score = float(tfidf_scores[i])

        # Final hybrid score
        final_score = 0.6 * wsm_adj + 0.4 * tfidf_score

        results.append({
            "role_id": role_id,
            "role_name": role["role_name"],
            "score": final_score
        })

    # Sort descending
    ranked = sorted(results, key=lambda x: x["score"], reverse=True)

    return ranked[:10]  # return top 10 roles


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run the model to give tech roles recommendations based on user profile"
    )
    
    # Define the final_payload_path argument
    parser.add_argument(
        '--final_payload_path', 
        type=str, 
        required=True,
        default="FINAL_PAYLOAD/SAMPLE_final_payload.json", 
        help="Path to the JSON file containing the processed final payload"
    )

    args = parser.parse_args()

    # Pass the parsed argument's value to the recommend function
    top_roles = recommend(args.final_payload_path)
    
    print(f"Top 10 Role Recommendations for input: {args.final_payload_path}\n")
    print("---")
    
    for idx, role in enumerate(top_roles, 1):
        print(f"{idx}. **{role['role_name']}** (Score: {role['score']:.4f})")
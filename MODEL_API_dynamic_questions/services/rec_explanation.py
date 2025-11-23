# -----------------------------------------
# Skill Name Mapping
# -----------------------------------------
SKILL_MAP = {
    "A": "Logical & Structured Thinking",
    "B": "Data & Analytical Insight",
    "C": "Creative & User-Centricity",
    "D": "Systemic & Risk Management",
    "E": "Communication & Stakeholder",
    "F": "Content & Language Fluency"
}


def generate_tech_rec_explanation(
    role_id,
    role_meta,
    wsm_score,
    tfidf_similarity,
    final_score,
    user_aptitude_vector,
    user_constraints_flags,
):
    """
    role_meta = {
        "role_name": "...",
        "weight_vector": {A,B,C,D,E,F}
    }

    user_constraints_flags = {
        "beginner_penalty_applied": True/False,
        "time_penalty_applied": True/False,
        "career_switch_bonus": True/False
    }
    """

    # -----------------------------------------
    # 1. Competency Contribution Analysis
    # -----------------------------------------
    competency_contrib = {}

    for comp_code, user_val in user_aptitude_vector.items():
        role_weight = role_meta["weight_vector"].get(comp_code, 0)
        competency_contrib[comp_code] = user_val * role_weight

    # Sort by contribution (descending)
    top_two = sorted(
        competency_contrib.items(),
        key=lambda x: x[1],
        reverse=True
    )[:2]

    # Convert skills code category to human readable names
    strong_components = [SKILL_MAP.get(code, code) for code, _ in top_two]
    strong_text = ", ".join(strong_components)

    # -----------------------------------------
    # 2. Constraint Effects Summary
    # -----------------------------------------
    notes = []

    if user_constraints_flags.get("beginner_penalty_applied"):
        notes.append("adjusted for your beginner-friendly preference")

    if user_constraints_flags.get("time_penalty_applied"):
        notes.append("adjusted based on your available study time")

    if user_constraints_flags.get("career_switch_bonus"):
        notes.append("boosted due to strong fit for career switching")

    if notes:
        constraint_text = "Additionally, the score was " + "; ".join(notes) + "."
    else:
        constraint_text = "No major constraints affected this recommendation."

    # -----------------------------------------
    # 3. Preference (TF-IDF) Alignment
    # -----------------------------------------
    if tfidf_similarity is not None:
        if tfidf_similarity >= 0.30:
            pref_text = "Your interests strongly align with this role's nature."
        elif tfidf_similarity >= 0.20:
            pref_text = "Your interests moderately align with key aspects of this role."
        else:
            pref_text = "This role is recommended mainly due to aptitude compatibility."
    else:
        # In case TF-IDF is optional
        pref_text = "Aptitude alignment is the primary basis for recommending this role."

    # -----------------------------------------
    # 4. Final Explanation Text
    # -----------------------------------------
    explanation = (
        f"The {role_meta['role_name']} role is recommended because your strongest "
        f"competencies align with what this role values most, particularly {strong_text}. "
        f"{pref_text} "
        f"{constraint_text} "
        f"Overall, this role achieved a final suitability score of {final_score:.2f}, "
        f"with a competency match score of {wsm_score:.2f} "
        f"and an interest-alignment score of {tfidf_similarity:.2f}."
    )

    return explanation
import numpy as np
from typing import List, Dict, Any, Tuple

def _safe_norm(v: np.ndarray) -> float:
    n = float(np.linalg.norm(v))
    return n if n != 0 else 0.0

def _format_pct(x: float) -> str:
    return f"{x*100:.0f}%" if x >= 0 else f"{x*100:.0f}%"

def explain_recommendations(user_scores: Dict[str, float],
                            role_model,
                            ranked_roles: List[Tuple[str, float]],
                            top_k: int = 3,
                            alpha: float = 0.6) -> List[Dict[str, Any]]:
    """
    Generate explanations for top-k roles.

    Parameters
    ----------
    user_scores : dict
        Unified user scores produced by build_user_scores(...)
    role_model : TechnicalHybridModel
        Instance of the model (reuse weights, dimensions, and scoring functions)
    ranked_roles : list of tuples (role_name, final_score)
        The ranked output from role_model.hybrid(...) (only top entries required)
    top_k : int
        How many top roles to explain (defaults to 3)
    alpha : float
        Fusion weight (must match the value used in model.hybrid)

    Returns
    -------
    List[dict]
        Each dict contains:
          - role_name
          - explanation_text (3-4 sentences)
          - breakdown (structured info useful for tooltips / UI)
    """
    explanations = []

    # Recompute components using the model's methods
    wsm_scores = role_model.weighted_scoring(user_scores)
    sim_scores = role_model.similarity_scores(user_scores)

    # Precompute technical question weights & base feature weights
    tech_weights = role_model.weights.get("technical_questions", {})
    base_weights = role_model.weights.get("base_features", {})

    # For each top role, compute contribution breakdown
    for role_name, final_score in ranked_roles[:top_k]:
        # Compose numeric values
        wsm_value = float(wsm_scores.get(role_name, 0.0))
        sim_value = float(sim_scores.get(role_name, 0.0))
        # recompute final to be sure it's consistent
        final_calc = float(alpha * wsm_value + (1 - alpha) * sim_value)

        # ---- Technical contributions ----
        # Only consider the technical_questions keys for competency contributions
        tech_contribs = []
        tech_total_raw = 0.0
        for skill, w in tech_weights.items():
            u_val = float(user_scores.get(skill, 0.0))
            # role skill value from model.roles
            # get role skill map
            role_skill_map = None
            for r in role_model.roles:
                if r.get("role") == role_name:
                    role_skill_map = r.get("skills", {})
                    break
            r_val = float(role_skill_map.get(skill, 0.0)) if role_skill_map else 0.0
            raw = u_val * r_val * float(w)
            tech_contribs.append((skill, raw, u_val, r_val, float(w)))
            tech_total_raw += raw

        # Sort by raw contribution descending
        tech_contribs_sorted = sorted(tech_contribs, key=lambda x: x[1], reverse=True)

        # Convert to percentage of technical component
        tech_breakdown = []
        for skill, raw, u_val, r_val, w in tech_contribs_sorted:
            pct = (raw / tech_total_raw) if tech_total_raw != 0 else 0.0
            tech_breakdown.append({
                "skill": skill,
                "user_value": u_val,
                "role_value": r_val,
                "weight": w,
                "raw_contribution": raw,
                "relative_share": round(float(pct), 4)
            })

        # Top 2 technical contributors (names)
        top_tech = tech_breakdown[:2] if tech_breakdown else []

        # ---- Base feature contributions ----
        base_contribs = []
        base_total_raw = 0.0
        for feat, w in base_weights.items():
            u_val = float(user_scores.get(feat, 0.0))
            raw = u_val * float(w)
            base_contribs.append((feat, raw, u_val, float(w)))
            base_total_raw += raw
        base_contribs_sorted = sorted(base_contribs, key=lambda x: x[1], reverse=True)
        base_breakdown = []
        for feat, raw, u_val, w in base_contribs_sorted:
            pct = (raw / base_total_raw) if base_total_raw != 0 else 0.0
            base_breakdown.append({
                "feature": feat,
                "user_value": u_val,
                "weight": w,
                "raw_contribution": raw,
                "relative_share": round(float(pct), 4)
            })
        top_base = base_breakdown[0] if base_breakdown else None

        # ---- Penalty / adjustment detection (best-effort) ----
        penalty_notes = []
        if abs(final_calc - final_score) > 1e-6:
            penalty_notes.append({
                "note": "Final score recomputed inside explainer. Use this as reference.",
                "reported_final": float(final_score),
                "recomputed_final": float(final_calc)
            })

        # ---- Build human-readable explanation text (3-4 sentences) ----
        # Sentence 1: core reason (top competencies)
        if top_tech:
            top_names = [t["skill"].replace("_", " ").title() for t in top_tech]
            s1 = f"The {role_name} role is recommended because your strongest competencies align with what this role values most particularly {', '.join(top_names)}."
        else:
            s1 = f"The {role_name} role is recommended because your profile shows aptitude compatible with this role."

        # Sentence 2: aptitude vs semantic (WSM vs similarity)
        # choose whichever component contributed more to the final score
        wsm_part = alpha * wsm_value
        sim_part = (1 - alpha) * sim_value
        if wsm_part >= sim_part:
            s2 = f"This recommendation is driven mainly by aptitude compatibility (technical & base-feature match) which contributed more to the final suitability score."
        else:
            s2 = f"This recommendation is driven mainly by skill-vector similarity (semantic fit) which contributed more to the final suitability score."

        # Sentence 3: mention base-feature influence or penalties
        if top_base and top_base["relative_share"] > 0:
            feat_name = top_base["feature"].replace("_", " ").title()
            s3 = f"Additionally, your base preference '{feat_name}' increased the fit for this role."
        else:
            s3 = "No strong preference-based adjustment was detected."

        # Sentence 4: final score summary
        s4 = f"Overall, this role achieved a final suitability score of {final_calc:.2f}."

        explanation_text = " ".join([s1, s2, s3, s4])

        # ---- Structured breakdown returned for UI/tooltips ----
        breakdown = {
            "scores": {
                "wsm": round(float(wsm_value), 4),
                "similarity": round(float(sim_value), 4),
                "final_score": round(float(final_calc), 4),
                "alpha": alpha
            },
            "technical_contributions": tech_breakdown,
            "base_feature_contributions": base_breakdown,
            "penalty_notes": penalty_notes
        }

        explanations.append({
            "role_name": role_name,
            "explanation_text": explanation_text,
            "breakdown": breakdown
        })

    return explanations

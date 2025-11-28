import sys, os

# Add project root to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from MODEL_API_TECHNICAL_ROLE.services.processing import build_user_scores
from MODEL_API_TECHNICAL_ROLE.services.model import TechnicalHybridModel
from MODEL_API_TECHNICAL_ROLE.services.explain_recommendation import explain_recommendations

# Load hybrid model
role_model = TechnicalHybridModel()

def run_role_pipeline(payload):
    """
    Pipeline for role recommendation only.
    """
    base_profile = payload["base_profile"]
    tech_answers = payload["technical_answers"]

    # Convert user answers to numeric scores
    user_scores = build_user_scores(base_profile, tech_answers)

    # Run hybrid model
    ranked = role_model.hybrid(user_scores)

    # Build top roles with scores
    top_k = 3
    top_ranked = ranked[:top_k]

    # Generate explanations (pass the model instance so explainer can recompute WSM/similarity identically)
    explanations = explain_recommendations(user_scores=user_scores,
                                          role_model=role_model,
                                          ranked_roles=top_ranked,
                                          top_k=top_k,
                                          alpha=0.6)

    # Merge explanations with simple role+score output
    top_roles_with_explanations = []
    for role_tuple, expl in zip(top_ranked, explanations):
        role_name, score = role_tuple
        top_roles_with_explanations.append({
            "role_name": role_name,
            "score": float(score),
            "explanation": expl["explanation_text"],
            #"explanation_breakdown": expl["breakdown"]
        })

    return {"top_roles": top_roles_with_explanations}

import sys, os

# Add project root to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from MODEL_technical_questions.processing import build_user_scores
from MODEL_technical_questions.model import TechnicalHybridModel

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

    # Return ONLY roles, no explanation, no courses
    return {
        "top_roles": [
            {"role_name": r, "score": float(s)}
            for r, s in ranked[:5]
        ]
    }

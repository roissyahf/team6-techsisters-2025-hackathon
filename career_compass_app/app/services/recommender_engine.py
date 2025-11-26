import json
import sys
import os

# Enable parent folder import
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from MODEL_technical_questions.processing import build_user_scores
from MODEL_technical_questions.model import TechnicalHybridModel

# Initialize hybrid model
role_model = TechnicalHybridModel()


def generate_explanation(user_scores):
    """
    Generates human-friendly explanations for why each recommended role fits the user.
    """
    explanation_parts = []

    if user_scores.get("programming", 0) >= 4:
        explanation_parts.append("strong programming skills")

    if user_scores.get("problem_solving", 0) >= 4:
        explanation_parts.append("excellent problem-solving ability")

    if user_scores.get("system_understanding", 0) >= 3:
        explanation_parts.append("good understanding of system architecture")

    if user_scores.get("tools_familiarity", 0) >= 3:
        explanation_parts.append("high familiarity with technical tools")

    if not explanation_parts:
        explanation_parts.append("a skill profile that aligns well with this role")

    return "Recommended because you have " + " and ".join(explanation_parts) + "."


def run_pipeline(payload):
    """
    Pipeline for TECHNICAL USER ROLE RECOMMENDATION.
    This powers your teammate's required API format.
    """

    # 1. Load inputs
    base_profile = payload["base_profile"]
    technical_answers = payload["technical_answers"]

    # 2. Build numeric score vector
    user_scores = build_user_scores(base_profile, technical_answers)

    # 3. Run hybrid model
    ranked_roles = role_model.hybrid(user_scores)

    # 4. Build output with explanations
    output = []
    for role_name, score in ranked_roles[:5]:  # top 5 roles
        output.append({
            "role_name": role_name,
            "score": float(score),
            "explanation": generate_explanation(user_scores)
        })

    return {"top_recommendation": output}
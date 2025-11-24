import json
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from MODEL_technical_questions.processing import build_user_scores
from MODEL_technical_questions.model import TechnicalHybridModel
from MODEL_technical_questions.course_recommender import CourseRecommender

# Instantiate your models
role_model = TechnicalHybridModel()
course_model = CourseRecommender()


def run_pipeline(payload):
    """
    Main pipeline for your technical user hybrid model.
    
    payload format:
    {
      "base_profile": {...},          # base questions JSON (same structure as sample.json)
      "technical_answers": {...}      # {"T1_programming": 4, ... }
    }
    """

    base_json = payload["base_profile"]
    technical_answers = payload["technical_answers"]

    # Convert base+technical to a single scoring dict
    user_scores = build_user_scores(base_json, technical_answers)

    # Run hybrid model
    ranked_roles = role_model.hybrid(user_scores)

    # Recommend top courses for top 3 roles
    course_suggestions = course_model.recommend_for_top_roles(ranked_roles, top_n=3)

    # Build API response
    response = {
        "top_roles": [
            {"role": role, "score": float(score)}
            for role, score in ranked_roles[:5]
        ],
        "recommended_courses": course_suggestions
    }

    return response

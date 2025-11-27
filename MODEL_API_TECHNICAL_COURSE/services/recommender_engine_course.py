import os
import sys

# Add project root so we can import MODEL_technical_questions
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from MODEL_API_TECHNICAL_COURSE.services.course_model_full import CourseRecommenderModel

course_model = CourseRecommenderModel()

def recommend_courses(payload):
    """
    payload example:
    {
      "top_role": "Software Engineer",
      "top_n": 5       # optional
    }
    """
    role_name = payload.get("top_role", "")
    top_n = int(payload.get("top_n", 5))

    result = course_model.recommend(role_name, top_n=top_n)
    return result

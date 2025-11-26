import json
import os

class CourseRecommender:
    """
    Course recommender: returns courses based on top roles.
    """

    def __init__(self,
                 role_dataset_path="../MODEL_technical_questions/role_dataset.json"):

        # Convert to absolute path to avoid import issues
        role_dataset_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "role_dataset.json"))

        with open(role_dataset_path, "r", encoding="utf-8") as f:
            self.roles = json.load(f)

    def recommend_for_role(self, role_name):
        """
        Given a role, return that role's course list.
        """
        for role in self.roles:
            if role["role"] == role_name:
                return role.get("courses", [])
        return []

    def recommend_for_top_roles(self, ranked_roles, top_n=3):
        """
        Given list of (role, score), return course recommendations for the top N.
        """
        result = {}
        for role_name, _score in ranked_roles[:top_n]:
            result[role_name] = self.recommend_for_role(role_name)
        return result

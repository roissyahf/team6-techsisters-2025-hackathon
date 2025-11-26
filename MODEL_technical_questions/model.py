import json
import numpy as np

class TechnicalHybridModel:
    """
    Hybrid Model for recommending tech roles to technical users.
    Combines:
    1. Weighted Scoring Model (WSM)
    2. Cosine Similarity
    """

    def __init__(self, 
                 role_dataset_path="../MODEL_technical_questions/role_dataset.json",
                 weight_path="../MODEL_technical_questions/scoring_weights.json"):

        # Load role dataset
        with open(role_dataset_path, "r", encoding="utf-8") as f:
            self.roles = json.load(f)

        # Load scoring weights
        with open(weight_path, "r", encoding="utf-8") as f:
            self.weights = json.load(f)

        # Skills we will use for similarity scoring
        self.skill_dimensions = [
            "programming",
            "problem_solving",
            "debugging",
            "system_understanding",
            "tools_familiarity",
            "design",
            "data_analysis",
            "business",
            "communication",
            "security_infra"
        ]

    def _build_vector(self, score_dict):
        """
        Convert a dictionary {skill: value} into a fixed-order numeric vector.
        Missing skills default to 0.
        """
        return np.array([float(score_dict.get(skill, 0.0)) for skill in self.skill_dimensions])

    def weighted_scoring(self, user_scores):
        """
        Weighted Scoring Model (WSM):
        Σ (user_skill × role_skill × weight)
        plus weighted base features.
        """
        role_scores = {}

        for role in self.roles:
            role_name = role["role"]
            role_skill_map = role["skills"]
            total = 0

            # Technical question scoring
            for skill, weight in self.weights["technical_questions"].items():
                u_val = float(user_scores.get(skill, 0))
                r_val = float(role_skill_map.get(skill, 0))
                total += u_val * r_val * float(weight)

            # Base features scoring
            for feat, weight in self.weights["base_features"].items():
                total += float(user_scores.get(feat, 0)) * float(weight)

            role_scores[role_name] = total

        return role_scores

    def similarity_scores(self, user_scores):
        """
        Compute cosine similarity between user skills and role vectors.
        """
        similarity = {}

        user_vec = self._build_vector(user_scores)

        for role in self.roles:
            role_vec = self._build_vector(role["skills"])

            dot = float(np.dot(user_vec, role_vec))
            norm = float(np.linalg.norm(user_vec) * np.linalg.norm(role_vec))

            similarity_score = (dot / norm) if norm != 0 else 0
            similarity[role["role"]] = similarity_score

        return similarity

    def hybrid(self, user_scores, alpha=0.6):
        """
        Final combined hybrid score:
        Hybrid = α × WSM + (1 − α) × Similarity
        """
        wsm_scores = self.weighted_scoring(user_scores)
        sim_scores = self.similarity_scores(user_scores)

        final_scores = {}

        for role_name in wsm_scores:
            final_scores[role_name] = (
                alpha * wsm_scores[role_name] +
                (1 - alpha) * sim_scores.get(role_name, 0)
            )

        ranked = sorted(final_scores.items(), key=lambda x: x[1], reverse=True)
        return ranked

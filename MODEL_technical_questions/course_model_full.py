import os
import pandas as pd


class CourseRecommenderModel:
    """
    Content-based course recommender for technical users.
    Uses Coursera course metadata (skills, rating, level, etc.)
    to recommend courses that match a given tech role.
    """

    def __init__(self,
                 dataset_path="MODEL_technical_questions/datasets/Coursera.csv"):

        # Make path absolute (robust when called from APIs)
        dataset_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "datasets", "Coursera.csv")
        )

        self.df = pd.read_csv(dataset_path)

        # Basic cleaning
        self.df["skills"] = self.df["skills"].fillna("").str.lower()
        self.df["level"] = self.df["level"].fillna("").str.lower()
        self.df["partner"] = self.df["partner"].fillna("")
        self.df["course"] = self.df["course"].fillna("")

        # Ensure numeric columns
        self.df["rating"] = pd.to_numeric(self.df["rating"], errors="coerce").fillna(0.0)
        self.df["reviewcount"] = pd.to_numeric(self.df["reviewcount"], errors="coerce").fillna(0)

        # Predefined mapping from role to skill keywords
        # 👉 You can refine / expand this mapping later.
        self.role_skill_keywords = self._build_role_skill_mapping()

    def _build_role_skill_mapping(self):
        """
        Map each role (or role group) to keywords we expect in the skills column.
        """
        return {
            # Software / backend / full-stack
            "software engineer": ["software", "programming", "python", "java", "c++", "oop"],
            "backend engineer": ["backend", "api", "database", "sql", "django", "spring"],
            "full-stack engineer": ["full-stack", "frontend", "backend", "react", "node", "web"],
            "frontend engineer": ["frontend", "html", "css", "javascript", "react", "ui"],
            "qa engineer": ["testing", "qa", "automation", "selenium"],

            # Data / analytics
            "data analyst": ["excel", "sql", "data analysis", "power bi", "tableau"],
            "data scientist": ["machine learning", "statistics", "python", "pandas"],
            "ml engineer": ["machine learning", "deep learning", "tensorflow", "pytorch"],
            "bi analyst": ["bi", "business intelligence", "power bi", "tableau", "dashboard"],
            "data engineer": ["data engineering", "etl", "spark", "hadoop"],

            # UX / design
            "ux designer": ["ux", "user experience", "wireframe", "figma"],
            "ui designer": ["ui", "interface", "visual design", "figma"],
            "product designer": ["product design", "ux", "ui"],
            "interaction designer": ["interaction", "prototype", "ux"],
            "frontend developer": ["frontend", "html", "css", "javascript"],

            # Infra / security
            "cybersecurity engineer": ["security", "cybersecurity", "network", "threat"],
            "cloud architect": ["cloud", "aws", "azure", "gcp"],
            "devops engineer": ["devops", "ci/cd", "docker", "kubernetes"],
            "site reliability engineer": ["sre", "reliability", "monitoring", "devops"],
            "network engineer": ["network", "routing", "switching"],

            # Product / project / BA
            "product manager": ["product management", "roadmap", "stakeholder"],
            "project manager": ["project management", "agile", "scrum"],
            "program manager": ["program management", "portfolio"],
            "business analyst": ["business analysis", "requirements", "process"],
            "it consultant": ["consulting", "strategy", "it"],

            # Content / marketing
            "technical writer": ["technical writing", "documentation"],
            "content strategist": ["content strategy", "content marketing"],
            "seo specialist": ["seo", "search", "keyword"],
            "digital marketing specialist": ["digital marketing", "social media", "campaign"],
            "copywriter": ["copywriting", "writing", "content"]
        }

    def _get_keywords_for_role(self, role_name: str):
        """
        Find best keyword list for a role_name, using simple fuzzy matching.
        """
        role_name = role_name.lower()
        # Exact match
        if role_name in self.role_skill_keywords:
            return self.role_skill_keywords[role_name]

        # Try partial match
        for key in self.role_skill_keywords:
            if key in role_name or role_name in key:
                return self.role_skill_keywords[key]

        # Fallback: generic tech keywords
        return ["python", "sql", "web", "cloud", "data", "software"]

    def recommend(self, role_name: str, top_n: int = 5):
        """
        Recommend top N courses for a given tech role.

        Returns a dict:
        {
          "role": "<role_name>",
          "keywords_used": [...],
          "courses": [
             {...}, {...}
          ]
        }
        """
        keywords = self._get_keywords_for_role(role_name)
        keywords_lower = [k.lower() for k in keywords]

        df = self.df.copy()

        # Score by keyword matches in 'skills' column
        def keyword_match_count(skills_text: str):
            text = skills_text.lower()
            return sum(1 for kw in keywords_lower if kw in text)

        df["keyword_matches"] = df["skills"].apply(keyword_match_count)

        # Filter out courses with zero relevance
        df = df[df["keyword_matches"] > 0]
        if df.empty:
            # Fallback: just highest rated courses overall
            df = self.df.copy()
            df["keyword_matches"] = 0

        # Compute a final score:
        #   base on rating, log(reviewcount), and keyword matches
        import numpy as np
        df["review_weight"] = np.log1p(df["reviewcount"])
        df["score"] = (
            df["rating"] * 0.6 +
            df["review_weight"] * 0.2 +
            df["keyword_matches"] * 0.2
        )

        df = df.sort_values("score", ascending=False).head(top_n)

        courses_output = []
        for _, row in df.iterrows():
            courses_output.append({
                "course_title": row["course"],
                "platform": row["partner"],
                "skills": row["skills"],
                "rating": float(row["rating"]),
                "reviewcount": int(row["reviewcount"]),
                "level": row["level"],
                "duration": row.get("duration", ""),
                "certificatetype": row.get("certificatetype", ""),
                "crediteligibility": row.get("crediteligibility", "")
            })

        return {
            "role": role_name,
            "keywords_used": keywords,
            "courses": courses_output
        }

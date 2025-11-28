import requests
import json

url = "http://127.0.0.1:9000/generate-action-plan"

# Example 1: Using NEW simplified "selected role" format
payload_new_format = {
    "persona_json": {
        "user_profile": {
            "timestamp": "2025-11-13T08:30:00Z",
            "user_id": "USR_20251113_002",
            "responses": {
                "Q1_current_status": {"question": "What best describes your current situation?", "answer": "Working Professional (Non-Tech)"},
                "Q2_tech_familiarity": {"question": "How familiar are you with technology and digital tools?", "answer": "Comfortable"},
                "Q3_tech_experience": {"question": "Have you ever taken a course, training, or worked on a project related to tech?", "answer": "Yes"},
                "Q4_interest_area": {"question": "Which of these areas interests you the most?", "answer": "Working with data and insights"},
                "Q5_motivation": {"question": "What motivates you most to pursue a tech career?", "answer": "Problem-solving"},
                "Q6_skill_level": {"question": "How would you describe your current technical skill level?", "answer": "Intermediate (I have some hands-on experience or projects)"},
                "Q7_project_experience": {"question": "Have you ever completed a personal or professional tech project?", "answer": "Yes, small projects"},
                "Q8_learning_preference": {"question": "How do you prefer to learn new skills?", "answer": "Self-learning (YouTube, blogs, articles)"},
                "Q9_time_commitment": {"question": "How much time can you dedicate to learning weekly?", "answer": "7-10 hours"},
                "Q10_goal": {"question": "What is your main goal right now?", "answer": "Get certified / build portfolio"}
            }
        }
    },
    # NEW SIMPLIFIED SELECTED ROLE FORMAT
    "selected_role_json": {
        "top_role": "Data Analyst"
    },
    # Course recommendations in new format
    "course_recommendations_json": {
        "role": "Data Analyst",
        "keywords_used": ["data", "analytics", "sql", "python"],
        "courses": [
            {
                "course_title": "Google Data Analytics Professional Certificate",
                "platform": "Google",
                "skills": "{\"data analysis\",\"sql\",\"spreadsheets\",\"data visualization\"}",
                "rating": 4.8,
                "reviewcount": 15234,
                "level": "beginner",
                "duration": "1 - 3 Months",
                "certificatetype": "Professional Certificate",
                "crediteligibility": False
            },
            {
                "course_title": "Data Analysis with Python",
                "platform": "IBM",
                "skills": "{\"python programming\",\"data analysis\",\"pandas\",\"numpy\"}",
                "rating": 4.6,
                "reviewcount": 8921,
                "level": "intermediate",
                "duration": "1 - 2 Months",
                "certificatetype": "Course",
                "crediteligibility": False
            }
        ]
    }
}

# Example 2: Using Model 1 legacy format (still supported)
payload_model1_legacy = {
    "persona_json": {
        "user_profile": {
            "timestamp": "2025-11-13T08:30:00Z",
            "user_id": "USR_20251113_003",
            "responses": {
                "Q1_current_status": {"question": "What best describes your current situation?", "answer": "Student"},
                "Q2_tech_familiarity": {"question": "How familiar are you with technology and digital tools?", "answer": "Very Comfortable"},
                "Q3_tech_experience": {"question": "Have you ever taken a course, training, or worked on a project related to tech?", "answer": "Yes"},
                "Q4_interest_area": {"question": "Which of these areas interests you the most?", "answer": "Building software and applications"},
                "Q5_motivation": {"question": "What motivates you most to pursue a tech career?", "answer": "Creating innovative solutions"},
                "Q6_skill_level": {"question": "How would you describe your current technical skill level?", "answer": "Beginner"},
                "Q7_project_experience": {"question": "Have you ever completed a personal or professional tech project?", "answer": "No"},
                "Q8_learning_preference": {"question": "How do you prefer to learn new skills?", "answer": "Online courses (Coursera, Udemy, etc.)"},
                "Q9_time_commitment": {"question": "How much time can you dedicate to learning weekly?", "answer": "3-6 hours"},
                "Q10_goal": {"question": "What is your main goal right now?", "answer": "Learn foundational skills"}
            }
        }
    },
    # LEGACY Model 1 format (still supported)
    "selected_role_json": {
        "role_id": "R06",
        "role_name": "Data Analyst",
        "score": 0.5129253349452318,
        "explanation": "The Data Analyst role is recommended because your strongest competencies align with what this role values most..."
    },
    "course_recommendations_json": {
        "role": "Data Analyst",
        "keywords_used": ["data", "analytics"],
        "courses": [
            {
                "course_title": "Introduction to Data Science",
                "platform": "IBM",
                "skills": "{\"data science\",\"python programming\"}",
                "rating": 4.7,
                "reviewcount": 581,
                "level": "beginner",
                "duration": "1 - 3 Months",
                "certificatetype": "Course",
                "crediteligibility": False
            }
        ]
    }
}

# Example 3: Using Model 2 legacy format (still supported)
payload_model2_legacy = {
    "persona_json": {
        "user_profile": {
            "timestamp": "2025-11-13T08:30:00Z",
            "user_id": "USR_20251113_004",
            "responses": {
                "Q1_current_status": {"question": "What best describes your current situation?", "answer": "Career Switcher"},
                "Q2_tech_familiarity": {"question": "How familiar are you with technology and digital tools?", "answer": "Comfortable"},
                "Q3_tech_experience": {"question": "Have you ever taken a course, training, or worked on a project related to tech?", "answer": "No"},
                "Q4_interest_area": {"question": "Which of these areas interests you the most?", "answer": "Building software and applications"},
                "Q5_motivation": {"question": "What motivates you most to pursue a tech career?", "answer": "Job security and stability"},
                "Q6_skill_level": {"question": "How would you describe your current technical skill level?", "answer": "Beginner"},
                "Q7_project_experience": {"question": "Have you ever completed a personal or professional tech project?", "answer": "No"},
                "Q8_learning_preference": {"question": "How do you prefer to learn new skills?", "answer": "Online courses (Coursera, Udemy, etc.)"},
                "Q9_time_commitment": {"question": "How much time can you dedicate to learning weekly?", "answer": "10+ hours"},
                "Q10_goal": {"question": "What is your main goal right now?", "answer": "Secure a tech job"}
            }
        }
    },
    # LEGACY Model 2 format (still supported)
    "selected_role_json": {
        "role_name": "Software Engineer",
        "score": 11.23
    },
    "course_recommendations_json": {
        "role": "Software Engineer",
        "keywords_used": ["software", "programming", "python", "java"],
        "courses": [
            {
                "course_title": "Introduction to Software Engineering",
                "platform": "IBM",
                "skills": "{\"software engineering\",\"computer programming\",\"python programming\"}",
                "rating": 4.7,
                "reviewcount": 581,
                "level": "beginner",
                "duration": "1 - 3 Months",
                "certificatetype": "Course",
                "crediteligibility": False
            }
        ]
    }
}

# Choose which payload to test
payload = payload_model2_legacy  # Change to test different formats

print("=" * 60)
print("Testing Action Plan Generator API")
print("=" * 60)
print(f"\nUsing format: {'NEW SIMPLIFIED' if payload == payload_new_format else 'LEGACY'}")
print(f"Selected Role: {payload['selected_role_json']}")
print("\nSending request to API...")

resp = requests.post(url, json=payload)

print(f"\n{'=' * 60}")
print(f"Status Code: {resp.status_code}")
print(f"{'=' * 60}")
print("\nResponse:")
print(json.dumps(resp.json(), indent=2))
import requests
import json

url = "http://127.0.0.1:9000/generate-action-plan"

# Example using Model 1 output format
payload_model1 = {
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
    # SELECTED ROLE from Model 1 (single object, not array)
    "selected_role_json": {
        "role_id": "R06",
        "role_name": "Data Analyst",
        "score": 0.5129253349452318,
        "explanation": "The Data Analyst role is recommended because your strongest competencies align with what this role values most..."
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

# Example using Model 2 output format
payload_model2 = {
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
    # SELECTED ROLE from Model 2 (single object, not array)
    "selected_role_json": {
        "role_name": "Software Engineer",
        "score": 11.23
    },
    # Course recommendations in new format
    "course_recommendations_json": {
        "role": "Software Engineer",
        "keywords_used": ["software", "programming", "python", "java", "c++", "oop"],
        "courses": [
            {
                "course_title": "Introduction to Software Engineering",
                "platform": "IBM",
                "skills": "{\"software engineering\",\"computer programming\",\"python programming\",\"agile software development\"}",
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
payload = payload_model1  # Change to payload_model2 to test Model 2 format

print("Sending request to API...")
resp = requests.post(url, json=payload)
print(f"\nStatus Code: {resp.status_code}")
print("\nResponse:")
print(json.dumps(resp.json(), indent=2))
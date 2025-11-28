
This folder focuses on **Personalized 6-Month Learning Action Plan Generation for Women Entering Tech**

**This API**:
- Accepts user persona data (base questions responses), selected tech role recommendation, and course recommendations
- Uses OpenAI's GPT-4o-mini to generate a structured, personalized 6-month learning roadmap
- Produces milestone-based action plans tailored to the user's time commitment, skill level, and learning preferences

**How it works**:
The three JSON inputs (persona profile, selected role, and course recommendations) are sent to the Flask API `API_action_plan/app.py`. The API processes these inputs through the `services/processing.py` module, which flattens and validates the data, infers learning constraints, and builds a comprehensive prompt. This prompt is then sent to the OpenAI API, which returns a structured JSON action plan with milestones, projects, and success metrics.

---

## Architecture Overview

### Input Processing Flow
1. **Raw Input Validation**: Three JSON objects are validated using Pydantic models
2. **Data Transformation**: `services/processing.py` normalizes and flattens the data
3. **Constraint Inference**: System automatically infers learning constraints based on user responses
4. **Prompt Building**: A detailed prompt is constructed with all user context
5. **LLM Generation**: OpenAI GPT-4o-mini generates the structured action plan
6. **Response Formatting**: The JSON response is validated and enhanced with metadata

### Key Components

**`app.py`**:
- Main Flask application server
- Handles API endpoint `/generate-action-plan`
- Manages OpenAI client initialization and LLM communication
- Validates and returns the final action plan JSON

**`services/processing.py`**:
- Flattens nested persona JSON into a structured format
- Normalizes selected role and course recommendation data
- Automatically infers learning constraints from user responses (availability, learning pace, difficulty, project requirements, format preferences)
- Builds the `ActionPlanRequest` payload for the LLM

---

## Running the Action Plan Generator API

### Prerequisites
Ensure you have the following installed:
- Python 3.12
- Required libraries (see `requirements.txt` below)

### Installation

1. Install dependencies:
```bash
pip install requirements.txt
```

2. Create a `.env` file in the `API_action_plan` folder:
```
OPENAI_API_KEY=your_openai_api_key_here
```

### Running the API Server

```bash
python API_action_plan/app.py
```

The server will start on `http://localhost:9000`

You should see:
```
OpenAI API connection successful
 * Running on http://0.0.0.0:9000
```

### Testing the API

**Recommended Method**: Use the provided test script
```bash
python API_action_plan/test_request.py
```

## API Endpoint

### `POST /generate-action-plan`

**Request Body**:
```json
{
  "persona_json": {
    "user_profile": {
      "timestamp": "2025-11-13T08:30:00Z",
      "user_id": "USR_20251113_002",
      "responses": {
        "Q1_current_status": {"question": "...", "answer": "Working Professional (Non-Tech)"},
        "Q2_tech_familiarity": {"question": "...", "answer": "Comfortable"},
        "Q3_tech_experience": {"question": "...", "answer": "Yes"},
        "Q4_interest_area": {"question": "...", "answer": "Working with data and insights"},
        "Q5_motivation": {"question": "...", "answer": "Problem-solving"},
        "Q6_skill_level": {"question": "...", "answer": "Intermediate"},
        "Q7_project_experience": {"question": "...", "answer": "Yes, small projects"},
        "Q8_learning_preference": {"question": "...", "answer": "Self-learning"},
        "Q9_time_commitment": {"question": "...", "answer": "7-10 hours"},
        "Q10_goal": {"question": "...", "answer": "Get certified / build portfolio"}
      }
    }
  },
  "selected_role_json": {
    "role_id": "R06",
    "role_name": "Data Analyst",
    "score": 0.5129253349452318,
    "explanation": "The Data Analyst role is recommended because..."
  },
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
        "crediteligibility": false
      }
    ]
  }
}
```

#### Input Field Details

**`persona_json`** (unchanged):
- Contains user profile with base questions responses
- Includes 10 questions (Q1-Q10) covering current status, tech familiarity, experience, interests, motivation, skill level, project experience, learning preference, time commitment, and goals

**`selected_role_json`** (supports 2 model formats):
- **IMPORTANT**: Must be a **single selected role object**, NOT an array of recommendations
- **Model 1 format** (with role_id):
```json
  {
    "role_id": "R06",
    "role_name": "Data Analyst",
    "score": 0.5129253349452318,
    "explanation": "The Data Analyst role is recommended..."
  }
```
- **Model 2 format** (without role_id):
```json
  {
    "role_name": "Software Engineer",
    "score": 11.23
  }
```
- Only `role_name` is required; `role_id`, `score`, and `explanation` are optional

**`course_recommendations_json`** (new nested structure):
- Wraps courses array with metadata
- Structure includes:
  - `role`: Target role name
  - `keywords_used`: Keywords used for course matching
  - `courses`: Array of course objects
- Course object fields:
  - `course_title`: Course name
  - `platform`: Platform offering the course (e.g., Google, IBM, Coursera)
  - `skills`: PostgreSQL array string format `{"skill1","skill2"}`
  - `rating`: Course rating (float)
  - `reviewcount`: Number of reviews (integer)
  - `level`: Difficulty level (beginner/intermediate/advanced)
  - `duration`: Time range (e.g., "1 - 3 Months", "1 - 4 Weeks")
  - `certificatetype`: Type of certificate
  - `crediteligibility`: Whether credit is eligible (boolean)

**Response** (200 OK):
```json
{
  "plan_meta": {
    "target_role": "Data Analyst",
    "start_date": null,
    "estimated_completion": "6 months",
    "weekly_commitment": "7-10 hours",
    "generated_at": "2025-11-25T10:30:00.000000"
  },
  "milestones": [
    {
      "milestone_number": 1,
      "title": "Foundations of Data Analysis",
      "duration_weeks": 6,
      "description": "Build core data analysis skills and learn SQL fundamentals",
      "learning_objectives": [
        "Understand data types and structures",
        "Write basic SQL queries",
        "Clean and prepare data for analysis"
      ],
      "recommended_courses": [
        {
          "name": "Google Data Analytics Professional Certificate",
          "platform": "Google",
          "duration_weeks": 12,
          "skill_focus": ["data analysis", "sql", "spreadsheets", "data visualization"],
          "difficulty": "Beginner",
          "rating": 4.8,
          "review_count": 15234
        }
      ],
      "projects": [
        {
          "project_name": "Sales Data Analysis Dashboard",
          "description": "Build an interactive dashboard analyzing sales trends",
          "skills_practiced": ["SQL", "Data Cleaning", "Visualization"]
        }
      ]
    }
  ],
  "success_metrics": {
    "technical_skills": ["SQL", "Python", "Data Visualization", "Statistical Analysis"],
    "soft_skills": ["Problem-solving", "Communication", "Critical Thinking"],
    "portfolio_items": ["Data Dashboard Project", "SQL Analysis Portfolio", "Customer Segmentation Analysis"]
  },
  "next_steps": [
    "Apply to entry-level Data Analyst positions",
    "Network with data professionals on LinkedIn",
    "Contribute to open-source data projects"
  ]
}
```

**Error Response** (400 Bad Request):
```json
{
  "error": "Input validation failed",
  "details": [
    {
      "loc": ["selected_role", "role_name"],
      "msg": "role_name is required",
      "type": "value_error"
    }
  ],
  "debug_note": "Check that your JSON structure matches the expected format"
}
```

---

## Testing with Different Inputs

> **Note**: Modify the `payload` dictionary in `test_request.py` to test different scenarios. The test file includes examples for both Model 1 and Model 2 formats.

### Testing Different Model Formats

**Model 1 Format** (with role_id):
```python
"selected_role_json": {
    "role_id": "R06",
    "role_name": "Data Analyst",
    "score": 0.5129253349452318,
    "explanation": "The Data Analyst role is recommended..."
}
```

**Model 2 Format** (without role_id):
```python
"selected_role_json": {
    "role_name": "Software Engineer",
    "score": 11.23
}
```

### Testing Different Persona Variations

**Test Limited Time Commitment**:
```python
"Q9_time_commitment": {"answer": "Less than 3 hours"}
```

**Test Different Skill Levels**:
```python
"Q6_skill_level": {"answer": "Beginner"}  # or "Intermediate" or "Expert"
```

**Test Different Roles**:
```python
# Model 1 format
"selected_role_json": {
    "role_id": "R01",
    "role_name": "Frontend Developer",
    "score": 0.48,
    "explanation": "..."
}

# Model 2 format
"selected_role_json": {
    "role_name": "Backend Engineer",
    "score": 10.54
}
```

### Testing Different Course Recommendations

**Test with Multiple Courses**:
```python
"course_recommendations_json": {
    "role": "Software Engineer",
    "keywords_used": ["software", "programming", "python"],
    "courses": [
        {
            "course_title": "Introduction to Software Engineering",
            "platform": "IBM",
            "skills": "{\"software engineering\",\"python programming\"}",
            "rating": 4.7,
            "reviewcount": 581,
            "level": "beginner",
            "duration": "1 - 3 Months",
            "certificatetype": "Course",
            "crediteligibility": False
        },
        {
            "course_title": "Python for Everybody",
            "platform": "University of Michigan",
            "skills": "{\"python programming\",\"data structures\"}",
            "rating": 4.9,
            "reviewcount": 23456,
            "level": "beginner",
            "duration": "1 - 2 Months",
            "certificatetype": "Specialization",
            "crediteligibility": True
        }
    ]
}
```

**Test with Empty Courses** (API will suggest generic resources):
```python
"course_recommendations_json": {
    "role": "Data Analyst",
    "keywords_used": [],
    "courses": []
}
```

**Test with No Course Recommendations** (set to `None`):
```python
"course_recommendations_json": None
```

### Quick Test Scenarios

Use the provided test script and switch between `payload_model1` and `payload_model2`:
```bash
# In test_request.py, change this line:
payload = payload_model1  # Test Model 1 format (with role_id)
# or
payload = payload_model2  # Test Model 2 format (without role_id)

# Then run:
python API_action_plan/test_request.py
```

---

### Important Notes

- **ONLY ONE ROLE**: The `selected_role_json` must be a single role object, not an array. Your frontend must select one role from the recommendations before calling this API.
- **Both Model Formats Supported**: The API automatically handles both tech role recommendation model outputs (Model 1 with `role_id` and Model 2 without).
- **Course Format**: The new nested structure with PostgreSQL array strings is automatically parsed and normalized.
- **Flexible**: If courses are not available, the LLM will suggest generic, verifiable resource categories marked as "suggested".
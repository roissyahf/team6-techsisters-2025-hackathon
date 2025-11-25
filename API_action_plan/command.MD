
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
    "score": 0.512,
    "explanation": "..."
  },
  "course_recommendations_json": [
    {
      "name": "Google Data Analytics",
      "platform": "Coursera",
      "duration_weeks": 8,
      "skill_focus": ["SQL", "Data Cleaning", "Spreadsheets"],
      "difficulty": "Beginner"
    }
  ]
}
```

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
      "description": "...",
      "learning_objectives": ["..."],
      "recommended_courses": [...],
      "projects": [...]
    }
  ],
  "success_metrics": {
    "technical_skills": ["SQL", "Python", "Data Visualization"],
    "soft_skills": ["Problem-solving", "Communication"],
    "portfolio_items": ["Data Dashboard Project", "SQL Analysis Portfolio"]
  },
  "next_steps": ["Apply to entry-level positions", "Network on LinkedIn"]
}
```

**Error Response** (400 Bad Request):
```json
{
  "error": "Error description",
  "debug_note": "Ensure the LLM returned valid JSON. Check OPENAI_API_KEY and network connectivity."
}
```


## Testing with Different Inputs

> **Note**: Modify the `payload` dictionary in `test_request.py` to test different user profiles:
> - Change `Q9_time_commitment` to test different weekly availability scenarios
> - Change `Q6_skill_level` to test different expertise levels (Beginner/Intermediate/Expert)
> - Change `selected_role_json` to test different tech roles
> - Modify `course_recommendations_json` to test with different course sets (or empty array)

Example modification:
```python
# In test_request.py, change these values:
"Q9_time_commitment": {"answer": "Less than 3 hours"},  # Test limited time
"Q6_skill_level": {"answer": "Beginner"},                # Test beginner level
"selected_role_json": {"role_id": "R01", "role_name": "Frontend Developer", ...}
```
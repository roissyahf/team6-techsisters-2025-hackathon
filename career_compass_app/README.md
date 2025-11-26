# Career Compass (Flask + PostgreSQL)

Replaces Books schema with a normalized survey schema for Career Compass.

## Setup
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Create DB (adjust user as needed)
createdb career_compass

export FLASK_APP=manage.py
flask db init            # only if migrations/ doesn't exist yet
flask db upgrade         # applies career_compass_init
```
API:
- POST /api/categories {name, description?, position?}
- GET  /api/categories
- POST /api/questions {category_id, prompt, type, is_required?, position?, meta?}
- GET  /api/questions
- POST /api/choices {question_id, label, value, position?, meta?}
- GET  /api/choices

Valid question types: single, multi, scale, text, boolean, number

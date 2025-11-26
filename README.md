# Compassly
_Add description_



## Key Features & Components
_Add description_



## Project Architecture
_Add description_



## Repository Structure
_Add description_



## Set up & Installation
### Prerequisites
_Add description_

### Installation
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Running the App
_Add description_

### [1] Full-stack
Create DB (adjust user as needed)
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
```

## [2] _Add more_
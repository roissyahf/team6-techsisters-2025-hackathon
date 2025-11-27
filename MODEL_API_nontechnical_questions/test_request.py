import sys
from pathlib import Path

# Get the path of the current file being executed
FILE = Path(__file__).resolve()
# Determine the project root directory
ROOT = FILE.parent.parent 
# Add the project root to Python's search path
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from utils.path_helpers import get_absolute_path
import requests
import json

# === Configuration ===
BASE_FILE = get_absolute_path('base_questions', 'sample_2.json') # adjust accordingly
DYNAMIC_FILE = get_absolute_path(
    'API_dynamic_questions', 
    'ANSWER_RESPONSE_dynamic_questions', 
    'NEW_SAMPLE_2_answer_dynamic_questions.json'
) # adjust accordingly

API_URL = "http://127.0.0.1:8080/recommend"

with open(BASE_FILE) as f:
    base = json.load(f)

with open(DYNAMIC_FILE) as f:
    dyn = json.load(f)

payload = {
    "base_persona_data": base,
    "dynamic_questions_data": dyn
}

resp = requests.post(
    "http://127.0.0.1:8080/recommend",
    json=payload
)

print(resp.status_code)
print(resp.text)
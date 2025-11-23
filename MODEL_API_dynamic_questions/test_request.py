import requests
import json

API_URL = "http://127.0.0.1:8080/recommend"

# change the file path accordingly based on which sample you want to test
BASE_FILE = "base_questions/sample_4.json"
DYNAMIC_FILE = "ANSWER_RESPONSE_dynamic_questions/NEW_SAMPLE_4_answer_dynamic_questions.json"

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

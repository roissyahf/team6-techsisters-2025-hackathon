import json
import requests

API_URL = "http://localhost:5005/recommend"

def main():
    # Load a sample base question file
    with open("base_questions/sample.json", "r", encoding="utf-8") as f:
        base_profile = json.load(f)

    technical_answers = {
        "T1_programming": 4,
        "T2_problem_solving": 4,
        "T3_debugging": 3,
        "T4_system_understanding": 3,
        "T5_tools_familiarity": 3
    }

    payload = {
        "base_profile": base_profile,
        "technical_answers": technical_answers
    }

    res = requests.post(API_URL, json=payload)
    print("Status:", res.status_code)
    print("Response:")
    print(json.dumps(res.json(), indent=4))

if __name__ == "__main__":
    main()

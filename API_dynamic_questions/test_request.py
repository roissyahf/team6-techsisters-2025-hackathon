import requests
import json
import os

# === Configuration ===
INPUT_FILE = "base_questions/sample_1.json" # adjust accordingly
OUTPUT_DIR = "RESPONSE_dynamic_questions"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "SAMPLE_1_generated_dynamic_questions.json")  # adjust accordingly
API_URL = "http://localhost:7070/generate_dynamic_questions"

# === Ensure output directory exists ===
os.makedirs(OUTPUT_DIR, exist_ok=True)

# === Load local JSON input ===
with open(INPUT_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

# === Send POST request to Flask API ===
try:
    response = requests.post(API_URL, headers={"Content-Type": "application/json"}, json=data)
    response.raise_for_status()  # Raise error if request failed
except requests.exceptions.RequestException as e:
    print(f"Request failed: {e}")
    exit(1)

# === Parse and save output JSON ===
try:
    result = response.json()
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"Response saved successfully to: {OUTPUT_FILE}")
except json.JSONDecodeError:
    print("Failed to parse response as JSON.")
    print("Raw response:", response.text)

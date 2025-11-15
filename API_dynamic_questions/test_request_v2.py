import requests
import json
import os

# === Configuration ===
INPUT_FILE = "base_questions/sample_6.json" # adjust accordingly
OUTPUT_DIR = "RESPONSE_dynamic_questions"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "SAMPLE_6_generated_dynamic_questions.json")  # adjust accordingly
API_URL = "http://localhost:7070/generate_dynamic_questions"

# === Ensure output directory exists ===
os.makedirs(OUTPUT_DIR, exist_ok=True)

# === Load local JSON input ===
with open(INPUT_FILE, "r", encoding="utf-8") as f:
    user_base_json = json.load(f)

# === Send POST request ===
try:
    response = requests.post(API_URL, headers={"Content-Type": "application/json"}, json=user_base_json)
    print(f"Status Code: {response.status_code}")
except requests.exceptions.RequestException as e:
    print(f"❌ Request failed: {e}")
    exit(1)

# === Handle Response ===
try:
    result = response.json()
    # Save to file
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"✅ Response saved to {OUTPUT_FILE}")
except json.JSONDecodeError:
    print("❌ Response is not valid JSON.")
    print("Raw response:", response.text)
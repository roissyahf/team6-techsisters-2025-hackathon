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
import os

# === Configuration ===
INPUT_FILE_PATH = get_absolute_path('base_questions', 'sample_1.json') # adjust accordingly
OUTPUT_DIR_PARTS = ['API_dynamic_technical_questions', 'RESPONSE_SAMPLE']
OUTPUT_FILENAME = "response_1.json" # adjust accordingly
OUTPUT_FILE_PATH = get_absolute_path(*OUTPUT_DIR_PARTS, OUTPUT_FILENAME)

API_URL = "http://localhost:7075/dynamic-technical-questions"

# === Ensure output directory exists ===
os.makedirs(get_absolute_path(*OUTPUT_DIR_PARTS), exist_ok=True)

# === Load local JSON input ===
with open(INPUT_FILE_PATH, "r", encoding="utf-8") as f:
    user_base_json = json.load(f)

# === Send POST request ===
try:
    response = requests.post(API_URL, headers={"Content-Type": "application/json"}, json=user_base_json)
    print(f"Status Code: {response.status_code}")
except requests.exceptions.RequestException as e:
    print(f"Request failed: {e}")
    exit(1)

# === Handle Response ===
try:
    result = response.json()
    # Save to file
    with open(OUTPUT_FILE_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"Response saved to {OUTPUT_FILE_PATH}")
except json.JSONDecodeError:
    print("Response is not valid JSON.")
    print("Raw response:", response.text)
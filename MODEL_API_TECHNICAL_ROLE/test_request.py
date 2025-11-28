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

BASE_DIR = Path(__file__).resolve().parents[1]

# --- 1. Configuration ---
# The API runs on port 5010 as defined in app.py, and the endpoint is /recommend-role
API_URL = "http://127.0.0.1:5010/recommend-role"

# Define the paths to the JSON input files
BASE_ANSWER_PATH = get_absolute_path('base_questions', 'sample_2.json')
TECHNICAL_ANSWERS_PATH = get_absolute_path('MODEL_API_TECHNICAL_ROLE', 'technical_questions_answer.json')

# --- 2. Load JSON Data ---
try:
    with open(BASE_ANSWER_PATH, 'r') as f:
        base_profile_data = json.load(f)
    
    with open(TECHNICAL_ANSWERS_PATH, 'r') as f:
        technical_answers_data = json.load(f)

except FileNotFoundError as e:
    print(f"Error: Required file not found. Please ensure {e.filename} exists.")
    exit()
except json.JSONDecodeError:
    print("Error: Could not decode JSON from one of the input files.")
    exit()

# --- 3. Construct the API Payload ---
# The API expects one JSON body with keys "base_profile" and "technical_answers"
payload = {
    "base_profile": base_profile_data,
    "technical_answers": technical_answers_data
}

# --- 4. Send the POST Request ---
print(f"Sending POST request to: {API_URL}")
print("Payload keys:", payload.keys())
print("-" * 30)

try:
    # Use the json parameter for requests, which automatically sets the Content-Type
    resp = requests.post(API_URL, json=payload)

    # --- 5. Print Results ---
    print(f"Status Code: {resp.status_code}")
    
    if resp.status_code == 200:
        print("Success! Response JSON:")
        # Pretty print the JSON response
        print(json.dumps(resp.json(), indent=4))
    else:
        print("Error response received:")
        # Print the response text for debugging
        print(resp.text)

except requests.exceptions.ConnectionError:
    print("\nConnection Error!")
    print(f"Please ensure your Flask API is running at {API_URL} (run 'python app.py' in the MODEL_API_TECHNICAL_ROLE directory first).")
except Exception as e:
    print(f"\nAn unexpected error occurred: {e}")
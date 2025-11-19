import requests
import json
import os

# 1. Define the API endpoint URL
API_URL = "http://127.0.0.1:8080/api/v1/recommend"

# 2. Define the path to sample data files
BASE_DATA_PATH = "base_questions/sample_3.json"
DYNAMIC_DATA_PATH = "ANSWER_RESPONSE_dynamic_questions/SAMPLE_3_answer_dynamic_questions.json"

def load_sample_data(filepath):
    """Loads JSON data from a file."""
    if not os.path.exists(filepath):
        print(f"Error: File not found at {filepath}")
        return None
    with open(filepath, 'r') as f:
        return json.load(f)

def run_test():
    """Constructs the payload and sends the POST request to the API."""
    
    base_data = load_sample_data(BASE_DATA_PATH)
    dynamic_data = load_sample_data(DYNAMIC_DATA_PATH)
    
    if not base_data or not dynamic_data:
        print("\nTest failed: Could not load required input data.")
        return

    # The final payload structure required by app.py
    payload = {
        "base_persona_data": base_data,
        "dynamic_questions_data": dynamic_data
    }

    print(f"Sending POST request to {API_URL}...")
    
    try:
        # Send the request
        response = requests.post(
            API_URL, 
            json=payload, 
            headers={"Content-Type": "application/json"}
        )
        
        # Check the response status code
        if response.status_code == 200:
            print("\n API Test Successful!")
            print("--- Top 10 Recommendations ---")
            
            # Print the formatted JSON response
            data = response.json()
            for i, rec in enumerate(data.get('recommendations', [])[:10], 1):
                print(f"{i}. {rec['role_name']} (Score: {rec['score']:.4f})")
                
        else:
            print(f"\n API Test Failed with Status Code: {response.status_code}")
            print("Response Body:")
            print(json.dumps(response.json(), indent=4))

    except requests.exceptions.ConnectionError:
        print("\n Connection Error: Ensure your Flask app is running at the specified URL.")
    except Exception as e:
        print(f"\n An unexpected error occurred: {e}")

if __name__ == "__main__":
    run_test()
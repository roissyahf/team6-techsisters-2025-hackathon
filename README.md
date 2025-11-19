# Tech Role Recommendation For Non Technical User: Dynamic Questions Generation & Hybrid Model


This repository presents a solution for recommending suitable technology roles to non-technical users. It utilizes a two-pronged approach: Dynamic Question Generation to build a rich user persona, and a Hybrid Recommendation Model to map the user's profile to relevant tech roles.


## Key Features & Components
This project focuses on two core technical areas:
1. Dynamic Question Generation:
- Generates follow-up questions tailored to a user's initial responses (persona).
- Implemented as a Flask API leveraging a Large Language Model (LLM) for question creativity.

2. Hybrid Recommendation System:
- Combines Weighted Score Modeling (WSM) for quantitative data (aptitude/constraints) and Content-Based Filtering (TF-IDF similarity) for qualitative text data (skills/preferences).
- The model calculates a final score for accurate role recommendation.


## Project Architecture
The system follows a sequential flow:
1. **Initial Survey Input**: User provides answers to a set of base questions (aptitude, background).
2. **Dynamic Question API**: The base answers are fed to the Flask API (`API_dynamic_questions/app_v2.py`), which uses an LLM to generate dynamic questions to capture nuanced skills and expectations.
3. **User Response Collection**: User answers the dynamic questions.
4. **Data Processing**: The base and dynamic responses are merged, cleaned, and transformed into a final payload ready for modeling (`MODEL_dynamic_questions/processing.py`).
5. **Hybrid Modeling**: The `MODEL_dynamic_questions/model.py` script consumes the final payload, applying the Weighted Score Model and TF-IDF similarity to calculate the top role recommendations.


## Repository Structure
```
├───ANSWER_RESPONSE_dynamic_questions				# sample answers to the dynamic questions
│       SAMPLE_1_answer_dynamic_questions.json
│       SAMPLE_2_answer_dynamic_questions.json
│       SAMPLE_3_answer_dynamic_questions.json
│       SAMPLE_answer_dynamic_questions.json
│
├───API_dynamic_questions							
│       app.py
│       app_v2.py									# final dynamic questions API
│       prompt.py
│       test_request.py
│       test_request_v2.py							# script to test the dynamic questions API
│
├───base_questions									# sample base questions response
│       sample.json
│       sample_1.json
│       sample_2.json
│       sample_3.json
│       sample_4.json
│       sample_5.json
│       sample_6.json
│
├───FINAL_PAYLOAD									# sample processed payload (input for model.py)
│       final_processed_expectation.json
│       SAMPLE_1_final_payload.json
│       SAMPLE_2_final_payload.json
│       SAMPLE_final_payload.json
│
├───MODEL_dynamic_questions
│       model.py									# modeling logic
│       processing.py								# processing logic
│
├───pickle_file
│       role_tfidf_matrix.pkl						# role_ids, matrix
│       tfidf.pkl									# vectorizer
│
├───RESPONSE_dynamic_questions						# sample generated dynamic questions (API output)
│       SAMPLE_1_generated_dynamic_questions.json
│       SAMPLE_2_generated_dynamic_questions.json
│       SAMPLE_3_generated_dynamic_questions.json
│       SAMPLE_4_generated_dynamic_questions.json
│       SAMPLE_5_generated_dynamic_questions.json
│       SAMPLE_6_generated_dynamic_questions.json
│       SAMPLE_generated_dynamic_questions.json
│
└───static_data
        constraints.json			# constraints of user needs & background
        descriptions.json			# 30 tech roles description 
        roles.json				# Aptitude score for each role
```

## Set up & Installation
### Prerequisites

You will need an **OpenAI API Key** to run the Dynamic Questions API.

Visit https://platform.openai.com/api-keys to get your key.

Create a file named `.env` in the root directory and securely store your key (e.g., OPENAI_API_KEY=YOUR_KEY_HERE).

### Installation
1. Clone the repository
```bash
git clone https://github.com/roissyahf/team6-techsisters-2025-hackathon
cd dynamic-questions-branch
```

2. Create and activate virtual environment (optional but recommended)
```bash
python -m venv venv
source venv/bin/activate    # On Windows: venv\Scripts\activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

### Running the Project
### 1. **Dynamic Questions API**
This Flask application uses the OpenAI API to generate dynamic questions based on the user's initial responses, capturing their persona, skills, and expectations.

- Run the API Server
```bash
python API_dynamic_questions/app_v2.py
```
The server will start on http://localhost:7070

- Test the API (Recommended Method): Use the provided test script
```bash
python API_dynamic_questions/test_request_v2.py
```

- Test via curl
```bash
curl -X POST http://localhost:7070/generate_dynamic_questions -H "Content-Type: application/json" -d "@base_questions/sample_1.json"
```

>> Note: Change sample_1.json to any file in the `base_questions` folder to test different initial inputs.


### **2. Data Processing Script**
This step transforms the raw base and dynamic question responses into a unified input payload for the recommendation model.
```bash
python model/processing.py --base base_questions/sample.json --dynamic ANSWER_RESPONSE_dynamic_questions/SAMPLE_answer_dynamic_questions.json --output FINAL_PAYLOAD/SAMPLE_final_payload.json
```

>> Note: Update the file paths (`--base, --dynamic, --output`) as needed.


### **3. Hybrid Recommendation Model**
This script runs the core recommendation logic, combining Weighted Sum Modeling (WSM) for quantitative scores and Content-Based Filtering (TF-IDF) for qualitative text similarity.
```bash
python MODEL_dynamic_questions/model.py --final_payload_path FINAL_PAYLOAD/SAMPLE_final_payload.json
```

>> Note: The `--final_payload_path` must point to the output file generated by the processing script.

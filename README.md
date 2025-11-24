# Tech Role Recommendation For Non Technical User: Dynamic Questions Generation & Hybrid Model
This repository presents a solution for **recommending suitable technology roles to non-technical users**. It utilizes a two-pronged approach: Dynamic Question Generation to build a rich user persona, and a Hybrid Recommendation Model to map the user's profile to relevant tech roles.


## Key Features & Components
This project focuses on two core technical areas:
1. **Dynamic Question Generation**:
- Generates follow-up questions tailored to a user's initial responses (persona).
- Implemented as a Flask API leveraging a Large Language Model (LLM) for question creativity.

2. **Hybrid Recommendation System**:
- Combines Weighted Score Modeling (WSM) for quantitative data (aptitude/constraints) and Content-Based Filtering (TF-IDF similarity) for qualitative text data (skills/preferences).
- The model calculates a final score for accurate role recommendation.


## Project Architecture
The system follows a sequential flow:
1. **Initial Survey Input**: User provides answers to a set of base questions (interest, background).
2. **Dynamic Question API**: The base questions answers are fed to the Flask API (`API_dynamic_questions/app.py`), which uses an LLM to generate dynamic questions to capture nuanced skills and expectations.
3. **User Response Collection**: User answers the dynamic questions.
4. **Hybrid Modeling API**: The base questions answers & dynamic queastions answer are fed to the Flask API `MODEL_API_dynamic_questions/app.py`, it will process the answers, then apply the Weighted Scoring Model and TF-IDF similarity to calculate the top role recommendations.


## Repository Structure
```
│   README.md
│   requirements.txt									# list of python library used
│
├───ANSWER_RESPONSE_dynamic_questions					# sample answers to the dynamic questions
│       NEW_SAMPLE_1_answer_dynamic_questions.json
│       NEW_SAMPLE_2_answer_dynamic_questions.json
│       NEW_SAMPLE_3_answer_dynamic_questions.json
│       NEW_SAMPLE_4_answer_dynamic_questions.json
│       NEW_SAMPLE_5_answer_dynamic_questions.json
│       NEW_SAMPLE_6_answer_dynamic_questions.json
│       NEW_SAMPLE_answer_dynamic_questions.json
│
├───API_dynamic_questions
│       app.py											# final dynamic questions API
│       test_request.py									# script to test the dynamic questions API
│
├───base_questions										# sample base questions response
│       sample.json
│       sample_1.json
│       sample_2.json
│       sample_3.json
│       sample_4.json
│       sample_5.json
│       sample_6.json
│
├───FINAL_PAYLOAD										# sample processed payload (input for the hybrid model)
│       NEW_SAMPLE_1_final_payload.json
│       NEW_SAMPLE_2_final_payload.json
│       NEW_SAMPLE_3_final_payload.json
│       NEW_SAMPLE_4_final_payload.json
│       NEW_SAMPLE_5_final_payload.json
│       NEW_SAMPLE_6_final_payload.json
│       NEW_SAMPLE_final_payload.json
│
├───MODEL_API_dynamic_questions
│   │   app.py											# API for the hybrid model
│   │   test_request.py									# script to test the hybrid model API
│   └───services
│       │   processing_engine.py
│       │   recommender_engine.py
│       │   rec_explanation.py
│
├───pickle_file
│       role_tfidf_matrix_upd.pkl						# updated role_ids, matrix
│       tfidf_upd.pkl									# updated vectorizer
│
├───RESPONSE_dynamic_questions							# sample generated dynamic questions (API output)
│       NEW_SAMPLE_1_generated_dynamic_questions.json
│       NEW_SAMPLE_2_generated_dynamic_questions.json
│       NEW_SAMPLE_3_generated_dynamic_questions.json
│       NEW_SAMPLE_4_generated_dynamic_questions.json
│       NEW_SAMPLE_5_generated_dynamic_questions.json
│       NEW_SAMPLE_6_generated_dynamic_questions.json
│       NEW_SAMPLE_generated_dynamic_questions.json
│
├───scripts
│       build_tfidf.py									# script to build TF-IDF vectorizer
│       sanity_check_roles.py							# script to check role id alignment
│       test_tfidf.py									# script to test the TF-IDF pipeline
│
├───static_data
│       descriptions_upd.json							# updated 30 tech roles description 
│       roles_upd.json									# updated aptitude score for 30 tech roles
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

2. Create and activate virtual environment with `Python version 3.12.x` (optional but recommended)
```bash
python -m venv venv
source venv/bin/activate    # On Windows: venv\Scripts\activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

### Running the Project
### 1. **Dynamic Questions Generation API**
This Flask application uses the OpenAI API to generate dynamic questions based on the user's initial responses, capturing their persona, skills, and expectations.

- Run the API Server
```bash
python API_dynamic_questions/app.py
```
The server will start on http://localhost:7070

- Test the API (Recommended Method): Use the provided test script
```bash
python API_dynamic_questions/test_request.py
```

- Test via curl
```bash
curl -X POST http://localhost:7070/generate_dynamic_questions -H "Content-Type: application/json" -d "@base_questions/sample_1.json"
```

> Note: Change `sample_1.json` to any file in the `base_questions` folder to test different initial inputs.


### **2. Hybrid Recommendation Model API**
- It will receive 2 JSON files: `base_questions` response answer & `dynamic_questions` response answer
- Then the `services/processing_engine.py` will transform the raw base and dynamic question responses into a unified input payload for the recommendation model.
- Next, `services/recommender_engine.py` runs the core recommendation logic, combining Weighted Sum Modeling (WSM) for quantitative scores and Content-Based Filtering (TF-IDF) for qualitative text similarity, returning top n tech role recommendation along with the explanation.

- Run the API Server
```bash
python MODEL_API_dynamic_questions/app.py
```
The server will start on http://localhost:8080

- Test the API (Recommended Method): Use the provided test script
```bash
python MODEL_API_dynamic_questions/test_request.py
```

> Note: Change `BASE_FILE` to any file in the `base_questions`, and change the `DYNAMIC_FILE` to any file in `ANSWER_RESPONSE_dynamic_questions` folder to test different initial inputs.
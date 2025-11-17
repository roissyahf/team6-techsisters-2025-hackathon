# Tech Role Recommendation For Non Technical User: Dynamic Questions Generation & Hybrid Model

## This a repository contains
- sample input base questions
- sample input base questions answer response
- sample dynamic questions based on base questions answer response
- sample dynamic questions answer response
- dynamic questions API
- processing script
- TF-IDF pickle for 30 role descriptions
- sample final payload, ready to be used as modeling input
- modeling logic to recommend tech roles

## Project Structure
```
├───ANSWER_RESPONSE_dynamic_questions				# sample dynamic questions answer response
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
├───base_questions									# sample base questions
│       sample.json
│       sample_1.json
│       sample_2.json
│       sample_3.json
│       sample_4.json
│       sample_5.json
│       sample_6.json
│
├───FINAL_PAYLOAD									# sample final payload
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
├───RESPONSE_dynamic_questions						# sample dynamic questions answer response
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

## How to Run:
_to be continued_

### Running the Dynamic Questions API

### Running the processing script

### Running the modeling script
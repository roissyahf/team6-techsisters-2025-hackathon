This folder focus on **Tech Roles Hybrid Recommendation for Non-technical Users API**

**This model**:
- Combines Weighted Score Modeling (WSM) for quantitative data (aptitude/constraints) and Content-Based Filtering (TF-IDF similarity) for qualitative text data (skills/preferences).
- The model calculates a final score for accurate role recommendation.

**How it works**:
The base questions answers & dynamic queastions answer are fed to the Flask API `MODEL_API_nontechnical_questions/app.py`, it will process the answers, then apply the Weighted Scoring Model and TF-IDF similarity to calculate the top role recommendations.


### Running the Hybrid Recommendation Model API for non technical users
- It will receive 2 JSON files: `base_questions` response answer & `dynamic_questions` response answer
- Then the `services/processing_engine.py` will transform the raw base and dynamic question responses into a unified input payload for the recommendation model.
- Next, `services/recommender_engine.py` runs the core recommendation logic, combining Weighted Sum Modeling (WSM) for quantitative scores and Content-Based Filtering (TF-IDF) for qualitative text similarity, returning top n tech role recommendation along with the explanation.

- Run the API Server
```bash
python MODEL_API_nontechnical_questions/app.py
```
The server will start on http://localhost:8080

- Test the API (Recommended Method): Use the provided test script
```bash
python MODEL_API_nontechnical_questions/test_request.py
```

> Note: Change `BASE_FILE` to any file in the `base_questions`, and change the `DYNAMIC_FILE` to any file in `API_dynamic_questions/ANSWER_RESPONSE_dynamic_questions` folder to test different initial inputs.
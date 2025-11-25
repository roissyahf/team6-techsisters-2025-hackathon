from flask import Flask, request, jsonify
from services.recommender_engine_role import run_role_pipeline

app = Flask(__name__)

@app.post("/recommend-role")
def recommend_role():
    """
    API for recommending tech roles for technical users.
    """
    data = request.get_json()
    result = run_role_pipeline(data)
    return jsonify(result)

if __name__ == "__main__":
    app.run(port=5010, debug=True)

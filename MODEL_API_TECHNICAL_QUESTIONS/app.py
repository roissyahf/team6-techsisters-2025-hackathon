import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from flask import Flask, request, jsonify
from services.recommender_engine import run_pipeline

app = Flask(__name__)

@app.route("/recommend", methods=["POST"])
def recommend():
    """
    Expect payload:
    {
        "base_profile": {...},   # same structure as sample.json
        "technical_answers": {...}  # { "T1_programming": 4, ... }
    }
    """
    data = request.get_json()
    result = run_pipeline(data)
    return jsonify(result)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5005, debug=True)

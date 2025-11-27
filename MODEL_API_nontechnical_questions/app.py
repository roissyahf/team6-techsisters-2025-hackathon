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
from flask import Flask, request, jsonify
from pathlib import Path
import pickle
from services.processing_engine import merge_for_model
from services.recommender_engine import recommend, load_json_data


app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parents[1]

STATIC_DATA_PATH = get_absolute_path("MODEL_API_nontechnical_questions", "static_data")
PICKLE_PATH = get_absolute_path("MODEL_API_nontechnical_questions", "pickle_file")

# --------------------------------------------------
# Preload static resources ONCE
# --------------------------------------------------

try:
    ROLES = load_json_data(STATIC_DATA_PATH / "roles_upd.json")
    DESCRIPTIONS = load_json_data(STATIC_DATA_PATH / "descriptions_upd.json")

    with open(PICKLE_PATH / "tfidf_upd.pkl", "rb") as f:
        VECTORIZER = pickle.load(f)

    with open(PICKLE_PATH / "role_tfidf_matrix_upd.pkl", "rb") as f:
        ROLE_IDS, ROLE_TFIDF_MATRIX = pickle.load(f)

    # Align roles with role_ids
    ROLES_BY_ID = {r["role_id"]: r for r in ROLES}

     # Fix: sanity check role IDs
    missing = [rid for rid in ROLE_IDS if rid not in ROLES_BY_ID]
    if missing:
        print("\n Mismatched role_ids vs roles.json:")
        for m in missing:
            print("   -", m)
        raise ValueError("Role ID mismatch detected. Fix your roles.json.")

    ORDERED_ROLES = [ROLES_BY_ID[rid] for rid in ROLE_IDS]

    print("Assets loaded successfully.")

except Exception as e:
    print("\n ERROR loading model assets:", e)
    raise e


# --------------------------------------------------
#                 API ENDPOINT
# --------------------------------------------------
@app.route("/recommend", methods=["POST"])
def recommend_roles():
    """
    Input:
    {
        "base_persona_data": {...},
        "dynamic_questions_data": {...}
    }
    """

    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON input"}), 400

        base_data = data.get("base_persona_data")
        dynamic_data = data.get("dynamic_questions_data")

        if not base_data or not dynamic_data:
            return jsonify({
                "error": "Missing 'base_persona_data' or 'dynamic_questions_data'."
            }), 400

    except Exception as e:
        return jsonify({"error": f"Failed to parse input JSON: {e}"}), 400

    try:
        # 1) Build the final_payloa
        final_payload = merge_for_model(base_data, dynamic_data)

        # 2) Generate recommendations
        top_roles = recommend(
            final_payload=final_payload,
            roles=ORDERED_ROLES,
            vectorizer=VECTORIZER,
            role_ids=ROLE_IDS,
            role_tfidf_matrix=ROLE_TFIDF_MATRIX
        )

    except Exception as e:
        print("Error while generating recommendations:", e)
        return jsonify({"error": "Internal processing error"}), 500

    return jsonify({
        "status": "success",
        "top_recommendations": top_roles
    }), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
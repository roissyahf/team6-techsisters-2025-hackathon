from flask import Flask, request, jsonify
from .services import recommender_engine

app = Flask(__name__)


@app.route('/api/v1/recommend', methods=['POST'])
def recommend_roles():
    """
    API endpoint to receive user input and return role recommendations.
    Expected JSON body structure:
    {
        "base_persona_data": { ... base questions response json ... },
        "dynamic_questions_data": { ... dynamic questions response json ... }
    }
    """
    
    # 1. Receive and Parse Input
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON input"}), 400
            
        base_data = data.get("base_persona_data")
        dynamic_data = data.get("dynamic_questions_data")
        
        if not base_data or not dynamic_data:
            return jsonify({"error": "Missing 'base_persona_data' or 'dynamic_questions_data' in the request body."}), 400

    except Exception as e:
        # Catch JSON parse errors, etc.
        return jsonify({"error": f"Error processing input: {e}"}), 400
        
    # 2. Delegate to Service Layer (The CORE LOGIC)
    try:
        # Call the single function that does all the heavy lifting
        recommendations = recommender_engine.get_recommendations(
            base_data, 
            dynamic_data
        )
        
    except Exception as e:
        # Catch errors from the recommender engine (e.g., missing keys, numpy errors)
        print(f"Service Layer Error: {e}")
        return jsonify({"error": "An internal error occurred during recommendation generation."}), 500

    # 3. Return Response
    return jsonify({
        "status": "success",
        "recommendations": recommendations
    }), 200

#if __name__ == '__main__':
# app.run(debug=True, host='0.0.0.0', port=8080)
from flask import Flask, request, jsonify
from services.recommender_engine_course import recommend_courses

app = Flask(__name__)

@app.post("/recommend-course")
def recommend_course():
    """
    API for recommending courses for a selected tech role.
    """
    data = request.get_json()
    result = recommend_courses(data)
    return jsonify(result)

if __name__ == "__main__":
    app.run(port=5011, debug=True)

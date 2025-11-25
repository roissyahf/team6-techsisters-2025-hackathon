import sys
from pathlib import Path

# Get the path of the current file being executed
FILE = Path(__file__).resolve()
# Determine the project root directory
ROOT = FILE.parent.parent.parent
# Add the project root to Python's search path
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))


from utils.path_helpers import get_absolute_path
# one-time script to generate TF-IDF assets
import json
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer

roles_description_path = get_absolute_path("MODEL_API_nontechnical_questions", "static_data", "descriptions_upd.json")
vectorizer_path = get_absolute_path("MODEL_API_nontechnical_questions", "pickle_file", "tfidf_upd.pkl")
matrix_path = get_absolute_path("MODEL_API_nontechnical_questions", "pickle_file", "role_tfidf_matrix_upd.pkl")


def build_tfidf():
    with open(roles_description_path, "r") as f:
        descriptions = json.load(f)

    role_ids = list(descriptions.keys())
    texts = list(descriptions.values())

    vectorizer = TfidfVectorizer(
        stop_words="english",
        max_features=8000,
        ngram_range=(1, 2),
        min_df=1
    )

    matrix = vectorizer.fit_transform(texts)

    # Save vectorizer & matrix
    pickle.dump(vectorizer, open(vectorizer_path, "wb"))
    pickle.dump((role_ids, matrix), open(matrix_path, "wb"))

    print("TF-IDF build completed.")

if __name__ == "__main__":
    build_tfidf()
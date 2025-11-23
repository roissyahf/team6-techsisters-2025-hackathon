# one-time script to generate TF-IDF assets

import json
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer

def build_tfidf():
    with open("static_data/descriptions_upd.json", "r") as f:
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
    pickle.dump(vectorizer, open("pickle_file/tfidf_upd.pkl", "wb"))
    pickle.dump((role_ids, matrix), open("pickle_file/role_tfidf_matrix_upd.pkl", "wb"))

    print("TF-IDF build completed.")

if __name__ == "__main__":
    build_tfidf()
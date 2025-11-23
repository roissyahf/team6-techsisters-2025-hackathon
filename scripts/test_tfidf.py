import numpy as np
import pickle
import json
import os


# ============================================================
# 1. Extract dynamic_text from a JSON payload
# ============================================================

def extract_dynamic_text(file_path):
    """
    Reads JSON, extracts 'dynamic_text', prints clean readable output.
    """
    print("\n" + "="*80)
    print(" STEP 1 — LOAD USER DYNAMIC TEXT ")
    print("="*80)

    if not os.path.exists(file_path):
        print(f"[ERROR] File not found: {file_path}")
        return None

    try:
        with open(file_path, "r") as f:
            payload = json.load(f)

        user_text = payload["dynamic_text"]

        print("\n[✓] Successfully extracted `dynamic_text` from:")
        print(f"    {file_path}")
        print("-"*80)
        print(user_text)
        print("-"*80)

        return user_text

    except json.JSONDecodeError:
        print("[ERROR] JSON decode error — check formatting.")
        return None
    except KeyError:
        print("[ERROR] Missing key `dynamic_text` in JSON file.")
        return None
    except Exception as e:
        print(f"[ERROR] Unexpected issue: {e}")
        return None



# ============================================================
# 2. Load Vectorizer + Role TF-IDF Matrix
# ============================================================

print("\n" + "="*80)
print(" STEP 2 — LOAD VECTORIZER & ROLE TF-IDF ")
print("="*80)

VECT = pickle.load(open("pickle_file/tfidf_upd.pkl", "rb"))
role_ids, ROLE_TFIDF = pickle.load(open("pickle_file/role_tfidf_matrix_upd.pkl", "rb"))

print("[✓] Loaded tfidf_upd.pkl")
print("[✓] Loaded role_tfidf_matrix_upd.pkl")

print(f"- Number of roles  : {len(role_ids)}")
print(f"- TF-IDF matrix    : {ROLE_TFIDF.shape[0]} rows x {ROLE_TFIDF.shape[1]} features")



# ============================================================
# 3. Vectorize the User Text
# ============================================================

user_text = extract_dynamic_text("FINAL_PAYLOAD/NEW_SAMPLE_4_final_payload.json") # change path accordingly

if user_text is None:
    print("STOP: Could not read dynamic_text.")
    exit()

vec = VECT.transform([user_text])
sims = (ROLE_TFIDF @ vec.T).toarray().flatten()



# ============================================================
# 4. Show Similarity Stats
# ============================================================

print("\n" + "="*80)
print(" STEP 3 — SIMILARITY STATISTICS ")
print("="*80)

print(f"Min similarity   : {sims.min():.5f}")
print(f"Max similarity   : {sims.max():.5f}")
print(f"Mean similarity  : {sims.mean():.5f}")
print(f"Std deviation    : {sims.std():.5f}")

print("\nTop 10 Role Similarities:")
ranked = sorted(zip(sims, role_ids), reverse=True)[:10]
for score, rid in ranked:
    print(f"  {rid:<5} → {score:.5f}")



# ============================================================
# 5. Inspect Top Contributing Terms for User
# ============================================================

print("\n" + "="*80)
print(" STEP 4 — USER TOP CONTRIBUTING TERMS ")
print("="*80)

feature_names = VECT.get_feature_names_out()
user_vec = vec.toarray().flatten()

top_idx = np.argsort(user_vec)[-30:][::-1]

print("Top 30 weighted terms for THIS user:\n")
for i in top_idx:
    term = feature_names[i]
    weight = round(user_vec[i], 4)
    print(f"  {term:<25} {weight}")



# ============================================================
# 6. Compare Against a Selected Role
# ============================================================

print("\n" + "="*80)
print(" STEP 5 — ROLE PROFILE INSPECTION ")
print("="*80)

target_role = "R16" # change it accordingly, based on your expected role_id
role_i = role_ids.index(target_role)

role_vec = ROLE_TFIDF[role_i].toarray().flatten()
top_role_idx = np.argsort(role_vec)[-20:][::-1]

print(f"Top terms representing role {target_role}:\n")
for i in top_role_idx:
    print(f"  {feature_names[i]}")
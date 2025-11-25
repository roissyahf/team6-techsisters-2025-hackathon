import json
from typing import Dict, Any, List, Union, Tuple
from pathlib import Path


# -------------------------
# 0. JSON Loader
# -------------------------
def load_json_data(filepath: Union[str, Path]) -> Dict[str, Any]:
    print(f"Loading data from: {filepath}")
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


# -------------------------
# 1. Dynamic responses helpers
# -------------------------
def validate_response_completeness(data: Dict[str, Any], expected_count: int = 6) -> None:
    responses: List[Dict[str, Any]] = data.get("user_profile", {}).get("responses", [])
    if len(responses) != expected_count:
        raise ValueError(
            f"Validation Error: Expected exactly {expected_count} competency responses, but found {len(responses)}."
        )

    for i, response in enumerate(responses):
        competency = response.get("competency")
        selected_answer = response.get("selected_answer", {})
        option_key = selected_answer.get("option_key")
        answer_text = selected_answer.get("answer_text")

        if not competency:
            raise ValueError(f"Validation Error: Response {i+1} missing 'competency'.")
        if not option_key or not str(option_key).strip():
            raise ValueError(f"Validation Error: Competency '{competency}' missing/empty 'option_key'.")
        if not answer_text or not str(answer_text).strip():
            raise ValueError(f"Validation Error: Competency '{competency}' missing/empty 'answer_text'.")


def simplify_response_structure(data: Dict[str, Any]) -> Dict[str, Any]:
    raw_responses: List[Dict[str, Any]] = data.get("user_profile", {}).get("responses", [])
    simplified_answers = []

    for resp in raw_responses:
        competency = resp["competency"]
        answer = resp["selected_answer"]
        simplified_answers.append({
            "competency": competency,
            "selected_option": answer["option_key"],
            "option_text": answer["answer_text"]
        })

    return {"dynamic_answers": simplified_answers}


def build_dynamic_text(persona_summary: str, simplified_data: Dict[str, Any]) -> str:
    answer_texts = [
        str(a["option_text"]).strip()
        for a in simplified_data.get("dynamic_answers", [])
        if "option_text" in a and str(a["option_text"]).strip()
    ]
    cleaned_texts = [t.rstrip('.').rstrip(' ').strip() for t in answer_texts]
    joined_answers = ". ".join(cleaned_texts)

    persona_part = persona_summary.rstrip(".").strip() + "."

    if joined_answers:
        final_document = f"{persona_part} {joined_answers}."
    else:
        final_document = persona_part

    return final_document.strip()


# -------------------------
# 2. Base persona helpers
# -------------------------
def build_user_persona_summary(user_profile_json: Dict[str, Any]) -> str:
    responses = user_profile_json.get("user_profile", {}).get("responses", {})

    def get_answer(qkey):
        return responses.get(qkey, {}).get("answer", "").strip()

    situation = get_answer("Q1_current_status")
    interest_area = get_answer("Q4_interest_area")
    skill_level = get_answer("Q6_skill_level")
    time = get_answer("Q9_time_commitment")

    persona_summary = (
        f"The user is currently a {situation.lower()}, "
        f"interested in {interest_area.lower()}, "
        f"identifying as {skill_level.lower()}, "
        f"and can dedicate about {time.lower()} per week to learning."
    )

    return persona_summary.strip()


def build_persona_flags(data: Dict[str, Any]) -> Dict[str, bool]:
    responses = data.get('user_profile', {}).get('responses', {})

    q6_answer = responses.get('Q6_skill_level', {}).get('answer', '')
    q9_answer = responses.get('Q9_time_commitment', {}).get('answer', '')
    q1_answer = responses.get('Q1_current_status', {}).get('answer', '')
    q5_answer = responses.get('Q5_motivation', {}).get('answer', '')

    is_beginner = "beginner" in q6_answer.lower()
    is_low_time = "less than 3" in q9_answer.lower() or "less than 3 hours" in q9_answer.lower()
    is_career_break = "career" in q1_answer.lower() and ("switch" in q1_answer.lower() or "break" in q1_answer.lower())
    is_remote_only = "remote" in q5_answer.lower() or "flexibility" in q5_answer.lower()

    return {
        "beginner": is_beginner,
        "low_time": is_low_time,
        "remote_only": is_remote_only,
        "career_break": is_career_break
    }


# -------------------------
# 3. Competency mapping
# -------------------------
def mapping_competency_scores(data: Dict[str, Any]) -> Dict[str, Union[Dict[str, float], Tuple[float, ...]]]:
    responses = data.get('user_profile', {}).get('responses', [])

    option_weights = {'A': 1.0, 'B': 0.75, 'C': 0.5, 'D': 0.25}
    COMPETENCIES = ['A', 'B', 'C', 'D', 'E', 'F']

    raw_scores = {comp: 0.0 for comp in COMPETENCIES}

    for r in responses:
        comp = r.get('competency')
        opt = r.get('selected_answer', {}).get('option_key')
        weight = option_weights.get(opt, 0.0)
        if comp in raw_scores:
            raw_scores[comp] = weight

    ordered_scores = tuple(raw_scores[comp] for comp in COMPETENCIES)

    return {'raw_scores': raw_scores, 'ordered_scores': ordered_scores}


# -------------------------
# 4. Build for model
# -------------------------
def merge_for_model(base_persona_data: Dict[str, Any],
                    dynamic_questions_data: Dict[str, Any]) -> Dict[str, Any]:

    print("\n--- Starting Data Processing and Merging ---")

    user_id = base_persona_data["user_profile"]["user_id"]

    # Validation
    validate_response_completeness(dynamic_questions_data, expected_count=6)

    # Persona
    persona_flags = build_persona_flags(base_persona_data)
    persona_summary = build_user_persona_summary(base_persona_data)
    print("Base Persona Summary and Flags calculated.")

    # Dynamic
    simplified_dynamic = simplify_response_structure(dynamic_questions_data)
    dynamic_text = build_dynamic_text(persona_summary, simplified_dynamic)
    competency_scores = mapping_competency_scores(dynamic_questions_data)

    print("Dynamic Answers Simplified, Text built, and Scores mapped.")

    final_payload = {
        "user_id": user_id,
        "persona_flags": persona_flags,
        "persona_summary": persona_summary,
        "aptitude_vector": competency_scores["ordered_scores"],
        "dynamic_answers": simplified_dynamic,
        "dynamic_text": dynamic_text
    }

    print(f"--- Payload for User ID: {user_id} successfully created. ---")
    return final_payload

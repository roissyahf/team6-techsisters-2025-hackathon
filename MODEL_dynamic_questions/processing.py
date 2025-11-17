import json
import argparse
import os
from typing import Dict, Any, List, Union, Tuple

# --- Helper Function for File Loading ---

def load_json_data(filepath: str) -> Dict[str, Any]:
    """Loads and returns JSON data from a given filepath."""
    print(f"Loading data from: {filepath}")
    try:
        with open(filepath, 'r') as file:
            data = json.load(file)
        return data
    except FileNotFoundError:
        raise FileNotFoundError(f"Error: The file '{filepath}' was not found.")
    except json.JSONDecodeError:
        raise json.JSONDecodeError(f"Error: Could not decode JSON from '{filepath}'. Check file format.")
    except Exception as e:
        raise Exception(f"An unexpected error occurred while loading '{filepath}': {e}")


# =====================================================================
# --- 1. Functions from build_answer_dynamic_questions.py ---
# =====================================================================

def validate_response_completeness(data: Dict[str, Any], expected_count: int = 6) -> None:
    """
    Validates the raw input JSON structure for dynamic competency responses.
    This logic is retained but not strictly needed for merge_for_model 
    if the input is guaranteed to be clean, but kept for safety.
    """
    # print(f"\n--- 1. Validating Response Completeness (Expecting {expected_count} answers) ---")
    
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
            raise ValueError(f"Validation Error: Response {i+1} is missing the 'competency' key.")
        if not option_key or not str(option_key).strip():
            raise ValueError(f"Validation Error: Competency '{competency}' is missing or has an empty 'option_key'.")
        if not answer_text or not str(answer_text).strip():
            raise ValueError(f"Validation Error: Competency '{competency}' is missing or has an empty 'answer_text'.")

    # print(f"Validation Successful: Found all {expected_count} required competency responses with necessary data.")


def simplify_response_structure(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transforms the complex JSON input (dynamic answers) into a simplified 
    structure for the final payload.
    """
    # print("\n--- 2. Simplifying Data Structure ---")
    raw_responses: List[Dict[str, Any]] = data.get("user_profile", {}).get("responses", [])

    simplified_answers = []
    for resp in raw_responses:
        # Extract required fields from the nested structure
        competency = resp["competency"]
        answer = resp["selected_answer"]

        simplified_answers.append({
            "competency": competency,
            "selected_option": answer["option_key"],
            "option_text": answer["answer_text"] 
        })

    simplified_data = {"dynamic_answers": simplified_answers}
    # print("Simplified structure created successfully.")
    return simplified_data


def build_dynamic_text(persona_summary: str, simplified_data: Dict[str, Any]) -> str:
    """
    Concatenates a persona summary with all chosen option_texts.
    """
    # print("\n--- 3. Building Final Document Text ---")

    answer_texts = [
        str(a["option_text"]).strip() 
        for a in simplified_data.get("dynamic_answers", []) 
        if "option_text" in a and str(a["option_text"]).strip()
    ]
    
    cleaned_texts = [t.rstrip('.').rstrip(' ').strip() for t in answer_texts]
    joined_answers = ". ".join(cleaned_texts)
    
    # Ensure the persona part ends with a period
    persona_part = persona_summary.rstrip(".").strip() + "."
    
    # Combine the two parts
    if joined_answers:
        final_document = f"{persona_part} {joined_answers}."
    else:
        final_document = persona_part
        
    # print("Document built successfully.")
    return final_document.strip()


# =====================================================================
# --- 2. Functions from build_base_persona.py ---
# =====================================================================

def build_user_persona_summary(user_profile_json: Dict[str, Any]) -> str:
    """
    Use base Q1, Q4, Q6, Q9 to Build user persona summary.
    """
    responses = user_profile_json.get("user_profile", {}).get("responses", {})

    situation = responses.get("Q1_current_status", {}).get("answer", "Unknown status")
    interest_area = responses.get("Q4_interest_area", {}).get("answer", "general interest in tech")
    skill_level = responses.get("Q6_skill_level", {}).get("answer", "beginner level")
    time = responses.get("Q9_time_commitment", {}).get("answer", "a few hours")

    persona_summary = (
        f"The user is currently a {situation.lower()}, "
        f"interested in {interest_area.lower()}, "
        f"identifying as {skill_level.lower()}, "
        f"and can dedicate about {time.lower()} per week to learning."
    )

    return persona_summary.strip()


def build_pesona_flags(data: Dict[str, Any]) -> Dict[str, bool]:
    """
    Calculates persona flags based on base questions response answers.
    """
    
    responses = data.get('user_profile', {}).get('responses', {})
    
    # 1. Beginner Flag (based on Q6: skill_level)
    q6_answer = responses.get('Q6_skill_level', {}).get('answer', '')
    is_beginner = q6_answer == "Beginner (I have little or no practical experience)"

    # 2. Low Time Flag (based on Q9: time_commitment)
    q9_answer = responses.get('Q9_time_commitment', {}).get('answer', '')
    is_low_time = q9_answer == "Less than 3 hours"

    # 3. Career Break Flag (based on Q1: current_status)
    q1_answer = responses.get('Q1_current_status', {}).get('answer', '')
    is_career_break = q1_answer == "Career Switcher"

    # 4. Remote Only Flag (based on Q5: motivation)
    q5_answer = responses.get('Q5_motivation', {}).get('answer', '')
    is_remote_only = q5_answer == "Flexibility / Remote work"

    return {
        "beginner": is_beginner,
        "low_time": is_low_time,
        "remote_only": is_remote_only,
        "career_break": is_career_break
    }


# =====================================================================
# --- 3. Functions from competency_score_mapping.py ---
# =====================================================================

def mapping_competency_scores(data: Dict[str, Any]) -> Dict[str, Union[Dict[str, float], Tuple[float, ...]]]:
    """
    Directly converts dynamic competency answers to single weighted scores.
    """
    
    full_data = data # Input is expected to be the parsed dict
    try:
        responses = full_data['user_profile']['responses']
    except KeyError:
        # Returning defaults if structure is missing, as per original logic's guard
        return {'raw_scores': {}, 'ordered_scores': tuple()}

    # Setup
    option_weights = {'A': 1.0, 'B': 0.75, 'C': 0.5, 'D': 0.25}
    COMPETENCIES = ['A', 'B', 'C', 'D', 'E', 'F']
    
    raw_scores: Dict[str, float] = {comp: 0.0 for comp in COMPETENCIES} # Initialize with 0.0 for unanswered

    # Assign single weighted score per response
    for r in responses:
        comp = r.get('competency')
        opt = r.get('selected_answer', {}).get('option_key') 
        
        weight = option_weights.get(opt, 0.0) 
        
        if comp in raw_scores:
            raw_scores[comp] = weight

    # Generate the ordered tuple
    ordered_scores = tuple(raw_scores[comp] for comp in COMPETENCIES)
    
    return {
        'raw_scores': raw_scores,
        'ordered_scores': ordered_scores
    }


# =====================================================================
# --- 4. Main Merging Logic ---
# =====================================================================

def merge_for_model(base_persona_data: Dict[str, Any], dynamic_questions_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Combines and processes data from base and dynamic questions into the final payload structure.
    """
    print("\n--- Starting Data Processing and Merging ---")
    
    # Ensure all required inputs are present before proceeding
    if "user_profile" not in base_persona_data or "user_id" not in base_persona_data["user_profile"]:
        raise KeyError("Base persona data is missing 'user_profile' or 'user_id'. Cannot proceed.")

    user_id = base_persona_data["user_profile"]["user_id"]
    
    # 1. Base Persona Calculations
    persona_flags = build_pesona_flags(base_persona_data)
    persona_summary = build_user_persona_summary(base_persona_data)
    print("✅ Base Persona Summary and Flags calculated.")

    # 2. Dynamic Answers Processing
    simplify_dynamic_response = simplify_response_structure(dynamic_questions_data)
    dynamic_text = build_dynamic_text(persona_summary, simplify_dynamic_response)
    competency_scores = mapping_competency_scores(dynamic_questions_data)
    print("✅ Dynamic Answers Simplified, Text built, and Scores mapped.")
    
    # 3. Final Payload Construction
    final_payload = {
        "user_id": user_id,
        "persona_flags": persona_flags,
        "persona_summary": persona_summary,
        "aptitude_vector": competency_scores["ordered_scores"],
        "dynamic_answers": simplify_dynamic_response,
        "dynamic_text": dynamic_text
    }
    
    print(f"--- Payload for User ID: {user_id} successfully created. ---")
    return final_payload

# =====================================================================
# --- 5. Main Execution Block (with Argument Parsing) ---
# =====================================================================

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Builds the final AI model payload by merging user profile data and dynamic answers."
    )
    
    # Required inputs for processing
    parser.add_argument(
        '--base', 
        type=str, 
        required=True, 
        default="base_questions/sample.json",
        help="Path to the JSON file containing base user persona answers (Q1, Q4, Q6, Q9, etc.)."
    )
    parser.add_argument(
        '--dynamic', 
        type=str, 
        required=True,
        default="ANSWER_RESPONSE_dynamic_questions/SAMPLE_answer_dynamic_questions.json",
        help="Path to the JSON file containing dynamic competency answers (A-F)."
    )
    
    # Static data files
    parser.add_argument(
        '--roles', 
        type=str, 
        default="static_data/roles.json",
        help="Path to the static roles JSON file (Optional: for context)."
    )
    parser.add_argument(
        '--descriptions', 
        type=str, 
        default="static_data/descriptions.json",
        help="Path to the static descriptions JSON file (Optional: for context)."
    )
    parser.add_argument(
        '--constraints', 
        type=str, 
        default="static_data/constraints.json",
        help="Path to the static constraints JSON file (Optional: for context)."
    )

    # Output file
    parser.add_argument(
        '--output', 
        type=str, 
        default="FINAL_PAYLOAD/SAMPLE_final_payload.json",
        help="Path to save the resulting final payload JSON file."
    )
    
    args = parser.parse_args()
    
    try:
        # 0. Load Data
        base_persona_data = load_json_data(args.base)
        dynamic_questions_data = load_json_data(args.dynamic)
        
        # 1. Merge data for model
        final_json = merge_for_model(base_persona_data, dynamic_questions_data)

        # 2. Output final JSON
        output_dir = os.path.dirname(args.output)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
            print(f"Created output directory: {output_dir}")

        with open(args.output, 'w') as f:
            json.dump(final_json, f, indent=4)
        
        print(f"\n✨ Final payload successfully written to {args.output} ✨")

    except (FileNotFoundError, json.JSONDecodeError, KeyError, ValueError) as e:
        print(f"\nFATAL ERROR: {e}")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
from pydantic import BaseModel, ValidationError
from typing import List, Optional, Dict, Any
from datetime import date


class CourseItem(BaseModel):
    name: str
    platform: Optional[str] = None
    duration_weeks: Optional[int] = None
    skill_focus: Optional[List[str]] = None
    difficulty: Optional[str] = None


class SelectedRoleRaw(BaseModel):
    # Accept flexible shape but require role_id and role_name when available
    role_id: Optional[str]
    role_name: Optional[str]
    score: Optional[float] = None
    explanation: Optional[str] = None


class PersonaFlat(BaseModel):
    Q1_current_status: str
    Q2_tech_familiarity: str
    Q3_tech_experience: str
    Q4_interest_area: str
    Q5_motivation: str
    Q6_skill_level: str
    Q7_project_experience: str
    Q8_learning_preference: str
    Q9_time_commitment: str
    Q10_goal: str


class Constraints(BaseModel):
    availability: Optional[str] = None
    learning_pace: Optional[str] = None
    difficulty: Optional[str] = None
    project_requirements: Optional[str] = None
    format_preference: Optional[str] = None


class ActionPlanRequest(BaseModel):
    persona: PersonaFlat
    selected_role: SelectedRoleRaw
    course_recommendations: List[CourseItem] = []
    weekly_commitment: str
    preferred_learning_format: Optional[str] = None
    start_date: Optional[date] = None
    constraints: Optional[Constraints] = None


def _safe_get_answer(responses: Dict[str, Any], key: str, default: str = "") -> str:
    return responses.get(key, {}).get("answer") or responses.get(key, {}).get("value") or default


def infer_constraints_from_persona(responses: Dict[str, Any]) -> Constraints:
    # Weekly commitment
    qc = _safe_get_answer(responses, "Q9_time_commitment", "")
    if "Less than" in qc or "<" in qc or "less than" in qc.lower():
        learning_pace = "Very limited weekly learning time — use micro-learning format"
    elif "3" in qc and "6" in qc or "3-6" in qc or "3-6" in qc:
        learning_pace = "Moderate schedule — learning pace must be kept realistic"
    elif "7" in qc and "10" in qc or "7-10" in qc or "7-10" in qc:
        learning_pace = "Strong commitment — can follow standard 6-month pacing"
    elif "10" in qc or "+" in qc or ">" in qc:
        learning_pace = "High availability — can accelerate or take optional advanced tracks"
    else:
        learning_pace = "Moderate schedule — learning pace must be kept realistic"

    # Availability
    status = _safe_get_answer(responses, "Q1_current_status", "").lower()
    if "student" in status:
        availability = "May have irregular availability due to academic load"
    elif "job seeker" in status:
        availability = "Can dedicate flexible time to learning"
    elif "working professional (non-tech)" in status or "non-tech" in status.lower():
        availability = "Limited weekday availability; plan around after-work hours"
    elif "working professional (tech)" in status or "tech" in status.lower():
        availability = "May already have some foundational skills; handle hybrid learning"
    elif "career switcher" in status:
        availability = "Needs structured roadmap and portfolio focus"
    else:
        availability = "Typical availability — adjust as needed"

    # Format preference
    pref = _safe_get_answer(responses, "Q8_learning_preference", "")
    if "online" in pref.lower() or "courses" in pref.lower():
        format_pref = "Prioritize structured video-based courses"
    elif "bootcamp" in pref.lower():
        format_pref = "User prefers intensive learning formats"
    elif "self" in pref.lower():
        format_pref = "User prefers flexible, self-paced materials"
    elif "mentorship" in pref.lower() or "group" in pref.lower():
        format_pref = "Should include interactive or community-based learning"
    else:
        format_pref = "Flexible — mix of formats"

    # Difficulty from skill level
    skill = _safe_get_answer(responses, "Q6_skill_level", "").lower()
    if "beginner" in skill:
        difficulty = "Avoid overly advanced content in early milestones"
    elif "intermediate" in skill:
        difficulty = "Can take intermediate-level exercises early on"
    elif "expert" in skill:
        difficulty = "Skip basics unless required for the role change"
    else:
        difficulty = "Start with foundational content, adjust if needed"

    # Project requirements
    tech_exp = _safe_get_answer(responses, "Q3_tech_experience", "").lower()
    proj_exp = _safe_get_answer(responses, "Q7_project_experience", "").lower()
    if ("no" in tech_exp and "no" in proj_exp) or (tech_exp == "" and proj_exp == ""):
        project_requirements = "Needs introductory guided projects"
    elif "small" in proj_exp or "some" in tech_exp:
        project_requirements = "Increase project complexity gradually"
    else:
        project_requirements = "Requires capstone-level projects"

    return Constraints(
        availability=availability,
        learning_pace=learning_pace,
        difficulty=difficulty,
        project_requirements=project_requirements,
        format_preference=format_pref,
    )


def flatten_persona(persona_json: Dict[str, Any]) -> PersonaFlat:
    # Expecting structure like: { "user_profile": { "responses": { "Q1_current_status": {"answer": "..."}, ... }}}
    responses = persona_json.get("user_profile", {}).get("responses", {})

    flat = {
        "Q1_current_status": _safe_get_answer(responses, "Q1_current_status", "Unknown"),
        "Q2_tech_familiarity": _safe_get_answer(responses, "Q2_tech_familiarity", "Unknown"),
        "Q3_tech_experience": _safe_get_answer(responses, "Q3_tech_experience", "No"),
        "Q4_interest_area": _safe_get_answer(responses, "Q4_interest_area", "General"),
        "Q5_motivation": _safe_get_answer(responses, "Q5_motivation", "Career growth"),
        "Q6_skill_level": _safe_get_answer(responses, "Q6_skill_level", "Beginner"),
        "Q7_project_experience": _safe_get_answer(responses, "Q7_project_experience", "No"),
        "Q8_learning_preference": _safe_get_answer(responses, "Q8_learning_preference", "Online courses"),
        "Q9_time_commitment": _safe_get_answer(responses, "Q9_time_commitment", "3-6 hours"),
        "Q10_goal": _safe_get_answer(responses, "Q10_goal", "Explore tech careers"),
    }

    return PersonaFlat(**flat)


def normalize_selected_role(selected_role_json: Dict[str, Any]) -> SelectedRoleRaw:
    if isinstance(selected_role_json, dict):
        role_id = selected_role_json.get("role_id") or selected_role_json.get("id") or selected_role_json.get("role")
        role_name = selected_role_json.get("role_name") or selected_role_json.get("name")
        score = selected_role_json.get("score")
        explanation = selected_role_json.get("explanation")
        return SelectedRoleRaw(role_id=role_id, role_name=role_name, score=score, explanation=explanation)
    else:
        raise ValidationError([{"loc": ("selected_role_json",), "msg": "Invalid selected role format", "type": "type_error"}], SelectedRoleRaw)


def normalize_courses(course_list_json: Optional[List[Dict[str, Any]]]) -> List[CourseItem]:
    out = []
    if not course_list_json:
        return out
    for c in course_list_json:
        try:
            out.append(CourseItem(**c))
        except ValidationError:
            name = c.get("name") or c.get("title") or "Unnamed Course"
            out.append(CourseItem(name=name))
    return out


def process_inputs(persona_json: Dict[str, Any], selected_role_json: Dict[str, Any], course_recommendations_json: Optional[List[Dict[str, Any]]] = None) -> ActionPlanRequest:
    # Flatten persona
    persona_flat = flatten_persona(persona_json)

    # Normalize role
    selected_role = normalize_selected_role(selected_role_json)

    # Normalize courses
    courses = normalize_courses(course_recommendations_json)

    # Infer constraints
    responses = persona_json.get("user_profile", {}).get("responses", {})
    constraints = infer_constraints_from_persona(responses)

    # Use persona's weekly commitment and learning pref
    weekly_commitment = persona_flat.Q9_time_commitment
    preferred_format = persona_flat.Q8_learning_preference

    # If role does not contain id/name, raise
    if not selected_role.role_id or not selected_role.role_name:
        raise ValidationError([{"loc": ("selected_role",), "msg": "selected role must contain role_id and role_name", "type": "value_error"}], SelectedRoleRaw)

    req = ActionPlanRequest(
        persona=persona_flat,
        selected_role=selected_role,
        course_recommendations=courses,
        weekly_commitment=weekly_commitment,
        preferred_learning_format=preferred_format,
        start_date=None,
        constraints=constraints,
    )

    return req
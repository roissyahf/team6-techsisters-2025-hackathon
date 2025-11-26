from pydantic import BaseModel, ValidationError
from typing import List, Optional, Dict, Any
from datetime import date


class CourseItem(BaseModel):
    name: str
    platform: Optional[str] = None
    duration_weeks: Optional[int] = None
    skill_focus: Optional[List[str]] = None
    difficulty: Optional[str] = None
    rating: Optional[float] = None
    review_count: Optional[int] = None


class SelectedRoleRaw(BaseModel):
    role_id: Optional[str] = None
    role_name: str
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
    """
    Handles both model output formats:
    - Model 1: {role_id, role_name, score, explanation}
    - Model 2: {role_name, score}
    
    Expects the SELECTED role only (single object), not the full array of recommendations
    """
    if isinstance(selected_role_json, dict):
        # Extract fields with fallbacks
        role_id = selected_role_json.get("role_id") or selected_role_json.get("id") or selected_role_json.get("role")
        role_name = selected_role_json.get("role_name") or selected_role_json.get("name")
        score = selected_role_json.get("score")
        explanation = selected_role_json.get("explanation")
        
        # Validate role_name is present
        if not role_name:
            raise ValidationError([{"loc": ("role_name",), "msg": "role_name is required", "type": "value_error"}], SelectedRoleRaw)
        
        return SelectedRoleRaw(role_id=role_id, role_name=role_name, score=score, explanation=explanation)
    else:
        raise ValidationError([{"loc": ("selected_role_json",), "msg": "Invalid selected role format", "type": "type_error"}], SelectedRoleRaw)


def parse_skills_string(skills_str: Optional[str]) -> List[str]:
    """
    Parse PostgreSQL array string format like '{"skill1","skill2","skill3"}'
    Returns a list of skills
    """
    if not skills_str:
        return []
    
    # Remove curly braces and quotes
    skills_str = skills_str.strip()
    if skills_str.startswith('{') and skills_str.endswith('}'):
        skills_str = skills_str[1:-1]
    
    # Split by comma and clean each skill
    skills = [skill.strip().strip('"').strip() for skill in skills_str.split(',')]
    return [s for s in skills if s]  # Remove empty strings


def parse_duration_to_weeks(duration_str: Optional[str]) -> Optional[int]:
    """
    Parse duration strings like '1 - 3 Months', '1 - 4 Weeks' to estimated weeks
    Returns approximate midpoint in weeks
    """
    if not duration_str:
        return None
    
    duration_str = duration_str.strip().lower()
    
    # Extract numbers
    import re
    numbers = re.findall(r'\d+', duration_str)
    
    if not numbers:
        return None
    
    # Calculate midpoint
    if len(numbers) >= 2:
        start = int(numbers[0])
        end = int(numbers[1])
        avg = (start + end) / 2
    else:
        avg = int(numbers[0])
    
    # Convert to weeks
    if 'month' in duration_str:
        return int(avg * 4)  # Approximate weeks per month
    elif 'week' in duration_str:
        return int(avg)
    else:
        return None


def normalize_courses(course_list_json: Optional[Dict[str, Any]]) -> List[CourseItem]:
    """
    Handles the new course recommendation format:
    {
        "role": "Software Engineer",
        "keywords_used": [...],
        "courses": [
            {
                "course_title": "...",
                "platform": "...",
                "skills": "{\"skill1\",\"skill2\"}",
                "rating": 4.9,
                "reviewcount": 952,
                "level": "beginner",
                "duration": "1 - 3 Months",
                "certificatetype": "Course",
                "crediteligibility": false
            }
        ]
    }
    """
    out = []
    
    if not course_list_json:
        return out
    
    # Extract the courses array
    courses_array = course_list_json.get("courses", [])
    
    if not courses_array:
        return out
    
    for c in courses_array:
        try:
            # Map new structure to CourseItem
            name = c.get("course_title") or c.get("name") or "Unnamed Course"
            platform = c.get("platform")
            
            # Parse skills from PostgreSQL array format
            skills_raw = c.get("skills")
            skill_focus = parse_skills_string(skills_raw)
            
            # Parse duration to weeks
            duration_str = c.get("duration")
            duration_weeks = parse_duration_to_weeks(duration_str)
            
            # Map level to difficulty
            level = c.get("level", "").strip().lower()
            if level:
                difficulty = level.capitalize()
            else:
                difficulty = None
            
            # Extract rating and review count
            rating = c.get("rating")
            review_count = c.get("reviewcount")
            
            out.append(CourseItem(
                name=name,
                platform=platform,
                duration_weeks=duration_weeks,
                skill_focus=skill_focus,
                difficulty=difficulty,
                rating=rating,
                review_count=review_count
            ))
        except Exception as e:
            # Fallback: add with minimal info
            print(f"Warning: Could not fully parse course: {e}")
            name = c.get("course_title") or c.get("name") or "Unnamed Course"
            out.append(CourseItem(name=name))
    
    return out


def process_inputs(persona_json: Dict[str, Any], selected_role_json: Dict[str, Any], course_recommendations_json: Optional[Dict[str, Any]] = None) -> ActionPlanRequest:
    """
    Main processing function that handles all input transformations
    
    Args:
        persona_json: User profile with base questions responses
        selected_role_json: SINGLE selected role object (from either model 1 or model 2)
        course_recommendations_json: Course recommendations in new format with nested structure
    
    Returns:
        ActionPlanRequest: Validated and normalized payload ready for LLM
    """
    # Flatten persona
    persona_flat = flatten_persona(persona_json)

    # Normalize role (handles both model formats)
    selected_role = normalize_selected_role(selected_role_json)

    # Normalize courses (handles new nested format)
    courses = normalize_courses(course_recommendations_json)

    # Infer constraints
    responses = persona_json.get("user_profile", {}).get("responses", {})
    constraints = infer_constraints_from_persona(responses)

    # Use persona's weekly commitment and learning pref
    weekly_commitment = persona_flat.Q9_time_commitment
    preferred_format = persona_flat.Q8_learning_preference

    # Validate role has name
    if not selected_role.role_name:
        raise ValidationError([{"loc": ("selected_role",), "msg": "selected role must contain role_name", "type": "value_error"}], SelectedRoleRaw)

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